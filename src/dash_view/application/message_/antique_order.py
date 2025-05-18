from common.utilities.util_menu_access import MenuAccess
import feffery_antd_components as fac
import feffery_utils_components as fuc
from common.utilities.util_logger import Log
from dash import html
from dash_components import Card
import dash_callback.application.message_.antique_order_c  # noqa: F401
from i18n import t__notification, translator


# 二级菜单的标题、图标和显示顺序
title = '文物管理'
icon = None
logger = Log.get_logger(__name__)
order = 2
access_metas = ('文物管理-页面',)


def render_content(menu_access: MenuAccess, **kwargs):
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
                                {'label': t__notification('待审核'), 'value': -1},
                                {'label': t__notification('已驳回'), 'value': 0},
                                {'label': t__notification('已通过'), 'value': 1},
                            ],
                            mode='multiple',
                            placeholder=t__notification('请选择文物状态'),
                            style={'width': '200px'},
                        ),
                        fac.AntdPopconfirm(
                            fac.AntdButton(
                                t__notification('通过选中'),
                                type='primary',
                                icon=fac.AntdIcon(icon='antd-check'),
                            ),
                            id='antique-button-pass',
                            title=t__notification('确认通过选中行吗？'),
                            locale=translator.get_current_locale(),
                        ),
                        fac.AntdPopconfirm(
                            fac.AntdButton(
                                t__notification('驳回选中'),
                                type='primary',
                                danger=True,
                                icon=fac.AntdIcon(icon='antd-close'),
                            ),
                            id='antique-button-reject',
                            title=t__notification('确认驳回选中行吗？'),
                            locale=translator.get_current_locale(),
                        ),
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