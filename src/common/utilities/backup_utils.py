import os
import shutil # shutil is no longer used for core backup/restore but might be for pre-restore backups if implemented
import datetime
import glob
import subprocess # For running mysqldump and mysql
from common.utilities.util_logger import Log

logger = Log.get_logger(__name__)

# MySQL Connection Details from your prompt
DB_HOST = '101.43.234.152'
DB_PORT = 3306
DB_USER = 'SE2025'
DB_PASSWORD = 'Cs22032025' # WARNING: Hardcoding passwords is a security risk!
DB_NAME = 'se2025'

# Backup Configuration
BACKUP_DIR = r'c:\Users\WPP_JKW\Team5-BackOffice-Museum\src\db_backups'
BACKUP_FILE_PREFIX = f'backup_{DB_NAME}_' # Using DB_NAME in prefix
BACKUP_FILE_SUFFIX = '.sql' # MySQL dumps are typically .sql files

def ensure_backup_dir_exists():
    """确保备份目录存在"""
    if not os.path.exists(BACKUP_DIR):
        try:
            os.makedirs(BACKUP_DIR)
            logger.info(f"备份目录 {BACKUP_DIR} 已创建。")
        except OSError as e:
            logger.error(f"创建备份目录 {BACKUP_DIR} 失败: {e}")
            raise # Re-raise the exception to be handled by the caller

def perform_backup(custom_suffix: str = None):
    """
    执行 MySQL 数据库备份。
    备份文件名格式: backup_{DB_NAME}_YYYYMMDD_HHMMSS[_custom_suffix].sql
    """
    ensure_backup_dir_exists()
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file_name = f"{BACKUP_FILE_PREFIX}{timestamp}"
    if custom_suffix:
        backup_file_name += f"_{custom_suffix}"
    backup_file_name += BACKUP_FILE_SUFFIX
    backup_file_path = os.path.join(BACKUP_DIR, backup_file_name)

    # Construct mysqldump command
    # Note: -p immediately followed by password, no space.
    cmd = [
        'mysqldump',
        f'--host={DB_HOST}',
        f'--port={str(DB_PORT)}', # Ensure port is a string
        f'--user={DB_USER}',
        f'--password={DB_PASSWORD}', # Security risk warning applies
        '--single-transaction',    # Recommended for InnoDB tables to ensure consistency
        '--routines',              # Include stored procedures and functions
        '--triggers',              # Include triggers
        '--events',                # Include events
        DB_NAME
    ]

    try:
        with open(backup_file_path, 'w', encoding='utf-8') as f_out: # Specify encoding for SQL dump
            process = subprocess.Popen(cmd, stdout=f_out, stderr=subprocess.PIPE, text=True, encoding='utf-8')
            _, stderr = process.communicate() # stdout is redirected to f_out

        if process.returncode == 0:
            logger.info(f"MySQL 数据库 '{DB_NAME}' 已成功备份到 {backup_file_path}")
            return backup_file_path, "备份成功"
        else:
            error_message = f"MySQL 备份失败。返回码: {process.returncode}。错误: {stderr.strip() if stderr else 'Unknown error'}"
            logger.error(error_message)
            if os.path.exists(backup_file_path): # Clean up failed/empty backup file
                try:
                    if os.path.getsize(backup_file_path) == 0:
                        os.remove(backup_file_path)
                except OSError:
                    pass # Ignore error during cleanup
            return None, f"备份失败: {stderr.strip() if stderr else 'mysqldump 执行错误'}"

    except FileNotFoundError:
        logger.error("mysqldump 命令未找到。请确保 MySQL 客户端已安装并在系统 PATH 中。")
        return None, "备份失败: mysqldump 命令未找到。"
    except Exception as e:
        logger.error(f"MySQL 备份过程中发生意外错误: {e}")
        if os.path.exists(backup_file_path): # Clean up potentially corrupted backup file
            try:
                os.remove(backup_file_path)
            except OSError:
                pass
        return None, f"备份失败: {str(e)}"

def list_backup_files():
    """列出所有备份文件及其信息 (与之前基本相同, 只是文件后缀可能变化)"""
    ensure_backup_dir_exists()
    backup_files_info = []
    try:
        pattern = os.path.join(BACKUP_DIR, f"{BACKUP_FILE_PREFIX}*{BACKUP_FILE_SUFFIX}")
        for file_path in glob.glob(pattern):
            if os.path.isfile(file_path):
                try:
                    stat = os.stat(file_path)
                    backup_files_info.append({
                        'filename': os.path.basename(file_path),
                        'size': stat.st_size,
                        'created_at': datetime.datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                        'full_path': file_path
                    })
                except Exception as e:
                    logger.warning(f"获取文件信息失败 {file_path}: {e}")
        backup_files_info.sort(key=lambda x: x['created_at'], reverse=True)
        return backup_files_info, "获取成功"
    except Exception as e:
        logger.error(f"列出备份文件失败: {e}")
        return [], f"列出备份文件失败: {str(e)}"

