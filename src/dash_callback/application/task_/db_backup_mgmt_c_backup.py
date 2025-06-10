from dash import Input, Output, State, html, no_update, ctx, dcc
from server import app
import feffery_antd_components as fac
from dash_components import MessageManager
from common.utilities import backup_utils_enhanced as backup_utils
from common.utilities.backup_scheduler import get_backup_scheduler
from i18n import t__task, t__default
import traceback
import subprocess
import os

print("=== 数据库备份回调模块开始加载 ===")

# 表格列定义
def get_table_columns():
    return [
        {'title': t__task('备份文件名'), 'dataIndex': 'filename', 'width': '25%'},
        {'title': t__task('文件大小'), 'dataIndex': 'size_formatted', 'width': '12%'},
        {'title': t__task('备份时间'), 'dataIndex': 'created_at', 'width': '18%'},
        {'title': t__task('备份类型'), 'dataIndex': 'backup_type', 'width': '10%'},
        {'title': t__task('状态'), 'dataIndex': 'status', 'width': '10%'},
        {
            'title': t__default('操作'),
            'dataIndex': 'operation',
            'renderOptions': {'renderType': 'button'},
            'width': '25%'
        },
    ]

# 格式化文件大小
def format_file_size(size_bytes):
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"

# 获取并格式化备份文件数据
def get_formatted_backup_data():
    try:
        files, msg = backup_utils.list_backup_files()
        print(f"获取备份文件: {len(files) if files else 0} 个文件, 消息: {msg}")
        
        if not files:
            return []
        
        data = []
        for f_info in files:
            # 备份类型标签
            backup_type = str(f_info.get('backup_type', 'unknown'))
            type_color = {
                'manual': 'blue',
                'scheduled': 'green', 
                'pre_restore': 'orange',
                'test': 'purple',
                'unknown': 'gray'
            }.get(backup_type, 'gray')
              # 状态标签 - 使用简单字符串避免组件问题
            success = f_info.get('success', True)
            status_text = '成功' if success else '失败'
              # 为每个文件创建多个操作按钮
            filename_safe = str(f_info.get('filename', '')).strip()
            operation_buttons = [
                {
                    'content': t__task('预览'),
                    'type': 'default',
                    'icon': fac.AntdIcon(icon='fc-search'),
                    'custom': f"preview:{filename_safe}"
                },
                {
                    'content': t__task('下载'),
                    'type': 'default',
                    'icon': fac.AntdIcon(icon='fc-export'),
                    'custom': f"download:{filename_safe}"
                },
                {
                    'content': t__task('恢复'),
                    'type': 'primary',
                    'icon': fac.AntdIcon(icon='fc-download'),
                    'custom': f"restore:{filename_safe}"
                },
                {
                    'content': t__default('删除'),
                    'type': 'primary',
                    'danger': True,
                    'icon': fac.AntdIcon(icon='fc-delete-row'),
                    'custom': f"delete:{filename_safe}"                }
            ]
            
            data.append({
                'key': filename_safe,
                'filename': filename_safe,
                'size': f_info['size'],
                'size_formatted': format_file_size(f_info['size']),
                'created_at': f_info['created_at'],
                'backup_type': backup_type,  # 使用简单字符串
                'status': status_text,  # 使用简单字符串
                'operation': operation_buttons
            })
        return data
    except Exception as e:
        print(f"格式化备份数据时出错: {e}")
        traceback.print_exc()
        return []

# 初始化表格数据
@app.callback(
    [Output('db-backup-files-table', 'columns'),
     Output('db-backup-files-table', 'data'),
     Output('db-backup-table-spin', 'spinning')],
    [Input('db-backup-init-timeout', 'timeoutCount'),
     Input('db-backup-refresh-button', 'nClicks')],
    prevent_initial_call=False
)
def initialize_backup_table(init_timeout, refresh_clicks):
    print(f"=== 初始化/刷新表格 ===")
    print(f"timeout: {init_timeout}, refresh_clicks: {refresh_clicks}")
    
    try:
        columns = get_table_columns()
        data = get_formatted_backup_data()
        print(f"表格数据: {len(columns)} 列, {len(data)} 行")
        return columns, data, False
    except Exception as e:
        print(f"初始化表格时出错: {e}")
        traceback.print_exc()
        return [], [], False

