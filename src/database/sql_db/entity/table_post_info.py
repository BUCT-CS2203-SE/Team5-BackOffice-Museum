from peewee import CharField, Model, IntegerField, TextField, BooleanField, BigIntegerField, SmallIntegerField
from ..conn import db


class BaseModel(Model):
    class Meta:
        database = db()
        
class SysPostInfo(BaseModel):
    post_id = CharField(primary_key=True)
    content = TextField()
    post_img_url = CharField()
    likes = IntegerField()
    is_favorited = BooleanField()
    user_id = IntegerField()
    nickname = CharField()
    img_url = CharField()
    create_time = CharField()
    create_timestamp = BigIntegerField()
    status = SmallIntegerField(default=-1)  # -1: 待审核, 0: 已驳回, 1: 已通过
    
    class Meta:
        table_name = 'post_info'