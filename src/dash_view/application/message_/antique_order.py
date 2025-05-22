from common.utilities.util_menu_access import MenuAccess
import feffery_antd_components as fac
import feffery_utils_components as fuc
from common.utilities.util_logger import Log
from dash import html
from dash_components import Card
import dash_callback.application.message_.antique_order_c  # noqa: F401
from i18n import t__notification, translator

from src.database.sql_db.dao.dao_antique_order import Antique
from src.database.sql_db.entity.table_antique_order import SysAntique

# 二级菜单的标题、图标和显示顺序
title = '文物管理'
icon = None
logger = Log.get_logger(__name__)
order = 2
access_metas = ('文物管理-页面',)

def render_content(menu_access: MenuAccess, **kwargs):
    query=SysAntique.select(SysAntique.Classifications)
    print(query)
    return [
        fac.Fragment(
            [
                fuc.FefferyTimeout(id='antique-init-timeout', delay=1),
            ]
        ),
        fac.AntdSpace(
            [
                fac.AntdSpace(
                    [
                        fac.AntdSelect(
                            id='antique-status-filter',
                            options=[
                                {'label': t__notification('绘画'), 'value':'绘画'},
                                {'label': t__notification('纺织品'), 'value': '纺织品'},
                                {'label': t__notification('装饰艺术'), 'value': '装饰艺术'},
                                {'label': t__notification('雕塑'), 'value': '雕塑'},
                                {'label': t__notification('金属艺术'), 'value': '金属艺术'},
                                {'label': t__notification('玉石与石头'), 'value': '玉石与石头'},
                                {'label': t__notification('印刷品和图纸'), 'value': '印刷品和图纸'},
                                {'label': t__notification('书籍和手稿'), 'value': '书籍和手稿'}
                            ],
                            mode='multiple',
                            placeholder=t__notification('请选择文物种类'),
                            style={'width': '200px'},
                        ),
                    ]
                ),
                fac.AntdSpace(
                    [
                    fac.AntdButton(
                        id='antique-button-add',
                        children=t__notification('新增文物'),
                        type='primary',
                        icon=fac.AntdIcon(icon='antd-plus'),
                    ),
                    fac.AntdPopconfirm(
                        fac.AntdButton(
                            t__notification('删除选中'),
                            type='primary',
                            danger=True,
                            icon=fac.AntdIcon(icon='antd-close'),
                        ),
                        id='antique-button-reject',
                        title=t__notification('确认删除选中行吗？'),
                        locale=translator.get_current_locale(),
                    )
                ]
                ),


                Card(
                    html.Div(
                        id='antique-table-container',
                        style={'width': '100%'},
                    ),
                    style={'width': '100%'},
                ),
            ],
            direction='vertical',
            style={
                'marginBottom': '10px',
                'width': '100%',
            },
        ),

    ]