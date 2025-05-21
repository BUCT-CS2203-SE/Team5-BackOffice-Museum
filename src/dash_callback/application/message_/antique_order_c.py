from opcode import hasarg

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