def perform_restore(backup_filename: str):
    """
    从指定的备份文件恢复 MySQL 数据库。
    警告：这是一个潜在的破坏性操作！它将用备份文件的内容覆盖当前数据库。
    """
    ensure_backup_dir_exists()
    backup_file_path = os.path.join(BACKUP_DIR, backup_filename)

    if not os.path.exists(backup_file_path):
        logger.error(f"备份文件 {backup_file_path} 不存在。")
        return False, "备份文件不存在"
    
    if os.path.getsize(backup_file_path) == 0:
        logger.error(f"备份文件 {backup_file_path} 为空，无法恢复。")
        return False, "备份文件为空"

    # Construct mysql command
    cmd = [
        'mysql',
        f'--host={DB_HOST}',
        f'--port={str(DB_PORT)}',
        f'--user={DB_USER}',
        f'--password={DB_PASSWORD}', # Security risk warning applies
        DB_NAME
    ]

    try:
        logger.warning(f"准备从 '{backup_file_path}' 恢复数据库 '{DB_NAME}'。这是一个高风险操作，将覆盖现有数据。")
        # 实际生产中，强烈建议在恢复前对当前数据库进行一次备份。
        # e.g., perform_backup(custom_suffix=f"prerestore_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}")

        with open(backup_file_path, 'r', encoding='utf-8') as f_in: # Specify encoding
            process = subprocess.Popen(cmd, stdin=f_in, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8')
            _, stderr = process.communicate() # stdout is usually empty for mysql client on success unless -v is used

        if process.returncode == 0:
            logger.info(f"MySQL 数据库 '{DB_NAME}' 已成功从 {backup_file_path} 恢复。")
            return True, "恢复成功。请检查数据以确保完整性。"
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

def delete_backup_file(backup_filename: str):
    """删除指定的备份文件 (与之前相同)"""
    ensure_backup_dir_exists()
    backup_file_path = os.path.join(BACKUP_DIR, backup_filename)
    try:
        if not os.path.exists(backup_file_path):
            logger.warning(f"尝试删除的备份文件 {backup_file_path} 不存在。")
            return False, "文件不存在"
        
        os.remove(backup_file_path)
        logger.info(f"备份文件 {backup_file_path} 已成功删除。")
        return True, "删除成功"
    except Exception as e:
        logger.error(f"删除备份文件 {backup_file_path} 失败: {e}")
        return False, f"删除失败: {str(e)}"

if __name__ == '__main__':
    # 测试代码 (需要配置好MySQL连接和客户端工具)
    # print("确保备份目录存在...")
    # ensure_backup_dir_exists()
    
    # print("尝试备份...")
    # backup_path, msg = perform_backup("manual_mysql_test")
    # print(f"备份结果: {msg},路径: {backup_path}")

    # print("列出备份文件...")
    # files, msg_list = list_backup_files()
    # print(f"列出结果: {msg_list}")
    # for f_info in files:
    #     print(f"  - {f_info['filename']} (大小: {f_info['size']} bytes, 创建于: {f_info['created_at']})")

    # if files:
    #     test_restore_filename = files[0]['filename']
    #     print(f"尝试从 {test_restore_filename} 恢复 (这是一个高风险操作，请谨慎测试)...")
    #     # 注意：恢复测试会覆盖现有数据库！
    #     # proceed_restore = input(f"确定要从 {test_restore_filename} 恢复数据库 {DB_NAME} 吗? (yes/no): ")
    #     # if proceed_restore.lower() == 'yes':
    #     #     success_restore, msg_restore = perform_restore(test_restore_filename)
    #     #     print(f"恢复结果: {msg_restore}, 状态: {success_restore}")
    #     # else:
    #     #     print("恢复操作已取消。")

        # print(f"尝试删除备份文件 {test_restore_filename}...")
        # success_delete, msg_delete = delete_backup_file(test_restore_filename)
        # print(f"删除结果: {msg_delete}, 状态: {success_delete}")
        
        # print("再次列出备份文件...")
        # files_after_delete, msg_list_after_delete = list_backup_files()
        # print(f"列出结果: {msg_list_after_delete}")
        # for f_info_ad in files_after_delete:
        #     print(f"  - {f_info_ad['filename']}")
    pass