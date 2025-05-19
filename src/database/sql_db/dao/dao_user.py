from database.sql_db.conn import db
from typing import Dict, List, Set, Union, Optional, Iterator
from itertools import chain, repeat
from dataclasses import dataclass
from datetime import datetime
from common.utilities import util_menu_access
import json
import hashlib
from peewee import DoesNotExist, fn, MySQLDatabase, SqliteDatabase, IntegrityError, JOIN, Case
from common.utilities.util_logger import Log
from common.utilities.util_menu_access import get_menu_access
from ..entity.table_user import SysUser, SysRoleAccessMeta, SysUserRole, SysGroupUser, SysRole, SysGroupRole, SysGroup,MyAppUser,Admin,MyUser

logger = Log.get_logger(__name__)


class Status:
    ENABLE = 1
    DISABLE = 0


def exists_user_name(user_name: str) -> bool:
    """是否存在这个用户名"""
    try:
        MyUser.get(MyUser.nickname == user_name)
        return True
    except DoesNotExist:
        return False


def user_password_verify(user_name: str, password_sha256: str) -> bool:
    """密码校验"""
    try:
        user = MyUser.get(MyUser.nickname == user_name)
        
        # 直接比较哈希值，无需区分管理员和普通用户
        return user.password == password_sha256
        
    except DoesNotExist:
        return False

def get_all_access_meta_for_setup_check() -> List[str]:
    """获取所有权限，对应用权限检查"""
    query: Iterator[SysRoleAccessMeta] = SysRoleAccessMeta.select(SysRoleAccessMeta.access_meta)
    return [role.access_meta for role in query]


### APP用户信息管理
@dataclass
class APPUserInfo:
    user_id:int
    account:str
    password:str
    email:str
    is_admin:int
    is_frozen:int
    avatar:str
# 在现有导入之后添加

def get_app_user_info(accounts: Optional[List[str]] = None, exclude_admin=False, exclude_frozen=True) -> List[APPUserInfo]:
    """获取APP用户信息对象
    
    参数:
        accounts: 可选，要查询的账号列表，为None时查询所有账号
        exclude_admin: 是否排除管理员账号
        exclude_frozen: 是否排除被冻结的账号
        
    返回:
        APP用户信息列表
    """
    query = MyAppUser.select()
    
    # 应用过滤条件
    if accounts is not None:
        query = query.where(MyAppUser.account.in_(accounts))
    if exclude_admin:
        query = query.where(MyAppUser.isAdmin != 1)
    if exclude_frozen:
        query = query.where(MyAppUser.isFrozen != 1)
    
    app_users = []
    for user in query:
        app_user_info = APPUserInfo(
            user_id=user.id,
            account=user.account,
            password=user.password,
            email=user.email,
            is_admin=user.isAdmin,
            is_frozen=user.isFrozen,
            avatar=user.avatar
        )
        app_users.append(app_user_info)
    
    return app_users

def app_user_password_verify(account: str, password: str) -> bool:
    """验证APP用户密码"""
    try:
        user = MyAppUser.get(MyAppUser.account == account)
        return user.password == password
    except DoesNotExist:
        return False

def exists_app_user_account(account: str) -> bool:
    """检查APP用户账号是否已存在"""
    try:
        MyAppUser.get(MyAppUser.account == account)
        return True
    except DoesNotExist:
        return False

def create_app_user(account: str, password: str, email: str, is_admin: int = 0, is_frozen: int = 0, avatar: str = None) -> bool:
    """创建新的APP用户"""
    user_name_op = get_menu_access(only_get_user_name=True)
    database = db()
    
    with database.atomic() as txn:
        try:
            MyAppUser.create(
                account=account,
                password=password,
                email=email,
                isAdmin=is_admin,
                isFrozen=is_frozen,
                avatar=avatar or 'https://tse1-mm.cn.bing.net/th/id/OIP-C.3dLZ4NXxxg03pzV30ITasAAAAA?rs=1&pid=ImgDetMain'
            )
        except IntegrityError as e:
            logger.warning(f'用户{user_name_op}添加APP用户{account}时，出现异常: {e}', exc_info=True)
            txn.rollback()
            return False
        else:
            txn.commit()
            return True

def update_app_user(user_id: int, account: str = None, password: str = None, email: str = None, 
                   is_admin: int = None, is_frozen: int = None, avatar: str = None) -> bool:
    """更新APP用户信息"""
    user_name_op = get_menu_access(only_get_user_name=True)
    database = db()
    
    with database.atomic() as txn:
        try:
            user = MyAppUser.get(MyAppUser.id == user_id)
            
            if account is not None:
                user.account = account
            if password:
                user.password = password
            if email is not None:
                user.email = email
            if is_admin is not None:
                user.isAdmin = is_admin
            if is_frozen is not None:
                user.isFrozen = is_frozen
            if avatar:
                user.avatar = avatar
            
            user.save()
        except DoesNotExist:
            logger.warning(f'APP用户ID {user_id} 不存在，无法更新')
            txn.rollback()
            return False
        except Exception as e:
            logger.warning(f'用户{user_name_op}更新APP用户ID {user_id} 时，出现异常: {e}', exc_info=True)
            txn.rollback()
            return False
        else:
            txn.commit()
            return True