# 更新定时备份状态显示
@app.callback(
    Output('db-backup-scheduler-status', 'children'),
    [Input('db-backup-status-timeout', 'timeoutCount'),
     Input('db-backup-start-scheduler-button', 'nClicks'),
     Input('db-backup-stop-scheduler-button', 'nClicks')],
    prevent_initial_call=False
)
def update_scheduler_status(timeout_count, start_clicks, stop_clicks):
    try:
        scheduler = get_backup_scheduler()
        status = scheduler.get_status()
        
        if status['is_running']:
            status_tag = fac.AntdTag(content=t__task('运行中'), color='green')
            next_runs = status.get('next_runs', {})
            
            if next_runs:
                next_run_info = []
                for job_id, next_time in next_runs.items():
                    if next_time:
                        next_run_info.append(f"{job_id}: {next_time}")
                
                next_run_text = "; ".join(next_run_info) if next_run_info else t__task('暂无计划任务')
            else:
                next_run_text = t__task('暂无计划任务')
        else:
            status_tag = fac.AntdTag(content=t__task('已停止'), color='red')
            next_run_text = t__task('调度器未运行')
        
        return fac.AntdSpace([
            fac.AntdText(t__task('状态：')),
            status_tag,
            fac.AntdText(f"{t__task('任务数')}: {status['enabled_jobs']}/{status['job_count']}"),
            html.Br(),
            fac.AntdText(f"{t__task('下次运行')}: {next_run_text}", type='secondary')
        ], direction='vertical', size=0)
        
    except Exception as e:
        print(f"更新调度器状态时出错: {e}")
        return fac.AntdAlert(
            message=t__task('状态获取失败'),
            description=str(e),
            type='error'
        )

# 处理定时备份启动/停止
@app.callback(
    [Output('db-backup-message-trigger', 'data', allow_duplicate=True)],
    [Input('db-backup-start-scheduler-button', 'nClicks'),
     Input('db-backup-stop-scheduler-button', 'nClicks')],
    prevent_initial_call=True
)
def handle_scheduler_control(start_clicks, stop_clicks):
    if not ctx.triggered:
        return [no_update]
    
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    try:
        scheduler = get_backup_scheduler()
        
        if triggered_id == 'db-backup-start-scheduler-button' and start_clicks:
            success, msg = scheduler.start()
            msg_type = 'success' if success else 'error'
            return [{'type': msg_type, 'message': msg}]
            
        elif triggered_id == 'db-backup-stop-scheduler-button' and stop_clicks:
            success, msg = scheduler.stop()
            msg_type = 'success' if success else 'error'
            return [{'type': msg_type, 'message': msg}]
    
    except Exception as e:
        error_msg = f"操作定时备份调度器时出错: {str(e)}"
        print(error_msg)
        return [{'type': 'error', 'message': error_msg}]
    
    return [no_update]

# 处理清理旧备份
@app.callback(
    [Output('db-backup-cleanup-confirm-modal', 'visible'),
     Output('db-backup-files-table', 'data', allow_duplicate=True),
     Output('db-backup-message-trigger', 'data', allow_duplicate=True)],
    [Input('db-backup-cleanup-button', 'nClicks'),
     Input('db-backup-cleanup-confirm-modal', 'okCounts')],
    [State('db-backup-cleanup-keep-count', 'value')],
    prevent_initial_call=True
)
def handle_cleanup_backups(cleanup_clicks, confirm_ok, keep_count):
    if not ctx.triggered:
        return no_update, no_update, no_update
    
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if triggered_id == 'db-backup-cleanup-button' and cleanup_clicks:
        # 显示确认对话框
        return True, no_update, no_update
    
    elif triggered_id == 'db-backup-cleanup-confirm-modal' and confirm_ok:
        try:
            keep_count = keep_count or 10
            success, msg = backup_utils.cleanup_old_backups(keep_count)
            
            if success:
                # 刷新表格数据
                new_data = get_formatted_backup_data()
                return False, new_data, {'type': 'success', 'message': msg}
            else:
                return False, no_update, {'type': 'error', 'message': msg}
                
        except Exception as e:
            error_msg = f"清理备份文件时出错: {str(e)}"
            print(error_msg)
            return False, no_update, {'type': 'error', 'message': error_msg}
    
    return no_update, no_update, no_update
