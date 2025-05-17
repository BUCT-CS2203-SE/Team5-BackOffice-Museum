from database.sql_db.entity.table_my_user import MyUser
from database.sql_db.conn import db
from common.utilities.util_logger import Log

from typing import Optional, List, Union, Dict, Any
from datetime import datetime
import hashlib
from peewee import DoesNotExist, IntegrityError

logger = Log.get_logger(__name__)

# 注意：MyUser 模型没有显式的 'user_status' 字段。
# 之前处理用户状态的函数（例如 exclude_disabled）
# 将假设用户始终处于活动状态，或者需要以不同的方式实现此逻辑
# （例如，使用 'spare' 字段或添加一个状态字段）。

# 假设：MyBaseModel（及其父类 BaseModel）提供以下审计字段：
# create_by: CharField
# create_datetime: DateTimeField
# update_by: CharField
# update_datetime: DateTimeField
# 如果没有，则需要调整使用这些字段的代码部分。

def exists_my_user_phone(phone: str) -> bool:
    """
    检查 MyUser 中是否存在具有给定电话号码的用户。
    """
    try:
        MyUser.get(MyUser.phone == phone)
        return True
    except DoesNotExist:
        return False

def my_user_password_verify(phone: str, password_plain: str) -> bool:
    """
    使用电话号码校验 MyUser 的密码。
    假设 MyUser 具有 'phone' 和 'password'（哈希）字段。
    注意：由于 MyUser 模型缺少显式的状态字段，因此不会检查用户状态。
    """
    if not password_plain:
        return False
    password_sha256_to_check = hashlib.sha256(password_plain.encode('utf-8')).hexdigest()
    try:
        MyUser.get(
            (MyUser.phone == phone) &
            (MyUser.password == password_sha256_to_check)
        )
        # 如果有状态字段，例如 MyUser.status == USER_STATUS_ENABLED，
        # 应在此处进行检查。
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
    在 MyUser 中创建一个新用户。
    'phone'、'nickname'、'password_plain'、'email' 是必填项。
    假设审计字段（create_by、create_datetime、update_by、update_datetime）
    由 MyBaseModel 处理，或者如果可用，则在此处设置。
    返回创建的 MyUser 实例，失败时返回 None。
    """
    if not all([phone, nickname, password_plain, email]):
        logger.warning("MyUser 创建：电话号码、昵称、密码和电子邮件不能为空。")
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

    # 如果审计字段是 MyUser 的一部分或可设置，则添加审计字段
    # 如果 MyBaseModel 自动处理这些字段，则可能不需要这些行
    # 或者应根据 BaseModel 的行为进行调整。
    if hasattr(MyUser, 'create_by'):
        my_user_data['create_by'] = created_by
    if hasattr(MyUser, 'create_datetime'):
        my_user_data['create_datetime'] = current_time
    if hasattr(MyUser, 'update_by'):
        my_user_data['update_by'] = created_by # 初始情况下，创建者也是最后的更新者
    if hasattr(MyUser, 'update_datetime'):
        my_user_data['update_datetime'] = current_time

    database = db()
    with database.atomic() as txn:
        try:
            user = MyUser.create(**my_user_data)
            txn.commit()
            logger.info(f'MyUser {phone} ({nickname}) 由 {created_by} 成功创建。')
            return user
        except IntegrityError as e:
            logger.warning(f'操作员 {created_by} 添加 MyUser {phone} 失败，原因是 IntegrityError: {e}', exc_info=True)
            txn.rollback()
            return None
        except Exception as e:
            logger.error(f'操作员 {created_by} 添加 MyUser {phone} 失败：{e}', exc_info=True)
            txn.rollback()
            return None

def get_my_user_by_phone(phone: str) -> Optional[MyUser]:
    """
    根据电话号码检索单个 MyUser。
    """
    try:
        return MyUser.get(MyUser.phone == phone)
    except DoesNotExist:
        return None
    except Exception as e:
        logger.error(f"根据电话号码 {phone} 获取 MyUser 时出错：{e}", exc_info=True)
        return None

def get_my_user_by_id(user_id: int) -> Optional[MyUser]:
    """
    根据 user_id（主键）检索单个 MyUser。
    """
    try:
        return MyUser.get(MyUser.user_id == user_id)
    except DoesNotExist:
        return None
    except Exception as e:
        logger.error(f"根据 ID {user_id} 获取 MyUser 时出错：{e}", exc_info=True)
        return None

def get_all_my_users() -> List[MyUser]:
    """
    从 MyUser 中检索所有用户。
    注意：MyUser 模型没有显式的状态字段，
    因此未实现按状态过滤（例如 exclude_disabled）。
    """
    try:
        return list(MyUser.select())
    except Exception as e:
        logger.error(f"获取所有 MyUser 时出错：{e}", exc_info=True)
        return []

def _get_my_user_for_update(identifier: Union[str, int]) -> Optional[MyUser]:
    """辅助函数：通过电话号码（str）或 user_id（int）获取用户。"""
    if isinstance(identifier, str): # 假设是电话号码
        return get_my_user_by_phone(identifier)
    elif isinstance(identifier, int): # 假设是 user_id
        return get_my_user_by_id(identifier)
    logger.warning(f"获取 MyUser 时标识符类型无效：{type(identifier)}")
    return None


def update_my_user(
    identifier: Union[str, int], # 电话号码（str）或 user_id（int）
    updated_by: Optional[str] = "system",
    **fields_to_update: Any
) -> bool:
    """
    更新 MyUser 信息。
    'identifier' 可以是用户的电话号码（str）或 user_id（int）。
    使用关键字参数指定要更新的字段（例如，nickname='新昵称', email='new@example.com'）。
    如果 'password_plain' 在 fields_to_update 中，它将被哈希并存储在 'password' 中。
    如果模型中有审计字段 'update_by' 和 'update_datetime'，它们会自动更新。
    """
    database = db()
    with database.atomic() as txn:
        try:
            user = _get_my_user_for_update(identifier)
            if not user:
                logger.warning(f'未找到标识符为 {identifier} 的 MyUser，无法更新。')
                return False

            for field, value in fields_to_update.items():
                if field == 'password_plain':
                    if value: # 仅在提供新密码时更新密码
                        hashed_password = hashlib.sha256(str(value).strip().encode('utf-8')).hexdigest()
                        user.password = hashed_password
                    # 否则：如果 password_plain 为空或 None，则不执行任何操作
                elif hasattr(user, field):
                    setattr(user, field, value)
                else:
                    logger.warning(f"MyUser 模型没有字段 '{field}'，跳过此字段的更新。")
            
            if hasattr(user, 'update_by'):
                user.update_by = updated_by
            if hasattr(user, 'update_datetime'):
                user.update_datetime = datetime.now()
            
            user.save()
            txn.commit()
            logger.info(f'MyUser {identifier} 由 {updated_by} 成功更新。')
            return True

        except Exception as e: # 捕获 _get_my_user_for_update 中的 DoesNotExist 异常（如果之前未处理）
            logger.error(f'操作员 {updated_by} 更新 MyUser {identifier} 失败：{e}', exc_info=True)
            txn.rollback()
            return False

def delete_my_user(identifier: Union[str, int], deleted_by: Optional[str] = "system") -> bool:
    """
    根据电话号码（str）或 user_id（int）从 MyUser 中删除用户。
    记录执行删除操作的操作员。
    """
    database = db()
    with database.atomic() as txn:
        try:
            user_to_delete = _get_my_user_for_update(identifier)
            if not user_to_delete:
                logger.warning(f'未找到标识符为 {identifier} 的 MyUser，无法由 {deleted_by} 删除。')
                return False # 或者，如果希望删除操作幂等，则返回 True

            deleted_rows = MyUser.delete().where(MyUser.user_id == user_to_delete.user_id).execute()
            # 替代方法：如果有实例，可以使用 user_to_delete.delete_instance()

            if deleted_rows == 0: # 如果找到 user_to_delete，但未通过查询删除，不应发生此情况
                logger.warning(f'MyUser {identifier}（ID: {user_to_delete.user_id}）已找到，但未被查询删除，由 {deleted_by}。')
                txn.rollback()
                return False
            
            txn.commit()
            logger.info(f'MyUser {identifier}（ID: {user_to_delete.user_id}）已由 {deleted_by} 成功删除。')
            return True
        except Exception as e:
            logger.error(f'操作员 {deleted_by} 删除 MyUser {identifier} 失败：{e}', exc_info=True)
            txn.rollback()
            return False

# --- 特定字段更新函数 ---

def _update_my_user_single_field(identifier: Union[str, int], field_name: str, value: Any, updated_by: Optional[str] = "system") -> bool:
    """
    内部辅助函数：更新 MyUser 的单个字段。
    'identifier' 可以是电话号码（str）或 user_id（int）。
    """
    if not hasattr(MyUser, field_name):
        logger.error(f"MyUser 模型没有字段 '{field_name}'。无法更新。")
        return False
        
    update_dict = {field_name: value}
    return update_my_user(identifier, updated_by=updated_by, **update_dict)

def update_my_user_nickname(identifier: Union[str, int], nickname: str, updated_by: Optional[str] = "system") -> bool:
    """更新 MyUser 的昵称。"""
    return _update_my_user_single_field(identifier, 'nickname', nickname, updated_by)

def update_my_user_email(identifier: Union[str, int], email: str, updated_by: Optional[str] = "system") -> bool:
    """更新 MyUser 的电子邮件。"""
    return _update_my_user_single_field(identifier, 'email', email, updated_by)

def update_my_user_gender(identifier: Union[str, int], gender: int, updated_by: Optional[str] = "system") -> bool:
    """更新 MyUser 的性别。"""
    return _update_my_user_single_field(identifier, 'gender', gender, updated_by)

def update_my_user_img_url(identifier: Union[str, int], img_url: str, updated_by: Optional[str] = "system") -> bool:
    """更新 MyUser 的头像 URL。"""
    return _update_my_user_single_field(identifier, 'img_url', img_url, updated_by)

def update_my_user_spare(identifier: Union[str, int], spare: Optional[str], updated_by: Optional[str] = "system") -> bool:
    """更新 MyUser 的备用字段。"""
    return _update_my_user_single_field(identifier, 'spare', spare, updated_by)

def update_my_user_password(
    phone: str, # 密码更新应主要使用电话号码进行验证
    new_password_plain: str,
    updated_by: Optional[str] = "system",
    old_password_plain: Optional[str] = None
) -> bool:
    """
    更新 MyUser 的密码。使用 'phone' 进行标识。
    如果提供了 old_password_plain，则会先进行验证。
    """
    if old_password_plain:
        if not my_user_password_verify(phone, old_password_plain):
            logger.warning(f"MyUser {phone} 在密码更新期间旧密码验证失败。")
            return False
            
    if not new_password_plain.strip():
        logger.warning("新密码不能为空，无法更新 MyUser 密码。")
        return False
    
    # update_my_user 函数会处理 'password_plain' 的哈希
    return update_my_user(phone, updated_by=updated_by, password_plain=new_password_plain)
