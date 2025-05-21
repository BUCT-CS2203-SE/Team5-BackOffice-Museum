from peewee import JOIN
from ..entity.table_post_comment import SysPostComment
from datetime import datetime,timedelta
from typing import List
from dataclasses import dataclass
from database.sql_db.conn import db
from peewee import fn

@dataclass
class PostComment:
    id: str
    content: str
    username: str
    avatarUrl: str
    createTime: str
    status: int


def get_comment_all() -> List[PostComment]:
    """获取所有评论内容"""
    query = (
        SysPostComment.select(SysPostComment.comment_id, SysPostComment.content, SysPostComment.nickname, SysPostComment.img_url, SysPostComment.create_timestamp, SysPostComment.status)
        .order_by(SysPostComment.create_timestamp.desc())
    )

    comments = []
    for comment in query.dicts():
        comments.append(
            PostComment(
                id=comment["comment_id"],
                content=comment["content"],
                username=comment["nickname"],
                avatarUrl=comment["img_url"],
                createTime=datetime.fromtimestamp(comment["create_timestamp"] / 1000).strftime("%Y年%m月%d日 %H:%M"),
                status=comment["status"]
            )
        )
    return comments

def get_comment_audit() -> List[PostComment]:
    """获取评论内容"""
    query = (
        SysPostComment.select(SysPostComment.comment_id, SysPostComment.content, SysPostComment.nickname, SysPostComment.img_url, SysPostComment.create_timestamp, SysPostComment.status)
        .where(SysPostComment.status == -1)
        .order_by(SysPostComment.create_timestamp.desc())
    )

    comments = []
    for comment in query.dicts():
        comments.append(
            PostComment(
                id=comment["comment_id"],
                content=comment["content"],
                username=comment["nickname"],
                avatarUrl=comment["img_url"],
                createTime=datetime.fromtimestamp(comment["create_timestamp"] / 1000).strftime("%Y年%m月%d日 %H:%M"),
                status=comment["status"]
            )
        )
    return comments

def get_comment_passed() -> List[PostComment]:
    """获取已通过的评论内容"""
    query = (
        SysPostComment.select(SysPostComment.comment_id, SysPostComment.content, SysPostComment.nickname, SysPostComment.img_url, SysPostComment.create_timestamp, SysPostComment.status)
        .where(SysPostComment.status == 1)
        .order_by(SysPostComment.create_timestamp.desc())
    )

    comments = []
    for comment in query.dicts():
        comments.append(
            PostComment(
                id=comment["comment_id"],
                content=comment["content"],
                username=comment["nickname"],
                avatarUrl=comment["img_url"],
                createTime=datetime.fromtimestamp(comment["create_timestamp"] / 1000).strftime("%Y年%m月%d日 %H:%M"),
                status=comment["status"]
            )
        )
    return comments

def get_comment_rejected() -> List[PostComment]:
    """获取已驳回的评论内容"""
    query = (
        SysPostComment.select(SysPostComment.comment_id, SysPostComment.content, SysPostComment.nickname, SysPostComment.img_url, SysPostComment.create_timestamp, SysPostComment.status)
        .where(SysPostComment.status == 0)
        .order_by(SysPostComment.create_timestamp.desc())
    )

    comments = []
    for comment in query.dicts():
        comments.append(
            PostComment(
                id=comment["comment_id"],
                content=comment["content"],
                username=comment["nickname"],
                avatarUrl=comment["img_url"],
                createTime=datetime.fromtimestamp(comment["create_timestamp"] / 1000).strftime("%Y年%m月%d日 %H:%M"),
                status=comment["status"]
            )
        )
    return comments

def get_comment_status_stats():
    """获取评论状态统计（包含总和）"""
    pending = SysPostComment.select().where(SysPostComment.status == -1).count()
    approved = SysPostComment.select().where(SysPostComment.status == 1).count()
    rejected = SysPostComment.select().where(SysPostComment.status == 0).count()
    
    return {
        '待审核': pending,
        '已通过': approved,
        '已驳回': rejected,
        '总计': pending + approved + rejected
    }

def batch_pass_comments(ids: List[str]) -> bool:
    """批量通过评论"""
    try:
        SysPostComment.update(status=1).where(SysPostComment.comment_id.in_(ids)).execute()
        return True
    except Exception:
        return False

def batch_reject_comments(ids: List[str]) -> bool:
    """批量驳回评论"""
    try:
        SysPostComment.update(status=0).where(SysPostComment.comment_id.in_(ids)).execute()
        return True
    except Exception:
        return False
    
def get_daily_comment_counts(days: int = 10):
    """获取最近N天的每日评论数量"""
    today = datetime.now().date()
    date_range = [
        (today - timedelta(days=days-1-i)).strftime('%Y-%m-%d') 
        for i in range(days)
    ]
    query = (
        SysPostComment.select(
            fn.DATE(SysPostComment.create_timestamp).alias('date'),
            fn.COUNT(SysPostComment.comment_id).alias('count')
        )
        .where(
            fn.DATE(SysPostComment.create_timestamp).between(
                today - timedelta(days=days),
                today
            )
        )
        .group_by(fn.DATE(SysPostComment.create_timestamp))
        .order_by(fn.DATE(SysPostComment.create_timestamp))
    )
    result = {r['date']: r['count'] for r in query.dicts()}
    
    return [
        {'date': date, 'count': result.get(date, 0)}
        for date in date_range
    ]
