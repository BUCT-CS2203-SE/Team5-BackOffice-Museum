from peewee import CharField, Model, DateTimeField, IntegerField, TextField, BooleanField
from ..conn import db


class BaseModel(Model):
    class Meta:
        database = db()


class SysComment(BaseModel):
    id = CharField(primary_key=True)
    artifactId = IntegerField()
    userId = CharField()
    username = CharField()
    avatarUrl = CharField()
    content = TextField()
    createTime = CharField()
    createTimestamp = DateTimeField()
    createdAt = DateTimeField()
    updatedAt = DateTimeField()
    status = IntegerField(default=-1)  # -1: 待审核, 0: 已驳回, 1: 已通过
    
    class Meta:
        table_name = 'comments'

