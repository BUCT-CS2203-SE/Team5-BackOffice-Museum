from peewee import CharField, Model, IntegerField, TextField, SmallIntegerField, BigIntegerField
from ..conn import db


class BaseModel(Model):
    class Meta:
        database = db()


class SysPostComment(BaseModel):
    comment_id = CharField(primary_key=True)
    post_id = CharField()
    user_id = IntegerField()
    nickname = CharField()
    img_url = CharField()
    content = TextField()
    create_time = CharField()
    create_timestamp = BigIntegerField()
    status = SmallIntegerField(default=-1)  # -1: 待审核, 0: 已驳回, 1: 已通过
    
    class Meta:
        table_name = 'post_comment'

