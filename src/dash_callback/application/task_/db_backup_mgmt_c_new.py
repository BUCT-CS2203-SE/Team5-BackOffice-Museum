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
            
            # 为每个文件创建多个操作按钮
            filename_safe = str(f_info.get('filename', '')).strip()
            operation_buttons = [
                {
                    'content': '预览',
                    'type': 'default',
                    'icon': fac.AntdIcon(icon='fc-search'),
                    'custom': f"preview:{filename_safe}"
                },
                {
                    'content': '下载',
                    'type': 'default',
                    'icon': fac.AntdIcon(icon='fc-export'),
                    'custom': f"download:{filename_safe}"
                },
                {
                    'content': '恢复',
                    'type': 'primary',
                    'icon': fac.AntdIcon(icon='fc-download'),
                    'custom': f"restore:{filename_safe}"
                },
                {
                    'content': '删除',
                    'type': 'primary',
                    'danger': True,
                    'icon': fac.AntdIcon(icon='fc-delete-row'),
                    'custom': f"delete:{filename_safe}"
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

print("=== 数据库备份回调模块加载完成 ===")