# 处理手动备份按钮点击
@app.callback(
    [Output('db-backup-manual-backup-button', 'loading'),
     Output('db-backup-files-table', 'data', allow_duplicate=True),
     Output('db-backup-message-trigger', 'data', allow_duplicate=True)],
    [Input('db-backup-manual-backup-button', 'nClicks')],
    prevent_initial_call=True
)
def handle_manual_backup(nClicks):
    print(f"=== 备份按钮点击 === nClicks: {nClicks}")
    
    if not nClicks:
        return False, no_update, no_update
    
    try:
        print("开始执行备份操作...")
        
        # 检查mysqldump命令是否可用
        try:
            result = subprocess.run(
                ['mysqldump', '--version'], 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                check=True, 
                timeout=10,
                text=True
            )
            print(f"mysqldump可用: {result.stdout.strip()}")
        except subprocess.TimeoutExpired:
            error_msg = "备份失败: mysqldump命令超时"
            print(error_msg)
            return False, no_update, {'type': 'error', 'message': error_msg}
        except (subprocess.SubprocessError, FileNotFoundError) as e:
            error_msg = "备份失败: mysqldump命令不可用，请确保MySQL客户端已安装"
            print(f"{error_msg}: {e}")
            return False, no_update, {'type': 'error', 'message': error_msg}
        
        # 执行备份（启用压缩）
        print("执行实际备份...")
        path, msg = backup_utils.perform_backup("manual", compress=True, backup_type="manual")
        print(f"备份结果: 路径={path}, 消息={msg}")
        
        if path and "成功" in msg:
            # 刷新表格数据
            new_data = get_formatted_backup_data()
            return False, new_data, {'type': 'success', 'message': msg}
        else:
            error_msg = msg or "备份失败，未知错误"
            return False, no_update, {'type': 'error', 'message': error_msg}
            
    except Exception as e:
        error_msg = f"备份过程中发生异常: {str(e)}"
        print(error_msg)
        traceback.print_exc()
        return False, no_update, {'type': 'error', 'message': error_msg}

# 显示消息提示
@app.callback(
    Output('db-backup-message-trigger', 'data', allow_duplicate=True),
    [Input('db-backup-message-trigger', 'data')],
    prevent_initial_call=True
)
def show_message(message_data):
    if message_data:
        if message_data['type'] == 'success':
            MessageManager.success(content=message_data['message'])
        else:
            MessageManager.error(content=message_data['message'])
    return no_update

