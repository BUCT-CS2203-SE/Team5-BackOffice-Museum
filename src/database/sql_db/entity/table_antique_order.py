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
    class Meta:
        table_name = 'art'