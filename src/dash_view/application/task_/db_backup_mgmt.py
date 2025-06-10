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
                            fac.AntdButton(
                                t__task('清理旧备份'),
                                id='db-backup-cleanup-button',
                                icon=fac.AntdIcon(icon='fc-delete-row'),
                                danger=True,
                                size='large'
                            ),
                        ],
                        size='middle'
                    ),
                ],
                style={'marginBottom': '20px'}
            ),

            # 定时备份管理区域
            fac.AntdCard(
                [
                    fac.AntdTitle(t__task('定时备份管理'), level=4),
                    fac.AntdSpace(
                        [
                            fac.AntdButton(
                                t__task('启动定时备份'),
                                id='db-backup-start-scheduler-button',
                                type='primary',
                                icon=fac.AntdIcon(icon='fc-start'),
                                size='large'
                            ),
                            fac.AntdButton(
                                t__task('停止定时备份'),
                                id='db-backup-stop-scheduler-button',
                                icon=fac.AntdIcon(icon='fc-stop'),
                                danger=True,
                                size='large'
                            ),
                            fac.AntdButton(
                                t__task('配置定时任务'),
                                id='db-backup-config-scheduler-button',
                                icon=fac.AntdIcon(icon='fc-settings'),
                                size='large'
                            ),
                        ],
                        size='middle'
                    ),
                    html.Div(id='db-backup-scheduler-status', style={'marginTop': '10px'}),
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

            # 备份内容预览模态框
            fac.AntdModal(
                id='db-backup-preview-modal',
                title=t__task('备份内容预览'),
                width='80%',
                style={'top': '20px'},
                children=[
                    fac.AntdSpin(
                        id='db-backup-preview-spin',
                        children=[
                            html.Div(id='db-backup-preview-content')
                        ]
                    )
                ]
            ),

            # 定时任务配置模态框
            fac.AntdModal(
                id='db-backup-scheduler-config-modal',
                title=t__task('定时备份配置'),
                width='70%',
                okText=t__task('保存配置'),
                cancelText=t__task('取消'),
                children=[
                    html.Div(id='db-backup-scheduler-config-content')
                ]
            ),

            # 清理确认模态框
            fac.AntdModal(
                id='db-backup-cleanup-confirm-modal',
                title=t__task('确认清理旧备份'),
                okText=t__task('确认清理'),
                cancelText=t__task('取消'),
                okButtonProps={'danger': True},
                children=[
                    fac.AntdAlert(
                        message=t__task('清理操作'),
                        description=html.Div([
                            html.P(t__task("将删除超出保留数量的旧备份文件")),
                            fac.AntdInputNumber(
                                id='db-backup-cleanup-keep-count',
                                placeholder=t__task('保留备份数量'),
                                value=10,
                                min=1,
                                max=100,
                                style={'width': '200px'}
                            ),
                            html.P(t__task("此操作不可恢复，请谨慎操作！"), 
                                   style={'color': 'orange', 'fontWeight': 'bold', 'marginTop': '10px'})
                        ]),
                        type='warning',
                        showIcon=True
                    )
                ]
            ),

            # 确认对话框
            fac.AntdModal(
                id='db-backup-restore-confirm-modal',
                title=t__task('确认恢复数据库'),
                okText=t__task('确认恢复'),
                cancelText=t__task('取消'),
                okButtonProps={'danger': True}
            ),
            fac.AntdModal(
                id='db-backup-delete-confirm-modal',
                title=t__task('确认删除备份文件'),
                okText=t__task('确认删除'),
                cancelText=t__task('取消'),
                okButtonProps={'danger': True}
            ),
            
            # 下载组件（全局，用于所有下载）
            dcc.Download(id='backup-file-download'),
            
            # 下载触发按钮（隐藏）
            html.Button(
                id='backup-download-trigger',
                style={'display': 'none'}
            ),
            
            # 初始化触发器和数据存储
            fuc.FefferyTimeout(id='db-backup-init-timeout', delay=100),
            fuc.FefferyTimeout(id='db-backup-status-timeout', delay=1000),
            dcc.Store(id='db-backup-selected-filename-store', storage_type='memory'),
            dcc.Store(id='db-backup-message-trigger', storage_type='memory'),
        ],
        style={'padding': '20px'}
    )