from peewee import CharField, Model, IntegerField, DateTimeField, ForeignKeyField, BooleanField
from ..conn import db


class BaseModel(Model):
    class Meta:
        database = db()
"""
下面的改动主要用于适配我们自己的数据库
主要的表还是User_info表 用这个实现后台登录等 更改一下admin的判断方式即可
以及加入APP_User的管理 也可以对APP_USER的后台用户进行修改
"""
class MyUser(BaseModel):
# 1	user_id 主键	int(11)			否	无	主键，用户唯一标识	AUTO_INCREMENT
# 2	nickname	varchar(255)	utf8mb4_general_ci		否	用户	昵称	
# 3	gender	int(11)			是	0	性别(0:默认 1:男 2:女)	
# 4	phone 索引	varchar(20)	utf8mb4_general_ci		否	无	手机号，登录时使用（唯一）	
# 5	password	varchar(255)	utf8mb4_general_ci		否	无	密码	
# 6	email	varchar(255)	utf8mb4_general_ci		否	无	邮箱	
# 7	img_url	varchar(255)	utf8mb4_general_ci		是	https://tse1-mm.cn.bing.net/th/id/OIP-C.3dLZ4NXxxg03pzV30ITasAAAAA?rs=1&pid=ImgDetMain	头像地址	
# 8	spare	varchar(255)	utf8mb4_general_ci		是	NULL	备用字段

    user_id= IntegerField(primary_key=True, help_text='主键，用户唯一标识')
    nickname= CharField(max_length=255, help_text='昵称')
    gender= IntegerField(null=True, default=0, help_text='性别(0:默认 1:男 2:女)')
    phone= CharField(max_length=20, help_text='手机号，登录时使用（唯一）')
    password= CharField(max_length=255, help_text='密码')
    email= CharField(max_length=255, help_text='邮箱')
    img_url= CharField(max_length=255, null=True, default='https://tse1-mm.cn.bing.net/th/id/OIP-C.3dLZ4NXxxg03pzV30ITasAAAAA?rs=1&pid=ImgDetMain', help_text='头像地址')
    spare= CharField(max_length=255, null=True, default='NULL', help_text='备用字段')
    class Meta:
        table_name = 'user_info'  # 数据库表名
class Admin(BaseModel):
# 管理员表
    admin_id=IntegerField(primary_key=True, help_text='主键，管理员唯一标识')
    user_id=IntegerField(help_text='用户id')
    nickname= CharField(max_length=255, help_text='昵称')

    class Meta:
        table_name='admin_info'

class MyAppUser(BaseModel):
# APP用户表
    id= IntegerField(primary_key=True, help_text='主键，用户唯一标识')
    account= CharField(max_length=255, help_text='账号')
    password= CharField(max_length=255, help_text='密码')
    email= CharField(max_length=255, help_text='邮箱')
    isAdmin=IntegerField(null=True, default=0, help_text='是否是管理员(0:默认 1:管理员)')
    isFrozen=IntegerField(null=True, default=0, help_text='是否冻结(0:默认 1:冻结)')
    avatar= CharField(max_length=255, null=True, default='https://tse1-mm.cn.bing.net/th/id/OIP-C.3dLZ4NXxxg03pzV30ITasAAAAA?rs=1&pid=ImgDetMain', help_text='头像地址')
    class Meta:
        table_name='app_user'
class SysGroup(BaseModel):
    group_name = CharField(primary_key=True, max_length=128, help_text='团队名称')
    group_status = BooleanField(help_text='团队状态（0：停用，1：启用）')
    update_datetime = DateTimeField(help_text='更新时间')
    update_by = CharField(max_length=32, help_text='被谁更新')
    create_datetime = DateTimeField(help_text='创建时间')
    create_by = CharField(max_length=32, help_text='被谁创建')
    group_remark = CharField(max_length=255, help_text='团队描述')

    class Meta:
        table_name = 'sys_group'


class SysRole(BaseModel):
    role_name = CharField(primary_key=True, max_length=32, help_text='角色名')
    role_status = BooleanField(help_text='角色状态（0：停用，1：启用）')
    update_datetime = DateTimeField(help_text='更新时间')
    update_by = CharField(max_length=32, help_text='被谁更新')
    create_datetime = DateTimeField(help_text='创建时间')
    create_by = CharField(max_length=32, help_text='被谁创建')
    role_remark = CharField(max_length=255, help_text='角色描述')

    class Meta:
        table_name = 'sys_role'


class SysGroupRole(BaseModel):
    group_name = ForeignKeyField(SysGroup, backref='roles', column_name='group_name', help_text='团队名称')
    role_name = ForeignKeyField(SysRole, backref='groups', column_name='role_name', help_text='角色名')

    class Meta:
        table_name = 'sys_group_role'
        indexes = ((('group_name', 'role_name'), True),)


class SysGroupUser(BaseModel):
    group_name = ForeignKeyField(SysGroup, backref='users', column_name='group_name', help_text='团队名称')
    user_name = CharField(max_length=32, help_text='用户名')
    is_admin = IntegerField(help_text='是否为管理员')

    class Meta:
        table_name = 'sys_group_user'
        indexes = ((('group_name', 'user_name'), True),)


class SysUser(BaseModel):
    user_name = CharField(primary_key=True, max_length=32, help_text='用户名')
    user_full_name = CharField(max_length=32, help_text='全名')
    user_status = BooleanField(help_text='用户状态（0：停用，1：启用）')
    password_sha256 = CharField(max_length=64, help_text='密码SHA256值')
    user_sex = CharField(max_length=64, help_text='性别')
    user_email = CharField(max_length=128, help_text='电子邮箱')
    phone_number = CharField(max_length=16, help_text='电话号码')
    update_by = CharField(max_length=32, help_text='被谁更新')
    update_datetime = DateTimeField(help_text='更新时间')
    create_by = CharField(max_length=32, help_text='被谁创建')
    create_datetime = DateTimeField(help_text='创建时间')
    user_remark = CharField(max_length=255, help_text='用户描述')
    otp_secret = CharField(max_length=16, help_text='OTP密钥')

    class Meta:
        table_name = 'sys_user'


class SysUserRole(BaseModel):
    user_name = ForeignKeyField(SysUser, backref='roles', column_name='user_name', help_text='用户名')
    role_name = ForeignKeyField(SysRole, backref='users', column_name='role_name', help_text='角色名')

    class Meta:
        table_name = 'sys_user_role'
        indexes = ((('user_name', 'role_name'), True),)


class SysRoleAccessMeta(BaseModel):
    role_name = ForeignKeyField(SysRole, backref='access_meta', column_name='role_name', help_text='角色名')
    access_meta = CharField(max_length=32, help_text='访问元数据')

    class Meta:
        table_name = 'sys_role_access_meta'
        indexes = ((('role_name', 'access_meta'), True),)
