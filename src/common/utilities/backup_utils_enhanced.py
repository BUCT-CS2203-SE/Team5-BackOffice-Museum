import os
import shutil
import datetime
import glob
import subprocess
import zipfile
import json
import threading
import tempfile
from pathlib import Path
from common.utilities.util_logger import Log
from config.dashgo_conf import SqlDbConf

logger = Log.get_logger(__name__)

# 从配置文件获取数据库连接信息
DB_HOST = SqlDbConf.HOST
DB_PORT = SqlDbConf.PORT
DB_USER = SqlDbConf.USER
DB_PASSWORD = SqlDbConf.PASSWORD
DB_NAME = SqlDbConf.DATABASE

# Backup Configuration
BACKUP_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'db_backups')
BACKUP_FILE_PREFIX = f'backup_{DB_NAME}_'
BACKUP_FILE_SUFFIX = '.sql'
BACKUP_ZIP_SUFFIX = '.zip'
BACKUP_METADATA_SUFFIX = '.json'

# 定时备份任务锁
_backup_lock = threading.Lock()

def ensure_backup_dir_exists():
    """确保备份目录存在"""
    if not os.path.exists(BACKUP_DIR):
        try:
            os.makedirs(BACKUP_DIR)
            logger.info(f"备份目录 {BACKUP_DIR} 已创建。")
        except OSError as e:
            logger.error(f"创建备份目录 {BACKUP_DIR} 失败: {e}")
            raise

def create_backup_metadata(backup_filename: str, backup_type: str = "manual", 
                         file_size: int = 0, success: bool = True, 
                         error_msg: str = None, compressed: bool = False):
    """创建备份元数据文件"""
    metadata = {
        "filename": backup_filename,
        "backup_type": backup_type,
        "database_name": DB_NAME,
        "host": DB_HOST,
        "port": DB_PORT,
        "created_at": datetime.datetime.now().isoformat(),
        "compressed": compressed,
        "file_size": file_size,
        "success": success,
        "error_message": error_msg
    }
    
    # 确定元数据文件名
    if compressed and backup_filename.endswith(BACKUP_ZIP_SUFFIX):
        metadata_filename = backup_filename.replace(BACKUP_ZIP_SUFFIX, BACKUP_METADATA_SUFFIX)
    else:
        metadata_filename = backup_filename.replace(BACKUP_FILE_SUFFIX, BACKUP_METADATA_SUFFIX)
    
    metadata_path = os.path.join(BACKUP_DIR, metadata_filename)
    
    try:
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        logger.info(f"备份元数据文件 {metadata_path} 已创建")
        return metadata_path
    except Exception as e:
        logger.error(f"创建备份元数据文件失败: {e}")
        return None

def get_backup_metadata(backup_filename: str):
    """获取备份文件的元数据"""
    if backup_filename.endswith(BACKUP_ZIP_SUFFIX):
        metadata_filename = backup_filename.replace(BACKUP_ZIP_SUFFIX, BACKUP_METADATA_SUFFIX)
    else:
        metadata_filename = backup_filename.replace(BACKUP_FILE_SUFFIX, BACKUP_METADATA_SUFFIX)
    
    metadata_path = os.path.join(BACKUP_DIR, metadata_filename)
    
    if not os.path.exists(metadata_path):
        return None
    
    try:
        with open(metadata_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"读取备份元数据文件失败: {e}")
        return None

