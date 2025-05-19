from common.utilities.util_menu_access import MenuAccess
import feffery_antd_components as fac
from common.utilities.util_logger import Log
from dash_components import Card, Table
from database.sql_db.dao import dao_user
from config.enums import Sex
import dash_callback.application.access_.app_mgmt_c  # noqa
from i18n import t__access, t__default
import feffery_utils_components as fuc

# 二级菜单的标题、图标和显示顺序
title = 'APP用户管理'
icon = None
order = 5
logger = Log.get_logger(__name__)
access_metas = ('APP用户管理-页面',)


def render_content(menu_access: MenuAccess, **kwargs):
    return fac.AntdCol(
        [
            fac.AntdRow(
                fac.AntdButton(
                    id='app-user-mgmt-button-add',
                    children=t__access('添加APP用户'),
                    type='primary',
                    icon=fac.AntdIcon(icon='antd-plus'),
                    style={'marginBottom': '10px'},
                )
            ),
            fac.AntdRow(
                [
                    Card(
                        Table(
                            id='app-user-mgmt-table',
                            columns=[
                                {'title': t__access('账号'), 'dataIndex': 'user_name'},
                                {'title': t__access('邮箱'), 'dataIndex': 'user_email'},
                                {'title': t__access('是否封禁'), 'dataIndex': 'user_status', 'renderOptions': {'renderType': 'tags'}},
                                {'title': t__access('管理员'), 'dataIndex': 'is_admin', 'renderOptions': {'renderType': 'tags'}},
                                {'title': t__default('操作'), 'dataIndex': 'operation', 'renderOptions': {'renderType': 'button'}},
                            ],
                            data=[
                                {
                                    'key': i.account,
                                    'user_name': i.account,
                                    'user_email': i.email,
                                    'user_status': {'tag': t__default('启用' if not i.is_frozen else '停用'), 'color': 'cyan' if not i.is_frozen else 'volcano'},
                                    'is_admin': {'tag': t__default('是' if i.is_admin == 1 else '否'), 'color': 'green' if i.is_admin == 1 else 'default'},
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
                                for i in dao_user.get_app_user_info(exclude_frozen=False)
                            ],
                            pageSize=10,
                        ),
                        style={'width': '100%'},
                    ),
                    # 添加APP用户的模态框
                    fac.AntdModal(
                        children=[
                            fac.AntdForm(
                                [
                                    fac.AntdFormItem(
                                        fac.AntdInput(id='app-user-mgmt-add-account', debounceWait=500),
                                        label=t__access('账号'),
                                        required=True,
                                        id='app-user-mgmt-add-account-form',
                                        hasFeedback=True,
                                    ),
                                    fac.AntdFormItem(
                                        fac.AntdInput(id='app-user-mgmt-add-email'),
                                        label=t__access('邮箱'),
                                    ),
                                    fac.AntdFormItem(
                                        fac.AntdInput(id='app-user-mgmt-add-password'),
                                        label=t__access('密码'),
                                        required=True,
                                    ),
                                    fac.AntdFlex(
                                        [
                                            fac.AntdFormItem(
                                                fac.AntdSwitch(id='app-user-mgmt-add-status'),
                                                label=t__access('用户状态'),
                                                required=True,
                                                style={'flex': 1}
                                            ),
                                            fac.AntdFormItem(
                                                fac.AntdSwitch(id='app-user-mgmt-add-is-admin'),
                                                label=t__access('是否管理员'),
                                                required=True,
                                                style={'flex': 1}
                                            ),
                                        ]
                                    ),
                                ],
                                labelAlign='left',
                                className={'.ant-form-item': {'marginBottom': '12px', 'marginRight': '8px'}},
                            )
                        ],
                        destroyOnClose=False,
                        renderFooter=True,
                        okText=t__default('确定'),
                        cancelText=t__default('取消'),
                        title=t__access('添加APP用户'),
                        mask=False,
                        maskClosable=False,
                        id='app-user-mgmt-add-modal',
                        style={'boxSizing': 'border-box'},
                    ),
                    # 删除APP用户的确认模态框
                    fac.AntdModal(
                        children=[
                            fac.AntdText(t__access('您确定要删除APP用户 ')),
                            fac.AntdText(
                                '',
                                id='app-user-mgmt-delete-user-name',
                                type='danger',
                                underline=True,
                            ),
                            fac.AntdText('?'),
                        ],
                        destroyOnClose=False,
                        renderFooter=True,
                        okText=t__default('确定'),
                        cancelText=t__default('取消'),
                        okButtonProps={'danger': True},
                        title=t__default('确认要删除？'),
                        mask=False,
                        maskClosable=False,
                        id='app-user-mgmt-delete-affirm-modal',
                    ),
                    # 更新APP用户的模态框
                    fac.AntdModal(
                        children=[
                            fac.AntdForm(
                                [
                                    fac.AntdFormItem(
                                        fac.AntdText(id='app-user-mgmt-update-user-name'),
                                        label=t__access('账号'),
                                    ),
                                    fac.AntdFormItem(
                                        fac.AntdInput(id='app-user-mgmt-update-user-full-name'),
                                        label=t__access('新账号'),
                                        required=True,
                                    ),
                                    fac.AntdFormItem(
                                        fac.AntdInput(id='app-user-mgmt-update-user-email'),
                                        label=t__access('邮箱'),
                                    ),
                                    fac.AntdFormItem(
                                        fac.AntdInput(id='app-user-mgmt-update-password'),
                                        label=t__access('新密码'),
                                    ),
                                    fac.AntdFlex(
                                        [
                                            fac.AntdFormItem(
                                                fac.AntdSwitch(id='app-user-mgmt-update-user-status'),
                                                label=t__access('用户状态'),
                                                required=True,
                                                style={'flex': 1}
                                            ),
                                            # 隐藏不需要的字段，但保持组件ID与回调一致
                                            fac.AntdFormItem(
                                                fac.AntdInput(id='app-user-mgmt-update-user-sex', style={'display': 'none'}),
                                                style={'display': 'none'}
                                            ),
                                            fac.AntdFormItem(
                                                fac.AntdInput(id='app-user-mgmt-update-phone-number', style={'display': 'none'}),
                                                style={'display': 'none'}
                                            ),
                                            fac.AntdFormItem(
                                                fac.AntdInput(id='app-user-mgmt-update-user-remark', style={'display': 'none'}),
                                                style={'display': 'none'}
                                            ),
                                        ]
                                    ),
                                    fac.AntdFormItem(
                                        fac.AntdSelect(id='app-user-mgmt-update-roles', mode='multiple'),
                                        label=t__access('角色'),
                                        style={'display': 'none'}
                                    ),
                                ],
                                labelAlign='left',
                                className={'.ant-form-item': {'marginBottom': '12px', 'marginRight': '8px'}},
                            )
                        ],
                        destroyOnClose=False,
                        renderFooter=True,
                        okText=t__default('确定'),
                        cancelText=t__default('取消'),
                        title=t__access('更新APP用户'),
                        mask=False,
                        maskClosable=False,
                        id='app-user-mgmt-update-modal',
                        style={'boxSizing': 'border-box'},
                    ),
                ],
            ),
        ],
    )

