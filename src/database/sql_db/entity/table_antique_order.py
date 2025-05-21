from peewee import CharField, Model, DateTimeField, IntegerField, TextField, BooleanField
from ..conn import db


class BaseModel(Model):
    class Meta:
        database = db()


class SysAntique(BaseModel):
    id = CharField(primary_key=True)
    Classifications = CharField()
    Artist=CharField()
    Credit= CharField()
    Description= CharField()
    Materials= CharField()
    Dimensions = TextField()
    Dynasty=CharField()
    Title=CharField()
    ImgUrl=CharField()
    ImgPath=CharField()
    spare_id = IntegerField(default=-1)  # -1: 待审核, 0: 已驳回, 1: 已通过
    class Meta:
        table_name = 'art'