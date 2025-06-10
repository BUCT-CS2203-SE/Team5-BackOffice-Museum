#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
备份系统测试脚本
测试增强版备份功能的各项特性
"""

import sys
import os
from pathlib import Path

# 添加src目录到Python路径
src_dir = Path(__file__).parent
sys.path.insert(0, str(src_dir))

from common.utilities import backup_utils_enhanced as backup_utils
from common.utilities.backup_scheduler import get_backup_scheduler

def test_backup_functions():
    """测试备份系统的各项功能"""
    print("=" * 60)
    print("🔧 备份系统功能测试开始")
    print("=" * 60)
    
    # 1. 测试备份目录创建
    print("\n1️⃣ 测试备份目录创建...")
    try:
        backup_utils.ensure_backup_dir_exists()
        print("✅ 备份目录创建成功")
    except Exception as e:
        print(f"❌ 备份目录创建失败: {e}")
        return False
      # 2. 测试备份文件列表
    print("\n2️⃣ 测试备份文件列表...")
    try:
        files, msg = backup_utils.list_backup_files()
        print(f"✅ 获取备份文件列表成功: {len(files)} 个文件")
        print(f"   消息: {msg}")
        if files:
            print("   现有备份文件:")
            for i, f_info in enumerate(files[:3]):  # 只显示前3个
                print(f"   [{i+1}] {f_info['filename']} ({format_file_size(f_info['size'])})")
                
    except Exception as e:
        print(f"❌ 获取备份文件列表失败: {e}")
    
    # 3. 测试手动备份
    print("\n3️⃣ 测试手动备份功能...")
    try:
        print("   开始执行备份...")
        backup_path, backup_msg = backup_utils.perform_backup(
            custom_suffix="test", 
            compress=True, 
            backup_type="test"
        )
        
        if backup_path:
            print(f"✅ 备份创建成功: {os.path.basename(backup_path)}")
            print(f"   路径: {backup_path}")
            print(f"   消息: {backup_msg}")
            
            # 4. 测试备份文件验证
            print("\n4️⃣ 测试备份文件验证...")
            filename = os.path.basename(backup_path)
            is_valid, valid_msg = backup_utils.validate_backup_file(filename)
            print(f"   验证结果: {'✅ 通过' if is_valid else '❌ 失败'}")
            print(f"   验证消息: {valid_msg}")
            
            # 5. 测试备份内容预览
            print("\n5️⃣ 测试备份内容预览...")
            try:
                preview_content, preview_msg = backup_utils.get_backup_content_preview(filename, max_lines=5)
                if preview_content:
                    print("✅ 备份内容预览成功")
                    print("   预览内容 (前5行):")
                    lines = preview_content.split('\n')[:5]
                    for line in lines:
                        print(f"   {line[:80]}...")  # 只显示前80个字符
                else:
                    print(f"❌ 备份内容预览失败: {preview_msg}")
            except Exception as e:
                print(f"❌ 备份内容预览异常: {e}")
            
            # 6. 测试下载路径获取
            print("\n6️⃣ 测试下载路径获取...")
            try:
                download_path = backup_utils.get_backup_file_path(filename)
                if download_path and os.path.exists(download_path):
                    print(f"✅ 下载路径获取成功: {download_path}")
                else:
                    print("❌ 下载路径获取失败: 文件不存在")
            except Exception as e:
                print(f"❌ 下载路径获取异常: {e}")
                
        else:
            print(f"❌ 备份创建失败: {backup_msg}")
            
    except Exception as e:
        print(f"❌ 备份功能测试异常: {e}")
        import traceback
        traceback.print_exc()
    
    # 7. 测试备份调度器
    print("\n7️⃣ 测试备份调度器...")
    try:
        scheduler = get_backup_scheduler()
        status = scheduler.get_status()
        jobs = scheduler.get_jobs()
        
        print(f"   调度器状态: {'运行中' if status['is_running'] else '已停止'}")
        print(f"   任务总数: {status['job_count']}")
        print(f"   启用任务: {status['enabled_jobs']}")
        print(f"   配置的任务: {list(jobs.keys())}")
        
        print("✅ 备份调度器测试成功")
        
    except Exception as e:
        print(f"❌ 备份调度器测试失败: {e}")
    
    print("\n" + "=" * 60)
    print("🎉 备份系统功能测试完成")
    print("=" * 60)
    
    return True

def format_file_size(size_bytes):
    """格式化文件大小"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"

def show_backup_info():
    """显示备份系统信息"""
    print("🏛️ 海外文物后台管理系统 - 备份系统增强版")
    print("=" * 60)
    print("✨ 新增功能:")
    print("   🔹 一键备份数据库")
    print("   🔹 备份内容预览 (前50-100行)")
    print("   🔹 备份文件下载")
    print("   🔹 备份文件压缩支持")
    print("   🔹 备份元数据管理")
    print("   🔹 备份完整性验证")
    print("   🔹 自动清理旧备份")
    print("   🔹 独立的定时备份调度器")
    print("   🔹 支持手动、定时、恢复前备份类型")
    print("   🔹 线程安全的备份操作")
    print("=" * 60)

if __name__ == '__main__':
    show_backup_info()
    
    # 检查命令行参数
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == 'test':
            test_backup_functions()
        elif command == 'info':
            show_backup_info()
        else:
            print(f"未知命令: {command}")
            print("可用命令: test, info")
    else:
        print("\n默认运行备份系统测试...")
        print("可使用参数: test, info")
        print()
        test_backup_functions()
