# -*- coding: utf-8 -*-
"""
文件下载路由
为备份文件提供下载支持
"""

import os
from flask import send_file, abort
from server import app
from common.utilities import backup_utils_enhanced as backup_utils
from common.utilities.util_logger import Log

logger = Log.get_logger(__name__)

@app.server.route('/download-backup/<filename>')
def download_backup_file(filename):
    """下载备份文件"""
    try:
        # 验证文件名安全性
        if '..' in filename or '/' in filename or '\\' in filename:
            logger.warning(f"不安全的文件名请求: {filename}")
            abort(400)
        
        # 获取文件路径
        file_path = backup_utils.get_backup_file_path(filename)
        
        if not file_path or not os.path.exists(file_path):
            logger.warning(f"请求的备份文件不存在: {filename}")
            abort(404)
        
        # 验证文件是否为备份文件
        if not (filename.startswith('backup_') and (filename.endswith('.sql') or filename.endswith('.zip'))):
            logger.warning(f"非法的备份文件访问请求: {filename}")
            abort(403)
        
        logger.info(f"下载备份文件: {filename}")
        
        # 返回文件
        return send_file(
            file_path,
            as_attachment=True,
            download_name=filename,
            mimetype='application/octet-stream'
        )
        
    except Exception as e:
        logger.error(f"下载备份文件时出错: {e}")
        abort(500)
