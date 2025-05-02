#!/usr/bin/env python3
"""
修仙数据库优化启动脚本
用于启动所有数据库优化服务
"""
import os
import sys
import asyncio
import argparse
import logging
from pathlib import Path

# 添加当前目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

try:
    from optimization_manager import apply_all_optimizations, get_manager
except ImportError:
    print("错误: 无法导入优化管理器模块。请确保optimization_manager.py文件在当前目录中。")
    sys.exit(1)

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("xiuxian_optimization_service.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("xiuxian_optimization_service")

async def start_services(pg_url: str, daemon: bool = False):
    """启动所有优化服务"""
    try:
        logger.info("正在启动修仙数据库优化服务...")
        
        # 应用所有优化
        success = await apply_all_optimizations(pg_url)
        if not success:
            logger.error("无法启动优化服务")
            return False
        
        logger.info("所有优化服务已成功启动")
        
        if daemon:
            # 保持程序运行
            try:
                while True:
                    await asyncio.sleep(3600)  # 每小时检查一次
                    logger.info("优化服务正在运行中...")
            except KeyboardInterrupt:
                logger.info("接收到停止信号，正在优雅关闭服务...")
                await get_manager().stop_services()
                logger.info("服务已停止")
        
        return True
        
    except Exception as e:
        logger.error(f"启动服务时出错: {e}")
        return False

def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="修仙数据库优化服务")
    parser.add_argument("--pg-url", type=str, help="PostgreSQL连接URL (例如: postgresql://username:password@localhost:5432/xiuxian)")
    parser.add_argument("--daemon", action="store_true", help="以守护进程模式运行")
    parser.add_argument("--config", type=str, help="配置文件路径")
    return parser.parse_args()

def load_config(config_path: str):
    """从配置文件加载设置"""
    import json
    
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"加载配置文件时出错: {e}")
        return None

def main():
    """主函数"""
    args = parse_arguments()
    
    pg_url = args.pg_url
    
    # 如果提供了配置文件，从中加载设置
    if args.config:
        config = load_config(args.config)
        if config and 'pg_url' in config:
            pg_url = config['pg_url']
    
    # 如果未提供PostgreSQL URL，尝试从环境变量获取
    if not pg_url:
        pg_url = os.environ.get('XIUXIAN_PG_URL')
    
    # 如果仍未获取到URL，显示错误并退出
    if not pg_url:
        logger.error("错误: 未提供PostgreSQL连接URL。请使用--pg-url参数、环境变量XIUXIAN_PG_URL或配置文件指定。")
        sys.exit(1)
    
    # 启动服务
    asyncio.run(start_services(pg_url, daemon=args.daemon))

if __name__ == "__main__":
    main() 