def compress_backup_file(sql_file_path: str):
    """压缩备份文件"""
    zip_file_path = sql_file_path.replace(BACKUP_FILE_SUFFIX, BACKUP_ZIP_SUFFIX)
    
    try:
        with zipfile.ZipFile(zip_file_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as zipf:
            zipf.write(sql_file_path, os.path.basename(sql_file_path))
        
        # 删除原始SQL文件
        os.remove(sql_file_path)
        logger.info(f"备份文件已压缩: {zip_file_path}")
        return zip_file_path, "压缩成功"
    except Exception as e:
        logger.error(f"压缩备份文件失败: {e}")
        return None, f"压缩失败: {str(e)}"

def extract_backup_file(zip_file_path: str):
    """解压备份文件到临时目录"""
    extract_dir = tempfile.mkdtemp()
    
    try:
        with zipfile.ZipFile(zip_file_path, 'r') as zipf:
            zipf.extractall(extract_dir)
        
        # 查找SQL文件
        sql_files = glob.glob(os.path.join(extract_dir, "*.sql"))
        if sql_files:
            return sql_files[0], "解压成功"
        else:
            return None, "压缩文件中没有找到SQL文件"
    except Exception as e:
        logger.error(f"解压备份文件失败: {e}")
        return None, f"解压失败: {str(e)}"

def perform_backup(custom_suffix: str = None, compress: bool = True, backup_type: str = "manual"):
    """
    执行 MySQL 数据库备份。
    """
    with _backup_lock:  # 确保同时只有一个备份任务运行
        ensure_backup_dir_exists()
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file_name = f"{BACKUP_FILE_PREFIX}{timestamp}"
        if custom_suffix:
            backup_file_name += f"_{custom_suffix}"
        backup_file_name += BACKUP_FILE_SUFFIX
        backup_file_path = os.path.join(BACKUP_DIR, backup_file_name)

        # Construct mysqldump command
        cmd = [
            'mysqldump',
            f'--host={DB_HOST}',
            f'--port={str(DB_PORT)}',
            f'--user={DB_USER}',
            f'--password={DB_PASSWORD}',
            '--single-transaction',
            '--routines',
            '--triggers', 
            '--events',
            '--add-drop-database',
            '--add-drop-table',
            '--create-options',
            '--disable-keys',
            '--extended-insert',
            '--lock-tables=false',
            '--set-charset',
            DB_NAME
        ]

        try:
            logger.info(f"开始备份数据库 '{DB_NAME}' 到 {backup_file_path}")
            
            with open(backup_file_path, 'w', encoding='utf-8') as f_out:
                process = subprocess.Popen(cmd, stdout=f_out, stderr=subprocess.PIPE, text=True, encoding='utf-8')
                _, stderr = process.communicate()

            if process.returncode == 0:
                backup_size = os.path.getsize(backup_file_path)
                logger.info(f"MySQL 数据库 '{DB_NAME}' 已成功备份到 {backup_file_path}，大小: {backup_size} bytes")
                
                final_path = backup_file_path
                final_filename = backup_file_name
                
                # 是否压缩备份文件
                if compress:
                    zip_path, zip_msg = compress_backup_file(backup_file_path)
                    if zip_path:
                        final_path = zip_path
                        final_filename = os.path.basename(zip_path)
                        zip_size = os.path.getsize(zip_path)
                        
                        # 创建压缩文件的元数据
                        create_backup_metadata(final_filename, backup_type, zip_size, True, None, True)
                        logger.info(f"备份文件已压缩: {zip_path}")
                    else:
                        # 压缩失败，保留原文件
                        create_backup_metadata(final_filename, backup_type, backup_size, True, None, False)
                        logger.warning(f"压缩失败，保留原始备份文件: {zip_msg}")
                else:
                    # 不压缩，创建原始文件的元数据
                    create_backup_metadata(final_filename, backup_type, backup_size, True, None, False)
                
                return final_path, "备份成功"
            else:
                error_message = f"MySQL 备份失败。返回码: {process.returncode}。错误: {stderr.strip() if stderr else 'Unknown error'}"
                logger.error(error_message)
                
                # 创建失败的元数据
                create_backup_metadata(backup_file_name, backup_type, 0, False, stderr.strip())
                
                # 清理失败的备份文件
                if os.path.exists(backup_file_path):
                    try:
                        if os.path.getsize(backup_file_path) == 0:
                            os.remove(backup_file_path)
                    except OSError:
                        pass
                return None, f"备份失败: {stderr.strip() if stderr else 'mysqldump 执行错误'}"

        except FileNotFoundError:
            error_msg = "mysqldump 命令未找到。请确保 MySQL 客户端已安装并在系统 PATH 中。"
            logger.error(error_msg)
            create_backup_metadata(backup_file_name, backup_type, 0, False, error_msg)
            return None, f"备份失败: {error_msg}"
        except Exception as e:
            error_msg = f"MySQL 备份过程中发生意外错误: {e}"
            logger.error(error_msg)
            create_backup_metadata(backup_file_name, backup_type, 0, False, str(e))
            if os.path.exists(backup_file_path):
                try:
                    os.remove(backup_file_path)
                except OSError:
                    pass
            return None, f"备份失败: {str(e)}"

def list_backup_files():
    """列出所有备份文件及其信息"""
    ensure_backup_dir_exists()
    backup_files_info = []
    try:
        # 查找SQL文件和ZIP文件
        sql_pattern = os.path.join(BACKUP_DIR, f"{BACKUP_FILE_PREFIX}*{BACKUP_FILE_SUFFIX}")
        zip_pattern = os.path.join(BACKUP_DIR, f"{BACKUP_FILE_PREFIX}*{BACKUP_ZIP_SUFFIX}")
        
        all_files = glob.glob(sql_pattern) + glob.glob(zip_pattern)
        
        for file_path in all_files:
            if os.path.isfile(file_path):
                try:
                    stat = os.stat(file_path)
                    filename = os.path.basename(file_path)
                    
                    # 获取备份元数据
                    metadata = get_backup_metadata(filename)
                    
                    file_info = {
                        'filename': filename,
                        'size': stat.st_size,
                        'created_at': datetime.datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                        'full_path': file_path,
                        'is_compressed': filename.endswith(BACKUP_ZIP_SUFFIX),
                        'backup_type': metadata.get('backup_type', 'unknown') if metadata else 'unknown',
                        'success': metadata.get('success', True) if metadata else True,
                        'database': metadata.get('database_name', DB_NAME) if metadata else DB_NAME,
                        'error_message': metadata.get('error_message') if metadata else None
                    }
                    backup_files_info.append(file_info)
                except Exception as e:
                    logger.warning(f"获取文件信息失败 {file_path}: {e}")
        
        # 按创建时间降序排列
        backup_files_info.sort(key=lambda x: x['created_at'], reverse=True)
        return backup_files_info, "获取成功"
    except Exception as e:
        logger.error(f"列出备份文件失败: {e}")
        return [], f"列出备份文件失败: {str(e)}"

def perform_restore(backup_filename: str):
    """
    从指定的备份文件恢复 MySQL 数据库。
    警告：这是一个潜在的破坏性操作！
    """
    ensure_backup_dir_exists()
    backup_file_path = os.path.join(BACKUP_DIR, backup_filename)

    if not os.path.exists(backup_file_path):
        logger.error(f"备份文件 {backup_file_path} 不存在。")
        return False, "备份文件不存在"

    # 处理压缩文件
    actual_sql_file = backup_file_path
    temp_sql_file = None
    
    if backup_filename.endswith(BACKUP_ZIP_SUFFIX):
        # 解压缩文件到临时位置
        temp_sql_file, decompress_msg = extract_backup_file(backup_file_path)
        if not temp_sql_file:
            return False, f"解压缩失败: {decompress_msg}"
        actual_sql_file = temp_sql_file
    
    if os.path.getsize(actual_sql_file) == 0:
        logger.error(f"备份文件 {actual_sql_file} 为空，无法恢复。")
        return False, "备份文件为空"

    # 在恢复前先创建当前数据库的备份
    try:
        logger.info("恢复前创建安全备份...")
        pre_restore_backup, backup_msg = perform_backup(
            custom_suffix=f"pre_restore_{datetime.datetime.now().strftime('%H%M%S')}", 
            compress=True, 
            backup_type="pre_restore"
        )
        if pre_restore_backup:
            logger.info(f"安全备份已创建: {pre_restore_backup}")
        else:
            logger.warning(f"安全备份创建失败: {backup_msg}")
    except Exception as e:
        logger.warning(f"创建安全备份时出错: {e}")

    # Construct mysql command
    cmd = [
        'mysql',
        f'--host={DB_HOST}',
        f'--port={str(DB_PORT)}',
        f'--user={DB_USER}',
        f'--password={DB_PASSWORD}',
        '--default-character-set=utf8mb4',
        DB_NAME
    ]

    try:
        logger.warning(f"准备从 '{actual_sql_file}' 恢复数据库 '{DB_NAME}'。这是一个高风险操作，将覆盖现有数据。")

        with open(actual_sql_file, 'r', encoding='utf-8') as f_in:
            process = subprocess.Popen(cmd, stdin=f_in, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8')
            stdout, stderr = process.communicate()

        # 清理临时文件
        if temp_sql_file and os.path.exists(temp_sql_file):
            try:
                os.remove(temp_sql_file)
                os.rmdir(os.path.dirname(temp_sql_file))
            except:
                pass

        if process.returncode == 0:
            logger.info(f"MySQL 数据库 '{DB_NAME}' 已成功从 {backup_filename} 恢复。")
            return True, "恢复成功。请检查数据以确保完整性，并考虑重启应用程序。"
        else:
            error_message = f"MySQL 恢复失败。返回码: {process.returncode}。错误: {stderr.strip() if stderr else 'Unknown error'}"
            logger.error(error_message)
            return False, f"恢复失败: {stderr.strip() if stderr else 'mysql 执行错误'}"

    except FileNotFoundError:
        logger.error("mysql 命令未找到。请确保 MySQL 客户端已安装并在系统 PATH 中。")
        return False, "恢复失败: mysql 命令未找到。"
    except Exception as e:
        logger.error(f"MySQL 恢复过程中发生意外错误: {e}")
        return False, f"恢复失败: {str(e)}"
    finally:
        # 确保清理临时文件
        if temp_sql_file and os.path.exists(temp_sql_file):
            try:
                os.remove(temp_sql_file)
                temp_dir = os.path.dirname(temp_sql_file)
                if os.path.exists(temp_dir):
                    os.rmdir(temp_dir)
            except:
                pass

def delete_backup_file(backup_filename: str):
    """删除指定的备份文件和相关元数据"""
    ensure_backup_dir_exists()
    backup_file_path = os.path.join(BACKUP_DIR, backup_filename)
    
    try:
        if not os.path.exists(backup_file_path):
            logger.warning(f"尝试删除的备份文件 {backup_file_path} 不存在。")
            return False, "文件不存在"
        
        # 删除备份文件
        os.remove(backup_file_path)
        logger.info(f"备份文件 {backup_file_path} 已成功删除。")
        
        # 删除对应的元数据文件
        if backup_filename.endswith(BACKUP_ZIP_SUFFIX):
            metadata_filename = backup_filename.replace(BACKUP_ZIP_SUFFIX, BACKUP_METADATA_SUFFIX)
        else:
            metadata_filename = backup_filename.replace(BACKUP_FILE_SUFFIX, BACKUP_METADATA_SUFFIX)
        
        metadata_path = os.path.join(BACKUP_DIR, metadata_filename)
        if os.path.exists(metadata_path):
            os.remove(metadata_path)
            logger.info(f"元数据文件 {metadata_path} 已删除。")
        
        return True, "删除成功"
    except Exception as e:
        logger.error(f"删除备份文件 {backup_file_path} 失败: {e}")
        return False, f"删除失败: {str(e)}"

def get_backup_file_path(backup_filename: str):
    """获取备份文件的完整路径，用于下载"""
    backup_file_path = os.path.join(BACKUP_DIR, backup_filename)
    
    if os.path.exists(backup_file_path):
        return backup_file_path
    else:
        return None

def get_backup_content_preview(backup_filename: str, max_lines=50):
    """获取备份文件内容预览"""
    backup_file_path = os.path.join(BACKUP_DIR, backup_filename)
    
    if not os.path.exists(backup_file_path):
        return None, "备份文件不存在"
    
    try:
        actual_sql_file = backup_file_path
        temp_sql_file = None
        
        # 如果是压缩文件，先解压
        if backup_filename.endswith(BACKUP_ZIP_SUFFIX):
            temp_sql_file, decompress_msg = extract_backup_file(backup_file_path)
            if not temp_sql_file:
                return None, f"解压缩失败: {decompress_msg}"
            actual_sql_file = temp_sql_file
        
        content_lines = []
        line_count = 0
        
        with open(actual_sql_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line_count >= max_lines:
                    content_lines.append(f"... (显示前{max_lines}行，文件可能包含更多内容)")
                    break
                content_lines.append(line.rstrip())
                line_count += 1
        
        # 清理临时文件
        if temp_sql_file and os.path.exists(temp_sql_file):
            try:
                os.remove(temp_sql_file)
                os.rmdir(os.path.dirname(temp_sql_file))
            except:
                pass
        
        return '\n'.join(content_lines), "获取成功"
        
    except Exception as e:
        logger.error(f"读取备份文件内容失败: {e}")
        return None, f"读取失败: {str(e)}"

def cleanup_old_backups(keep_count=10):
    """清理旧的备份文件，保留最新的指定数量"""
    try:
        files, msg = list_backup_files()
        if not files:
            return True, "没有备份文件需要清理"
        
        if len(files) <= keep_count:
            return True, f"当前备份文件数量({len(files)})未超过保留数量({keep_count})"
        
        # 按时间排序，删除最旧的文件
        files_to_delete = files[keep_count:]
        deleted_count = 0
        
        for file_info in files_to_delete:
            success, _ = delete_backup_file(file_info['filename'])
            if success:
                deleted_count += 1
        
        return True, f"清理完成，删除了 {deleted_count} 个旧备份文件"
        
    except Exception as e:
        logger.error(f"清理旧备份文件失败: {e}")
        return False, f"清理失败: {str(e)}"

def validate_backup_file(backup_filename: str):
    """验证备份文件的完整性"""
    backup_file_path = os.path.join(BACKUP_DIR, backup_filename)
    
    if not os.path.exists(backup_file_path):
        return False, "备份文件不存在"
    
    try:
        actual_sql_file = backup_file_path
        temp_sql_file = None
        
        # 如果是压缩文件，先解压进行验证
        if backup_filename.endswith(BACKUP_ZIP_SUFFIX):
            temp_sql_file, decompress_msg = extract_backup_file(backup_file_path)
            if not temp_sql_file:
                return False, f"解压缩失败: {decompress_msg}"
            actual_sql_file = temp_sql_file
        
        # 检查文件大小
        if os.path.getsize(actual_sql_file) == 0:
            return False, "备份文件为空"
        
        # 检查文件格式（简单验证）
        with open(actual_sql_file, 'r', encoding='utf-8') as f:
            first_lines = [f.readline().strip() for _ in range(10)]
            
            # 检查是否包含MySQL dump特征
            has_mysql_dump = any(
                'MySQL dump' in line or 
                'mysqldump' in line or 
                '-- Host:' in line or
                'CREATE DATABASE' in line or
                'USE ' in line
                for line in first_lines
            )
            
            if not has_mysql_dump:
                return False, "文件格式不正确，可能不是有效的MySQL备份文件"
        
        # 清理临时文件
        if temp_sql_file and os.path.exists(temp_sql_file):
            try:
                os.remove(temp_sql_file)
                os.rmdir(os.path.dirname(temp_sql_file))
            except:
                pass
        
        return True, "备份文件验证通过"
        
    except Exception as e:
        logger.error(f"验证备份文件失败: {e}")
        return False, f"验证失败: {str(e)}"
