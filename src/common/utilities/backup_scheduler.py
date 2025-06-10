"""
独立的数据库备份调度器
不依赖框架的任务调度系统，实现独立的定时备份功能
"""

import threading
import time
import schedule
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from common.utilities.util_logger import Log
from common.utilities import backup_utils_enhanced as backup_utils

logger = Log.get_logger(__name__)

class BackupScheduler:
    """独立的备份调度器"""
    
    def __init__(self):
        self.is_running = False
        self.scheduler_thread = None
        self.jobs = {}  # 存储定时任务
        self.config_file = os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'backup_schedule.json')
        self.load_schedule_config()
        
    def load_schedule_config(self):
        """加载调度配置"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.jobs = config.get('jobs', {})
                    logger.info(f"加载了 {len(self.jobs)} 个备份任务配置")
            else:
                # 创建默认配置
                self.create_default_config()
        except Exception as e:
            logger.error(f"加载备份调度配置失败: {e}")
            self.create_default_config()
    
    def create_default_config(self):
        """创建默认的备份调度配置"""
        default_config = {
            "jobs": {
                "daily_backup": {
                    "name": "每日自动备份",
                    "enabled": True,
                    "schedule_type": "daily",
                    "time": "02:00",
                    "compress": True,
                    "keep_count": 7,
                    "description": "每日凌晨2点执行自动备份，保留7天"
                },
                "weekly_backup": {
                    "name": "每周备份",
                    "enabled": False,
                    "schedule_type": "weekly",
                    "day": "sunday",
                    "time": "03:00",
                    "compress": True,
                    "keep_count": 4,
                    "description": "每周日凌晨3点执行备份，保留4周"
                }
            },
            "global_settings": {
                "max_concurrent_backups": 1,
                "backup_timeout_minutes": 30,
                "auto_cleanup": True
            }
        }
        
        self.jobs = default_config["jobs"]
        self.save_schedule_config(default_config)
    
    def save_schedule_config(self, config=None):
        """保存调度配置"""
        try:
            if config is None:
                config = {
                    "jobs": self.jobs,
                    "global_settings": {
                        "max_concurrent_backups": 1,
                        "backup_timeout_minutes": 30,
                        "auto_cleanup": True
                    }
                }
            
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            logger.info("备份调度配置已保存")
        except Exception as e:
            logger.error(f"保存备份调度配置失败: {e}")
    
    def add_job(self, job_id: str, job_config: Dict):
        """添加备份任务"""
        try:
            self.jobs[job_id] = job_config
            self.save_schedule_config()
            
            if self.is_running:
                self._schedule_job(job_id, job_config)
            
            logger.info(f"备份任务已添加: {job_id}")
            return True, "任务添加成功"
        except Exception as e:
            logger.error(f"添加备份任务失败: {e}")
            return False, f"添加失败: {str(e)}"
    
    def remove_job(self, job_id: str):
        """删除备份任务"""
        try:
            if job_id in self.jobs:
                del self.jobs[job_id]
                self.save_schedule_config()
                
                # 从schedule中移除
                schedule.clear(job_id)
                
                logger.info(f"备份任务已删除: {job_id}")
                return True, "任务删除成功"
            else:
                return False, "任务不存在"
        except Exception as e:
            logger.error(f"删除备份任务失败: {e}")
            return False, f"删除失败: {str(e)}"
    
    def update_job(self, job_id: str, job_config: Dict):
        """更新备份任务"""
        try:
            if job_id in self.jobs:
                self.jobs[job_id] = job_config
                self.save_schedule_config()
                
                # 重新调度任务
                schedule.clear(job_id)
                if self.is_running and job_config.get('enabled', True):
                    self._schedule_job(job_id, job_config)
                
                logger.info(f"备份任务已更新: {job_id}")
                return True, "任务更新成功"
            else:
                return False, "任务不存在"
        except Exception as e:
            logger.error(f"更新备份任务失败: {e}")
            return False, f"更新失败: {str(e)}"
    
    def _schedule_job(self, job_id: str, job_config: Dict):
        """调度单个任务"""
        if not job_config.get('enabled', True):
            return
        
        schedule_type = job_config.get('schedule_type', 'daily')
        time_str = job_config.get('time', '02:00')
        
        job_func = lambda: self._execute_backup(job_id, job_config)
        
        if schedule_type == 'daily':
            schedule.every().day.at(time_str).do(job_func).tag(job_id)
        elif schedule_type == 'weekly':
            day = job_config.get('day', 'monday').lower()
            getattr(schedule.every(), day).at(time_str).do(job_func).tag(job_id)
        elif schedule_type == 'interval':
            hours = job_config.get('interval_hours', 24)
            schedule.every(hours).hours.do(job_func).tag(job_id)
        
        logger.info(f"任务 {job_id} 已调度: {schedule_type} at {time_str}")
    
    def _execute_backup(self, job_id: str, job_config: Dict):
        """执行备份任务"""
        try:
            logger.info(f"开始执行定时备份任务: {job_id}")
            
            # 执行备份
            compress = job_config.get('compress', True)
            backup_path, backup_msg = backup_utils.perform_backup(
                custom_suffix=f"scheduled_{job_id}",
                compress=compress,
                backup_type="scheduled"
            )
            
            if backup_path:
                logger.info(f"定时备份任务 {job_id} 执行成功: {backup_msg}")
                
                # 自动清理旧备份
                keep_count = job_config.get('keep_count', 7)
                if keep_count > 0:
                    cleanup_success, cleanup_msg = backup_utils.cleanup_old_backups(keep_count)
                    if cleanup_success:
                        logger.info(f"旧备份清理完成: {cleanup_msg}")
                    else:
                        logger.warning(f"旧备份清理失败: {cleanup_msg}")
            else:
                logger.error(f"定时备份任务 {job_id} 执行失败: {backup_msg}")
                
        except Exception as e:
            logger.error(f"执行定时备份任务 {job_id} 时出错: {e}")
    
    def start(self):
        """启动备份调度器"""
        if self.is_running:
            return True, "调度器已在运行"
        
        try:
            # 清除所有现有任务
            schedule.clear()
            
            # 调度所有启用的任务
            for job_id, job_config in self.jobs.items():
                if job_config.get('enabled', True):
                    self._schedule_job(job_id, job_config)
            
            # 启动调度器线程
            self.is_running = True
            self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
            self.scheduler_thread.start()
            
            logger.info("备份调度器已启动")
            return True, "调度器启动成功"
        except Exception as e:
            logger.error(f"启动备份调度器失败: {e}")
            return False, f"启动失败: {str(e)}"
    
    def stop(self):
        """停止备份调度器"""
        if not self.is_running:
            return True, "调度器未运行"
        
        try:
            self.is_running = False
            schedule.clear()
            
            if self.scheduler_thread and self.scheduler_thread.is_alive():
                self.scheduler_thread.join(timeout=5)
            
            logger.info("备份调度器已停止")
            return True, "调度器停止成功"
        except Exception as e:
            logger.error(f"停止备份调度器失败: {e}")
            return False, f"停止失败: {str(e)}"
    
    def _run_scheduler(self):
        """调度器主循环"""
        logger.info("备份调度器主循环开始")
        
        while self.is_running:
            try:
                schedule.run_pending()
                time.sleep(60)  # 每分钟检查一次
            except Exception as e:
                logger.error(f"调度器主循环出错: {e}")
                time.sleep(60)
        
        logger.info("备份调度器主循环结束")
    
    def get_status(self):
        """获取调度器状态"""
        return {
            'is_running': self.is_running,
            'job_count': len(self.jobs),
            'enabled_jobs': len([j for j in self.jobs.values() if j.get('enabled', True)]),
            'next_runs': self._get_next_runs()
        }
    
    def _get_next_runs(self):
        """获取下次运行时间"""
        if not self.is_running:
            return {}
        
        next_runs = {}
        for job in schedule.jobs:
            if hasattr(job, 'tags') and job.tags:
                job_id = list(job.tags)[0]
                next_runs[job_id] = job.next_run.strftime('%Y-%m-%d %H:%M:%S') if job.next_run else None
        
        return next_runs
    
    def get_jobs(self):
        """获取所有任务配置"""
        return self.jobs.copy()

# 全局调度器实例
_scheduler_instance = None

def get_backup_scheduler():
    """获取备份调度器单例"""
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = BackupScheduler()
    return _scheduler_instance

def start_backup_scheduler():
    """启动备份调度器"""
    scheduler = get_backup_scheduler()
    return scheduler.start()

def stop_backup_scheduler():
    """停止备份调度器"""
    scheduler = get_backup_scheduler()
    return scheduler.stop()

if __name__ == '__main__':
    # 测试代码
    scheduler = BackupScheduler()
    print("测试备份调度器...")
    
    # 添加测试任务
    test_job = {
        "name": "测试备份",
        "enabled": True,
        "schedule_type": "interval",
        "interval_hours": 1,
        "compress": True,
        "keep_count": 3,
        "description": "每小时执行一次测试备份"
    }
    
    scheduler.add_job("test_backup", test_job)
    
    # 启动调度器
    success, msg = scheduler.start()
    print(f"启动结果: {success}, {msg}")
    
    # 显示状态
    status = scheduler.get_status()
    print(f"调度器状态: {status}")
    
    # 运行一段时间后停止
    try:
        time.sleep(10)
    except KeyboardInterrupt:
        pass
    
    success, msg = scheduler.stop()
    print(f"停止结果: {success}, {msg}")
