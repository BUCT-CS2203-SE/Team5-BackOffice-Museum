import feffery_antd_components as fac
import feffery_utils_components as fuc
from dash import html, dcc
from common.utilities.util_menu_access import MenuAccess
from i18n import t__task

# 二级菜单的标题、图标和显示顺序
title = '数据库备份与恢复' 
icon = 'fc-database' 
order = 3 

access_metas = ('数据库备份与恢复-页面',)

def render_content(menu_access: MenuAccess, **kwargs):
    return html.Div(
        [
            # 手动操作区域
            fac.AntdCard(
                [
                    fac.AntdTitle(t__task('手动操作'), level=4),
                    fac.AntdSpace(
                        [
                            fac.AntdButton(
                                t__task('立即备份数据库'),
                                id='db-backup-manual-backup-button',
                                type='primary',
                                icon=fac.AntdIcon(icon='fc-upload'),
                                size='large'
                            ),
                            fac.AntdButton(
                                t__task('刷新列表'),
                                id='db-backup-refresh-button',
                                icon=fac.AntdIcon(icon='fc-refresh'),
                                size='large'
                            ),
                        ],
                        size='middle'
                    ),
                ],
                style={'marginBottom': '20px'}
            ),

            # 备份文件列表区域
            fac.AntdCard(
                [
                    fac.AntdTitle(t__task('备份文件列表'), level=4),
                    fac.AntdSpin( 
                        id='db-backup-table-spin',
                        children=[
                            fac.AntdTable(
                                id='db-backup-files-table',
                                locale='zh-cn', 
                                bordered=True,
                                style={'width': '100%'},
                                pagination={
                                    'pageSize': 10,
                                    'showSizeChanger': True,
                                    'showQuickJumper': True,
                                }
                            )
                        ]
                    ),
                ]
            ),

            # 计划备份说明
            fac.AntdCard(
                [
                    fac.AntdTitle(t__task('计划备份'), level=4),
                    fac.AntdAlert(
                        message=t__task('计划备份设置'),
                        description=t__task('注意：计划备份任务的创建和管理，请前往"任务管理"页面。您可以在那里创建一个新的定时任务，其执行的脚本应调用备份功能。'),
                        type='info',
                        showIcon=True
                    ),
                ],
                style={'marginTop': '20px'}
            ),

            # 确认对话框 - 修复okDanger参数问题
            fac.AntdModal(
                id='db-backup-restore-confirm-modal',
                title=t__task('确认恢复数据库'),
                okText=t__task('确认恢复'),
                cancelText=t__task('取消'),
                okButtonProps={'danger': True}  # 使用okButtonProps替代okDanger
            ),
            fac.AntdModal(
                id='db-backup-delete-confirm-modal',
                title=t__task('确认删除备份文件'),
                okText=t__task('确认删除'),
                cancelText=t__task('取消'),
                okButtonProps={'danger': True}  # 使用okButtonProps替代okDanger
            ),
            
            # 初始化触发器和数据存储
            fuc.FefferyTimeout(id='db-backup-init-timeout', delay=100),
            dcc.Store(id='db-backup-selected-filename-store', storage_type='memory'),
            dcc.Store(id='db-backup-message-trigger', storage_type='memory'),
        ],
        style={'padding': '20px'}
    )