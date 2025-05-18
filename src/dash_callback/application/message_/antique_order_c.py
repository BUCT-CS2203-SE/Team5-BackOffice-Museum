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
    from database.sql_db.dao import dao_antique_order
    if status_filter is None or len(status_filter) == 0:
        antiques = dao_antique_order.get_antique_all()
    else:
        antiques = []
        if -1 in status_filter:
            antiques.extend(dao_antique_order.get_antique_audit())
        if 0 in status_filter:
            antiques.extend(dao_antique_order.get_antique_rejected())
        if 1 in status_filter:
            antiques.extend(dao_antique_order.get_antique_passed())
    return [
        {
            'id': antique.relic_id,
            'relic_id': antique.relic_id,
            'relic_name': antique.relic_name,
            'relic_type': antique.relic_type,
            'relic_time':antique.relic_time,
            'relic_loc': antique.relic_loc,
            'relic_intro':antique.relic_intro,
            'spare_id': antique.spare_id,
            'status_tag': {
                'text': t__notification('待审核') if antique.spare_id == -1 else
                t__notification('已驳回') if antique.spare_id == 0 else
                t__notification('已通过'),
                'status': 'warning' if antique.spare_id == -1 else
                'error' if antique.spare_id == 0 else
                'success'
            }
        }
        for antique in antiques
    ]


@app.callback(
    Output('antique-table-container', 'children'),
    [Input('antique-init-timeout', 'timeoutCount'),
     Input('antique-status-filter', 'value')],
    prevent_initial_call=True,
)
def init_table(timeoutCount, status_filter):
    """页面加载时初始化渲染文物信息表格"""
    logger.info(f"初始化文物表格，状态筛选：{status_filter}")
    return [
        fac.AntdTable(
            id='antique-table',
            columns=[
                {'title': t__notification('文物ID'), 'dataIndex': 'relic_id', 'width': 'calc(100% / 8)'},
                {'title': t__notification('名称'), 'dataIndex': 'relic_name', 'width': 'calc(100% / 8)'},
                {'title': t__notification('年代'), 'dataIndex': 'relic_time', 'width': 'calc(100% / 8)'},
                {'title': t__notification('简介'), 'dataIndex': 'relic_intro', 'width': 'calc(100% / 8)'},
                {'title': t__notification('备用ID'), 'dataIndex': 'spare_id', 'width': 'calc(100% / 8)'},
                {'title': t__notification('位置'), 'dataIndex': 'relic_loc', 'width': 'calc(100% / 8)'},
                {'title': t__notification('类型'), 'dataIndex': 'relic_type', 'width': 'calc(100% / 8)'},
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
    Output('antique-table', 'data', allow_duplicate=True),
    Input('antique-button-pass', 'confirmCounts'),
    [State('antique-table', 'selectedRows'),
     State('antique-status-filter', 'value')],
    prevent_initial_call=True,
)
def handle_batch_pass(confirmCounts, selectedRows, status_filter):
    """批量通过评论"""
    logger.info(f"批量通过文物，选中行：{selectedRows}")
    if not selectedRows:
        MessageManager.warning(content=t__notification('请先选择要通过的文物'))
        return dash.no_update

    from database.sql_db.dao import dao_antique_order
    antique_ids = [row['id'] for row in selectedRows]

    if dao_antique_order.batch_pass_antiques(antique_ids):
        MessageManager.success(content=t__notification('选中文物通过成功'))
        # 重置选中行
        set_props('antique-table', {'selectedRows': []})
        set_props('antique-table', {'selectedRowKeys': []})
        return get_table_data(status_filter)
    else:
        MessageManager.error(content=t__notification('选中文物通过失败'))
        return dash.no_update


@app.callback(
    Output('antique-table', 'data', allow_duplicate=True),
    Input('antique-button-reject', 'confirmCounts'),
    [State('antique-table', 'selectedRows'),
     State('antique-status-filter', 'value')],
    prevent_initial_call=True,
)
def handle_batch_reject(confirmCounts, selectedRows, status_filter):
    """批量驳回评论"""
    logger.info(f"批量驳回文物，选中行：{selectedRows}")
    if not selectedRows:
        MessageManager.warning(content=t__notification('请先选择要驳回的文物'))
        return dash.no_update

    from database.sql_db.dao import dao_antique_order
    antique_ids = [row['id'] for row in selectedRows]

    if dao_antique_order.batch_reject_antiques(antique_ids):
        MessageManager.success(content=t__notification('选中评论驳回文物'))
        # 重置选中行
        set_props('antique-table', {'selectedRows': []})
        set_props('antique-table', {'selectedRowKeys': []})
        return get_table_data(status_filter)
    else:
        MessageManager.error(content=t__notification('选中文物驳回失败'))
        return dash.no_update