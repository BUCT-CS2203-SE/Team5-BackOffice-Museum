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
    from database.sql_db.dao import dao_post_comment

    if status_filter is None or len(status_filter) == 0:
        comments = dao_post_comment.get_comment_all()
    else:
        comments = []
        if -1 in status_filter:
            comments.extend(dao_post_comment.get_comment_audit())
        if 0 in status_filter:
            comments.extend(dao_post_comment.get_comment_rejected())
        if 1 in status_filter:
            comments.extend(dao_post_comment.get_comment_passed())

    return [
        {
            'id': comment.id,
            'content': comment.content,
            'create_datetime': comment.createTime,
            'create_by': comment.username,
            'avatar': {
                'src': comment.avatarUrl if hasattr(comment, 'avatarUrl') else None,
                'height': '40px',
                'width': '40px',
                'preview': False
            },
            'status': comment.status,
            'status_tag': {
                'text': t__notification('待审核') if comment.status == -1 else 
                       t__notification('已驳回') if comment.status == 0 else 
                       t__notification('已通过'),
                'status': 'warning' if comment.status == -1 else 
                         'error' if comment.status == 0 else 
                         'success'
            }
        }
        for comment in comments
    ]


@app.callback(
    Output('comment-table-container', 'children'),
    [Input('comment-init-timeout', 'timeoutCount'),
     Input('comment-status-filter', 'value')],
    prevent_initial_call=True,
)
def init_table(timeoutCount, status_filter):
    """页面加载时初始化渲染表格"""
    logger.info(f"初始化表格，状态筛选：{status_filter}")
    return [
        fac.AntdTable(
            id='comment-table',
            columns=[
                {
                    'title': t__notification('头像'),
                    'dataIndex': 'avatar',
                    'width': 'calc(100% / 8)',
                    'renderOptions': {
                        'renderType': 'image-avatar'
                    }
                },
                {'title': t__notification('创建人'), 'dataIndex': 'create_by', 'width': 'calc(100% / 8)'},
                {'title': t__notification('内容'), 'dataIndex': 'content', 'width': 'calc(100% * 3 / 8)'},
                {'title': t__notification('发布时间'), 'dataIndex': 'create_datetime', 'width': 'calc(100% * 2 / 8)'},
                {
                    'title': t__notification('状态'),
                    'dataIndex': 'status_tag',
                    'renderOptions': {
                        'renderType': 'status-badge'
                    },
                    'width': 'calc(100% / 8)'
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
    Output('comment-table', 'data', allow_duplicate=True),
    Input('comment-button-pass', 'confirmCounts'),
    [State('comment-table', 'selectedRows'),
     State('comment-status-filter', 'value')],
    prevent_initial_call=True,
)
def handle_batch_pass(confirmCounts, selectedRows, status_filter):
    """批量通过评论"""
    logger.info(f"批量通过评论，选中行：{selectedRows}")
    if not selectedRows:
        MessageManager.warning(content=t__notification('请先选择要通过的评论'))
        return dash.no_update

    from database.sql_db.dao import dao_post_comment
    comment_ids = [row['id'] for row in selectedRows]
    
    if dao_post_comment.batch_pass_comments(comment_ids):
        MessageManager.success(content=t__notification('选中评论通过成功'))
        # 重置选中行
        set_props('comment-table', {'selectedRows': []})
        set_props('comment-table', {'selectedRowKeys': []})
        return get_table_data(status_filter)
    else:
        MessageManager.error(content=t__notification('选中评论通过失败'))
        return dash.no_update


@app.callback(
    Output('comment-table', 'data', allow_duplicate=True),
    Input('comment-button-reject', 'confirmCounts'),
    [State('comment-table', 'selectedRows'),
     State('comment-status-filter', 'value')],
    prevent_initial_call=True,
)
def handle_batch_reject(confirmCounts, selectedRows, status_filter):
    """批量驳回评论"""
    logger.info(f"批量驳回评论，选中行：{selectedRows}")
    if not selectedRows:
        MessageManager.warning(content=t__notification('请先选择要驳回的评论'))
        return dash.no_update

    from database.sql_db.dao import dao_post_comment
    comment_ids = [row['id'] for row in selectedRows]
    
    if dao_post_comment.batch_reject_comments(comment_ids):
        MessageManager.success(content=t__notification('选中评论驳回成功'))
        # 重置选中行
        set_props('comment-table', {'selectedRows': []})
        set_props('comment-table', {'selectedRowKeys': []})
        return get_table_data(status_filter)
    else:
        MessageManager.error(content=t__notification('选中评论驳回失败'))
        return dash.no_update
