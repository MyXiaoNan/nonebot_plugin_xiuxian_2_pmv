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
                "size": size_result["size"],
                "size_bytes": size_result["bytes"],
                "row_count": count_result,
                "inserts": stat_result["inserts"] if stat_result else 0,
                "updates": stat_result["updates"] if stat_result else 0,
                "deletes": stat_result["deletes"] if stat_result else 0,
                "live_tuples": stat_result["live_tuples"] if stat_result else 0,
                "dead_tuples": stat_result["dead_tuples"] if stat_result else 0,
            }
    
    return stats

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
    stats_before = await get_table_stats()
    
    for table in TABLES:
        results[table] = await vacuum_table(table, full=full)
    
    stats_after = await get_table_stats()
    
    # 计算节省的空间
    total_saved = 0
    for table in TABLES:
        saved = stats_before[table]["size_bytes"] - stats_after[table]["size_bytes"]
        total_saved += saved if saved > 0 else 0
    
    if total_saved > 0:
        logger.info(f"VACUUM 操作总共节省了 {total_saved / (1024*1024):.2f} MB 空间")
    
    return results

async def automatic_vacuum_task():
    """自动VACUUM任务"""
    try:
        # 初始化上次操作时间
        for table in TABLES:
            VACUUM_CONFIG["last_vacuum_time"][table] = 0
            VACUUM_CONFIG["last_analyze_time"][table] = 0
        
        VACUUM_CONFIG["last_vacuum_full_time"] = 0
        
        while True:
            now = datetime.datetime.now().timestamp()
            
            # 获取表统计信息
            stats = await get_table_stats()
            
            # 检查每个表是否需要VACUUM
            for table in TABLES:
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
            
            # 根据数据库大小和特性调整设置
            updates = []
            
            # 仅在必要时更新设置
            if settings.get('autovacuum') != 'on':
                updates.append("SET autovacuum = on")
            
            if settings.get('autovacuum_vacuum_threshold') != '50':
                updates.append("SET autovacuum_vacuum_threshold = 50")
                
            if settings.get('autovacuum_analyze_threshold') != '50':
                updates.append("SET autovacuum_analyze_threshold = 50")
                
            if settings.get('autovacuum_vacuum_scale_factor') != '0.1':
                updates.append("SET autovacuum_vacuum_scale_factor = 0.1")
                
            if settings.get('autovacuum_analyze_scale_factor') != '0.05':
                updates.append("SET autovacuum_analyze_scale_factor = 0.05")
                
            if settings.get('autovacuum_naptime') != '60':
                updates.append("SET autovacuum_naptime = '60s'")
                
            if settings.get('autovacuum_max_workers') != '3':
                updates.append("SET autovacuum_max_workers = 3")
            
            # 应用优化设置
            if updates:
                for update in updates:
                    await conn.execute(update)
                logger.info(f"已优化自动VACUUM设置: {len(updates)}个参数已更新")
            else:
                logger.info("自动VACUUM设置已经是最优的")
                
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

async def start_vacuum_service():
    """启动VACUUM服务"""
    # 优化自动VACUUM设置
    await optimize_autovacuum_settings()
    
    # 启动自动VACUUM任务
    asyncio.create_task(automatic_vacuum_task())
    
    logger.info("VACUUM优化服务已启动")

# 用于命令行测试的入口点
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="PostgreSQL数据库VACUUM优化工具")
    parser.add_argument("--vacuum", type=str, help="对指定表执行VACUUM")
    parser.add_argument("--vacuum-full", type=str, help="对指定表执行VACUUM FULL")
    parser.add_argument("--vacuum-all", action="store_true", help="对所有表执行VACUUM")
    parser.add_argument("--vacuum-full-all", action="store_true", help="对所有表执行VACUUM FULL")
    parser.add_argument("--analyze", type=str, help="对指定表执行ANALYZE")
    parser.add_argument("--analyze-all", action="store_true", help="对所有表执行ANALYZE")
    parser.add_argument("--reindex", type=str, help="重建指定表的索引")
    parser.add_argument("--reindex-all", action="store_true", help="重建所有表的索引")
    parser.add_argument("--stats", action="store_true", help="显示表统计信息")
    parser.add_argument("--optimize-settings", action="store_true", help="优化自动VACUUM设置")
    parser.add_argument("--start-service", action="store_true", help="启动VACUUM服务")
    parser.add_argument("--pg-url", type=str, help="PostgreSQL连接URL")
    args = parser.parse_args()
    
    async def main():
        # 连接到数据库
        if args.pg_url:
            pool = await asyncpg.create_pool(args.pg_url)
            set_pool(pool)
        else:
            print("错误: 必须提供PostgreSQL连接URL")
            return
        
        try:
            if args.vacuum:
                await vacuum_table(args.vacuum)
            elif args.vacuum_full:
                await vacuum_table(args.vacuum_full, full=True)
            elif args.vacuum_all:
                await vacuum_all_tables()
            elif args.vacuum_full_all:
                await vacuum_all_tables(full=True)
            elif args.analyze:
                await analyze_table(args.analyze)
            elif args.analyze_all:
                for table in TABLES:
                    await analyze_table(table)
            elif args.reindex:
                await reindex_table(args.reindex)
            elif args.reindex_all:
                await reindex_all_tables()
            elif args.stats:
                stats = await get_table_stats()
                for table, info in stats.items():
                    print(f"\n表 {table}:")
                    print(f"  大小: {info['size']}")
                    print(f"  行数: {info['row_count']}")
                    print(f"  插入数: {info['inserts']}")
                    print(f"  更新数: {info['updates']}")
                    print(f"  删除数: {info['deletes']}")
                    print(f"  活元组: {info['live_tuples']}")
                    print(f"  死元组: {info['dead_tuples']}")
                    if info['live_tuples'] > 0:
                        dead_ratio = info['dead_tuples'] / info['live_tuples']
                        print(f"  死元组比例: {dead_ratio:.2%}")
            elif args.optimize_settings:
                await optimize_autovacuum_settings()
            elif args.start_service:
                await start_vacuum_service()
                # 保持程序运行
                while True:
                    await asyncio.sleep(3600)
        finally:
            # 关闭连接池
            if pool:
                await pool.close()
    
    asyncio.run(main()) 