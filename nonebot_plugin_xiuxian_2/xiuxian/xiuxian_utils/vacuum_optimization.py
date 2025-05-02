"""
PostgreSQL数据库垃圾回收优化模块
提供自动和手动VACUUM功能，优化数据库性能
"""
import asyncio
import logging
import datetime
import asyncpg
from typing import List, Dict, Optional, Union

# 初始化日志
logger = logging.getLogger("xiuxian_vacuum")

# 全局连接池引用
_POOL = None

def set_pool(pool):
    """设置全局连接池引用"""
    global _POOL
    _POOL = pool

# 数据库表清单
TABLES = [
    "xiuxian_user",
    "xiuxian_time",
    "xiuxian_buff",
    "xiuxian_sect",
    "xiuxian_back",
    "xiuxian_impart"
]

# 垃圾回收配置
VACUUM_CONFIG = {
    "auto_vacuum_interval": 12 * 3600,  # 12小时自动VACUUM
    "vacuum_full_interval": 7 * 24 * 3600,  # 7天执行一次VACUUM FULL
    "analyze_interval": 6 * 3600,  # 6小时自动ANALYZE
    "aggressive_vacuum_threshold": 10000,  # 当表修改超过这个数时执行更积极的VACUUM
    "last_vacuum_time": {},  # 记录上次VACUUM时间
    "last_analyze_time": {},  # 记录上次ANALYZE时间
    "last_vacuum_full_time": None,  # 上次完整VACUUM时间
}

async def get_table_stats():
    """获取表统计信息"""
    if _POOL is None:
        raise ValueError("连接池未初始化")
    
    stats = {}
    
    async with _POOL.acquire() as conn:
        for table in TABLES:
            # 检查表是否存在
            exists = await check_table_exists(table)
            if not exists:
                stats[table] = {
                    "exists": False,
                    "size": "0 bytes",
                    "size_bytes": 0,
                    "row_count": 0,
                    "inserts": 0,
                    "updates": 0,
                    "deletes": 0,
                    "live_tuples": 0,
                    "dead_tuples": 0,
                }
                continue
                
            try:
                # 获取表的大小
                size_query = f"SELECT pg_size_pretty(pg_total_relation_size('{table}')) as size, pg_total_relation_size('{table}') as bytes"
                size_result = await conn.fetchrow(size_query)
                
                # 获取表的行数
                count_query = f"SELECT COUNT(*) as count FROM {table}"
                count_result = await conn.fetchval(count_query)
                
                # 获取表的修改统计
                stat_query = f"""
                SELECT 
                    n_tup_ins as inserts, 
                    n_tup_upd as updates, 
                    n_tup_del as deletes,
                    n_live_tup as live_tuples,
                    n_dead_tup as dead_tuples
                FROM pg_stat_user_tables 
                WHERE relname = '{table}'
                """
                stat_result = await conn.fetchrow(stat_query)
                
                stats[table] = {
                    "exists": True,
                    "size": size_result["size"],
                    "size_bytes": size_result["bytes"],
                    "row_count": count_result,
                    "inserts": stat_result["inserts"] if stat_result else 0,
                    "updates": stat_result["updates"] if stat_result else 0,
                    "deletes": stat_result["deletes"] if stat_result else 0,
                    "live_tuples": stat_result["live_tuples"] if stat_result else 0,
                    "dead_tuples": stat_result["dead_tuples"] if stat_result else 0,
                }
            except Exception as e:
                logger.error(f"获取表 {table} 的统计信息时出错: {e}")
                stats[table] = {
                    "exists": True,
                    "size": "0 bytes",
                    "size_bytes": 0,
                    "row_count": 0,
                    "inserts": 0,
                    "updates": 0,
                    "deletes": 0,
                    "live_tuples": 0,
                    "dead_tuples": 0,
                }
    
    return stats