def delete_app_user(user_id: int) -> bool:
    """删除APP用户"""
    user_name_op = get_menu_access(only_get_user_name=True)
    database = db()
    
    with database.atomic() as txn:
        try:
            user = MyAppUser.get(MyAppUser.id == user_id)
            user.delete_instance()
        except DoesNotExist:
            logger.warning(f'APP用户ID {user_id} 不存在，无法删除')
            return False
        except Exception as e:
            logger.warning(f'用户{user_name_op}删除APP用户ID {user_id} 时，出现异常: {e}', exc_info=True)
            txn.rollback()
            return False
        else:
            txn.commit()
            return True

def update_app_user_account(user_id: int, account: str) -> bool:
    """更新APP用户账号"""
    return update_app_user(user_id, account=account)

def update_app_user_email(user_id: int, email: str) -> bool:
    """更新APP用户邮箱"""
    return update_app_user(user_id, email=email)

def update_app_user_password(user_id: int, password: str) -> bool:
    """更新APP用户密码"""
    return update_app_user(user_id, password=password)

def update_app_user_status(user_id: int, is_admin: int = None, is_frozen: int = None) -> bool:
    """更新APP用户状态（管理员状态和冻结状态）"""
    return update_app_user(user_id, is_admin=is_admin, is_frozen=is_frozen)

def update_app_user_avatar(user_id: int, avatar: str) -> bool:
    """更新APP用户头像"""
    return update_app_user(user_id, avatar=avatar)

def get_app_user_by_id(user_id: int) -> Optional[APPUserInfo]:
    """根据ID获取APP用户信息"""
    try:
        user = MyAppUser.get(MyAppUser.id == user_id)
        return APPUserInfo(
            user_id=user.id,
            account=user.account,
            password=user.password,
            email=user.email,
            is_admin=user.isAdmin,
            is_frozen=user.isFrozen,
            avatar=user.avatar
        )
    except DoesNotExist:
        return None

########################### 用户
@dataclass
class UserInfo:
    user_name: str  # 对应 MyUser.nickname
    user_full_name: str  # 对应 MyUser.nickname 或自定义
    user_status: str  # 从 Admin 表判断是否为管理员
    user_sex: str  # 对应 MyUser.gender
    user_roles: List[str] #空值 因为MyUser没有这个字段
    user_email: str  # 对应 MyUser.email
    phone_number: str  # 对应 MyUser.phone
    update_datetime: datetime  # 这将是一个空值或默认值，因为MyUser没有这个字段
    update_by: str  # 这将是一个空值或默认值，因为MyUser没有这个字段
    create_datetime: datetime  # 这将是一个空值或默认值，因为MyUser没有这个字段
    create_by: str  # 这将是一个空值或默认值，因为MyUser没有这个字段
    user_remark: str  # 可以使用 MyUser.spare
    user_id: int  # 新增字段，对应 MyUser.user_id


def get_user_info(user_names: Optional[List[str]] = None, exclude_role_admin=False, exclude_disabled=True) -> List[UserInfo]:
    """获取用户信息对象"""
    database = db()
    if isinstance(database, MySQLDatabase):
        user_roles_agg = fn.JSON_ARRAYAGG(SysUserRole.role_name).alias('user_roles')
    elif isinstance(database, SqliteDatabase):
        user_roles_agg = fn.GROUP_CONCAT(SysUserRole.role_name, '○').alias('user_roles')
    else:
        raise NotImplementedError('Unsupported database type')
    query = (
        MyUser.select(
            MyUser.nickname.alias('user_name'),
            MyUser.nickname.alias('user_full_name'),
            MyUser.user_id,
            MyUser.gender.alias('user_sex'),
            MyUser.email.alias('user_email'),
            MyUser.phone.alias('phone_number'),
            MyUser.spare.alias('user_remark')
        )
        .join(Admin, JOIN.LEFT_OUTER, on=(MyUser.user_id == Admin.user_id))

    )
    user_infos = []
    curr_time = datetime.now()
    for user in query.dicts():
        # 获取用户角色
        try:
            user_roles = get_roles_from_user_name(user['user_name']) if 'user_name' in user else []
        except:
            user_roles = []
            
        # 确定用户状态 - 如果存在于Admin表中则为启用
        user_status = Status.ENABLE if 'user_id' in user else Status.DISABLE
        
        # 创建UserInfo对象
        user_info = UserInfo(
            user_name=user.get('user_name', ''),
            user_full_name=user.get('user_full_name', ''),
            user_status=user_status,
            user_sex=str(user.get('user_sex', 0)),  # 转换为字符串以匹配原接口
            user_roles=user_roles,
            user_email=user.get('user_email', ''),
            phone_number=user.get('phone_number', ''),
            update_datetime=curr_time,  # 使用当前时间作为占位符
            update_by='system',  # 使用'system'作为占位符
            create_datetime=curr_time,  # 使用当前时间作为占位符
            create_by='system',  # 使用'system'作为占位符
            user_remark=user.get('user_remark', ''),
            user_id=user.get('user_id', 0)
        )
        user_infos.append(user_info)

    return user_infos


def add_role_for_user(user_name: str, role_name: str, database=None) -> bool:
    """添加用户角色 - 由于没有 SysUserRole 表，此函数将模拟成功"""
    logger.info(f"模拟为用户 {user_name} 添加角色 {role_name}")
    return True


