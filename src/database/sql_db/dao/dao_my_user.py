from database.sql_db.entity.table_my_user import MyUser
from database.sql_db.conn import db
from common.utilities.util_logger import Log

from typing import Optional, List, Union, Dict, Any
from datetime import datetime
import hashlib
from peewee import DoesNotExist, IntegrityError

logger = Log.get_logger(__name__)

# Note: MyUser model does not have an explicit 'user_status' field.
# Functions that previously handled user status (e.g., exclude_disabled)
# will assume users are always active or this logic needs to be implemented
# differently (e.g., using the 'spare' field or by adding a status field).

# Assumption: MyBaseModel (and its parent BaseModel) provides the following audit fields:
# create_by: CharField
# create_datetime: DateTimeField
# update_by: CharField
# update_datetime: DateTimeField
# If not, the parts of the code using these fields will need adjustment.

def exists_my_user_phone(phone: str) -> bool:
    """
    Checks if a user with the given phone number exists in MyUser.
    """
    try:
        MyUser.get(MyUser.phone == phone)
        return True
    except DoesNotExist:
        return False

def my_user_password_verify(phone: str, password_plain: str) -> bool:
    """
    Password校验 for MyUser using phone number.
    Assumes MyUser has 'phone' and 'password' (hashed) fields.
    Note: Does not check for user status as MyUser model lacks an explicit status field.
    """
    if not password_plain:
        return False
    password_sha256_to_check = hashlib.sha256(password_plain.encode('utf-8')).hexdigest()
    try:
        MyUser.get(
            (MyUser.phone == phone) &
            (MyUser.password == password_sha256_to_check)
        )
        # If a status field were available, e.g., MyUser.status == USER_STATUS_ENABLED,
        # it would be checked here.
        return True
    except DoesNotExist:
        return False

def create_my_user(
    phone: str,
    nickname: str,
    password_plain: str,
    email: str,
    gender: Optional[int] = 0,
    img_url: Optional[str] = 'https://tse1-mm.cn.bing.net/th/id/OIP-C.3dLZ4NXxxg03pzV30ITasAAAAA?rs=1&pid=ImgDetMain',
    spare: Optional[str] = None,
    created_by: Optional[str] = "system",
) -> Optional[MyUser]:
    """
    Creates a new user in MyUser.
    'phone', 'nickname', 'password_plain', 'email' are required.
    Audit fields (create_by, create_datetime, update_by, update_datetime) are assumed
    to be handled by MyBaseModel or set here if available.
    Returns the created MyUser instance or None on failure.
    """
    if not all([phone, nickname, password_plain, email]):
        logger.warning("MyUser creation: Phone, nickname, password, and email cannot be empty.")
        return None

    hashed_password = hashlib.sha256(password_plain.strip().encode('utf-8')).hexdigest()
    current_time = datetime.now()

    my_user_data = {
        'phone': phone,
        'nickname': nickname,
        'password': hashed_password,
        'email': email,
        'gender': gender,
        'img_url': img_url,
        'spare': spare,
    }

    # Add audit fields if they are part of MyUser directly or settable
    # If MyBaseModel handles them automatically, these lines might not be needed
    # or should be adapted based on BaseModel's behavior.
    if hasattr(MyUser, 'create_by'):
        my_user_data['create_by'] = created_by
    if hasattr(MyUser, 'create_datetime'):
        my_user_data['create_datetime'] = current_time
    if hasattr(MyUser, 'update_by'):
        my_user_data['update_by'] = created_by # Initially, creator is also the last updater
    if hasattr(MyUser, 'update_datetime'):
        my_user_data['update_datetime'] = current_time

    database = db()
    with database.atomic() as txn:
        try:
            user = MyUser.create(**my_user_data)
            txn.commit()
            logger.info(f'MyUser {phone} ({nickname}) created successfully by {created_by}.')
            return user
        except IntegrityError as e:
            logger.warning(f'Operator {created_by} adding MyUser {phone} failed due to IntegrityError: {e}', exc_info=True)
            txn.rollback()
            return None
        except Exception as e:
            logger.error(f'Operator {created_by} adding MyUser {phone} failed: {e}', exc_info=True)
            txn.rollback()
            return None

def get_my_user_by_phone(phone: str) -> Optional[MyUser]:
    """
    Retrieves a single MyUser by phone number.
    """
    try:
        return MyUser.get(MyUser.phone == phone)
    except DoesNotExist:
        return None
    except Exception as e:
        logger.error(f"Error fetching MyUser by phone {phone}: {e}", exc_info=True)
        return None

def get_my_user_by_id(user_id: int) -> Optional[MyUser]:
    """
    Retrieves a single MyUser by user_id (primary key).
    """
    try:
        return MyUser.get(MyUser.user_id == user_id)
    except DoesNotExist:
        return None
    except Exception as e:
        logger.error(f"Error fetching MyUser by ID {user_id}: {e}", exc_info=True)
        return None

def get_all_my_users() -> List[MyUser]:
    """
    Retrieves all users from MyUser.
    Note: MyUser model does not have an explicit status field,
    so filtering by status (e.g., exclude_disabled) is not implemented here.
    """
    try:
        return list(MyUser.select())
    except Exception as e:
        logger.error(f"Error fetching all MyUsers: {e}", exc_info=True)
        return []

def _get_my_user_for_update(identifier: Union[str, int]) -> Optional[MyUser]:
    """Helper to get user by phone (str) or user_id (int)."""
    if isinstance(identifier, str): # Assumed to be phone
        return get_my_user_by_phone(identifier)
    elif isinstance(identifier, int): # Assumed to be user_id
        return get_my_user_by_id(identifier)
    logger.warning(f"Invalid identifier type for fetching MyUser: {type(identifier)}")
    return None


