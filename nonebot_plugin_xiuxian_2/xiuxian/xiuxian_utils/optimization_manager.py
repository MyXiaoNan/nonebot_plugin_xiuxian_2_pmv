"""
数据库优化管理器
整合事务、查询、备份和垃圾回收优化
"""
import asyncio
import logging
import os
from pathlib import Path
import importlib.util
import sys
import asyncpg
from typing import Optional, Dict, Any

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("xiuxian_optimization.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("xiuxian_optimizer")

# 优化模块路径
MODULE_PATHS = {
    "transaction": "transaction_optimization.py",
    "query": "query_optimization.py",
    "backup": "backup_strategy.py",
    "vacuum": "vacuum_optimization.py"
}

# 数据库配置
DB_CONFIG = {
    "pg_url": None,  # 将在运行时设置
    "min_connections": 10,
    "max_connections": 50,
    "command_timeout": 30.0,
    "max_inactive_connection_lifetime": 600.0,
    "statement_cache_size": 1000
}

# 全局连接池
_POOL = None

def set_pg_url(url: str):
    """设置PostgreSQL连接URL"""
    DB_CONFIG["pg_url"] = url

async def create_pool() -> asyncpg.Pool:
    """创建数据库连接池"""
    global _POOL
    
    if not DB_CONFIG["pg_url"]:
        raise ValueError("未设置PostgreSQL连接URL")
    
    logger.info("创建数据库连接池...")
    
    _POOL = await asyncpg.create_pool(
        DB_CONFIG["pg_url"],
        min_size=DB_CONFIG["min_connections"],
        max_size=DB_CONFIG["max_connections"],
        command_timeout=DB_CONFIG["command_timeout"],
        max_inactive_connection_lifetime=DB_CONFIG["max_inactive_connection_lifetime"],
        statement_cache_size=DB_CONFIG["statement_cache_size"]
    )
    
    logger.info("数据库连接池创建成功")
    return _POOL

async def close_pool():
    """关闭数据库连接池"""
    global _POOL
    
    if _POOL:
        logger.info("关闭数据库连接池...")
        await _POOL.close()
        _POOL = None
        logger.info("数据库连接池已关闭")

def load_module(module_name: str, module_path: str):
    """动态加载Python模块"""
    try:
        # 获取绝对路径
        abs_path = os.path.abspath(module_path)
        
        # 检查文件是否存在
        if not os.path.exists(abs_path):
            logger.error(f"模块文件不存在: {abs_path}")
            return None
        
        # 加载模块
        spec = importlib.util.spec_from_file_location(module_name, abs_path)
        if not spec:
            logger.error(f"无法为 {module_path} 创建模块规范")
            return None
            
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        
        logger.info(f"已加载模块: {module_name}")
        return module
    
    except Exception as e:
        logger.error(f"加载模块 {module_name} 时出错: {e}")
        return None

class OptimizationManager:
    """优化管理器类"""
    def __init__(self):
        self.pool = None
        self.modules = {}
        self.services_running = False
    
    async def initialize(self, pg_url: str):
        """初始化优化管理器"""
        try:
            # 设置数据库URL
            set_pg_url(pg_url)
            
            # 创建连接池
            self.pool = await create_pool()
            
            # 加载所有模块
            for name, path in MODULE_PATHS.items():
                module = load_module(f"xiuxian_{name}", path)
                if module and hasattr(module, "set_pool"):
                    module.set_pool(self.pool)
                self.modules[name] = module
            
            # 设置备份模块的PostgreSQL URL
            if self.modules.get("backup") and hasattr(self.modules["backup"], "set_pg_url"):
                self.modules["backup"].set_pg_url(pg_url)
            
            logger.info("优化管理器初始化完成")
            return True
            
        except Exception as e:
            logger.error(f"初始化优化管理器时出错: {e}")
            return False
    
    async def start_services(self):
        """启动所有优化服务"""
        if self.services_running:
            logger.warning("服务已经在运行中")
            return
        
        try:
            # 启动备份服务
            if self.modules.get("backup") and hasattr(self.modules["backup"], "start_backup_service"):
                await self.modules["backup"].start_backup_service()
            
            # 启动VACUUM服务
            if self.modules.get("vacuum") and hasattr(self.modules["vacuum"], "start_vacuum_service"):
                await self.modules["vacuum"].start_vacuum_service()
            
            # 创建物化视图
            if self.modules.get("query") and hasattr(self.modules["query"], "create_materialized_views"):
                await self.modules["query"].create_materialized_views()
            
            self.services_running = True
            logger.info("所有优化服务已启动")
            
        except Exception as e:
            logger.error(f"启动优化服务时出错: {e}")
    
    async def stop_services(self):
        """停止所有服务"""
        if not self.services_running:
            return
        
        try:
            # 关闭连接池
            await close_pool()
            
            self.services_running = False
            logger.info("所有优化服务已停止")
            
        except Exception as e:
            logger.error(f"停止优化服务时出错: {e}")
    
    async def run_manual_vacuum(self, full: bool = False):
        """手动执行VACUUM"""
        if not self.modules.get("vacuum"):
            logger.error("VACUUM模块未加载")
            return False
        
        try:
            if hasattr(self.modules["vacuum"], "vacuum_all_tables"):
                result = await self.modules["vacuum"].vacuum_all_tables(full=full)
                return result
            return False
        except Exception as e:
            logger.error(f"执行手动VACUUM时出错: {e}")
            return False
    
    async def create_backup(self):
        """手动创建备份"""
        if not self.modules.get("backup"):
            logger.error("备份模块未加载")
            return None
        
        try:
            if hasattr(self.modules["backup"], "create_backup"):
                result = await self.modules["backup"].create_backup()
                return result
            return None
        except Exception as e:
            logger.error(f"创建备份时出错: {e}")
            return None
    
    async def optimize_query(self, query: str, params: list = None):
        """分析并优化SQL查询"""
        if not self.modules.get("query"):
            logger.error("查询优化模块未加载")
            return None
            
        try:
            if hasattr(self.modules["query"], "optimize_query"):
                result = await self.modules["query"].optimize_query(query, params)
                return result
            return None
        except Exception as e:
            logger.error(f"优化查询时出错: {e}")
            return None
    
    async def refresh_views(self):
        """刷新物化视图"""
        if not self.modules.get("query"):
            logger.error("查询优化模块未加载")
            return False
            
        try:
            if hasattr(self.modules["query"], "refresh_materialized_view"):
                await self.modules["query"].refresh_materialized_view("xiuxian_user_stats")
                await self.modules["query"].refresh_materialized_view("xiuxian_top_users")
                logger.info("物化视图已刷新")
                return True
            return False
        except Exception as e:
            logger.error(f"刷新物化视图时出错: {e}")
            return False
    
    def get_cached_query(self):
        """获取缓存查询函数"""
        if not self.modules.get("query"):
            logger.error("查询优化模块未加载")
            return None
            
        if hasattr(self.modules["query"], "cached_query"):
            return self.modules["query"].cached_query
        return None
    
    def get_monitored_query(self):
        """获取监控查询函数"""
        if not self.modules.get("query"):
            logger.error("查询优化模块未加载")
            return None
            
        if hasattr(self.modules["query"], "monitored_query"):
            return self.modules["query"].monitored_query
        return None
    
    def get_transaction_context(self):
        """获取事务上下文管理器"""
        if not self.modules.get("transaction"):
            logger.error("事务优化模块未加载")
            return None
            
        if hasattr(self.modules["transaction"], "transaction"):
            return self.modules["transaction"].transaction
        return None
    
    def get_lock_context(self):
        """获取锁上下文管理器"""
        if not self.modules.get("transaction"):
            logger.error("事务优化模块未加载")
            return None
            
        if hasattr(self.modules["transaction"], "with_lock"):
            return self.modules["transaction"].with_lock
        return None
    
    def get_retry_decorator(self):
        """获取重试装饰器"""
        if not self.modules.get("transaction"):
            logger.error("事务优化模块未加载")
            return None
            
        if hasattr(self.modules["transaction"], "retry_operation"):
            return self.modules["transaction"].retry_operation
        return None

# 全局优化管理器实例
_MANAGER = None

def get_manager() -> OptimizationManager:
    """获取优化管理器实例"""
    global _MANAGER
    
    if _MANAGER is None:
        _MANAGER = OptimizationManager()
    
    return _MANAGER

async def apply_all_optimizations(pg_url: str):
    """应用所有优化"""
    manager = get_manager()
    
    # 初始化管理器
    success = await manager.initialize(pg_url)
    if not success:
        logger.error("无法初始化优化管理器")
        return False
    
    # 启动所有服务
    await manager.start_services()
    
    return True

# 用于命令行测试的入口点
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="数据库优化管理器")
    parser.add_argument("--pg-url", type=str, required=True, help="PostgreSQL连接URL")
    parser.add_argument("--start", action="store_true", help="启动所有优化服务")
    parser.add_argument("--vacuum", action="store_true", help="执行手动VACUUM")
    parser.add_argument("--vacuum-full", action="store_true", help="执行手动VACUUM FULL")
    parser.add_argument("--backup", action="store_true", help="创建手动备份")
    parser.add_argument("--refresh-views", action="store_true", help="刷新物化视图")
    args = parser.parse_args()
    
    async def main():
        if args.start:
            # 应用所有优化
            success = await apply_all_optimizations(args.pg_url)
            if success:
                print("所有优化服务已启动")
                # 保持程序运行
                try:
                    while True:
                        await asyncio.sleep(3600)
                except KeyboardInterrupt:
                    print("正在停止服务...")
                    await get_manager().stop_services()
        else:
            # 单独执行某个操作
            manager = get_manager()
            await manager.initialize(args.pg_url)
            
            if args.vacuum:
                await manager.run_manual_vacuum()
            elif args.vacuum_full:
                await manager.run_manual_vacuum(full=True)
            elif args.backup:
                backup_path = await manager.create_backup()
                if backup_path:
                    print(f"备份已创建: {backup_path}")
            elif args.refresh_views:
                await manager.refresh_views()
            
            await manager.stop_services()
    
    asyncio.run(main()) 