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
    antiques=[]
    if status_filter is None or len(status_filter) == 0:
        antiques = dao_antique_order.get_antique_all()
        #在这里添加条件
    else:
        antiques=[]
        if '绘画' in status_filter:
            antiques.extend(dao_antique_order.get_antique_paint('绘画'))
        if '纺织品' in status_filter:
            antiques.extend(dao_antique_order.get_antique_paint('纺织品'))
        if '装饰艺术' in status_filter:
            antiques.extend(dao_antique_order.get_antique_paint('装饰艺术'))
        if '金属艺术' in status_filter:
            antiques.extend(dao_antique_order.get_antique_paint('金属艺术'))
        if '印刷品和图纸' in status_filter:
            antiques.extend(dao_antique_order.get_antique_paint('印刷品和图纸'))
        if '书籍和手稿' in status_filter:
            antiques.extend(dao_antique_order.get_antique_paint('书籍和手稿'))
        if '玉石与石头' in status_filter:
            antiques.extend(dao_antique_order.get_antique_paint('玉石与石头'))
        if '雕塑' in status_filter:
            antiques.extend(dao_antique_order.get_antique_paint('雕塑'))
    return [
        {
            'id': antique.id,
            'Classifications':antique.Classifications,
            'Artist':antique.Artist,
            'Credit':antique.Credit,
            'Description':antique.Description,
            'Materials':antique.Materials,
            'Dimensions':antique.Dimensions,
            'Dynasty':antique.Dynasty,
            'Title':antique.Title,
            'ImgUrl':{
                'src':antique.ImgUrl if hasattr(antique,'ImgUrl') else None,
                'height': '200px',
                'width': '200px',
                'preview': False
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
        fac.AntdModal(
            id='antique-table-add-modal',
            title=t__notification('新增文物'),
            renderFooter=True,
            okClickClose=False,
        ),
        fac.AntdTable(
            id='antique-table',
            columns=[
                {
                    'title': t__notification('图片'),
                    'dataIndex': 'ImgUrl',
                    'width': 'calc(100%  / 8)',
                    'renderOptions': {
                        'renderType': 'image'
                    }
                },
                {'title': t__notification('文物ID'), 'dataIndex': 'id', 'width': 'calc(100% / 20)'},
                {'title': t__notification('种类'), 'dataIndex': 'Classifications', 'width': 'calc(100% / 20)'},
                {'title': t__notification('作者'), 'dataIndex': 'Artist', 'width': 'calc(100% / 15)'},
                {'title': t__notification('来源'), 'dataIndex': 'Credit', 'width': 'calc(100% / 15)'},
                {'title': t__notification('描述'), 'dataIndex': 'Description', 'width': 'calc(100% / 4)'},
                {'title': t__notification('材料'), 'dataIndex': 'Materials', 'width': 'calc(100% / 15)'},
                {'title': t__notification('尺寸'), 'dataIndex': 'Dimensions', 'width': 'calc(100% / 4)'},
                {'title': t__notification('朝代'), 'dataIndex': 'Dynasty', 'width': 'calc(100% / 8)'},
                {'title': t__notification('标题'), 'dataIndex': 'Title', 'width': 'calc(100% / 4)'},


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
    Output('antique-table-add-modal', 'visible'),
    Input('antique-button-add', 'nClicks'),
    prevent_initial_call=True,
)
def open_add_modal(nClicks):
    """显示新增数据模态框"""
    return True


@app.callback(
    Output('antique-table-add-modal', 'children'),
    Input('antique-table-add-modal', 'visible'),
    running=[Output('antique-table-add-modal', 'loading'), True, False],
    prevent_initial_call=True,
)
def refresh_add_modal(visible):
    """刷新新增数据模态框内容"""

    if visible:
        time.sleep(0.5)

        return fac.AntdForm(
            [
                fac.AntdFormItem(
                    fac.AntdInput(id='antique-classification'),
                    label=t__notification('种类'),
                ),
                fac.AntdFormItem(
                    fac.AntdInput(id='antique-artist'),
                    label=t__notification('作者'),
                ),
                fac.AntdFormItem(
                    fac.AntdInput(id='antique-src'),
                    label=t__notification('来源'),
                ),
                fac.AntdFormItem(
                    fac.AntdInput(id='antique-text'),
                    label=t__notification('描述'),
                ),
                fac.AntdFormItem(
                    fac.AntdInput(id='antique-marital'),
                    label=t__notification('材料'),
                ),
                fac.AntdFormItem(
                    fac.AntdInput(id='antique-size'),
                    label=t__notification('尺寸'),
                ),
                fac.AntdFormItem(
                    fac.AntdInput(id='antique-dynasty'),
                    label=t__notification('朝代'),
                ),
                fac.AntdFormItem(
                    fac.AntdInput(id='antique-title'),
                    label=t__notification('标题'),
                ),
                fac.AntdFormItem(
                    fac.AntdInput(id='antique-ImgUrl'),
                    label=t__notification('URL'),
                ),
            ],
        )
    return dash.no_update


@app.callback(
    Output('antique-table', 'data', allow_duplicate=True),
    Input('antique-table-add-modal', 'okCounts'),
    State('antique-classification', 'value'),
    State('antique-artist', 'value'),
    State('antique-src', 'value'),
    State('antique-text', 'value'),
    State('antique-marital', 'value'),
    State('antique-size', 'value'),
    State('antique-dynasty', 'value'),
    State('antique-title', 'value'),
    State('antique-ImgUrl', 'value'),
    prevent_initial_call=True,
)
def handle_add_data(okCounts, classification, artist,src, text,marital,size, dynasty, title, ImgUrl):
    """处理新增数据逻辑"""
    print(classification, artist,src, text,marital,size, dynasty, title, ImgUrl)
    from database.sql_db.dao import dao_antique_order


    p=dao_antique_order.add_antique(classification, artist,src,text,marital,size,dynasty, title, ImgUrl)
    if p:
        MessageManager.success(content=t__notification('数据新增成功'))
    else:
        MessageManager.success(content=t__notification('数据新增失败'))
    return get_table_data()


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
    logger.info(f"批量驳回评论，选中行：{selectedRows}")
    if not selectedRows:
        MessageManager.warning(content=t__notification('请先选择要删除的文物'))
        return dash.no_update

    from database.sql_db.dao import dao_antique_order
    antique_ids = [row['id'] for row in selectedRows]

    if dao_antique_order.batch_reject_antiques(antique_ids):
        MessageManager.success(content=t__notification('选中文物删除成功'))
        # 重置选中行
        set_props('antique-table', {'selectedRows': []})
        set_props('antique-table', {'selectedRowKeys': []})
        return get_table_data(status_filter)
    else:
        MessageManager.error(content=t__notification('选中文物删除失败'))
        return dash.no_update


