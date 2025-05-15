from peewee import CharField, IntegerField,Model, DateTimeField, TextField # 根据需要导入字段类型
from .table_user import BaseModel # 假设您的基础模型定义
from database.sql_db.conn import db # 导入数据库连接实例
 
class MyBaseModel(Model):
    class Meta:
        database = db()  # 使用数据库连接实例

class MyUser(MyBaseModel):
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
class Admin(MyBaseModel):
    admin_id=IntegerField(primary_key=True, help_text='主键，管理员唯一标识')
    user_id=IntegerField(help_text='用户id',help_text='用户id')
    nickname= CharField(max_length=255, help_text='昵称')
# 1	admin_id 主键	int(11)			否	无	主键，管理员唯一标识	AUTO_INCREME
class MyAppUser(MyBaseModel):
# APP用户表
    id= IntegerField(primary_key=True, help_text='主键，用户唯一标识')
    account= CharField(max_length=255, help_text='账号')
    password= CharField(max_length=255, help_text='密码')
    email= CharField(max_length=255, help_text='邮箱')
    isAdmin=IntegerField(null=True, default=0, help_text='是否是管理员(0:默认 1:管理员)')
    isFrozen=IntegerField(null=True, default=0, help_text='是否冻结(0:默认 1:冻结)')
    avatar= CharField(max_length=255, null=True, default='https://tse1-mm.cn.bing.net/th/id/OIP-C.3dLZ4NXxxg03pzV30ITasAAAAA?rs=1&pid=ImgDetMain', help_text='头像地址')
