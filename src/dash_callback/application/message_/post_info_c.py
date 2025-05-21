from server import app
from dash.dependencies import Input, Output, State
import feffery_antd_components as fac
import dash
from dash import set_props
from dash_components import MessageManager
import time
from feffery_dash_utils.style_utils import style
from i18n import t__notification
from common.utilities.util_logger import Log

logger = Log.get_logger(__name__)


def get_table_data(status_filter=None):
    from database.sql_db.dao import dao_post_info

    if status_filter is None or len(status_filter) == 0:
        posts = dao_post_info.get_post_all()
    else:
        posts = []
        if -1 in status_filter:
            posts.extend(dao_post_info.get_post_audit())
        if 0 in status_filter:
            posts.extend(dao_post_info.get_post_rejected())
        if 1 in status_filter:
            posts.extend(dao_post_info.get_post_passed())

    return [
        {
            'id': post.id,
            'content': post.content,
            'create_datetime': post.createTime,
            'create_by': post.username,
            'avatar': {
                'src': post.avatarUrl if hasattr(post, 'avatarUrl') else None,
                'height': '60px',
                'preview': False,
            },
            'post_image': {
                'src': post.imageUrl if hasattr(post, 'imageUrl') else None,
                'height': '60px',
            },
            'status': post.status,
            'status_tag': {
                'text': t__notification('待审核') if post.status == -1 else 
                       t__notification('已驳回') if post.status == 0 else 
                       t__notification('已通过'),
                'status': 'warning' if post.status == -1 else 
                         'error' if post.status == 0 else 
                         'success'
            }
        }
        for post in posts
    ]


@app.callback(
    Output('post-table-container', 'children'),
    [Input('post-init-timeout', 'timeoutCount'),
     Input('post-status-filter', 'value')],
    prevent_initial_call=True,
)
def init_table(timeoutCount, status_filter):
    """页面加载时初始化渲染表格"""
    logger.info(f"初始化表格，状态筛选：{status_filter}")
    return [
        fac.AntdTable(
            id='post-table',
            columns=[
                {
                    'title': t__notification('头像'),
                    'dataIndex': 'avatar',
                    'width': 'calc(100% / 12)',
                    'renderOptions': {
                        'renderType': 'image-avatar'
                    }
                },
                {
                    'title': t__notification('帖子图片'),
                    'dataIndex': 'post_image',
                    'width': 'calc(100% * 2 / 12)',
                    'renderOptions': {
                        'renderType': 'image'
                    }
                },
                {'title': t__notification('创建人'), 'dataIndex': 'create_by', 'width': 'calc(100% / 12)'},
                {'title': t__notification('内容'), 'dataIndex': 'content', 'width': 'calc(100% * 5 / 12)'},
                {'title': t__notification('发布时间'), 'dataIndex': 'create_datetime', 'width': 'calc(100% * 2 / 12)'},
                {
                    'title': t__notification('状态'),
                    'dataIndex': 'status_tag',
                    'renderOptions': {
                        'renderType': 'status-badge'
                    },
                    'width': 'calc(100% / 12)'
                },
            ],
            rowSelectionType='checkbox',
            data=get_table_data(status_filter),
            pagination={
                'pageSize': 10,
                'showSizeChanger': True,
                'showQuickJumper': True,
            },
            bordered=True,
            size='middle',
        ),
    ]


@app.callback(
    Output('post-table', 'data', allow_duplicate=True),
    Input('post-button-pass', 'confirmCounts'),
    [State('post-table', 'selectedRows'),
     State('post-status-filter', 'value')],
    prevent_initial_call=True,
)
def handle_batch_pass(confirmCounts, selectedRows, status_filter):
    """批量通过帖子"""
    logger.info(f"批量通过帖子，选中行：{selectedRows}")
    if not selectedRows:
        MessageManager.warning(content=t__notification('请先选择要通过的帖子'))
        return dash.no_update

    from database.sql_db.dao import dao_post_info
    post_ids = [row['id'] for row in selectedRows]
    
    if dao_post_info.batch_pass_posts(post_ids):
        MessageManager.success(content=t__notification('选中帖子通过成功'))
        # 重置选中行
        set_props('post-table', {'selectedRows': []})
        set_props('post-table', {'selectedRowKeys': []})
        return get_table_data(status_filter)
    else:
        MessageManager.error(content=t__notification('选中帖子通过失败'))
        return dash.no_update


@app.callback(
    Output('post-table', 'data', allow_duplicate=True),
    Input('post-button-reject', 'confirmCounts'),
    [State('post-table', 'selectedRows'),
     State('post-status-filter', 'value')],
    prevent_initial_call=True,
)
def handle_batch_reject(confirmCounts, selectedRows, status_filter):
    """批量驳回帖子"""
    logger.info(f"批量驳回帖子，选中行：{selectedRows}")
    if not selectedRows:
        MessageManager.warning(content=t__notification('请先选择要驳回的帖子'))
        return dash.no_update

    from database.sql_db.dao import dao_post_info
    post_ids = [row['id'] for row in selectedRows]
    
    if dao_post_info.batch_reject_posts(post_ids):
        MessageManager.success(content=t__notification('选中帖子驳回成功'))
        # 重置选中行
        set_props('post-table', {'selectedRows': []})
        set_props('post-table', {'selectedRowKeys': []})
        return get_table_data(status_filter)
    else:
        MessageManager.error(content=t__notification('选中帖子驳回失败'))
        return dash.no_update
