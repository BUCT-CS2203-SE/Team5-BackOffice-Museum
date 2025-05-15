from peewee import JOIN
from ..entity.table_comment import SysComment
from datetime import datetime
from typing import List
from dataclasses import dataclass
from database.sql_db.conn import db

@dataclass
class Comment:
    id: str
    content: str
    username: str
    avatarUrl: str
    createTime: str
    status: int


def get_comment_all() -> List[Comment]:
    """获取所有评论内容"""
    query = (
        SysComment.select(SysComment.id, SysComment.content, SysComment.username, SysComment.avatarUrl, SysComment.createTime, SysComment.status)
        .order_by(SysComment.createTime.desc())
    )

    comments = []
    for comment in query.dicts():
        comments.append(
            Comment(
                id=comment["id"],
                content=comment["content"],
                username=comment["username"],
                avatarUrl=comment["avatarUrl"],
                createTime=comment["createTime"],
                status=comment["status"]
            )
        )
    return comments

def get_comment_audit() -> List[Comment]:
    """获取评论内容"""
    query = (
        SysComment.select(SysComment.id, SysComment.content, SysComment.username, SysComment.avatarUrl, SysComment.createTime, SysComment.status)
        .where(SysComment.status == -1)
        .order_by(SysComment.createTime.desc())
    )

    comments = []
    for comment in query.dicts():
        comments.append(
            Comment(
                id=comment["id"],
                content=comment["content"],
                username=comment["username"],
                avatarUrl=comment["avatarUrl"],
                createTime=comment["createTime"],
                status=comment["status"]
            )
        )
    return comments

def get_comment_passed() -> List[Comment]:
    """获取已通过的评论内容"""
    query = (
        SysComment.select(SysComment.id, SysComment.content, SysComment.username, SysComment.avatarUrl, SysComment.createTime, SysComment.status)
        .where(SysComment.status == 1)
        .order_by(SysComment.createTime.desc())
    )

    comments = []
    for comment in query.dicts():
        comments.append(
            Comment(
                id=comment["id"],
                content=comment["content"],
                username=comment["username"],
                avatarUrl=comment["avatarUrl"],
                createTime=comment["createTime"],
                status=comment["status"]
            )
        )
    return comments

def get_comment_rejected() -> List[Comment]:
    """获取已驳回的评论内容"""
    query = (
        SysComment.select(SysComment.id, SysComment.content, SysComment.username, SysComment.avatarUrl, SysComment.createTime, SysComment.status)
        .where(SysComment.status == 0)
        .order_by(SysComment.createTime.desc())
    )

    comments = []
    for comment in query.dicts():
        comments.append(
            Comment(
                id=comment["id"],
                content=comment["content"],
                username=comment["username"],
                avatarUrl=comment["avatarUrl"],
                createTime=comment["createTime"],
                status=comment["status"]
            )
        )
    return comments

def pass_comment(id: str) -> bool:
    """通过评论"""
    return SysComment.update(status=1).where(SysComment.id == id).execute()

def reject_comment(id: str) -> bool:
    """驳回评论"""
    return SysComment.update(status=0).where(SysComment.id == id).execute()

def batch_pass_comments(ids: List[str]) -> bool:
    """批量通过评论"""
    try:
        SysComment.update(status=1).where(SysComment.id.in_(ids)).execute()
        return True
    except Exception:
        return False

def batch_reject_comments(ids: List[str]) -> bool:
    """批量驳回评论"""
    try:
        SysComment.update(status=0).where(SysComment.id.in_(ids)).execute()
        return True
    except Exception:
        return False
        
