from dash import Input, Output, State, html, no_update, ctx, dcc
from server import app
import feffery_antd_components as fac
from dash_components import MessageManager
from common.utilities import backup_utils
from i18n import t__task, t__default # 假设备份相关的翻译也放在task.json

# 表格列定义
def get_table_columns():
    return [
        {'title': t__task('备份文件名'), 'dataIndex': 'filename', 'width': '40%'},
        {'title': t__task('文件大小 (Bytes)'), 'dataIndex': 'size', 'width': '20%'},
        {'title': t__task('备份时间'), 'dataIndex': 'created_at', 'width': '25%'},
        {
            'title': t__default('操作'),
            'dataIndex': 'operation',
            'renderOptions': {'renderType': 'buttonGroup'},
            'width': '15%'
        },
    ]

# 获取并格式化备份文件数据
def get_formatted_backup_data():
    files, msg = backup_utils.list_backup_files()
    if not files and msg != "获取成功": # 如果列表为空但不是因为确实没有文件而是因为错误
        MessageManager.error(content=msg)
        return []
    
    data = []
    for f_info in files:
        data.append({
            'key': f_info['filename'],
            'filename': f_info['filename'],
            'size': f_info['size'],
            'created_at': f_info['created_at'],
            'operation': [
                {
                    'content': t__task('恢复'),
                    'type': 'primary',
                    'icon': fac.AntdIcon(icon='fc-download'),
                    'custom': f"restore:{f_info['filename']}"
                },
                {
                    'content': t__default('删除'),
                    'type': 'primary',
                    'danger': True,
                    'icon': fac.AntdIcon(icon='fc-delete-row'),
                    'custom': f"delete:{f_info['filename']}"
                }
            ]
        })
    return data

@app.callback(
    Output('db-backup-files-table', 'columns'),
    Output('db-backup-files-table', 'data'),
    Output('db-backup-table-spin', 'spinning'), # 控制loading状态
    Input('db-backup-init-timeout', 'timeoutCount'),
    Input('db-backup-manual-backup-button', 'nClicks'), # 备份后刷新
    Input('db-backup-restore-confirm-modal', 'okCounts'), # 恢复操作不直接刷新，因为可能需要重启
    Input('db-backup-delete-confirm-modal', 'okCounts'), # 删除后刷新
    prevent_initial_call=True 
)
def load_and_refresh_backup_table(init_timeout, backup_nclicks, restore_ok, delete_ok):
    triggered_id = ctx.triggered_id

    if triggered_id == 'db-backup-manual-backup-button':
        if backup_nclicks:
            _, msg = backup_utils.perform_backup("manual")
            if "成功" in msg:
                MessageManager.success(content=msg)
            else:
                MessageManager.error(content=msg)
    
    # 对于删除操作，在确认后刷新
    if triggered_id == 'db-backup-delete-confirm-modal' and delete_ok:
        # 实际删除操作在另一个回调中处理，这里只是刷新
        pass

    columns = get_table_columns()
    data = get_formatted_backup_data()
    return columns, data, False # spinning=False

# 处理手动备份按钮点击 (实际备份操作已移至上面的回调，这里可以简化或移除，除非有额外逻辑)
# @app.callback(
#     Output('db-backup-files-table', 'data', allow_duplicate=True), # 更新表格数据
#     Input('db-backup-manual-backup-button', 'nClicks'),
#     prevent_initial_call=True
# )
# def handle_manual_backup(nClicks):
#     if nClicks:
#         backup_file_path, msg = backup_utils.perform_backup("manual")
#         if backup_file_path:
#             MessageManager.success(content=msg)
#             return get_formatted_backup_data()
#         else:
#             MessageManager.error(content=msg)
#             return no_update
#     return no_update

# 处理表格中的按钮点击（恢复/删除）
@app.callback(
    Output('db-backup-restore-confirm-modal', 'visible'),
    Output('db-backup-delete-confirm-modal', 'visible'),
    Output('db-backup-selected-filename-store', 'data'),
    Output('db-backup-restore-confirm-modal', 'children'), # 设置恢复确认信息
    Output('db-backup-delete-confirm-modal', 'children'), # 设置删除确认信息
    Input('db-backup-files-table', 'nClicksButton'),
    State('db-backup-files-table', 'clickedCustom'),
    prevent_initial_call=True
)
def handle_table_button_clicks(nClicksButton, clickedCustom):
    if nClicksButton and clickedCustom:
        action, filename = clickedCustom.split(':', 1)
        if action == 'restore':
            modal_content = html.Div([
                fac.AntdText(t__task("您确定要从备份文件 ")),
                fac.AntdText(filename, strong=True),
                fac.AntdText(t__task(" 恢复数据库吗？")),
                html.Br(),
                fac.AntdText(t__task("此操作可能导致当前数据丢失，并建议在恢复后重启应用程序。"), style={'color': 'red'})
            ])
            return True, False, filename, modal_content, no_update
        elif action == 'delete':
            modal_content = html.Div([
                fac.AntdText(t__task("您确定要删除备份文件 ")),
                fac.AntdText(filename, strong=True),
                fac.AntdText(t__task(" 吗？此操作不可恢复。"))
            ])
            return False, True, filename, no_update, modal_content
    return False, False, no_update, no_update, no_update

# 处理恢复确认
@app.callback(
    # Output('db-backup-files-table', 'data', allow_duplicate=True), # 恢复后不直接刷新列表，提示重启
    Input('db-backup-restore-confirm-modal', 'okCounts'),
    State('db-backup-selected-filename-store', 'data'),
    prevent_initial_call=True
)
def handle_restore_confirmation(okCounts, filename):
    if okCounts and filename:
        success, msg = backup_utils.perform_restore(filename)
        if success:
            MessageManager.success(content=msg, duration=10) # 持续时间长一点提示用户重启
        else:
            MessageManager.error(content=msg)
        # 不刷新表格，因为恢复操作可能需要应用重启才能看到效果
        # return get_formatted_backup_data() 
    return #no_update

# 处理删除确认
@app.callback(
    # Output('db-backup-files-table', 'data', allow_duplicate=True), # 刷新逻辑已合并到 load_and_refresh_backup_table
    Input('db-backup-delete-confirm-modal', 'okCounts'),
    State('db-backup-selected-filename-store', 'data'),
    prevent_initial_call=True
)
def handle_delete_confirmation(okCounts, filename):
    if okCounts and filename:
        success, msg = backup_utils.delete_backup_file(filename)
        if success:
            MessageManager.success(content=msg)
            # 表格刷新将由 load_and_refresh_backup_table 通过 Input('db-backup-delete-confirm-modal', 'okCounts') 触发
        else:
            MessageManager.error(content=msg)
    return #no_update

# 初始加载时设置表格spinning状态
@app.callback(
    Output('db-backup-table-spin', 'spinning', allow_duplicate=True),
    Input('db-backup-init-timeout', 'timeoutCount'),
    prevent_initial_call=True
)
def initial_spin_true(n):
    if n == 1: # 确保只在第一次触发
        return True
    return no_update