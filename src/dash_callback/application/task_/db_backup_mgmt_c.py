from dash import Input, Output, State, html, no_update, ctx
from server import app
import feffery_antd_components as fac
from dash_components import MessageManager
from common.utilities import backup_utils
from i18n import t__task, t__default
import traceback
import subprocess

print("=== 数据库备份回调模块开始加载 ===")

# 表格列定义
def get_table_columns():
    return [
        {'title': t__task('备份文件名'), 'dataIndex': 'filename', 'width': '35%'},
        {'title': t__task('文件大小'), 'dataIndex': 'size_formatted', 'width': '15%'},
        {'title': t__task('备份时间'), 'dataIndex': 'created_at', 'width': '25%'},
        {
            'title': t__default('操作'),
            'dataIndex': 'operation',
            'renderOptions': {'renderType': 'button'},  # 修改为 'button'
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
            # 为每个文件创建多个操作按钮
            operation_buttons = [
                {
                    'content': t__task('恢复'),
                    'type': 'primary',
                    'icon': fac.AntdIcon(icon='fc-download'),
                    'custom': f"restore:{f_info['filename']}"
                },
                {
                    'content': t__task('下载'),
                    'type': 'default',
                    'icon': fac.AntdIcon(icon='fc-export'),
                    'custom': f"download:{f_info['filename']}"
                },
                {
                    'content': t__default('删除'),
                    'type': 'primary',
                    'danger': True,
                    'icon': fac.AntdIcon(icon='fc-delete-row'),
                    'custom': f"delete:{f_info['filename']}"
                }
            ]
            
            data.append({
                'key': f_info['filename'],
                'filename': f_info['filename'],
                'size': f_info['size'],
                'size_formatted': format_file_size(f_info['size']),
                'created_at': f_info['created_at'],
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
     Output('db-backup-message-trigger', 'data')],
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
        
        # 执行备份
        print("执行实际备份...")
        path, msg = backup_utils.perform_backup("manual")
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

# 处理表格中的按钮点击（恢复/删除/下载）
@app.callback(
    [Output('db-backup-restore-confirm-modal', 'visible'),
     Output('db-backup-delete-confirm-modal', 'visible'),
     Output('db-backup-selected-filename-store', 'data'),
     Output('db-backup-restore-confirm-modal', 'children'),
     Output('db-backup-delete-confirm-modal', 'children')],
    [Input('db-backup-files-table', 'nClicksButton')],
    [State('db-backup-files-table', 'clickedCustom')],
    prevent_initial_call=True
)
def handle_table_button_clicks(nClicksButton, clickedCustom):
    print(f"=== 表格按钮点击 === nClicks: {nClicksButton}, custom: {clickedCustom}")
    
    if not nClicksButton or not clickedCustom:
        return False, False, no_update, no_update, no_update
        
    try:
        action, filename = clickedCustom.split(':', 1)
        print(f"操作: {action}, 文件: {filename}")
        
        if action == 'restore':
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
                        html.P(t__task("建议在恢复后重启应用程序以确保数据一致性。"))
                    ]),
                    type='error',
                    showIcon=True
                )
            ])
            return True, False, filename, modal_content, no_update
            
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
            return False, True, filename, no_update, modal_content
            
        elif action == 'download':
            # 下载功能可以在这里实现
            print(f"下载文件: {filename}")
            MessageManager.info(content=f"下载功能暂未实现: {filename}")
            return False, False, no_update, no_update, no_update
            
    except Exception as e:
        print(f"处理表格按钮点击异常: {e}")
        traceback.print_exc()
    
    return False, False, no_update, no_update, no_update

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

print("=== 数据库备份回调模块加载完成 ===")