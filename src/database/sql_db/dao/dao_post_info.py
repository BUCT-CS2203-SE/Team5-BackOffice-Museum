from peewee import JOIN
from ..entity.table_post_info import SysPostInfo
from datetime import datetime,timedelta
from typing import List
from dataclasses import dataclass
from database.sql_db.conn import db
from peewee import fn

@dataclass
class PostInfo:
    id: str
    content: str
    username: str
    imageUrl: str
    avatarUrl: str
    createTime: str
    status: int
    
def get_post_all() -> List[PostInfo]:
    """获取所有评论内容"""
    query = (
        SysPostInfo.select(SysPostInfo.post_id, SysPostInfo.content, SysPostInfo.nickname,SysPostInfo.post_img_url, SysPostInfo.img_url, SysPostInfo.create_timestamp, SysPostInfo.status)
        .order_by(SysPostInfo.create_timestamp.desc())
    )

    posts = []
    for post in query.dicts():
        posts.append(
            PostInfo(
                id=post["post_id"],
                content=post["content"],
                username=post["nickname"],
                imageUrl=post["post_img_url"],
                avatarUrl=post["img_url"],
                createTime=datetime.fromtimestamp(post["create_timestamp"] / 1000).strftime("%Y年%m月%d日 %H:%M"),
                status=post["status"]
            )
        )
    return posts

def get_post_audit() -> List[PostInfo]:
    """获取评论内容"""
    query = (
        SysPostInfo.select(SysPostInfo.post_id, SysPostInfo.content, SysPostInfo.nickname, SysPostInfo.img_url, SysPostInfo.create_timestamp, SysPostInfo.status)
        .where(SysPostInfo.status == -1)
        .order_by(SysPostInfo.create_timestamp.desc())
    )

    posts = []
    for post in query.dicts():
        posts.append(
            PostInfo(
                id=post["post_id"],
                content=post["content"],
                username=post["nickname"],
                imageUrl=post["post_img_url"],
                avatarUrl=post["img_url"],
                createTime=datetime.fromtimestamp(post["create_timestamp"] / 1000).strftime("%Y年%m月%d日 %H:%M"),
                status=post["status"]
            )
        )
    return posts

def get_post_passed() -> List[PostInfo]:
    """获取已通过的评论内容"""
    query = (
        SysPostInfo.select(SysPostInfo.post_id, SysPostInfo.content, SysPostInfo.nickname, SysPostInfo.img_url, SysPostInfo.create_timestamp, SysPostInfo.status)
        .where(SysPostInfo.status == 1)
        .order_by(SysPostInfo.create_timestamp.desc())
    )

    posts = []
    for post in query.dicts():
        posts.append(
            PostInfo(
                id=post["post_id"],
                content=post["content"],
                username=post["nickname"],
                imageUrl=post["post_img_url"],
                avatarUrl=post["img_url"],
                createTime=datetime.fromtimestamp(post["create_timestamp"] / 1000).strftime("%Y年%m月%d日 %H:%M"),
                status=post["status"]
            )
        )
    return posts

def get_post_rejected() -> List[PostInfo]:
    """获取已驳回的评论内容"""
    query = (
        SysPostInfo.select(SysPostInfo.post_id, SysPostInfo.content, SysPostInfo.nickname, SysPostInfo.img_url, SysPostInfo.create_timestamp, SysPostInfo.status)
        .where(SysPostInfo.status == 0)
        .order_by(SysPostInfo.create_timestamp.desc())
    )

    posts = []
    for post in query.dicts():
        posts.append(
            PostInfo(
                id=post["post_id"],
                content=post["content"],
                username=post["nickname"],
                imageUrl=post["post_img_url"],
                avatarUrl=post["img_url"],
                createTime=datetime.fromtimestamp(post["create_timestamp"] / 1000).strftime("%Y年%m月%d日 %H:%M"),
                status=post["status"]
            )
        )
    return posts

def get_post_status_stats():
    """获取评论状态统计（包含总和）"""
    pending = SysPostInfo.select().where(SysPostInfo.status == -1).count()
    approved = SysPostInfo.select().where(SysPostInfo.status == 1).count()
    rejected = SysPostInfo.select().where(SysPostInfo.status == 0).count()
    
    return {
        '待审核': pending,
        '已通过': approved,
        '已驳回': rejected,
        '总计': pending + approved + rejected
    }

def batch_pass_posts(ids: List[str]) -> bool:
    """批量通过评论"""
    try:
        SysPostInfo.update(status=1).where(SysPostInfo.post_id.in_(ids)).execute()
        return True
    except Exception:
        return False

def batch_reject_posts(ids: List[str]) -> bool:
    """批量驳回评论"""
    try:
        SysPostInfo.update(status=0).where(SysPostInfo.post_id.in_(ids)).execute()
        return True
    except Exception:
        return False
    
def get_daily_post_counts(days: int = 10):
    """获取最近N天的每日评论数量"""
    today = datetime.now().date()
    date_range = [
        (today - timedelta(days=days-1-i)).strftime('%Y-%m-%d') 
        for i in range(days)
    ]
    query = (
        SysPostInfo.select(
            fn.DATE(SysPostInfo.create_timestamp).alias('date'),
            fn.COUNT(SysPostInfo.post_id).alias('count')
        )
        .where(
            fn.DATE(SysPostInfo.create_timestamp).between(
                today - timedelta(days=days),
                today
            )
        )
        .group_by(fn.DATE(SysPostInfo.create_timestamp))
        .order_by(fn.DATE(SysPostInfo.create_timestamp))
    )
    result = {r['date']: r['count'] for r in query.dicts()}
    
    return [
        {'date': date, 'count': result.get(date, 0)}
        for date in date_range
    ]
