#!/usr/bin/env python3
"""
独立的备份调度器启动脚本
可以独立于主应用运行，专门负责定时备份任务
"""

import sys
import os
import signal
import time
from pathlib import Path

# 添加src目录到Python路径
src_dir = Path(__file__).parent
sys.path.insert(0, str(src_dir))

from common.utilities.backup_scheduler import BackupScheduler
from common.utilities.util_logger import Log

logger = Log.get_logger(__name__)

class BackupSchedulerService:
    """备份调度器服务"""
    
    def __init__(self):
        self.scheduler = BackupScheduler()
        self.running = False
        
    def start(self):
        """启动服务"""
        logger.info("正在启动备份调度器服务...")
        
        try:
            success, msg = self.scheduler.start()
            if success:
                self.running = True
                logger.info(f"备份调度器服务启动成功: {msg}")
                
                # 显示状态信息
                status = self.scheduler.get_status()
                logger.info(f"当前状态: {status}")
                
                # 显示任务列表
                jobs = self.scheduler.get_jobs()
                logger.info(f"已配置的任务:")
                for job_id, job_config in jobs.items():
                    enabled = "启用" if job_config.get('enabled', True) else "禁用"
                    logger.info(f"  - {job_id}: {job_config.get('name', '未命名')} ({enabled})")
                
                return True
            else:
                logger.error(f"备份调度器服务启动失败: {msg}")
                return False
                
        except Exception as e:
            logger.error(f"启动备份调度器服务时出错: {e}")
            return False
    
    def stop(self):
        """停止服务"""
        logger.info("正在停止备份调度器服务...")
        
        try:
            success, msg = self.scheduler.stop()
            if success:
                self.running = False
                logger.info(f"备份调度器服务已停止: {msg}")
            else:
                logger.warning(f"停止备份调度器服务时出现问题: {msg}")
                
        except Exception as e:
            logger.error(f"停止备份调度器服务时出错: {e}")
    
    def run(self):
        """运行服务主循环"""
        if not self.start():
            return 1
        
        def signal_handler(signum, frame):
            logger.info(f"收到信号 {signum}，正在关闭服务...")
            self.stop()
            sys.exit(0)
        
        # 注册信号处理器
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        try:
            logger.info("备份调度器服务正在运行，按 Ctrl+C 停止...")
            
            while self.running:
                time.sleep(1)
                
                # 每分钟输出一次状态（可选）
                if int(time.time()) % 3600 == 0:  # 每小时输出一次
                    status = self.scheduler.get_status()
                    next_runs = status.get('next_runs', {})
                    if next_runs:
                        logger.info(f"下次备份时间: {next_runs}")
                        
        except KeyboardInterrupt:
            logger.info("收到中断信号，正在停止服务...")
        finally:
            self.stop()
        
        return 0

def main():
    """主函数"""
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == 'start':
            service = BackupSchedulerService()
            return service.run()
        
        elif command == 'status':
            try:
                scheduler = BackupScheduler()
                status = scheduler.get_status()
                jobs = scheduler.get_jobs()
                
                print("=== 备份调度器状态 ===")
                print(f"运行状态: {'运行中' if status['is_running'] else '已停止'}")
                print(f"任务总数: {status['job_count']}")
                print(f"启用任务: {status['enabled_jobs']}")
                
                print("\n=== 任务列表 ===")
                for job_id, job_config in jobs.items():
                    enabled = "启用" if job_config.get('enabled', True) else "禁用"
                    schedule_type = job_config.get('schedule_type', 'unknown')
                    time_info = job_config.get('time', 'N/A')
                    
                    if schedule_type == 'weekly':
                        day = job_config.get('day', 'N/A')
                        time_info = f"{day} {time_info}"
                    
                    print(f"  {job_id}: {job_config.get('name', '未命名')}")
                    print(f"    状态: {enabled}")
                    print(f"    类型: {schedule_type}")
                    print(f"    时间: {time_info}")
                    print(f"    保留: {job_config.get('keep_count', 'N/A')} 个备份")
                    print()
                
                if status['is_running']:
                    next_runs = status.get('next_runs', {})
                    if next_runs:
                        print("=== 下次执行时间 ===")
                        for job_id, next_time in next_runs.items():
                            print(f"  {job_id}: {next_time or '未知'}")                
                return 0
                
            except Exception as e:
                print(f"获取状态失败: {e}")
                return 1
        
        elif command == 'test':
            # 测试备份功能
            try:
                from common.utilities import backup_utils_enhanced as backup_utils
                print("正在执行测试备份...")
                
                path, msg = backup_utils.perform_backup("test", compress=True, backup_type="test")
                if path:
                    print(f"测试备份成功: {path}")
                    print(f"消息: {msg}")
                    
                    # 验证备份文件
                    filename = os.path.basename(path)
                    valid, valid_msg = backup_utils.validate_backup_file(filename)
                    print(f"备份验证: {'通过' if valid else '失败'} - {valid_msg}")
                    
                else:
                    print(f"测试备份失败: {msg}")
                    return 1
                
                return 0
                
            except Exception as e:
                print(f"测试备份时出错: {e}")
                return 1
        
        else:
            print(f"未知命令: {command}")
            print_usage()
            return 1
    
    else:
        print_usage()
        return 1

def print_usage():
    """打印使用说明"""
    print("备份调度器服务控制脚本")
    print()
    print("用法:")
    print("  python app_backup_scheduler.py start   - 启动备份调度器服务")
    print("  python app_backup_scheduler.py status  - 查看服务状态")
    print("  python app_backup_scheduler.py test    - 执行测试备份")
    print()
    print("启动后，服务将在后台运行定时备份任务。")
    print("使用 Ctrl+C 或发送 SIGTERM 信号来停止服务。")

if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