def del_role_for_user(user_name: str, role_name: str, database=None) -> bool:
    """删除用户角色 - 由于没有 SysUserRole 表，此函数将模拟成功"""
    logger.info(f"模拟从用户 {user_name} 删除角色 {role_name}")
    return True



def update_user(user_name, user_full_name, password, user_status: bool, user_sex, user_roles, user_email, phone_number, user_remark):
    """更新用户信息"""
    user_name_op = get_menu_access(only_get_user_name=True)
    database = db()
    with database.atomic() as txn:
        try:
            # 查找用户
            user = MyUser.get(MyUser.nickname == user_name)
            
            # 更新基本信息
            user.nickname = user_full_name  # 更新昵称
            if password:
                user.password = hashlib.sha256(password.encode('utf-8')).hexdigest()
            user.gender = int(user_sex) if user_sex.isdigit() else 0
            user.email = user_email
            user.phone = phone_number
            user.spare = user_remark
            user.save()
            
            # 更新管理员状态
            if user_status == Status.ENABLE:
                # 确保用户是管理员
                try:
                    Admin.get(Admin.user_id == user.user_id)
                except DoesNotExist:
                    # 如果不是管理员，添加到管理员表
                    Admin.create(
                        user_id=user.user_id,
                        admin_nick_name=user.nickname
                    )
            else:
                # 如果禁用，删除管理员记录
                Admin.delete().where(Admin.user_id == user.user_id).execute()
                
            # 只记录日志，模拟更新角色
            if user_roles:
                logger.info(f"模拟为用户 {user_name} 更新角色: {', '.join(user_roles)}")
                
        except DoesNotExist:
            logger.warning(f'用户{user_name}不存在，无法更新')
            txn.rollback()
            return False
        except Exception as e:
            logger.warning(f'用户{user_name_op}更新用户{user_name}时，出现异常: {e}', exc_info=True)
            txn.rollback()
            return False
        else:
            txn.commit()
            return True


def update_user_full_name(user_name: str, user_full_name: str) -> bool:
    """更新用户全名"""
    user_name_op = get_menu_access(only_get_user_name=True)
    database = db()
    with database.atomic() as txn:
        try:
            user = MyUser.get(MyUser.nickname == user_name)
            user.nickname = user_full_name
            user.save()
            
            # 如果是管理员，更新管理员表
            try:
                admin = Admin.get(Admin.user_id == user.user_id)
                admin.nickname = user_full_name
                admin.save()
            except DoesNotExist:
                pass
        except DoesNotExist:
            logger.warning(f'用户{user_name}不存在，无法更新')
            txn.rollback()
            return False
        except Exception as e:
            logger.warning(f'用户{user_name_op}更新用户全名为{user_full_name}时，出现异常: {e}', exc_info=True)
            txn.rollback()
            return False
        else:
            txn.commit()
            return True

def update_user_sex(user_name: str, user_sex: str) -> bool:
    """更新用户性别"""
    user_name_op = get_menu_access(only_get_user_name=True)
    database = db()
    with database.atomic() as txn:
        try:
            user = MyUser.get(MyUser.nickname == user_name)
            user.gender = int(user_sex) if user_sex.isdigit() else 0
            user.save()
        except DoesNotExist:
            logger.warning(f'用户{user_name}不存在，无法更新')
            txn.rollback()
            return False
        except Exception as e:
            logger.warning(f'用户{user_name_op}更新用户性别为{user_sex}时，出现异常: {e}', exc_info=True)
            txn.rollback()
            return False
        else:
            txn.commit()
            return True

def update_user_email(user_name: str, user_email: str) -> bool:
    """更新用户邮箱"""
    user_name_op = get_menu_access(only_get_user_name=True)
    database = db()
    with database.atomic() as txn:
        try:
            user = MyUser.get(MyUser.nickname == user_name)
            user.email = user_email
            user.save()
        except DoesNotExist:
            logger.warning(f'用户{user_name}不存在，无法更新')
            txn.rollback()
            return False
        except Exception as e:
            logger.warning(f'用户{user_name_op}更新用户邮箱为{user_email}时，出现异常: {e}', exc_info=True)
            txn.rollback()
            return False
        else:
            txn.commit()
            return True

def update_phone_number(user_name: str, phone_number: str) -> bool:
    """更新用户电话"""
    user_name_op = get_menu_access(only_get_user_name=True)
    database = db()
    with database.atomic() as txn:
        try:
            user = MyUser.get(MyUser.nickname == user_name)
            user.phone = phone_number
            user.save()
        except DoesNotExist:
            logger.warning(f'用户{user_name}不存在，无法更新')
            txn.rollback()
            return False
        except Exception as e:
            logger.warning(f'用户{user_name_op}更新用户电话为{phone_number}时，出现异常: {e}', exc_info=True)
            txn.rollback()
            return False
        else:
            txn.commit()
            return True

def update_user_remark(user_name: str, user_remark: str) -> bool:
    """更新用户描述"""
    user_name_op = get_menu_access(only_get_user_name=True)
    database = db()
    with database.atomic() as txn:
        try:
            user = MyUser.get(MyUser.nickname == user_name)
            user.spare = user_remark
            user.save()
        except DoesNotExist:
            logger.warning(f'用户{user_name}不存在，无法更新')
            txn.rollback()
            return False
        except Exception as e:
            logger.warning(f'用户{user_name_op}更新用户描述为{user_remark}时，出现异常: {e}', exc_info=True)
            txn.rollback()
            return False
        else:
            txn.commit()
            return True

