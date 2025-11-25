"""
事务和并发优化模块
用于提供PostgreSQL事务和并发处理的优化功能
"""
import asyncio
from typing import Any, List
import asyncpg
from contextlib import asynccontextmanager
from functools import wraps

# 全局连接池引用
_POOL = None

def set_pool(pool):
    """设置全局连接池引用"""
    global _POOL
    _POOL = pool

@asynccontextmanager
async def transaction(isolation_level="read committed"):
    """
    事务上下文管理器，提供可配置的事务隔离级别
    
    isolation_level 选项:
    - "serializable": 最高隔离级别，防止所有并发问题，但性能最低
    - "repeatable read": 防止脏读和不可重复读，但不防止幻读
    - "read committed": 防止脏读，默认级别
    - "read uncommitted": 最低隔离级别，性能最高但可能出现脏读
    """
    if _POOL is None:
        raise ValueError("连接池未初始化")
        
    conn = await _POOL.acquire()
    tr = None
    try:
        tr = conn.transaction(isolation=isolation_level)
        await tr.start()
        yield conn
        await tr.commit()
    except Exception as e:
        if tr and not tr.is_closed():
            await tr.rollback()
        raise e
    finally:
        await _POOL.release(conn)

async def with_lock(user_id: int, timeout: float = 10.0):
    """
    使用行级锁防止并发更新同一用户数据
    
    示例用法:
    async with with_lock(user_id):
        # 更新用户操作
    """
    if _POOL is None:
        raise ValueError("连接池未初始化")
        
    conn = await _POOL.acquire()
    try:
        # 使用pg_advisory_lock，一种轻量级锁机制
        # 将user_id转换为大整数作为锁ID
        await conn.execute(f"SELECT pg_advisory_lock({user_id})")
        yield conn
    finally:
        await conn.execute(f"SELECT pg_advisory_unlock({user_id})")
        await _POOL.release(conn)

async def update_user_with_lock(user_id: int, update_query: str, *args):
    """
    使用行锁安全地更新用户数据
    
    参数:
        user_id: 用户ID
        update_query: 更新SQL
        args: SQL参数
    
    示例:
    await update_user_with_lock(
        123, 
        "UPDATE xiuxian_user SET exp = exp + $1 WHERE user_id = $2", 
        1000, 123
    )
    """
    async with transaction("read committed") as conn:
        # 使用FOR UPDATE锁定行
        await conn.execute(
            "SELECT id FROM xiuxian_user WHERE user_id = $1 FOR UPDATE", 
            user_id
        )
        # 执行更新
        return await conn.execute(update_query, *args)

def retry_operation(max_retries: int = 3, retry_delay: float = 0.5):
    """
    重试装饰器，处理并发冲突等临时错误
    
    参数:
        max_retries: 最大重试次数
        retry_delay: 重试间隔（秒）
    
    用法:
    @retry_operation(max_retries=5)
    async def some_function(arg1, arg2):
        # 可能失败的数据库操作
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except asyncpg.exceptions.DeadlockDetectedError as e:
                    last_error = e
                    await asyncio.sleep(retry_delay * (2 ** attempt))  # 指数退避
                except asyncpg.exceptions.UniqueViolationError as e:
                    # 唯一约束冲突，这种情况不重试
                    raise e
                except (asyncpg.exceptions.PostgresError) as e:
                    last_error = e
                    if "could not serialize access" in str(e):
                        # 序列化失败，可以重试
                        await asyncio.sleep(retry_delay * (2 ** attempt))
                    else:
                        # 其他PostgreSQL错误，不重试
                        raise e
            
            # 如果所有重试都失败
            raise last_error or RuntimeError("操作失败，超出最大重试次数")
        
        return wrapper
    return decorator

# 批量操作函数
async def bulk_insert(table: str, columns: List[str], values: List[List[Any]], 
                     chunk_size: int = 1000):
    """
    高效的批量插入函数
    
    参数:
        table: 表名
        columns: 列名列表
        values: 值的列表的列表
        chunk_size: 每次插入的最大行数
    """
    if not values:
        return 0
        
    if _POOL is None:
        raise ValueError("连接池未初始化")
    
    async with _POOL.acquire() as conn:
        async with conn.transaction():
            count = 0
            # 分块处理
            for i in range(0, len(values), chunk_size):
                chunk = values[i:i+chunk_size]
                
                # 构建VALUES部分，每行一个($1, $2, ...)元组
                placeholders = []
                flat_values = []
                
                for row in chunk:
                    # 为这一行创建占位符 ($1, $2, ...)
                    row_placeholders = []
                    for j, val in enumerate(row):
                        param_idx = len(flat_values) + 1  # PostgreSQL参数从1开始
                        row_placeholders.append(f"${param_idx}")
                        flat_values.append(val)
                        
                    placeholders.append(f"({', '.join(row_placeholders)})")
                
                # 构建完整SQL
                columns_str = ', '.join(columns)
                values_str = ', '.join(placeholders)
                
                sql = f"INSERT INTO {table} ({columns_str}) VALUES {values_str}"
                
                result = await conn.execute(sql, *flat_values)
                count += int(result.split()[1])  # 解析"INSERT 0 X"中的X
            
            return count 