# 处理表格中的按钮点击（预览/下载/恢复/删除）
@app.callback(
    [Output('db-backup-restore-confirm-modal', 'visible'),
     Output('db-backup-delete-confirm-modal', 'visible'),
     Output('db-backup-preview-modal', 'visible'),
     Output('db-backup-selected-filename-store', 'data'),
     Output('db-backup-restore-confirm-modal', 'children'),
     Output('db-backup-delete-confirm-modal', 'children'),
     Output('db-backup-preview-content', 'children'),
     Output('db-backup-preview-spin', 'spinning')],
    [Input('db-backup-files-table', 'nClicksButton')],
    [State('db-backup-files-table', 'clickedCustom')],
    prevent_initial_call=True
)
def handle_table_button_clicks(nClicksButton, clickedCustom):
    print(f"=== 表格按钮点击 === nClicks: {nClicksButton}, custom: {clickedCustom}")
    
    if not nClicksButton or not clickedCustom:
        return False, False, False, no_update, no_update, no_update, no_update, False
        
    try:
        action, filename = clickedCustom.split(':', 1)
        print(f"操作: {action}, 文件: {filename}")
        
        if action == 'preview':
            # 显示备份内容预览
            try:
                content, msg = backup_utils.get_backup_content_preview(filename, max_lines=100)
                if content:
                    preview_content = html.Div([
                        fac.AntdAlert(
                            message=t__task('备份文件预览'),
                            description=f"{t__task('文件')}: {filename} | {t__task('预览前100行')}",
                            type='info',
                            showIcon=True,
                            style={'marginBottom': '10px'}
                        ),
                        html.Pre(
                            content,
                            style={
                                'background': '#f6f8fa',
                                'padding': '10px',
                                'border': '1px solid #d1d9e0',
                                'borderRadius': '6px',
                                'fontSize': '12px',
                                'overflow': 'auto',
                                'maxHeight': '500px',
                                'whiteSpace': 'pre-wrap'
                            }
                        )
                    ])
                else:
                    preview_content = fac.AntdAlert(
                        message=t__task('预览失败'),
                        description=msg,
                        type='error'
                    )
                
                return False, False, True, filename, no_update, no_update, preview_content, False
            except Exception as e:
                error_content = fac.AntdAlert(
                    message=t__task('预览出错'),
                    description=str(e),
                    type='error'
                )
                return False, False, True, filename, no_update, no_update, error_content, False
          elif action == 'download':
            # 下载功能 - 在预览窗口显示下载链接
            try:
                file_path = backup_utils.get_backup_file_path(filename)
                if file_path and os.path.exists(file_path):
                    # 确保文件名安全用于URL
                    import urllib.parse
                    safe_filename = urllib.parse.quote(filename, safe='')
                    download_url = f"/download-backup/{safe_filename}"
                    file_size = format_file_size(os.path.getsize(file_path))
                    
                    download_content = html.Div([
                        fac.AntdAlert(
                            message=t__task('文件下载'),
                            description=f"{t__task('文件')}: {filename} | {t__task('大小')}: {file_size}",
                            type='info',
                            showIcon=True,
                            style={'marginBottom': '15px'}
                        ),
                        html.Div([
                            fac.AntdButton(
                                [
                                    fac.AntdIcon(icon='fc-download'),
                                    " ",
                                    t__task('下载备份文件')
                                ],
                                type='primary',
                                size='large',
                                href=download_url,
                                target='_blank',
                                style={'marginRight': '10px'}
                            ),
                            fac.AntdButton(
                                [
                                    fac.AntdIcon(icon='fc-search'),
                                    " ",
                                    t__task('预览文件内容')
                                ],
                                type='default',
                                size='large',
                                id=f'preview-backup-{filename}',
                                custom=f"preview:{filename}"
                            )
                        ], style={'textAlign': 'center'}),
                        
                        fac.AntdDivider(),
                        
                        fac.AntdDescriptions(
                            [
                                fac.AntdDescriptionsItem(
                                    t__task('文件名'),
                                    label=t__task('文件名')
                                ),
                                fac.AntdDescriptionsItem(
                                    file_size,
                                    label=t__task('文件大小')
                                ),
                                fac.AntdDescriptionsItem(
                                    download_url,
                                    label=t__task('下载链接')
                                )
                            ],
                            title=t__task('文件信息'),
                            bordered=True,
                            size='small',
                            items=[
                                {'label': t__task('文件名'), 'children': filename},
                                {'label': t__task('文件大小'), 'children': file_size},
                                {'label': t__task('下载地址'), 'children': download_url}
                            ]
                        )
                    ])
                    
                    return False, False, True, filename, no_update, no_update, download_content, False
                else:
                    MessageManager.error(content=t__task('文件不存在'))
                    return False, False, False, no_update, no_update, no_update, no_update, False
            except Exception as e:
                MessageManager.error(content=f"下载准备失败: {str(e)}")
                return False, False, False, no_update, no_update, no_update, no_update, False
            
        elif action == 'restore':
            modal_content = html.Div([
                fac.AntdAlert(
                    message=t__task('危险操作警告'),
                    description=html.Div([
                        html.P([
                            t__task("您确定要从备份文件 "),
                            html.Strong(filename),
                            t__task(" 恢复数据库吗？")
                        ]),
                        html.P(t__task("此操作将完全覆盖当前数据库内容，可能导致数据丢失！"), 
                               style={'color': 'red', 'fontWeight': 'bold'}),
                        html.P(t__task("系统会在恢复前自动创建当前数据库的安全备份。")),
                        html.P(t__task("建议在恢复后重启应用程序以确保数据一致性。"))
                    ]),
                    type='error',
                    showIcon=True
                )
            ])
            return True, False, False, filename, modal_content, no_update, no_update, False
            
        elif action == 'delete':
            modal_content = html.Div([
                fac.AntdAlert(
                    message=t__task('确认删除'),
                    description=html.Div([
                        html.P([
                            t__task("您确定要删除备份文件 "),
                            html.Strong(filename),
                            t__task(" 吗？")
                        ]),
                        html.P(t__task("此操作不可恢复，请谨慎操作！"), 
                               style={'color': 'orange', 'fontWeight': 'bold'})
                    ]),
                    type='warning',
                    showIcon=True
                )
            ])
            return False, True, False, filename, no_update, modal_content, no_update, False
            
    except Exception as e:
        print(f"处理表格按钮点击异常: {e}")
        traceback.print_exc()
    
    return False, False, False, no_update, no_update, no_update, no_update, False

