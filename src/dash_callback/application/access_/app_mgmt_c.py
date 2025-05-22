from server import app
from dash.dependencies import Input, Output, State
import dash
from database.sql_db.dao import dao_user
from dash_components import MessageManager
from i18n import t__access, t__default

# 通用函数：更新表格数据
def update_table_data():
    """获取最新的APP用户数据并格式化为表格数据"""
    app_users = dao_user.get_app_user_info(exclude_frozen=False)  # 包括已禁用用户
    return [
        {
            'key': i.account,
            'user_name': i.account,
            'user_full_name': i.account,
            'user_email': i.email,
            'user_status': {
                'tag': t__default('启用' if not i.is_frozen else '禁用'), 
                'color': 'green' if not i.is_frozen else 'red'  # 改进颜色表示
            },
            'is_admin': {
                'tag': t__default('管理员' if i.is_admin == 1 else '普通用户'), 
                'color': 'cyan' if i.is_admin == 1 else 'blue'  # 改进颜色表示
            },
            'operation': [
                {
                    'content': t__default('编辑'),
                    'type': 'primary',
                    'custom': 'update:' + i.account,
                },
                *(
                    [
                        {
                            'content': t__default('删除'),
                            'type': 'primary',
                            'custom': 'delete:' + i.account,
                            'danger': True,
                        }
                    ]
                    if i.is_admin != 1
                    else []
                ),
            ],
        }
        for i in app_users
    ]

@app.callback(
    [
        # 删除用户弹窗
        Output('app-user-mgmt-delete-affirm-modal', 'visible'),
        Output('app-user-mgmt-delete-user-name', 'children'),
        # 更新用户弹窗
        Output('app-user-mgmt-update-modal', 'visible'),
        Output('app-user-mgmt-update-user-name', 'children'),
        Output('app-user-mgmt-update-user-full-name', 'value'),
        Output('app-user-mgmt-update-user-email', 'value'),
        Output('app-user-mgmt-update-phone-number', 'value'),
        Output('app-user-mgmt-update-user-status', 'checked'),
        Output('app-user-mgmt-update-user-status', 'readOnly'),
        Output('app-user-mgmt-update-password', 'value'),
        Output('app-user-mgmt-update-user-remark', 'value'),
        Output('app-user-mgmt-update-roles', 'value'),
        Output('app-user-mgmt-update-roles', 'options'),
        Output('app-user-mgmt-update-roles', 'disabled'),
        Output('app-user-mgmt-update-is-admin', 'checked'),  # 添加新输出
    ],
    Input('app-user-mgmt-table', 'nClicksButton'),
    State('app-user-mgmt-table', 'clickedCustom'),
    prevent_initial_call=True,
)
def update_delete_role(nClicksButton, clickedCustom: str):
    user_name = clickedCustom.split(':')[1]
    if clickedCustom.startswith('delete:'):
        return [
            True,
            user_name,
        ] + [dash.no_update] * 13  # 增加一个dash.no_update
    elif clickedCustom.startswith('update:'):
        # 获取 APP 用户信息
        app_users = dao_user.get_app_user_info([user_name], exclude_frozen=False)  # 移除exclude_frozen过滤
        if not app_users:
            # 如果找不到用户，返回 no_update
            return [dash.no_update] * 15  # 增加一个输出
        
        app_user = app_users[0]
        
        return [dash.no_update] * 2 + [
            True,  # 显示更新模态框
            app_user.account,  # 用户名
            app_user.account,  # 全名，使用账号作为全名
            app_user.email,  # 邮箱
            "",  # 电话号码 - APP 用户没有此字段，设为空
            not bool(app_user.is_frozen),  # 用户状态 - 未冻结 = 启用
            False,  # 管理员状态是否只读
            "",  # 密码字段，更新时为空
            "",  # 备注 - APP 用户没有此字段，设为空
            [],  # 用户角色 - APP 用户没有角色，设为空列表
            [i.role_name for i in dao_user.get_role_info(exclude_disabled=True)],  # 可选角色列表
            app_user.is_admin == 1,  # 如果是管理员，角色选择被禁用
            app_user.is_admin == 1,  # 添加管理员状态开关的值
        ]

