"""
PostgreSQL数据库自动备份模块
每分钟自动备份一次数据库
"""
import asyncio
import os
import subprocess
import logging
import datetime
import tarfile
import shutil
from pathlib import Path
from ..xiuxian_config import XiuConfig

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
BOT_PATH = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
BOT_PATH = os.path.dirname(BOT_PATH)
READPATH = Path(BOT_PATH) / "data" / "xiuxian"
BACKUPPATH = READPATH / "备份"

# 获取数据路径
try:
    # 确保备份路径存在
    if not os.path.exists(BACKUPPATH):
        os.makedirs(BACKUPPATH, exist_ok=True)
    logger.info(f"备份路径设置为: {BACKUPPATH}")
except Exception as e:
    logger.error(f"设置备份路径时出错: {e}")
    # 回退到默认路径
    if not os.path.exists(READPATH / "备份"):
        os.makedirs(READPATH / "备份", exist_ok=True)
    logger.info(f"回退备份路径设置为: {READPATH / '备份'}")

# 全局连接池引用
_POOL = None
# 备份服务状态
_BACKUP_SERVICE_RUNNING = False
# 备份任务
_BACKUP_TASK = None

def set_pool(pool):
    """设置全局连接池引用"""
    global _POOL
    _POOL = pool

# 备份配置
BACKUP_CONFIG = {
    "backup_dir": BACKUPPATH,  # 使用正确的备份路径
    "pg_dump_path": "pg_dump",  # 可能需要指定完整路径，如 "/usr/bin/pg_dump"
    "database_name": "xiuxian",
    "pg_url": None,  # 将在运行时设置
    "keep_backups": XiuConfig().backup_quantity,  # 保留60个备份（1小时）
    "backup_interval":  XiuConfig().backup_interval * 60,  # 60秒 = 1分钟
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
    backup_count = 0
    last_error = None
    
    while True:
        try:
            backup_count += 1
            logger.info(f"开始计划备份 #{backup_count}...")
            
            # 尝试创建备份
            backup_path = await create_backup()
            
            if backup_path:
                logger.info(f"备份 #{backup_count} 成功创建: {backup_path}, 大小: {os.path.getsize(backup_path) / 1024:.2f} KB")
                last_error = None  # 重置错误状态
                
                # 记录当前拥有的备份数量
                backup_files = list(Path(BACKUP_CONFIG["backup_dir"]).glob("xiuxian_backup_*.sql*"))
                logger.info(f"当前备份文件数量: {len(backup_files)}, 最大保留数量: {BACKUP_CONFIG['keep_backups']}")
            else:
                logger.warning(f"备份 #{backup_count} 创建失败")
            
            # 检查/更新数据库结构
            try:
                await check_db_structure()
            except Exception as e:
                logger.error(f"数据库结构检查失败: {e}")
            
            # 等待下一次备份
            interval_minutes = BACKUP_CONFIG['backup_interval'] // 60
            logger.info(f"备份 #{backup_count} 完成，{interval_minutes} 分钟后进行下一次备份")
            
            # 精确计算下一次备份时间
            next_backup_time = datetime.datetime.now() + datetime.timedelta(seconds=BACKUP_CONFIG["backup_interval"])
            logger.info(f"下一次备份计划时间: {next_backup_time.strftime('%Y-%m-%d %H:%M:%S')}")
            
            await asyncio.sleep(BACKUP_CONFIG["backup_interval"])
        
        except asyncio.CancelledError:
            logger.info("备份任务被取消")
            break
        except Exception as e:
            # 避免不停地记录相同的错误
            if str(e) != str(last_error):
                logger.error(f"自动备份任务 #{backup_count} 出错: {e}")
                last_error = e
            
            # 出错后等待一小段时间再重试
            logger.info("将在60秒后重试备份")
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
    global _BACKUP_SERVICE_RUNNING, _BACKUP_TASK
    
    # 检查服务是否已经在运行
    if _BACKUP_SERVICE_RUNNING:
        logger.info("备份服务已经在运行，跳过重复启动")
        return _BACKUP_TASK
        
    logger.info("正在启动数据库备份服务...")
    
    # 检查配置
    if not BACKUP_CONFIG["pg_url"]:
        logger.error("未设置PostgreSQL连接URL，无法启动备份服务")
        return None
    
    # 确保备份目录存在
    backup_dir = ensure_backup_dir()
    logger.info(f"备份将保存到: {backup_dir}")
    
    # 创建一个初始备份
    try:
        initial_backup = await create_backup()
        if initial_backup:
            logger.info(f"初始备份创建成功: {initial_backup}")
        else:
            logger.warning("初始备份创建失败")
    except Exception as e:
        logger.error(f"创建初始备份时出错: {e}")
    
    # 启动自动备份任务
    _BACKUP_TASK = asyncio.create_task(automatic_backup_task())
    _BACKUP_SERVICE_RUNNING = True
    logger.info("数据库备份服务已启动，每分钟进行一次备份")
    
    return _BACKUP_TASK
