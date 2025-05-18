from peewee import CharField, Model, DateTimeField, IntegerField, TextField, BooleanField
from ..conn import db


class BaseModel(Model):
    class Meta:
        database = db()


class SysAntique(BaseModel):
    relic_id = CharField(primary_key=True)
    relic_type = IntegerField()
    relic_name = CharField()
    relic_time = CharField()
    relic_loc = CharField()
    relic_intro = TextField()
    spare_id = IntegerField(default=-1)  # -1: 待审核, 0: 已驳回, 1: 已通过
    class Meta:
        table_name = 'antiques'