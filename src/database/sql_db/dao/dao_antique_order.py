from peewee import JOIN
from ..entity.table_antique_order import SysAntique
from datetime import datetime
from typing import List
from dataclasses import dataclass
from database.sql_db.conn import db

def __query__(spare_id):
    query = (
        SysAntique.select(SysAntique.relic_id, SysAntique.relic_name, SysAntique.relic_type, SysAntique.relic_time,
                          SysAntique.relic_loc, SysAntique.relic_intro,SysAntique.spare_id)
        .where(SysAntique.spare_id == spare_id)
        .order_by(SysAntique.relic_id.desc())
    )
    return query

@dataclass
class Antique:
    relic_id: str
    relic_name:str
    relic_type:str
    relic_time:str
    relic_loc:str
    relic_intro:str
    spare_id:str

def get_antique_all() -> List[Antique]:
    """获取所有文物内容"""
    query = (
        SysAntique.select(SysAntique.relic_id, SysAntique.relic_name, SysAntique.relic_type, SysAntique.relic_time,
                          SysAntique.relic_loc, SysAntique.relic_intro, SysAntique.spare_id)
        .order_by(SysAntique.relic_id)
    )

    antiques = []
    for antique in query.dicts():
        antiques.append(
            Antique(
                relic_id=antique["relic_id"],
                relic_name=antique["relic_name"],
                relic_time=antique["relic_time"],
                relic_intro=antique["relic_intro"],
                spare_id=antique["spare_id"],
                relic_loc=antique["relic_loc"],
                relic_type=antique["relic_type"],
            )
        )
    return antiques


def get_antique_audit() -> List[Antique]:
    """获取文物状态内容"""
    query = __query__(-1)
    antiques = []
    for antique in query.dicts():
        antiques.append(
            Antique(
                relic_id=antique["relic_id"],
                relic_name=antique["relic_name"],
                relic_time=antique["relic_time"],
                relic_intro=antique["relic_intro"],
                spare_id=antique["spare_id"],
                relic_loc=antique["relic_loc"],
                relic_type=antique["relic_type"],

            )
        )
    return antiques


def get_antique_passed() -> List[Antique]:
    """获取已通过的评论内容"""
    query = __query__(1)
    antiques = []
    for antique in query.dicts():
        antiques.append(
            Antique(
                relic_id=antique["relic_id"],
                relic_name=antique["relic_name"],
                relic_time=antique["relic_time"],
                relic_intro=antique["relic_intro"],
                spare_id=antique["spare_id"],
                relic_loc=antique["relic_loc"],
                relic_type=antique["relic_type"],
            )
        )
    return antiques


def get_antique_rejected() -> List[Antique]:
    """获取已驳回的评论内容"""
    query =__query__(0)
    antiques = []
    for antique in query.dicts():
        antiques.append(
            Antique(
                relic_id=antique["relic_id"],
                relic_name=antique["relic_name"],
                relic_time=antique["relic_time"],
                relic_intro=antique["relic_intro"],
                spare_id=antique["spare_id"],
                relic_loc=antique["relic_loc"],
                relic_type=antique["relic_type"],
            )
        )
    return antiques


def pass_antique(relic_id: str) -> bool:
    """通过文物"""
    return SysAntique.update(spare_id=1).where(SysAntique.relic_id == relic_id).execute()


def reject_antique(relic_id: str) -> bool:
    """驳回文物"""
    return SysAntique.update(spare_id=0).where(SysAntique.relic_id ==relic_id).execute()


def batch_pass_antiques(relic_ids: List[str]) -> bool:
    """批量通过文物"""
    try:
        SysAntique.update(spare_id=1).where(SysAntique.relic_id.in_(relic_ids)).execute()
        return True
    except Exception:
        return False


def batch_reject_antiques(relic_ids: List[str]) -> bool:
    """批量驳回文物"""
    try:
        SysAntique.update(spare_id=0).where(SysAntique.relic_id.in_(relic_ids)).execute()
        return True
    except Exception:
        return False