# 处理恢复确认
@app.callback(
    [Output('db-backup-files-table', 'data', allow_duplicate=True),
     Output('db-backup-restore-confirm-modal', 'visible', allow_duplicate=True)],
    [Input('db-backup-restore-confirm-modal', 'okCounts')],
    [State('db-backup-selected-filename-store', 'data')],
    prevent_initial_call=True
)
def handle_restore_confirmation(okCounts, filename):
    print(f"=== 恢复确认 === okCounts: {okCounts}, filename: {filename}")
    
    if not okCounts or not filename:
        return no_update, no_update
    
    try:
        print(f"执行恢复操作，文件: {filename}")
        success, msg = backup_utils.perform_restore(filename)
        
        if success:
            MessageManager.success(content=msg, duration=10)
        else:
            MessageManager.error(content=msg)
            
        return no_update, False
        
    except Exception as e:
        error_msg = f"恢复操作异常: {str(e)}"
        print(error_msg)
        traceback.print_exc()
        MessageManager.error(content=error_msg)
        return no_update, False

# 处理删除确认
@app.callback(
    [Output('db-backup-files-table', 'data', allow_duplicate=True),
     Output('db-backup-delete-confirm-modal', 'visible', allow_duplicate=True)],
    [Input('db-backup-delete-confirm-modal', 'okCounts')],
    [State('db-backup-selected-filename-store', 'data')],
    prevent_initial_call=True
)
def handle_delete_confirmation(okCounts, filename):
    print(f"=== 删除确认 === okCounts: {okCounts}, filename: {filename}")
    
    if not okCounts or not filename:
        return no_update, no_update
    
    try:
        print(f"执行删除操作，文件: {filename}")
        success, msg = backup_utils.delete_backup_file(filename)
        
        if success:
            MessageManager.success(content=msg)
            # 刷新表格数据
            new_data = get_formatted_backup_data()
            return new_data, False
        else:
            MessageManager.error(content=msg)
            return no_update, False
            
    except Exception as e:
        error_msg = f"删除操作异常: {str(e)}"
        print(error_msg)
        traceback.print_exc()
        MessageManager.error(content=error_msg)
        return no_update, False