async def check_table_exists(table: str) -> bool:
    """检查表是否存在"""
    if _POOL is None:
        return False
    
    try:
        async with _POOL.acquire() as conn:
            result = await conn.fetchval(
                "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = $1)",
                table
            )
            return bool(result)
    except Exception as e:
        logger.error(f"检查表 {table} 是否存在时出错: {e}")
        return False

async def check_all_tables_exist() -> bool:
    """检查所有必要的表是否都存在"""
    if _POOL is None:
        return False
    
    all_exist = True
    for table in TABLES:
        exists = await check_table_exists(table)
        if not exists:
            all_exist = False
            logger.warning(f"表 {table} 不存在")
    
    return all_exist

async def vacuum_table(table: str, full: bool = False, analyze: bool = True):
    """
    对指定表执行VACUUM操作
    
    参数:
        table: 表名
        full: 是否执行VACUUM FULL (会锁表)
        analyze: 是否同时执行ANALYZE
    """
    if _POOL is None:
        raise ValueError("连接池未初始化")
    
    # 先检查表是否存在
    if not await check_table_exists(table):
        logger.error(f"对表 {table} 执行 VACUUM 失败: 表不存在")
        return False
    
    try:
        start_time = datetime.datetime.now()
        operation = "VACUUM FULL" if full else "VACUUM"
        if analyze:
            operation += " ANALYZE"
            
        logger.info(f"开始对表 {table} 执行 {operation}")
        
        async with _POOL.acquire() as conn:
            await conn.execute(f"{operation} {table}")
        
        end_time = datetime.datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        logger.info(f"表 {table} 的 {operation} 完成，耗时 {duration:.2f} 秒")
        
        # 更新上次操作时间
        now = datetime.datetime.now().timestamp()
        if full:
            VACUUM_CONFIG["last_vacuum_full_time"] = now
        elif analyze:
            VACUUM_CONFIG["last_vacuum_time"][table] = now
            VACUUM_CONFIG["last_analyze_time"][table] = now
        else:
            VACUUM_CONFIG["last_vacuum_time"][table] = now
            
        return True
    except Exception as e:
        logger.error(f"对表 {table} 执行 {operation} 失败: {e}")
        return False

async def analyze_table(table: str):
    """
    对指定表执行ANALYZE操作
    
    参数:
        table: 表名
    """
    if _POOL is None:
        raise ValueError("连接池未初始化")
    
    # 先检查表是否存在
    if not await check_table_exists(table):
        logger.error(f"对表 {table} 执行 ANALYZE 失败: 表不存在")
        return False
    
    try:
        start_time = datetime.datetime.now()
        logger.info(f"开始对表 {table} 执行 ANALYZE")
        
        async with _POOL.acquire() as conn:
            await conn.execute(f"ANALYZE {table}")
        
        end_time = datetime.datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        logger.info(f"表 {table} 的 ANALYZE 完成，耗时 {duration:.2f} 秒")
        
        # 更新上次分析时间
        VACUUM_CONFIG["last_analyze_time"][table] = datetime.datetime.now().timestamp()
        return True
    except Exception as e:
        logger.error(f"对表 {table} 执行 ANALYZE 失败: {e}")
        return False

async def vacuum_all_tables(full: bool = False):
    """
    对所有表执行VACUUM操作
    
    参数:
        full: 是否执行VACUUM FULL
    """
    results = {}
    
    # 检查是否所有表都存在
    tables_exist = await check_all_tables_exist()
    if not tables_exist:
        logger.warning("一些表不存在，只对存在的表执行VACUUM")
    
    try:
        stats_before = await get_table_stats()
        
        for table in TABLES:
            # 检查表是否存在
            if not await check_table_exists(table):
                logger.warning(f"表 {table} 不存在，跳过VACUUM")
                results[table] = False
                continue
                
            try:
                results[table] = await vacuum_table(table, full=full)
            except Exception as e:
                logger.error(f"对表 {table} 执行VACUUM时出错: {e}")
                results[table] = False
        
        # 尝试获取操作后的表统计信息，如果失败不影响整体结果
        try:
            stats_after = await get_table_stats()
            
            # 计算节省的空间
            total_saved = 0
            for table in TABLES:
                if table not in stats_before or table not in stats_after:
                    continue
                if not stats_before[table]["exists"] or not stats_after[table]["exists"]:
                    continue
                    
                saved = stats_before[table]["size_bytes"] - stats_after[table]["size_bytes"]
                total_saved += saved if saved > 0 else 0
            
            if total_saved > 0:
                logger.info(f"VACUUM 操作总共节省了 {total_saved / (1024*1024):.2f} MB 空间")
        except Exception as e:
            logger.error(f"获取VACUUM后表统计信息时出错: {e}")
        
        return results
    except Exception as e:
        logger.error(f"执行全部表VACUUM时出错: {e}")
        return {table: False for table in TABLES}

