from common.utilities.util_menu_access import MenuAccess
import random
import feffery_antd_charts as fact
import feffery_antd_components as fac
import feffery_utils_components as fuc
from feffery_dash_utils.style_utils import style
from dash_components import Card
import feffery_antd_components as fac
from common.utilities.util_logger import Log
from i18n import t__dashboard
from datetime import datetime, timedelta
from peewee import fn
from database.sql_db.dao import dao_post_comment
from database.sql_db.dao import dao_announcement
from database.sql_db.dao.dao_post_comment import get_daily_comment_counts

stats = dao_post_comment.get_comment_status_stats()
# 二级菜单的标题、图标和显示顺序
title = '工作台'
icon = None
order = 1
logger = Log.get_logger(__name__)
today = datetime.now()
access_metas = ('工作台-页面',)

def chart_block(title, chart):
    return fac.AntdFlex(
        [
            fac.AntdText(
                title,
                style={
                    'borderLeft': '3px solid #1890ff',
                    'paddingLeft': '8px',
                    'fontSize': '15px',
                    'fontWeight': '500'
                }
            ),
            chart,
        ],
        vertical=True,
        gap=8,
        style={
            'height': 'calc(100% - 20px)',
            'padding': '8px'
        }
    )
#chartblock似乎有点bug，不能运行得改成最开始的那个函数
"""def chart_block(title, chart):

    return fac.AntdFlex(
        [
            fac.AntdText(
                title,
                style=style(borderLeft='3px solid #1890ff', paddingLeft=8, fontSize=15),
            ),
            chart,
        ],
        vertical=True,
        gap=8,
        style=style(height='calc(100% - 20px)'),
    )"""