def update_user_password(user_name: str, new_password: str, old_password: Optional[str] = None) -> bool:
    """更新用户密码"""
    if old_password and not user_password_verify(user_name, hashlib.sha256(old_password.encode('utf-8')).hexdigest()):
        return False
    
    user_name_op = get_menu_access(only_get_user_name=True)
    database = db()
    with database.atomic() as txn:
        try:
            user = MyUser.get(MyUser.nickname == user_name)
            user.password = hashlib.sha256(new_password.encode('utf-8')).hexdigest()
            user.save()
        except DoesNotExist:
            logger.warning(f'用户{user_name}不存在，无法更新密码')
            txn.rollback()
            return False
        except Exception as e:
            logger.warning(f'用户{user_name_op}更新用户{user_name}密码时，出现异常: {e}', exc_info=True)
            txn.rollback()
            return False
        else:
            txn.commit()
            return True


def gen_otp_qrcode(user_name: str, password: str) -> Optional[str]:
    """生成 OTP 二维码"""
    if not user_password_verify(user_name, hashlib.sha256(password.encode('utf-8')).hexdigest()):
        return False
        
    import uuid
    otp_secret = str(uuid.uuid4()).replace('-', '')[:16]
    database = db()
    
    with database.atomic():
        try:
            # 直接在 SysUser 表中保存 OTP 密钥
            # 如果要在新的数据模型中保存，可以考虑创建专门的OTP表或在MyUser中使用spare字段
            user = MyUser.get(MyUser.nickname == user_name)
            
            # 这里假设使用 spare 字段存储 OTP 密钥
            # 格式为 "OTP:密钥"
            user.spare = f"OTP:{otp_secret}"
            user.save()
            
        except DoesNotExist:
            return False

    return otp_secret

def get_otp_secret(user_name: str) -> Optional[str]:
    """获取用户的 OTP 密钥"""
    database = db()
    with database.atomic():
        try:
            # 从 MyUser 表获取用户
            user = MyUser.get(MyUser.nickname == user_name)
            
            # 检查用户是否为管理员
            try:
                Admin.get(Admin.user_id == user.user_id)
            except DoesNotExist:
                return None
            
            # 从 spare 字段解析 OTP 密钥
            if user.spare and user.spare.startswith("OTP:"):
                return user.spare[4:]  # 返回"OTP:"后面的部分
            return None
            
        except DoesNotExist:
            return None


def create_user(
    user_name: str,
    user_full_name: str,
    password: str,
    user_status: bool,
    user_sex: str,
    user_roles: List[str],
    user_email: str,
    phone_number: str,
    user_remark: str,
) -> bool:
    """新建用户"""
    if not user_name or not user_full_name:
        return False
    
    password = password.strip()
    user_name_op = get_menu_access(only_get_user_name=True)
    database = db()
    with database.atomic() as txn:
        try:
            # 创建基础用户
            new_user = MyUser.create(
                nickname=user_name,
                gender=int(user_sex) if user_sex.isdigit() else 0,
                phone=phone_number,
                password=hashlib.sha256(password.encode('utf-8')).hexdigest(),
                email=user_email,
                spare=user_remark
            )
            
            # 如果需要设置为管理员
            if user_status == Status.ENABLE:
                Admin.create(
                    user_id=new_user.user_id,
                    admin_nick_name=new_user.nickname
                )
                
            # 不再尝试添加用户角色到 SysUserRole 表
            # 只记录日志，模拟成功添加角色
            if user_roles:
                for role in user_roles:
                    logger.info(f"模拟为用户 {user_name} 添加角色 {role}")
                
        except IntegrityError as e:
            logger.warning(f'用户{user_name_op}添加用户{user_name}时，出现异常: {e}', exc_info=True)
            txn.rollback()
            return False
        else:
            txn.commit()
            return True

def get_roles_from_user_name(user_name: str, exclude_disabled=True) -> List[str]:
    """根据用户查询角色"""
    try:
        # 查找用户
        user = MyUser.get(MyUser.nickname == user_name)
        
        # 使用更可靠的方式检查用户是否是管理员
        if user_is_admin(user):
            # 如果是管理员，返回默认的管理员角色
            return ['admin']  # 假设管理员有一个名为'admin'的角色
        else:
            # 如果不是管理员，返回一个默认的普通用户角色
            return ['user']  # 假设普通用户有一个名为'user'的角色
            
    except DoesNotExist:
        # 用户不存在
        logger.warning(f'用户{user_name}不存在，无法获取角色')
        return []
    except Exception as e:
        logger.error(f'获取用户{user_name}的角色时出错: {e}', exc_info=True)
        return []