async def start_vacuum_service():
    """启动VACUUM服务"""
    # 检查表是否存在
    tables_exist = await check_all_tables_exist()
    if not tables_exist:
        logger.warning("一些必要的表不存在，VACUUM服务将在表创建后启动")
        # 启动一个延迟任务，每5分钟检查一次表是否已创建
        asyncio.create_task(wait_for_tables_and_start())
        return
    
    # 优化自动VACUUM设置
    await optimize_autovacuum_settings()
    
    # 启动自动VACUUM任务
    asyncio.create_task(automatic_vacuum_task())
    
    logger.info("VACUUM优化服务已启动")

async def wait_for_tables_and_start():
    """等待表创建完成后启动VACUUM服务"""
    retry_count = 0
    max_retries = 12  # 最多尝试12次，即1小时
    
    while retry_count < max_retries:
        logger.info(f"等待表创建完成，第{retry_count+1}次检查...")
        tables_exist = await check_all_tables_exist()
        
        if tables_exist:
            logger.info("所有必要的表已创建，现在启动VACUUM服务")
            # 优化自动VACUUM设置
            await optimize_autovacuum_settings()
            
            # 启动自动VACUUM任务
            asyncio.create_task(automatic_vacuum_task())
            
            logger.info("VACUUM优化服务已启动")
            return
        
        # 等待5分钟后再次检查
        await asyncio.sleep(300)
        retry_count += 1
    
    logger.warning("在1小时内未能检测到所有必要的表，VACUUM服务未启动")

async def automatic_vacuum_task():
    """自动VACUUM任务"""
    try:
        # 初始化上次操作时间
        for table in TABLES:
            VACUUM_CONFIG["last_vacuum_time"][table] = 0
            VACUUM_CONFIG["last_analyze_time"][table] = 0
        
        VACUUM_CONFIG["last_vacuum_full_time"] = 0
        
        while True:
            # 检查表是否都存在
            tables_exist = await check_all_tables_exist()
            if not tables_exist:
                logger.warning("一些表不存在，跳过本次VACUUM检查")
                await asyncio.sleep(1800)  # 30分钟后再检查
                continue
                
            now = datetime.datetime.now().timestamp()
            
            try:
                # 获取表统计信息
                stats = await get_table_stats()
                
                # 检查每个表是否需要VACUUM
                for table in TABLES:
                    # 跳过不存在的表
                    if not await check_table_exists(table):
                        continue
                        
                    # 判断是否需要VACUUM
                    last_vacuum = VACUUM_CONFIG["last_vacuum_time"].get(table, 0)
                    if now - last_vacuum > VACUUM_CONFIG["auto_vacuum_interval"]:
                        logger.info(f"表 {table} 超过自动VACUUM间隔，执行常规VACUUM")
                        await vacuum_table(table, full=False, analyze=False)
                        continue
                    
                    # 检查是否有大量修改需要紧急VACUUM
                    dead_ratio = 0
                    if stats[table]["live_tuples"] > 0:
                        dead_ratio = stats[table]["dead_tuples"] / stats[table]["live_tuples"]
                    
                    if (dead_ratio > 0.2 or stats[table]["dead_tuples"] > VACUUM_CONFIG["aggressive_vacuum_threshold"]):
                        logger.info(f"表 {table} 检测到大量死元组 ({stats[table]['dead_tuples']}行)，执行紧急VACUUM")
                        await vacuum_table(table, full=False, analyze=True)
                    
                    # 判断是否需要ANALYZE
                    last_analyze = VACUUM_CONFIG["last_analyze_time"].get(table, 0)
                    if now - last_analyze > VACUUM_CONFIG["analyze_interval"]:
                        logger.info(f"表 {table} 超过自动ANALYZE间隔，执行ANALYZE")
                        await analyze_table(table)
                
                # 判断是否需要完整VACUUM
                if now - VACUUM_CONFIG["last_vacuum_full_time"] > VACUUM_CONFIG["vacuum_full_interval"]:
                    logger.info("超过完整VACUUM间隔，执行VACUUM FULL")
                    await vacuum_all_tables(full=True)
            except Exception as e:
                logger.error(f"执行VACUUM检查时出错: {e}")
            
            # 等待下一次检查
            await asyncio.sleep(3600)  # 每小时检查一次
            
    except Exception as e:
        logger.error(f"自动VACUUM任务出错: {e}")
        # 出错后等待一小段时间再重试
        await asyncio.sleep(60)
        asyncio.create_task(automatic_vacuum_task())