def render_content(menu_access: MenuAccess, **kwargs):
    return fac.AntdSpace(
        [
            Card(
                fac.AntdSpace(
                    [
                        fac.AntdAvatar(
                            id='workbench-avatar',
                            mode='image',
                            src=f'/avatar/{menu_access.user_info.user_name}',
                            alt=menu_access.user_info.user_full_name,
                            size=70,
                            style={'marginRight': '20px'},
                        ),
                        fac.AntdText(t__dashboard('你好，')),
                        fac.AntdText(menu_access.user_info.user_full_name, id='workbench-user-full-name'),
                        fac.AntdText(t__dashboard('!')),
                    ]
                )
            ),
            fuc.FefferyGrid(
                [
                fuc.FefferyGridItem(
                        chart_block(
                            title='评论量',
                            chart=fact.AntdLine(
                                data=get_daily_comment_counts(10),
                                xField='date',
                                yField='count',
                                slider={},
                                yAxis={
                                    'title': {
                                        'text': '评论量'
                                    }
                                }
                            ),
                        ),
                        key='评论量留存',
                    ),
                    fuc.FefferyGridItem(
                        chart_block(
                            title='访客量',
                            chart=fact.AntdArea(
                                data=[
                                    {
                                        'date':(today - timedelta(days=9-i)).strftime('%Y-%m-%d'),
                                        'y': random.randint(50, 100),
                                    }
                                    for i in range(1, 10)
                                ],
                                xField='date',
                                yField='y',
                                areaStyle={'fill': 'l(270) 0:#ffffff 0.5:#7ec2f3 1:#1890ff'},
                            ),
                        ),
                        key='访客量留存',
                    ),
                    fuc.FefferyGridItem(
                        chart_block(
                            title='柱状图示例',
                            chart=fact.AntdColumn(
                                data=[
                                    {
                                        'date': f'2020-0{i}',
                                        'y': random.randint(0, 100),
                                        'type': f'item{j}',
                                    }
                                    for i in range(1, 10)
                                    for j in range(1, 4)
                                ],
                                xField='date',
                                yField='y',
                                seriesField='type',
                                isGroup=True,
                            ),
                        ),
                        key='柱状图',
                    ),
                    fuc.FefferyGridItem(
                        chart_block(
                            title='公告',
                            chart=fact.AntdBar(
                                data=[
                                    {
                                        'date': (today - timedelta(days=9-i)).strftime('%Y-%m-%d'),
                                        'y': random.randint(0, 100),
                                    }
                                    for i in range(1, 7)
                                ],
                                xField='count',
                                yField='date',
                                seriesField='date',
                                legend={
                                    'position': 'top-left',
                                },
                            ),
                        ),
                        key='条形图',
                    ),
                    fuc.FefferyGridItem(
                        chart_block(
                            title='评论状态分布',
                            chart=fact.AntdPie(
                                data=[
                                    {'type': '待审核', 'value': stats['待审核']},
                                    {'type': '已通过', 'value': stats['已通过']},
                                    {'type': '已驳回', 'value': stats['已驳回']}
                                ],
                                colorField='type',
                                angleField='value',
                                radius=0.9,
                            ),
                        ),
                        key='评论状态分布',
                    ),
                    fuc.FefferyGridItem(
                        chart_block(
                            title='双轴图示例',
                            chart=fact.AntdDualAxes(
                                data=[
                                    # 左轴数据
                                    [
                                        {
                                            'date': f'2020-0{i}',
                                            'y1': random.randint(50, 100),
                                        }
                                        for i in range(1, 10)
                                    ],
                                    # 右轴数据
                                    [
                                        {
                                            'date': f'2020-0{i}',
                                            'y2': random.randint(100, 1000),
                                        }
                                        for i in range(1, 10)
                                    ],
                                ],
                                xField='date',
                                yField=['y1', 'y2'],
                                geometryOptions=[
                                    {'geometry': 'line'},
                                    {'geometry': 'column'},
                                ],
                            ),
                        ),
                        key='双轴图',
                    ),
                    fuc.FefferyGridItem(
                        chart_block(
                            title='迷你面积图示例',
                            chart=fact.AntdTinyArea(
                                data=[random.randint(50, 100) for _ in range(20)],
                                height=60,
                                smooth=True,
                            ),
                        ),
                        key='迷你面积图示例',
                    ),
                    fuc.FefferyGridItem(
                        chart_block(
                            title='进度条图示例',
                            chart=fact.AntdProgress(percent=0.7, barWidthRatio=0.2),
                        ),
                        key='进度条图',
                    ),
                    fuc.FefferyGridItem(
                        chart_block(
                            title='进度环图示例',
                            chart=fact.AntdRingProgress(
                                percent=0.6,
                                color=['#F4664A', '#E8EDF3'],
                                innerRadius=0.85,
                                radius=0.98,
                                statistic={
                                    'title': {
                                        'style': {
                                            'color': '#363636',
                                            'fontSize': '12px',
                                            'lineHeight': '14px',
                                        },
                                        'formatter': {'func': "() => '进度'"},
                                    },
                                },
                            ),
                        ),
                        key='进度环图',
                    ),
                ],
                layouts=[
                    dict(i='评论量留存', x=0, y=0, w=1, h=2),
                    dict(i='访客量留存', x=1, y=0, w=1, h=2),
                    #dict(i='柱状图', x=2, y=0, w=1, h=2),
                    #dict(i='条形图', x=0, y=1, w=1, h=2),
                    dict(i='评论状态分布', x=1, y=1, w=1, h=2),
                    #dict(i='双轴图', x=2, y=1, w=1, h=2),
                    #dict(i='迷你面积图', x=0, y=2, w=1, h=1),
                    #dict(i='进度条图', x=1, y=2, w=1, h=1),
                    #dict(i='进度环图', x=2, y=2, w=1, h=2),
                ],
                cols=3,
                rowHeight=150,
                placeholderBorderRadius='5px',
                margin=[12, 12],
            ),
        ],
        direction='vertical',
        style={'width': '100%'},
    )
