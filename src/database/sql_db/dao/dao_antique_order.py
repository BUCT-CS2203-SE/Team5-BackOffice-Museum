from peewee import JOIN
from ..entity.table_antique_order import SysAntique
from datetime import datetime
from typing import List
from dataclasses import dataclass
from database.sql_db.conn import db

def __query__(type):
    query = (
        SysAntique.select(SysAntique.id,SysAntique.Classifications , SysAntique.Artist, SysAntique.Credit,
                          SysAntique.Description, SysAntique.Materials,SysAntique.Dimensions,SysAntique.Dynasty,SysAntique.Title)
         .where(SysAntique.Classifications == type)
    )
    return query

@dataclass
class Antique:
    id: str
    Classifications : str
    Artist : str
    Credit : str
    Description : str
    Materials : str
    Dimensions : str
    Dynasty : str
    Title : str
    ImgUrl : str
    ImgPath : str

def get_antique_all() -> List[Antique]:
    """获取所有文物内容"""
    query = (
        SysAntique.select(SysAntique.id, SysAntique.Classifications, SysAntique.Artist, SysAntique.Credit,
                          SysAntique.Description, SysAntique.Materials, SysAntique.Dimensions, SysAntique.Dynasty,
                          SysAntique.Title,SysAntique.ImgUrl,SysAntique.ImgPath)
    )

    antiques = []
    for antique in query.dicts():
        antiques.append(
            Antique(
                id=antique["id"],
                Classifications=antique["Classifications"],
                Artist=antique["Artist"],
                Credit=antique["Credit"],
                Description=antique["Description"],
                Materials=antique["Materials"],
                Dimensions=antique["Dimensions"],
                Dynasty=antique["Dynasty"],
                Title=antique["Title"],
                ImgUrl = antique.get("ImgUrl", "") , # 如果没有 ImgUrl，就用空字符串
                ImgPath=antique.get("ImgPath", "")  # 如果没有 ImgUrl，就用空字符串
            )
        )
    return antiques
def insert_antique(title,artist,dynasty,classification,credit,description,materials,dimensions,imgurl):
    SysAntique.create(
        Title=title,
        Artist=artist,
        Dynasty=dynasty,
        Classifications=classification,
        Credit=credit,
        Description=description,
        Materials=materials,
        Dimensions=dimensions,
        ImgUrl=imgurl,
        ImgPath=''  # 如果你没有上传文件功能，可以先留空
    )
def get_antique_paint(type) -> List[Antique]:
    """获取指定文物内容"""
    #query =__query__("绘画")
    query = (
        SysAntique.select(SysAntique.id, SysAntique.Classifications, SysAntique.Artist, SysAntique.Credit,
                          SysAntique.Description, SysAntique.Materials, SysAntique.Dimensions, SysAntique.Dynasty,
                          SysAntique.Title)
        .where(SysAntique.Classifications == type)
    )
    antiques = []
    for antique in query.dicts():
        antiques.append(
            Antique(
                id=antique["id"],
                Classifications=antique["Classifications"],
                Artist=antique["Artist"],
                Credit=antique["Credit"],
                Description=antique["Description"],
                Materials=antique["Materials"],
                Dimensions=antique["Dimensions"],
                Dynasty=antique["Dynasty"],
                Title=antique["Title"],
                ImgUrl=antique.get("ImgUrl", ""),  # 如果没有 ImgUrl，就用空字符串
                ImgPath=antique.get("ImgPath", "")
            )
        )
    return antiques



'''
def pass_antique(relic_id: str) -> bool:
    """通过文物"""
    return SysAntique.update(spare_id=1).where(SysAntique.relic_id == relic_id).execute()

'''
def reject_antique(relic_id: str) -> bool:
    """驳回文物"""
    return SysAntique.delete().where(SysAntique.id ==relic_id).execute()

'''
def batch_pass_antiques(relic_ids: List[str]) -> bool:
    """批量通过文物"""
    try:
        SysAntique.update(spare_id=1).where(SysAntique.relic_id.in_(relic_ids)).execute()
        return True
    except Exception:
        return False

'''
def add_antique(classification, artist,src, text,marital,size, dynasty, title, ImgUrl):
    try:
        print(classification, artist,src, text,marital,size, dynasty, title, ImgUrl)
        SysAntique.create(Classifications=classification, Artist=artist,Credit=src, Description= text,Materials=marital,Dimensions = size,Dynasty= dynasty, Title=title, ImgUrl=ImgUrl)
        return True
    except Exception as e:
        print('失败',e)
        return False
'''
def add_announcement(announcement: str, user_name: str) -> bool:
    """新增文物"""
    database = db()
    with database.atomic() as txn:
        SysAnnouncement.create(announcement=announcement, user_name=user_name, datetime=datetime.now(), status=True)
'''
def batch_reject_antiques(relic_ids: List[str]) -> bool:
    """批量驳回文物"""
    try:
        SysAntique.delete().where(SysAntique.id.in_(relic_ids)).execute()

        return True
    except Exception:
        return False