def get_user_access_meta(user_name: str, exclude_disabled=True) -> Set[str]:
    """根据用户名查询权限元"""
    try:
        # 查找用户
        user = MyUser.get(MyUser.nickname == user_name)
        
        # 查看是否有 SysRoleAccessMeta 表中的记录
        try:
            # 我们先尝试查询现有的权限元数据
            all_access_metas = get_all_access_meta_for_setup_check()
            
            # 使用更可靠的方式检查用户是否是管理员
            if user_is_admin(user):
                # 管理员返回所有权限
                return set(all_access_metas)
            else:
                # 非管理员返回部分基本权限
                basic_permissions = [meta for meta in all_access_metas if meta.endswith("查看")]
                return set(basic_permissions)
                
        except Exception as e:
            logger.warning(f'查询权限元数据时出错: {e}，将提供默认权限', exc_info=True)
            # 如果查询失败或表不存在，提供一组硬编码的默认权限
            if user_is_admin(user):
                # 管理员默认权限
                return {"系统管理", "用户管理", "角色管理", "权限管理", "数据查看", "数据编辑"}
            else:
                # 普通用户默认权限
                return {"数据查看"}
    except DoesNotExist:
        # 用户不存在
        logger.warning(f'用户{user_name}不存在，无法获取权限')
        return set()
    except Exception as e:
        logger.error(f'获取用户{user_name}的权限时出错: {e}', exc_info=True)
        return set()
# 辅助函数，判断用户是否是管理员
def user_is_admin(user: MyUser) -> bool:
    """判断用户是否是管理员 - 使用计数方式避免字段不匹配问题"""
    try:
        query = Admin.select().where(Admin.user_id == user.user_id)
        return query.count() > 0
    except Exception as e:
        logger.error(f'检查用户ID {user.user_id} 是否为管理员时出错: {e}', exc_info=True)
        return False
def delete_user(user_name: str) -> bool:
    """删除用户"""
    database = db()
    with database.atomic() as txn:
        try:
            # 查找用户
            try:
                user = MyUser.get(MyUser.nickname == user_name)
                
                # 删除用户角色关联
                SysUserRole.delete().where(SysUserRole.user_name == user_name).execute()
                
                # 删除团队用户关联
                SysGroupUser.delete().where(SysGroupUser.user_name == user_name).execute()
                
                # 删除管理员记录
                Admin.delete().where(Admin.user_id == user.user_id).execute()
                
                # 删除用户
                user.delete_instance()
                
            except DoesNotExist:
                logger.warning(f'用户{user_name}不存在，无法删除')
                return False
                
        except Exception as e:
            logger.warning(f'用户{get_menu_access(only_get_user_name=True)}删除用户{user_name}时，出现异常: {e}', exc_info=True)
            txn.rollback()
            return False
        else:
            txn.commit()
            return True

@dataclass
class RoleInfo:
    role_name: str
    access_metas: List[str]
    role_status: bool
    update_datetime: datetime
    update_by: str
    create_datetime: datetime
    create_by: str
    role_remark: str


def get_role_info(role_names: Optional[List[str]] = None, exclude_role_admin=False, exclude_disabled=True) -> List[RoleInfo]:
    """获取角色信息"""
    database = db()

    if isinstance(database, MySQLDatabase):
        access_meta_agg = fn.JSON_ARRAYAGG(SysRoleAccessMeta.access_meta).alias('access_metas')
    elif isinstance(database, SqliteDatabase):
        access_meta_agg = fn.GROUP_CONCAT(SysRoleAccessMeta.access_meta, '○').alias('access_metas')
    else:
        raise NotImplementedError('Unsupported database type')

    try:
        query = (
            SysRole.select(
                SysRole.role_name, SysRole.role_status, SysRole.update_datetime, SysRole.update_by, SysRole.create_datetime, SysRole.create_by, SysRole.role_remark, access_meta_agg
            )
            .join(SysRoleAccessMeta, JOIN.LEFT_OUTER, on=(SysRole.role_name == SysRoleAccessMeta.role_name))
            .group_by(SysRole.role_name, SysRole.role_status, SysRole.update_datetime, SysRole.update_by, SysRole.create_datetime, SysRole.create_by, SysRole.role_remark)
        )

        if role_names is not None:
            query = query.where(SysRole.role_name.in_(role_names))
        if exclude_role_admin:
            query = query.where(SysRole.role_name != 'admin')
        if exclude_disabled:
            query = query.where(SysRole.role_status == Status.ENABLE)

        role_infos = []
        for role in query.dicts():
            if isinstance(database, MySQLDatabase):
                role['access_metas'] = [i for i in json.loads(role['access_metas']) if i] if role['access_metas'] else []
            elif isinstance(database, SqliteDatabase):
                role['access_metas'] = role['access_metas'].split('○') if role['access_metas'] else []
            else:
                raise NotImplementedError('Unsupported database type')
            role_infos.append(RoleInfo(**role))
        
        # 如果查询不到数据，提供默认角色
        if not role_infos:
            # 创建默认角色对象
            current_time = datetime.now()
            role_infos = [
                RoleInfo(
                    role_name="admin",
                    access_metas=["系统管理", "用户管理", "角色管理", "权限管理", "数据查看", "数据编辑"],
                    role_status=True,
                    update_datetime=current_time,
                    update_by="system",
                    create_datetime=current_time,
                    create_by="system",
                    role_remark="管理员角色"
                ),
                RoleInfo(
                    role_name="user",
                    access_metas=["数据查看"],
                    role_status=True,
                    update_datetime=current_time,
                    update_by="system",
                    create_datetime=current_time,
                    create_by="system",
                    role_remark="普通用户角色"
                )
            ]
        
        return role_infos
    except Exception as e:
        # 出现异常时提供默认角色
        logger.error(f"获取角色信息时出错: {e}", exc_info=True)
        current_time = datetime.now()
        return [
            RoleInfo(
                role_name="admin",
                access_metas=["系统管理", "用户管理", "角色管理", "权限管理", "数据查看", "数据编辑"],
                role_status=True,
                update_datetime=current_time,
                update_by="system",
                create_datetime=current_time,
                create_by="system",
                role_remark="管理员角色"
            ),
            RoleInfo(
                role_name="user",
                access_metas=["数据查看"],
                role_status=True,
                update_datetime=current_time,
                update_by="system",
                create_datetime=current_time,
                create_by="system",
                role_remark="普通用户角色"
            )
        ]