################### 更新 APP 用户
@app.callback(
    Output('app-user-mgmt-table', 'data', allow_duplicate=True),
    Input('app-user-mgmt-update-modal', 'okCounts'),
    [
        State('app-user-mgmt-update-user-name', 'children'),
        State('app-user-mgmt-update-user-full-name', 'value'),
        State('app-user-mgmt-update-user-email', 'value'),
        State('app-user-mgmt-update-phone-number', 'value'),
        State('app-user-mgmt-update-user-status', 'checked'),
        State('app-user-mgmt-update-is-admin', 'checked'),  # 添加新状态
        State('app-user-mgmt-update-user-sex', 'value'),
        State('app-user-mgmt-update-password', 'value'),
        State('app-user-mgmt-update-user-remark', 'value'),
        State('app-user-mgmt-update-roles', 'value'),
    ],
    prevent_initial_call=True,
)
def update_app_user(okCounts, account, user_full_name, user_email, phone_number, user_status, is_admin, user_sex, password, user_remark, user_roles):
    if not account or not user_full_name:
        MessageManager.warning(content=t__access('用户名/全名不能为空'))
        return dash.no_update
    
    # 获取用户信息以获取 user_id，确保包含已停用用户
    app_users = dao_user.get_app_user_info([account], exclude_frozen=False)
    if not app_users:
        MessageManager.warning(content=t__access('用户不存在'))
        return dash.no_update
    
    app_user = app_users[0]
    
    # 更新 APP 用户，加入管理员状态的更新
    rt = dao_user.update_app_user(
        user_id=app_user.user_id,
        account=user_full_name,  # 使用全名作为新账号
        password=password if password else None,  # 如果提供了密码则更新
        email=user_email,
        is_frozen=0 if user_status else 1,  # 状态取反：启用=未冻结
        is_admin=1 if is_admin else 0,  # 更新管理员状态
        avatar=None  # 不更新头像
    )
    
    # 构建状态变更消息
    status_changes = []
    if user_status != (not bool(app_user.is_frozen)):
        status_changes.append("用户状态已" + ("启用" if user_status else "禁用"))
    
    if is_admin != (app_user.is_admin == 1):
        status_changes.append("管理员权限已" + ("授予" if is_admin else "移除"))
    
    status_msg = "，".join(status_changes) if status_changes else ""
    
    if rt:
        MessageManager.success(content=t__access(f'APP用户更新成功{status_msg and "（" + status_msg + "）"}'))
        # 重新获取所有用户（包括已禁用的）
        return update_table_data()
    else:
        MessageManager.warning(content=t__access('APP用户更新失败'))
        return dash.no_update

################### 打开新建APP用户模态框
@app.callback(
    [
        Output('app-user-mgmt-add-modal', 'visible'),
        Output('app-user-mgmt-add-account', 'value'),
        Output('app-user-mgmt-add-email', 'value'),
        Output('app-user-mgmt-add-status', 'checked'),
        Output('app-user-mgmt-add-is-admin', 'checked'),
        Output('app-user-mgmt-add-password', 'value'),
    ],
    Input('app-user-mgmt-button-add', 'nClicks'),
    prevent_initial_call=True,
)
def open_add_app_user_modal(nClicks):
    """显示新建APP用户的弹窗"""
    from uuid import uuid4

    # 生成随机初始密码
    initial_password = str(uuid4())[:12].replace('-', '')
    
    return [
        True,          # 显示模态框
        '',            # 账号置空
        '',            # 邮箱置空
        True,          # 默认启用状态
        False,         # 默认非管理员
        initial_password,  # 默认随机密码
    ]
################### 检查APP用户账号是否可用
@app.callback(
    [
        Output('app-user-mgmt-add-account-form', 'validateStatus', allow_duplicate=True),
        Output('app-user-mgmt-add-account-form', 'help', allow_duplicate=True),
    ],
    Input('app-user-mgmt-add-account', 'debounceValue'),
    prevent_initial_call=True,
)
def check_app_user_account(account):
    """校验新建APP用户账号的有效性"""
    if not account:
        return 'error', t__access('请填写APP用户账号')
    if not dao_user.exists_app_user_account(account):
        return 'success', t__access('该账号可用')
    else:
        return 'error', t__access('该账号已存在')
    
################### 新建APP用户
@app.callback(
    Output('app-user-mgmt-table', 'data', allow_duplicate=True),
    Input('app-user-mgmt-add-modal', 'okCounts'),
    [
        State('app-user-mgmt-add-account', 'debounceValue'),
        State('app-user-mgmt-add-email', 'value'),
        State('app-user-mgmt-add-status', 'checked'),
        State('app-user-mgmt-add-is-admin', 'checked'),
        State('app-user-mgmt-add-password', 'value'),
    ],
    prevent_initial_call=True,
)
def add_app_user(okCounts, account, email, status, is_admin, password):
    """新建APP用户"""
    if not account or not password:
        MessageManager.warning(content=t__access('账号和密码不能为空'))
        return dash.no_update
    
    # 检查账号是否已存在
    if dao_user.exists_app_user_account(account):
        MessageManager.warning(content=t__access('该账号已存在'))
        return dash.no_update
    
    # 创建APP用户
    rt = dao_user.create_app_user(
        account=account,
        password=password,
        email=email,
        is_admin=1 if is_admin else 0,
        is_frozen=0 if status else 1,  # 状态取反：启用=未冻结
        avatar=None  # 使用默认头像
    )
    
    if rt:
        MessageManager.success(content=t__access(f'APP用户添加成功'))
        return update_table_data()
    else:
        MessageManager.warning(content=t__access('APP用户添加失败'))
        return dash.no_update

################### 删除 APP 用户
@app.callback(
    Output('app-user-mgmt-table', 'data', allow_duplicate=True),
    Input('app-user-mgmt-delete-affirm-modal', 'okCounts'),
    State('app-user-mgmt-delete-user-name', 'children'),
    prevent_initial_call=True,
)
def delete_app_user(okCounts, account):
    """删除 APP 用户"""
    # 获取用户信息以获取 user_id
    app_users = dao_user.get_app_user_info([account])
    if not app_users:
        MessageManager.warning(content=t__access('用户不存在'))
        return dash.no_update
    
    app_user = app_users[0]
    
    # 执行删除操作
    rt = dao_user.delete_app_user(app_user.user_id)
    
    if rt:
        MessageManager.success(content=t__access('APP用户删除成功'))
        return update_table_data()
    else:
        MessageManager.warning(content=t__access('APP用户删除失败'))
        return dash.no_update