def update_my_user(
    identifier: Union[str, int], # phone (str) or user_id (int)
    updated_by: Optional[str] = "system",
    **fields_to_update: Any
) -> bool:
    """
    Updates MyUser information.
    'identifier' can be the user's phone (str) or user_id (int).
    Use keyword arguments for fields to update (e.g., nickname='New Nick', email='new@example.com').
    If 'password_plain' is in fields_to_update, it will be hashed and stored in 'password'.
    Audit fields 'update_by' and 'update_datetime' are automatically updated if available in the model.
    """
    database = db()
    with database.atomic() as txn:
        try:
            user = _get_my_user_for_update(identifier)
            if not user:
                logger.warning(f'MyUser with identifier {identifier} not found, cannot update.')
                return False

            for field, value in fields_to_update.items():
                if field == 'password_plain':
                    if value: # Only update password if a new one is provided
                        hashed_password = hashlib.sha256(str(value).strip().encode('utf-8')).hexdigest()
                        user.password = hashed_password
                    # else: do nothing if password_plain is empty or None
                elif hasattr(user, field):
                    setattr(user, field, value)
                else:
                    logger.warning(f"MyUser model does not have field '{field}' for user {identifier}. Skipping update for this field.")
            
            if hasattr(user, 'update_by'):
                user.update_by = updated_by
            if hasattr(user, 'update_datetime'):
                user.update_datetime = datetime.now()
            
            user.save()
            txn.commit()
            logger.info(f'MyUser {identifier} updated successfully by {updated_by}.')
            return True

        except Exception as e: # Catches DoesNotExist from _get_my_user_for_update if not handled before
            logger.error(f'Operator {updated_by} updating MyUser {identifier} failed: {e}', exc_info=True)
            txn.rollback()
            return False

def delete_my_user(identifier: Union[str, int], deleted_by: Optional[str] = "system") -> bool:
    """
    Deletes a user from MyUser by phone (str) or user_id (int).
    Logs the operator performing the deletion.
    """
    database = db()
    with database.atomic() as txn:
        try:
            user_to_delete = _get_my_user_for_update(identifier)
            if not user_to_delete:
                logger.warning(f'MyUser with identifier {identifier} not found for deletion by {deleted_by}.')
                return False # Or True if idempotent deletion is preferred

            deleted_rows = MyUser.delete().where(MyUser.user_id == user_to_delete.user_id).execute()
            # Alternative: user_to_delete.delete_instance() if you have the instance

            if deleted_rows == 0: # Should not happen if user_to_delete was found
                logger.warning(f'MyUser {identifier} (ID: {user_to_delete.user_id}) found but not deleted by query, by {deleted_by}.')
                txn.rollback()
                return False
            
            txn.commit()
            logger.info(f'MyUser {identifier} (ID: {user_to_delete.user_id}) deleted successfully by {deleted_by}.')
            return True
        except Exception as e:
            logger.error(f'Operator {deleted_by} deleting MyUser {identifier} failed: {e}', exc_info=True)
            txn.rollback()
            return False

# --- Specific field update functions ---

def _update_my_user_single_field(identifier: Union[str, int], field_name: str, value: Any, updated_by: Optional[str] = "system") -> bool:
    """
    Internal helper: Updates a single field for a MyUser.
    'identifier' can be phone (str) or user_id (int).
    """
    if not hasattr(MyUser, field_name):
        logger.error(f"MyUser model does not have field '{field_name}'. Cannot update.")
        return False
        
    update_dict = {field_name: value}
    return update_my_user(identifier, updated_by=updated_by, **update_dict)

def update_my_user_nickname(identifier: Union[str, int], nickname: str, updated_by: Optional[str] = "system") -> bool:
    """Updates MyUser's nickname."""
    return _update_my_user_single_field(identifier, 'nickname', nickname, updated_by)

def update_my_user_email(identifier: Union[str, int], email: str, updated_by: Optional[str] = "system") -> bool:
    """Updates MyUser's email."""
    return _update_my_user_single_field(identifier, 'email', email, updated_by)

def update_my_user_gender(identifier: Union[str, int], gender: int, updated_by: Optional[str] = "system") -> bool:
    """Updates MyUser's gender."""
    return _update_my_user_single_field(identifier, 'gender', gender, updated_by)

def update_my_user_img_url(identifier: Union[str, int], img_url: str, updated_by: Optional[str] = "system") -> bool:
    """Updates MyUser's image URL."""
    return _update_my_user_single_field(identifier, 'img_url', img_url, updated_by)

def update_my_user_spare(identifier: Union[str, int], spare: Optional[str], updated_by: Optional[str] = "system") -> bool:
    """Updates MyUser's spare field."""
    return _update_my_user_single_field(identifier, 'spare', spare, updated_by)

def update_my_user_password(
    phone: str, # Password updates should primarily use phone for verification
    new_password_plain: str,
    updated_by: Optional[str] = "system",
    old_password_plain: Optional[str] = None
) -> bool:
    """
    Updates MyUser's password. Uses 'phone' for identification.
    If old_password_plain is provided, it's verified first.
    """
    if old_password_plain:
        if not my_user_password_verify(phone, old_password_plain):
            logger.warning(f"Old password verification failed for MyUser {phone} during password update.")
            return False
            
    if not new_password_plain.strip():
        logger.warning("New password cannot be empty for MyUser password update.")
        return False
    
    # The update_my_user function handles hashing 'password_plain'
    return update_my_user(phone, updated_by=updated_by, password_plain=new_password_plain)