# 处理定时任务配置
@app.callback(
    [Output('db-backup-scheduler-config-modal', 'visible'),
     Output('db-backup-scheduler-config-content', 'children')],
    [Input('db-backup-config-scheduler-button', 'nClicks'),
     Input('db-backup-scheduler-config-modal', 'okCounts'),
     Input('db-backup-scheduler-config-modal', 'cancelCounts')],
    prevent_initial_call=True
)
def handle_scheduler_config(config_clicks, ok_counts, cancel_counts):
    if not ctx.triggered:
        return no_update, no_update
    
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if triggered_id == 'db-backup-config-scheduler-button' and config_clicks:
        # 显示配置界面
        try:
            scheduler = get_backup_scheduler()
            jobs = scheduler.get_jobs()
            
            config_content = html.Div([
                fac.AntdAlert(
                    message=t__task('定时备份配置'),
                    description=t__task('配置自动备份任务的执行时间和参数'),
                    type='info',
                    showIcon=True,
                    style={'marginBottom': '20px'}
                ),
                
                # 每日备份配置
                fac.AntdCard(
                    [
                        fac.AntdTitle(t__task('每日自动备份'), level=5),
                        fac.AntdRow([
                            fac.AntdCol([
                                fac.AntdSwitch(
                                    id='daily-backup-enabled',
                                    checked=jobs.get('daily_backup', {}).get('enabled', True),
                                    checkedChildren=t__task('启用'),
                                    unCheckedChildren=t__task('禁用')
                                )
                            ], span=6),
                            fac.AntdCol([
                                fac.AntdTimePicker(
                                    id='daily-backup-time',
                                    value=jobs.get('daily_backup', {}).get('time', '02:00'),
                                    format='HH:mm',
                                    placeholder=t__task('选择执行时间')
                                )
                            ], span=8),
                            fac.AntdCol([
                                fac.AntdInputNumber(
                                    id='daily-backup-keep-count',
                                    value=jobs.get('daily_backup', {}).get('keep_count', 7),
                                    min=1,
                                    max=30,
                                    placeholder=t__task('保留天数')
                                )
                            ], span=6),
                        ], gutter=10),
                        fac.AntdText(t__task('每日在指定时间自动备份数据库'), type='secondary')
                    ],
                    style={'marginBottom': '15px'}
                ),
                
                # 每周备份配置
                fac.AntdCard(
                    [
                        fac.AntdTitle(t__task('每周备份'), level=5),
                        fac.AntdRow([
                            fac.AntdCol([
                                fac.AntdSwitch(
                                    id='weekly-backup-enabled',
                                    checked=jobs.get('weekly_backup', {}).get('enabled', False),
                                    checkedChildren=t__task('启用'),
                                    unCheckedChildren=t__task('禁用')
                                )
                            ], span=4),
                            fac.AntdCol([
                                fac.AntdSelect(
                                    id='weekly-backup-day',
                                    value=jobs.get('weekly_backup', {}).get('day', 'sunday'),
                                    options=[
                                        {'label': t__task('周一'), 'value': 'monday'},
                                        {'label': t__task('周二'), 'value': 'tuesday'},
                                        {'label': t__task('周三'), 'value': 'wednesday'},
                                        {'label': t__task('周四'), 'value': 'thursday'},
                                        {'label': t__task('周五'), 'value': 'friday'},
                                        {'label': t__task('周六'), 'value': 'saturday'},
                                        {'label': t__task('周日'), 'value': 'sunday'},
                                    ],
                                    placeholder=t__task('选择星期')
                                )
                            ], span=6),
                            fac.AntdCol([
                                fac.AntdTimePicker(
                                    id='weekly-backup-time',
                                    value=jobs.get('weekly_backup', {}).get('time', '03:00'),
                                    format='HH:mm',
                                    placeholder=t__task('选择执行时间')
                                )
                            ], span=6),
                            fac.AntdCol([
                                fac.AntdInputNumber(
                                    id='weekly-backup-keep-count',
                                    value=jobs.get('weekly_backup', {}).get('keep_count', 4),
                                    min=1,
                                    max=12,
                                    placeholder=t__task('保留周数')
                                )
                            ], span=6),
                        ], gutter=10),
                        fac.AntdText(t__task('每周在指定日期和时间备份数据库'), type='secondary')
                    ]
                )
            ])
            
            return True, config_content
            
        except Exception as e:
            error_content = fac.AntdAlert(
                message=t__task('配置加载失败'),
                description=str(e),
                type='error'
            )
            return True, error_content
    
    elif triggered_id == 'db-backup-scheduler-config-modal' and ok_counts:
        # TODO: 保存配置的逻辑将在下面的回调中实现
        return False, no_update
    
    elif triggered_id == 'db-backup-scheduler-config-modal' and cancel_counts:
        return False, no_update
    
    return no_update, no_update

# 保存定时任务配置
@app.callback(
    Output('db-backup-message-trigger', 'data', allow_duplicate=True),
    [Input('db-backup-scheduler-config-modal', 'okCounts')],
    [State('daily-backup-enabled', 'checked'),
     State('daily-backup-time', 'value'),
     State('daily-backup-keep-count', 'value'),
     State('weekly-backup-enabled', 'checked'),
     State('weekly-backup-day', 'value'),
     State('weekly-backup-time', 'value'),
     State('weekly-backup-keep-count', 'value')],
    prevent_initial_call=True
)
def save_scheduler_config(ok_counts, daily_enabled, daily_time, daily_keep,
                         weekly_enabled, weekly_day, weekly_time, weekly_keep):
    if not ok_counts:
        return no_update
    
    try:
        scheduler = get_backup_scheduler()
        
        # 更新每日备份配置
        daily_config = {
            "name": "每日自动备份",
            "enabled": daily_enabled or False,
            "schedule_type": "daily",
            "time": daily_time or "02:00",
            "compress": True,
            "keep_count": daily_keep or 7,
            "description": "每日自动备份数据库"
        }
        
        # 更新每周备份配置
        weekly_config = {
            "name": "每周备份",
            "enabled": weekly_enabled or False,
            "schedule_type": "weekly",
            "day": weekly_day or "sunday",
            "time": weekly_time or "03:00",
            "compress": True,
            "keep_count": weekly_keep or 4,
            "description": "每周备份数据库"
        }
        
        # 保存配置
        scheduler.update_job('daily_backup', daily_config)
        scheduler.update_job('weekly_backup', weekly_config)
        
        return {'type': 'success', 'message': t__task('定时备份配置已保存')}
        
    except Exception as e:
        error_msg = f"保存配置失败: {str(e)}"
        print(error_msg)
        return {'type': 'error', 'message': error_msg}

print("=== 数据库备份回调模块加载完成 ===")