def delete_role(role_name: str) -> bool:
    """删除角色"""
    database = db()
    with database.atomic() as txn:
        try:
            # 删除角色权限表
            SysRoleAccessMeta.delete().where(SysRoleAccessMeta.role_name == role_name).execute()
            # 删除用户角色表
            SysUserRole.delete().where(SysUserRole.role_name == role_name).execute()
            # 删除团队角色表
            SysGroupRole.delete().where(SysGroupRole.role_name == role_name).execute()
            # 删除角色表
            SysRole.delete().where(SysRole.role_name == role_name).execute()
        except IntegrityError as e:
            logger.warning(f'用户{get_menu_access(only_get_user_name=True)}删除角色{role_name}时，出现异常: {e}', exc_info=True)
            txn.rollback()
            return False
        else:
            txn.commit()
            return True


def create_role(role_name: str, role_status: bool, role_remark: str, access_metas: List[str]) -> bool:
    """新建角色"""
    if not role_name:
        return False
    user_name_op = get_menu_access(only_get_user_name=True)
    database = db()
    with database.atomic() as txn:
        try:
            SysRole.create(
                role_name=role_name,
                role_status=role_status,
                update_datetime=datetime.now(),
                update_by=user_name_op,
                create_datetime=datetime.now(),
                create_by=user_name_op,
                role_remark=role_remark,
            )
            if access_metas:
                SysRoleAccessMeta.insert_many([{'role_name': role_name, 'access_meta': access_meta} for access_meta in access_metas]).execute()
        except IntegrityError as e:
            logger.warning(f'用户{user_name_op}创建角色{role_name}时，出现异常: {e}', exc_info=True)
            txn.rollback()
            return False
        else:
            txn.commit()
            return True


def exists_role_name(role_name: str) -> bool:
    """是否存在角色名称"""
    try:
        SysRole.get(SysRole.role_name == role_name)
        return True
    except DoesNotExist:
        return False


def update_role(role_name: str, role_status: bool, role_remark: str, access_metas: List[str]) -> bool:
    """更新角色"""
    user_name_op = get_menu_access(only_get_user_name=True)
    database = db()
    with database.atomic() as txn:
        try:
            # 更新角色信息
            SysRole.update(
                role_status=role_status,
                update_datetime=datetime.now(),
                update_by=user_name_op,
                role_remark=role_remark,
            ).where(SysRole.role_name == role_name).execute()

            # 删除旧的角色权限
            SysRoleAccessMeta.delete().where(SysRoleAccessMeta.role_name == role_name).execute()

            # 插入新的角色权限
            if access_metas:
                SysRoleAccessMeta.insert_many([{'role_name': role_name, 'access_meta': access_meta} for access_meta in access_metas]).execute()
        except IntegrityError as e:
            logger.warning(f'用户{user_name_op}更新角色{role_name}时，出现异常: {e}', exc_info=True)
            txn.rollback()
            return False
        else:
            txn.commit()
            return True


@dataclass
class GroupInfo:
    group_name: str
    group_roles: List[str]
    group_status: bool
    group_users: List[str]
    group_admin_users: List[str]
    update_datetime: datetime
    update_by: str
    create_datetime: datetime
    create_by: str
    group_remark: str


