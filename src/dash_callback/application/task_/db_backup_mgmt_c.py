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
        {'title': '备份文件名', 'dataIndex': 'filename', 'width': '25%'},
        {'title': '文件大小', 'dataIndex': 'size_formatted', 'width': '12%'},
        {'title': '备份时间', 'dataIndex': 'created_at', 'width': '18%'},
        {'title': '备份类型', 'dataIndex': 'backup_type', 'width': '10%'},
        {'title': '状态', 'dataIndex': 'status', 'width': '10%'},
        {
            'title': '操作',
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
            
            # 状态标签 - 使用简单字符串避免组件问题
            success = f_info.get('success', True)
            status_text = '成功' if success else '失败'
              # 为每个文件创建多个操作按钮 - 简化按钮配置
            filename_safe = str(f_info.get('filename', '')).strip()
            operation_buttons = [
                {
                    'content': '预览',
                    'type': 'default',
                    'custom': f"preview-{filename_safe}"
                },
                {
                    'content': '下载',
                    'type': 'default',
                    'custom': f"download-{filename_safe}"
                },
                {
                    'content': '恢复',
                    'type': 'primary',
                    'custom': f"restore-{filename_safe}"
                },
                {
                    'content': '删除',
                    'type': 'primary',
                    'danger': True,
                    'custom': f"delete-{filename_safe}"
                }
            ]
            
            data.append({
                'key': filename_safe,
                'filename': filename_safe,
                'size': f_info['size'],
                'size_formatted': format_file_size(f_info['size']),
                'created_at': f_info['created_at'],
                'backup_type': backup_type,
                'status': status_text,
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

# 处理表格操作按钮点击
@app.callback(
    [Output('db-backup-files-table', 'data', allow_duplicate=True),
     Output('db-backup-message-trigger', 'data', allow_duplicate=True),
     Output('backup-file-download', 'data', allow_duplicate=True)],
    [Input('db-backup-files-table', 'clickedCustom')],
    prevent_initial_call=True
)
def handle_table_operations(clicked_custom):
    print(f"=== 表格操作按钮点击 === clicked_custom: {clicked_custom}")
    
    if not clicked_custom:
        return no_update, no_update, no_update
    
    try:
        # 解析操作和文件名
        parts = clicked_custom.split('-', 1)
        if len(parts) != 2:
            return no_update, {'type': 'error', 'message': '无效的操作格式'}, no_update
        
        operation, filename = parts
        print(f"操作: {operation}, 文件名: {filename}")
        
        if operation == "preview":
            # 预览操作 - 显示文件信息
            message = f"预览文件: {filename}"
            return no_update, {'type': 'success', 'message': message}, no_update
            
        elif operation == "download":
            # 下载操作 - 触发浏览器下载
            try:
                file_path = backup_utils.get_backup_file_path(filename)
                if file_path and os.path.exists(file_path):
                    download_data = dcc.send_file(file_path, filename=filename)
                    return no_update, {'type': 'success', 'message': f'开始下载: {filename}'}, download_data
                else:
                    return no_update, {'type': 'error', 'message': f'文件不存在: {filename}'}, no_update
            except Exception as e:
                return no_update, {'type': 'error', 'message': f'下载失败: {str(e)}'}, no_update
            
        elif operation == "restore":
            # 恢复操作
            try:
                success, msg = backup_utils.perform_restore(filename)
                if success:
                    return no_update, {'type': 'success', 'message': f'恢复成功: {msg}'}, no_update
                else:
                    return no_update, {'type': 'error', 'message': f'恢复失败: {msg}'}, no_update
            except Exception as e:
                return no_update, {'type': 'error', 'message': f'恢复过程中出错: {str(e)}'}, no_update
                
        elif operation == "delete":
            # 删除操作
            try:
                success, msg = backup_utils.delete_backup_file(filename)
                if success:
                    # 刷新表格数据
                    new_data = get_formatted_backup_data()
                    return new_data, {'type': 'success', 'message': f'删除成功: {msg}'}, no_update
                else:
                    return no_update, {'type': 'error', 'message': f'删除失败: {msg}'}, no_update
            except Exception as e:
                return no_update, {'type': 'error', 'message': f'删除过程中出错: {str(e)}'}, no_update
        
        else:
            return no_update, {'type': 'error', 'message': f'未知操作: {operation}'}, no_update
            
    except Exception as e:
        error_msg = f"处理表格操作时出错: {str(e)}"
        print(error_msg)
        traceback.print_exc()
        return no_update, {'type': 'error', 'message': error_msg}, no_update

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
            status_tag = fac.AntdTag(content='运行中', color='green')
            next_runs = status.get('next_runs', {})
            
            if next_runs:
                next_run_info = []
                for job_id, next_time in next_runs.items():
                    if next_time:
                        next_run_info.append(f"{job_id}: {next_time}")
                
                next_run_text = "; ".join(next_run_info) if next_run_info else '暂无计划任务'
            else:
                next_run_text = '暂无计划任务'
        else:
            status_tag = fac.AntdTag(content='已停止', color='red')
            next_run_text = '调度器未运行'
        
        return fac.AntdSpace([
            fac.AntdText('状态：'),
            status_tag,
            fac.AntdText(f"任务数: {status['enabled_jobs']}/{status['job_count']}"),
            html.Br(),
            fac.AntdText(f"下次运行: {next_run_text}", type='secondary')
        ], direction='vertical', size=0)
        
    except Exception as e:
        print(f"更新调度器状态时出错: {e}")
        return fac.AntdAlert(
            message='状态获取失败',
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
    
    try:
        triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
        scheduler = get_backup_scheduler()
        
        if triggered_id == 'db-backup-start-scheduler-button' and start_clicks:
            success, msg = scheduler.start()
            msg_type = 'success' if success else 'error'
            return [{'type': msg_type, 'message': f'启动定时备份: {msg}'}]
        
        elif triggered_id == 'db-backup-stop-scheduler-button' and stop_clicks:
            success, msg = scheduler.stop()
            msg_type = 'success' if success else 'error'
            return [{'type': msg_type, 'message': f'停止定时备份: {msg}'}]
    
    except Exception as e:
        error_msg = f"操作定时备份调度器时出错: {str(e)}"
        print(error_msg)
        return [{'type': 'error', 'message': error_msg}]
    
    return [no_update]

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
                    message='定时备份配置',
                    description='配置自动备份任务的执行时间和参数',
                    type='info',
                    showIcon=True,
                    style={'marginBottom': '20px'}
                ),
                
                # 每日备份配置
                fac.AntdCard(
                    [
                        fac.AntdTitle('每日自动备份', level=5),
                        fac.AntdRow([
                            fac.AntdCol([
                                fac.AntdSwitch(
                                    id='daily-backup-enabled',
                                    checked=jobs.get('daily_backup', {}).get('enabled', True),
                                    checkedChildren='启用',
                                    unCheckedChildren='禁用'
                                )
                            ], span=6),
                            fac.AntdCol([
                                fac.AntdTimePicker(
                                    id='daily-backup-time',
                                    value=jobs.get('daily_backup', {}).get('time', '02:00'),
                                    format='HH:mm',
                                    placeholder='选择执行时间'
                                )
                            ], span=8),
                            fac.AntdCol([
                                fac.AntdInputNumber(
                                    id='daily-backup-keep-count',
                                    value=jobs.get('daily_backup', {}).get('keep_count', 7),
                                    min=1,
                                    max=30,
                                    placeholder='保留天数'
                                )
                            ], span=6),
                        ], gutter=10),
                        fac.AntdText('每日在指定时间自动备份数据库', type='secondary')
                    ],
                    style={'marginBottom': '15px'}
                ),
                
                # 每周备份配置
                fac.AntdCard(
                    [
                        fac.AntdTitle('每周备份', level=5),
                        fac.AntdRow([
                            fac.AntdCol([
                                fac.AntdSwitch(
                                    id='weekly-backup-enabled',
                                    checked=jobs.get('weekly_backup', {}).get('enabled', False),
                                    checkedChildren='启用',
                                    unCheckedChildren='禁用'
                                )
                            ], span=4),
                            fac.AntdCol([
                                fac.AntdSelect(
                                    id='weekly-backup-day',
                                    value=jobs.get('weekly_backup', {}).get('day', 'sunday'),
                                    options=[
                                        {'label': '周一', 'value': 'monday'},
                                        {'label': '周二', 'value': 'tuesday'},
                                        {'label': '周三', 'value': 'wednesday'},
                                        {'label': '周四', 'value': 'thursday'},
                                        {'label': '周五', 'value': 'friday'},
                                        {'label': '周六', 'value': 'saturday'},
                                        {'label': '周日', 'value': 'sunday'},
                                    ],
                                    placeholder='选择星期'
                                )
                            ], span=6),
                            fac.AntdCol([
                                fac.AntdTimePicker(
                                    id='weekly-backup-time',
                                    value=jobs.get('weekly_backup', {}).get('time', '03:00'),
                                    format='HH:mm',
                                    placeholder='选择执行时间'
                                )
                            ], span=8),
                            fac.AntdCol([
                                fac.AntdInputNumber(
                                    id='weekly-backup-keep-count',
                                    value=jobs.get('weekly_backup', {}).get('keep_count', 4),
                                    min=1,
                                    max=12,
                                    placeholder='保留周数'
                                )
                            ], span=6),
                        ], gutter=10),
                        fac.AntdText('每周在指定日期和时间备份数据库', type='secondary')
                    ]
                )
            ])
            
            return True, config_content
            
        except Exception as e:
            error_content = fac.AntdAlert(
                message='配置加载失败',
                description=str(e),
                type='error'
            )
            return True, error_content
    
    elif triggered_id == 'db-backup-scheduler-config-modal' and ok_counts:
        # 关闭模态框，保存配置的逻辑在下面的回调中实现
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
        
        return {'type': 'success', 'message': '定时备份配置已保存'}
        
    except Exception as e:
        error_msg = f"保存配置失败: {str(e)}"
        print(error_msg)
        traceback.print_exc()
        return {'type': 'error', 'message': error_msg}

print("=== 数据库备份回调模块加载完成 ===")