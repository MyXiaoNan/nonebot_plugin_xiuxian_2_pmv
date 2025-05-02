"""
PostgreSQL数据库自动备份模块
每30分钟自动备份一次数据库
"""
import asyncio
import os
import subprocess
import time
import logging
import datetime
import tarfile
import shutil
from pathlib import Path
import asyncpg
from functools import partial

# 初始化日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("xiuxian_backup.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("xiuxian_backup")

# 全局连接池引用
_POOL = None

def set_pool(pool):
    """设置全局连接池引用"""
    global _POOL
    _POOL = pool

# 备份配置
BACKUP_CONFIG = {
    "backup_dir": os.path.expanduser("~/zhenxun_bot/data/xiuxian/backups"),
    "pg_dump_path": "pg_dump",  # 可能需要指定完整路径，如 "/usr/bin/pg_dump"
    "database_name": "xiuxian",
    "pg_url": None,  # 将在运行时设置
    "keep_backups": 48,  # 保留48个备份（24小时）
    "backup_interval": 30 * 60,  # 30分钟
    "compress_backups": True
}

def set_pg_url(url):
    """设置PostgreSQL连接URL"""
    BACKUP_CONFIG["pg_url"] = url

def ensure_backup_dir():
    """确保备份目录存在"""
    backup_dir = Path(BACKUP_CONFIG["backup_dir"])
    backup_dir.mkdir(parents=True, exist_ok=True)
    return backup_dir

def get_backup_filename():
    """生成备份文件名"""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"xiuxian_backup_{timestamp}.sql"

def compress_backup(file_path):
    """压缩备份文件"""
    if not BACKUP_CONFIG["compress_backups"]:
        return file_path
        
    tar_path = f"{file_path}.tar.gz"
    with tarfile.open(tar_path, "w:gz") as tar:
        tar.add(file_path, arcname=os.path.basename(file_path))
    
    # 删除原始SQL文件
    os.remove(file_path)
    return tar_path

def cleanup_old_backups():
    """清理旧备份"""
    backup_dir = Path(BACKUP_CONFIG["backup_dir"])
    backups = sorted([
        f for f in backup_dir.glob("xiuxian_backup_*.sql*")
    ], key=lambda x: os.path.getmtime(x))
    
    # 保留最近的N个备份
    if len(backups) > BACKUP_CONFIG["keep_backups"]:
        for old_backup in backups[:-BACKUP_CONFIG["keep_backups"]]:
            try:
                os.remove(old_backup)
                logger.info(f"已删除旧备份: {old_backup}")
            except Exception as e:
                logger.error(f"删除旧备份时出错: {e}")

async def create_backup():
    """创建数据库备份"""
    try:
        backup_dir = ensure_backup_dir()
        backup_filename = get_backup_filename()
        backup_path = os.path.join(backup_dir, backup_filename)
        
        # 构建pg_dump命令
        pg_url = BACKUP_CONFIG["pg_url"]
        if not pg_url:
            logger.error("未设置PostgreSQL连接URL")
            return None
        
        # 执行pg_dump
        cmd = [
            BACKUP_CONFIG["pg_dump_path"],
            "-d", pg_url,
            "-f", backup_path,
            "--format=plain",
            "--no-owner",
            "--no-acl"
        ]
        
        # 执行命令
        process = subprocess.Popen(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE
        )
        stdout, stderr = process.communicate()
        
        if process.returncode != 0:
            logger.error(f"备份创建失败: {stderr.decode()}")
            return None
        
        # 压缩备份
        final_path = compress_backup(backup_path)
        
        # 清理旧备份
        cleanup_old_backups()
        
        logger.info(f"备份成功创建: {final_path}")
        return final_path
    
    except Exception as e:
        logger.error(f"备份过程中出错: {e}")
        return None

async def automatic_backup_task():
    """自动备份任务"""
    while True:
        try:
            logger.info("开始计划备份...")
            await create_backup()
            
            # 检查/更新数据库结构
            await check_db_structure()
            
            # 等待下一次备份
            logger.info(f"备份完成，等待 {BACKUP_CONFIG['backup_interval'] // 60} 分钟后再次备份")
            await asyncio.sleep(BACKUP_CONFIG["backup_interval"])
        
        except Exception as e:
            logger.error(f"自动备份任务出错: {e}")
            # 出错后等待一小段时间再重试
            await asyncio.sleep(60)