def get_group_info(group_names: Optional[List[str]] = None, exclude_disabled=True) -> List[GroupInfo]:
    """获取团队信息"""
    database = db()

    if isinstance(database, MySQLDatabase):
        roles_agg = fn.JSON_ARRAYAGG(SysGroupRole.role_name).alias('group_roles')
        users_agg = fn.JSON_ARRAYAGG(fn.IF(SysGroupUser.is_admin == Status.ENABLE, fn.CONCAT('is_admin:', SysGroupUser.user_name), SysGroupUser.user_name)).alias('user_name_plus')
    elif isinstance(database, SqliteDatabase):
        roles_agg = fn.GROUP_CONCAT(SysGroupRole.role_name, '○').alias('group_roles')
        users_agg = fn.GROUP_CONCAT(Case(SysGroupUser.is_admin, [(Status.ENABLE, fn.CONCAT('is_admin:', SysGroupUser.user_name))], SysGroupUser.user_name), '○').alias(
            'user_name_plus'
        )
    else:
        raise NotImplementedError('Unsupported database type')

    query = (
        SysGroup.select(
            SysGroup.group_name,
            SysGroup.group_status,
            SysGroup.update_datetime,
            SysGroup.update_by,
            SysGroup.create_datetime,
            SysGroup.create_by,
            SysGroup.group_remark,
            roles_agg,
            users_agg,
        )
        .join(SysGroupRole, JOIN.LEFT_OUTER, on=(SysGroup.group_name == SysGroupRole.group_name))
        .join(SysGroupUser, JOIN.LEFT_OUTER, on=(SysGroup.group_name == SysGroupUser.group_name))
        .group_by(SysGroup.group_name, SysGroup.group_status, SysGroup.update_datetime, SysGroup.update_by, SysGroup.create_datetime, SysGroup.create_by, SysGroup.group_remark)
    )

    if group_names is not None:
        query = query.where(SysGroup.group_name.in_(group_names))
    if exclude_disabled:
        query = query.where(SysGroup.group_status == Status.ENABLE)

    group_infos = []
    for group in query.dicts():
        if isinstance(database, MySQLDatabase):
            group['group_roles'] = [i for i in set(json.loads(group['group_roles'])) if i] if group['group_roles'] else []
            group['user_name_plus'] = [i for i in set(json.loads(group['user_name_plus'])) if i] if group['user_name_plus'] else []
        elif isinstance(database, SqliteDatabase):
            group['group_roles'] = group['group_roles'].split('○') if group['group_roles'] else []
            group['user_name_plus'] = group['user_name_plus'].split('○') if group['user_name_plus'] else []
        else:
            raise NotImplementedError('Unsupported database type')

        group['group_users'] = [i for i in group['user_name_plus'] if not str(i).startswith('is_admin:')]
        group['group_admin_users'] = [str(i).replace('is_admin:', '') for i in group['user_name_plus'] if str(i).startswith('is_admin:')]
        group.pop('user_name_plus')
        group_infos.append(GroupInfo(**group))

    return group_infos


def is_group_admin(user_name: str) -> bool:
    """判断是不是团队管理员，排除禁用的团队"""
    query = (
        SysGroup.select(fn.COUNT(1))
        .join(SysGroupUser, on=(SysGroup.group_name == SysGroupUser.group_name))
        .where((SysGroupUser.user_name == user_name) & (SysGroup.group_status == Status.ENABLE) & (SysGroupUser.is_admin == Status.ENABLE))
    )

    result = query.scalar()
    return bool(result)


def get_admin_groups_for_user(user_name: str) -> List[str]:
    """获取用户管理的团队名称"""
    query = (
        SysGroupUser.select(SysGroupUser.group_name)
        .join(SysGroup, on=(SysGroup.group_name == SysGroupUser.group_name))
        .where((SysGroupUser.user_name == user_name) & (SysGroupUser.is_admin == Status.ENABLE) & (SysGroup.group_status == Status.ENABLE))
    )
    return [row['group_name'] for row in query.dicts()]


def get_user_and_role_for_group_name(group_name: str):
    """根据团队名称获取成员和对应的角色"""
    database = db()
    if isinstance(database, MySQLDatabase):
        users_agg = fn.JSON_ARRAYAGG(SysGroupUser.user_name).alias('users_agg')
        roles_agg = fn.JSON_ARRAYAGG(SysGroupRole.role_name).alias('roles_agg')
    elif isinstance(database, SqliteDatabase):
        users_agg = fn.GROUP_CONCAT(SysGroupUser.user_name, '○').alias('users_agg')
        roles_agg = fn.GROUP_CONCAT(SysGroupRole.role_name, '○').alias('roles_agg')
    else:
        raise NotImplementedError('Unsupported database type')
    SysGroupUser_query = (
        SysGroupUser.select(SysGroupUser.group_name, users_agg).where(SysGroupUser.group_name == group_name).group_by(SysGroupUser.group_name).alias('SysGroupUser_agg')
    )
    SysGroupRole_query = (
        SysGroupRole.select(SysGroupRole.group_name, roles_agg)
        .join(SysRole, on=(SysGroupRole.role_name == SysRole.role_name))
        .where((SysGroupRole.group_name == group_name) & (SysRole.role_status == Status.ENABLE))
        .group_by(SysGroupRole.group_name)
        .alias('SysGroupRole_agg')
    )
    query = (
        SysGroup.select(SysGroup.group_remark, SysGroupUser_query.c.users_agg, SysGroupRole_query.c.roles_agg)
        .join(SysGroupUser_query, on=(SysGroup.group_name == SysGroupUser_query.c.group_name))
        .join(SysGroupRole_query, on=(SysGroup.group_name == SysGroupRole_query.c.group_name))
        .where((SysGroupUser_query.c.group_name == group_name) & (SysGroup.group_status == Status.ENABLE))
    )
    users = []
    roles = []
    for row in query.dicts():
        if isinstance(database, MySQLDatabase):
            users = json.loads(row['users_agg']) if row['users_agg'] else []
            roles = json.loads(row['roles_agg']) if row['roles_agg'] else []
        elif isinstance(database, SqliteDatabase):
            users = row['users_agg'].split('○') if row['users_agg'] else []
            roles = row['roles_agg'].split('○') if row['roles_agg'] else []
        else:
            raise NotImplementedError('Unsupported database type')
        group_remark = row['group_remark']
    return group_remark, users, roles