async def optimize_autovacuum_settings():
    """优化PostgreSQL的自动VACUUM设置"""
    if _POOL is None:
        raise ValueError("连接池未初始化")
    
    try:
        async with _POOL.acquire() as conn:
            # 检查当前设置
            current_settings = await conn.fetch("""
            SELECT name, setting, unit 
            FROM pg_settings 
            WHERE name LIKE 'autovacuum%' OR name LIKE '%vacuum%'
            """)
            
            settings = {}
            for row in current_settings:
                settings[row['name']] = row['setting']
            
            # 记录当前设置而不尝试更改它们
            logger.info("当前自动VACUUM设置:")
            for name, value in settings.items():
                logger.info(f"  {name}: {value}")
            
            # 以下参数需要在配置文件中修改，无法在运行时更改
            # 记录建议设置
            logger.info("建议的自动VACUUM设置:")
            logger.info("  autovacuum = on")
            logger.info("  autovacuum_vacuum_threshold = 50")
            logger.info("  autovacuum_analyze_threshold = 50")
            logger.info("  autovacuum_vacuum_scale_factor = 0.1")
            logger.info("  autovacuum_analyze_scale_factor = 0.05")
            logger.info("  autovacuum_naptime = 60s")
            logger.info("  autovacuum_max_workers = 3")
            
            # 可以在不修改参数的情况下仅执行ANALYZE来更新统计信息
            for table in TABLES:
                await analyze_table(table)
                
            logger.info("已执行表分析以更新统计信息")
            return True
    except Exception as e:
        logger.error(f"优化自动VACUUM设置时出错: {e}")
        return False

async def reindex_table(table: str):
    """
    对指定表重建索引
    
    参数:
        table: 表名
    """
    if _POOL is None:
        raise ValueError("连接池未初始化")
    
    try:
        start_time = datetime.datetime.now()
        logger.info(f"开始重建表 {table} 的索引")
        
        async with _POOL.acquire() as conn:
            # 获取表的所有索引
            indexes = await conn.fetch(f"""
            SELECT indexname 
            FROM pg_indexes 
            WHERE tablename = '{table}'
            """)
            
            for index in indexes:
                index_name = index['indexname']
                await conn.execute(f"REINDEX INDEX {index_name}")
                logger.info(f"已重建索引: {index_name}")
        
        end_time = datetime.datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        logger.info(f"表 {table} 的索引重建完成，耗时 {duration:.2f} 秒")
        return True
    except Exception as e:
        logger.error(f"重建表 {table} 的索引时出错: {e}")
        return False

async def reindex_all_tables():
    """重建所有表的索引"""
    results = {}
    for table in TABLES:
        results[table] = await reindex_table(table)
    return results