async def check_db_structure():
    """检查并维护数据库结构"""
    if _POOL is None:
        logger.warning("连接池未初始化，无法检查数据库结构")
        return
    
    try:
        async with _POOL.acquire() as conn:
            # 检查索引碎片
            await conn.execute("VACUUM ANALYZE xiuxian_user;")
            await conn.execute("VACUUM ANALYZE xiuxian_back;")
            await conn.execute("VACUUM ANALYZE xiuxian_time;")
            logger.info("数据库维护完成：已整理碎片")
    except Exception as e:
        logger.error(f"数据库维护时出错: {e}")

async def restore_backup(backup_path):
    """恢复指定的备份"""
    try:
        if not os.path.exists(backup_path):
            logger.error(f"备份文件不存在: {backup_path}")
            return False
        
        # 临时解压缩
        if backup_path.endswith('.tar.gz'):
            temp_dir = os.path.join(BACKUP_CONFIG["backup_dir"], "temp_restore")
            os.makedirs(temp_dir, exist_ok=True)
            
            with tarfile.open(backup_path, 'r:gz') as tar:
                tar.extractall(path=temp_dir)
            
            # 找到解压后的SQL文件
            sql_files = list(Path(temp_dir).glob("*.sql"))
            if not sql_files:
                logger.error(f"备份文件中没有找到SQL文件")
                shutil.rmtree(temp_dir)
                return False
                
            backup_sql = str(sql_files[0])
        else:
            backup_sql = backup_path
        
        # 构建psql恢复命令
        pg_url = BACKUP_CONFIG["pg_url"]
        cmd = [
            "psql",  # 可能需要完整路径
            "-d", pg_url,
            "-f", backup_sql
        ]
        
        # 执行恢复
        process = subprocess.Popen(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE
        )
        stdout, stderr = process.communicate()
        
        # 清理临时文件
        if backup_path.endswith('.tar.gz'):
            shutil.rmtree(temp_dir)
        
        if process.returncode != 0:
            logger.error(f"恢复失败: {stderr.decode()}")
            return False
            
        logger.info(f"成功从备份恢复: {backup_path}")
        return True
        
    except Exception as e:
        logger.error(f"恢复备份时出错: {e}")
        return False

def list_available_backups():
    """列出所有可用的备份"""
    backup_dir = Path(BACKUP_CONFIG["backup_dir"])
    backups = []
    
    if not backup_dir.exists():
        return backups
    
    # 查找所有备份文件
    for ext in ["sql", "sql.tar.gz"]:
        backups.extend(backup_dir.glob(f"xiuxian_backup_*.{ext}"))
    
    # 按时间排序（最新的优先）
    backups.sort(key=lambda x: os.path.getmtime(x), reverse=True)
    
    # 返回文件名和大小
    result = []
    for backup in backups:
        size_mb = os.path.getsize(backup) / (1024 * 1024)
        time_created = datetime.datetime.fromtimestamp(
            os.path.getmtime(backup)
        ).strftime("%Y-%m-%d %H:%M:%S")
        
        result.append({
            "path": str(backup),
            "filename": backup.name,
            "size_mb": round(size_mb, 2),
            "created_at": time_created
        })
    
    return result

async def start_backup_service():
    """启动备份服务"""
    # 确保目录存在
    ensure_backup_dir()
    
    # 创建初始备份
    await create_backup()
    
    # 启动自动备份任务
    asyncio.create_task(automatic_backup_task())
    
    logger.info("备份服务已启动")

# 用于命令行测试的入口点
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="修仙数据库备份工具")
    parser.add_argument("--backup", action="store_true", help="创建备份")
    parser.add_argument("--list", action="store_true", help="列出所有备份")
    parser.add_argument("--restore", type=str, help="恢复指定备份")
    parser.add_argument("--start-service", action="store_true", help="启动备份服务")
    parser.add_argument("--pg-url", type=str, help="PostgreSQL连接URL")
    args = parser.parse_args()
    
    # 设置PostgreSQL URL
    if args.pg_url:
        set_pg_url(args.pg_url)
    
    # 执行请求的操作
    if args.backup:
        asyncio.run(create_backup())
    elif args.list:
        backups = list_available_backups()
        for b in backups:
            print(f"{b['filename']} ({b['size_mb']}MB) - {b['created_at']}")
    elif args.restore:
        asyncio.run(restore_backup(args.restore))
    elif args.start_service:
        asyncio.run(start_backup_service()) 