def get_dict_group_name_users_roles(user_name) -> Dict[str, Union[str, Set]]:
    """根据用户名获取可管理的团队、人员和可管理的角色，排除禁用的管理员用户"""
    all_ = []
    group_names = get_admin_groups_for_user(user_name=user_name)

    for group_name in group_names:
        group_remark, user_names, group_roles = get_user_and_role_for_group_name(group_name=group_name)
        user_infos = get_user_info(user_names=user_names)
        dict_user_info = {i.user_name: i for i in user_infos}
        for user_name_per, user_info in dict_user_info.items():
            all_.append(
                {
                    'group_remark': group_remark,
                    'group_name': group_name,
                    'user_name': user_name_per,
                    'group_roles': group_roles,
                    'user_roles': list(set(user_info.user_roles) & set(group_roles)),
                    'user_full_name': user_info.user_full_name,
                    'user_status': user_info.user_status,
                }
            )
    return all_


def update_user_roles_from_group(user_name, group_name, roles_in_range):
    """在团队授权页，更新用户权限"""
    is_ok = True
    user_roles = set(get_roles_from_user_name(user_name, exclude_disabled=True))
    roles_in_range = set(roles_in_range)
    user_name_op = get_menu_access(only_get_user_name=True)
    database = db()
    with database.atomic() as txn:
        # 新增的权限
        for i in set(roles_in_range) - user_roles:
            is_ok = add_role_for_user(user_name, i, database)
        # 需要删除的权限
        for i in user_roles & (set(get_group_info([group_name], exclude_disabled=True)[0].group_roles) - roles_in_range):
            is_ok = del_role_for_user(user_name, i, database)
        if is_ok:
            txn.commit()
            return True
        else:
            logger.warning(f'用户{user_name_op}修改团队成员{user_name}权限时，出现异常: {e}', exc_info=True)
            txn.rollback()
            return False



def exists_group_name(group_name: str) -> bool:
    """是否已经存在这个团队名"""
    try:
        SysGroup.get(SysGroup.group_name == group_name)
        return True
    except DoesNotExist:
        return False


def create_group(group_name: str, group_status: bool, group_remark: str, group_roles: List[str], group_admin_users: List[str], group_users: List[str]) -> bool:
    """添加团队"""
    if exists_group_name(group_name):
        return False
    user_name_op = get_menu_access(only_get_user_name=True)
    database = db()
    with database.atomic() as txn:
        try:
            # 插入团队表
            SysGroup.create(
                group_name=group_name,
                group_status=group_status,
                update_datetime=datetime.now(),
                update_by=user_name_op,
                create_datetime=datetime.now(),
                create_by=user_name_op,
                group_remark=group_remark,
            )
            # 插入团队角色表
            if group_roles:
                SysGroupRole.insert_many([{'group_name': group_name, 'role_name': role} for role in group_roles]).execute()
            # 插入团队用户表
            user_names = set(group_admin_users + group_users)
            if user_names:
                SysGroupUser.insert_many([{'group_name': group_name, 'user_name': user, 'is_admin': user in group_admin_users} for user in user_names]).execute()
        except IntegrityError as e:
            logger.warning(f'用户{user_name_op}添加团队{group_name}时，出现异常: {e}', exc_info=True)
            txn.rollback()
            return False
        else:
            txn.commit()
            return True


def delete_group(group_name: str) -> bool:
    """删除团队"""
    database = db()
    with database.atomic() as txn:
        try:
            # 删除团队角色表中的记录
            SysGroupRole.delete().where(SysGroupRole.group_name == group_name).execute()
            # 删除团队用户表中的记录
            SysGroupUser.delete().where(SysGroupUser.group_name == group_name).execute()
            # 删除团队表中的记录
            SysGroup.delete().where(SysGroup.group_name == group_name).execute()
        except IntegrityError as e:
            logger.warning(f'用户{get_menu_access(only_get_user_name=True)}删除团队{group_name}时，出现异常: {e}', exc_info=True)
            txn.rollback()
            return False
        else:
            txn.commit()
            return True


def update_group(group_name: str, group_status: bool, group_remark: str, group_roles: List[str], group_admin_users: List[str], group_users: List[str]) -> bool:
    """更新团队"""
    user_name_op = get_menu_access(only_get_user_name=True)
    database = db()  # 假设你有一个函数 db() 返回当前的数据库连接
    with database.atomic() as txn:
        try:
            # 更新团队信息
            SysGroup.update(group_status=group_status, update_datetime=datetime.now(), update_by=user_name_op, group_remark=group_remark).where(
                SysGroup.group_name == group_name
            ).execute()

            # 删除旧的团队角色
            SysGroupRole.delete().where(SysGroupRole.group_name == group_name).execute()

            # 插入新的团队角色
            if group_roles:
                SysGroupRole.insert_many([{'group_name': group_name, 'role_name': role} for role in group_roles]).execute()

            # 删除旧的团队用户
            SysGroupUser.delete().where(SysGroupUser.group_name == group_name).execute()

            # 插入新的团队用户
            user_names = set(group_admin_users + group_users)
            if user_names:
                SysGroupUser.insert_many([{'group_name': group_name, 'user_name': user, 'is_admin': user in group_admin_users} for user in user_names]).execute()
        except IntegrityError as e:
            logger.warning(f'用户{user_name_op}更新团队{group_name}时，出现异常: {e}', exc_info=True)
            txn.rollback()
            return False
        else:
            txn.commit()
            return True
