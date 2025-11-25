"""
查询优化模块
用于提供PostgreSQL查询优化功能
"""
from typing import List, Dict
import time
import logging

logger = logging.getLogger("xiuxian_query_optimizer")

# 全局连接池引用
_POOL = None
# 查询缓存
_QUERY_CACHE = {}
# 慢查询阈值(秒)
SLOW_QUERY_THRESHOLD = 0.5

def set_pool(pool):
    """设置全局连接池引用"""
    global _POOL
    _POOL = pool

async def explain_query(query: str, params: List = None) -> List[Dict]:
    """
    分析查询执行计划
    
    参数:
        query: SQL查询
        params: 查询参数
    
    返回:
        查询计划的JSON表示
    """
    if _POOL is None:
        raise ValueError("连接池未初始化")
    
    params = params or []
    explain_query = f"EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) {query}"
    
    async with _POOL.acquire() as conn:
        result = await conn.fetch(explain_query, *params)
        return result[0][0]


async def optimize_query(query: str, params: List = None) -> Dict:
    """
    分析并提供查询优化建议
    
    参数:
        query: SQL查询
        params: 查询参数
    
    返回:
        优化建议字典
    """
    plan = await explain_query(query, params)
    
    # 提取执行时间
    execution_time = plan[0]["Execution Time"]
    planning_time = plan[0]["Planning Time"]
    
    # 分析结果
    result = {
        "execution_time_ms": execution_time,
        "planning_time_ms": planning_time,
        "total_time_ms": execution_time + planning_time,
        "is_slow": execution_time > SLOW_QUERY_THRESHOLD * 1000,
        "suggestions": []
    }
    
    # 查找全表扫描
    def find_seq_scans(node):
        findings = []
        if node.get("Node Type") == "Seq Scan":
            findings.append({
                "issue": "全表扫描",
                "table": node.get("Relation Name"),
                "suggestion": f"考虑为表 {node.get('Relation Name')} 添加索引，覆盖 {node.get('Filter', '未知条件')}"
            })
        
        for child in node.get("Plans", []):
            findings.extend(find_seq_scans(child))
        
        return findings
    
    # 查找高成本操作
    def find_high_cost(node, threshold=1000):
        findings = []
        if node.get("Total Cost", 0) > threshold:
            findings.append({
                "issue": "高成本操作",
                "node_type": node.get("Node Type"),
                "cost": node.get("Total Cost"),
                "suggestion": f"优化 {node.get('Node Type')} 操作，当前成本 {node.get('Total Cost')}"
            })
        
        for child in node.get("Plans", []):
            findings.extend(find_high_cost(child, threshold))
        
        return findings
    
    # 分析查询计划
    node = plan[0]["Plan"]
    result["suggestions"].extend(find_seq_scans(node))
    result["suggestions"].extend(find_high_cost(node))
    
    # 基本建议
    if result["is_slow"]:
        result["suggestions"].append({
            "issue": "查询慢",
            "suggestion": "考虑重写查询或添加适当的索引"
        })
    
    return result

class QueryCache:
    """
    简单的查询结果缓存
    适用于频繁重复且结果不常变化的查询
    """
    def __init__(self, ttl=60):  # 默认缓存60秒
        self.cache = {}
        self.ttl = ttl
    
    def get(self, key):
        """获取缓存的查询结果"""
        if key in self.cache:
            entry = self.cache[key]
            if time.time() < entry["expires"]:
                return entry["data"]
            else:
                # 过期了，删除
                del self.cache[key]
        return None
    
    def set(self, key, data):
        """缓存查询结果"""
        self.cache[key] = {
            "data": data,
            "expires": time.time() + self.ttl
        }
    
    def invalidate(self, key=None):
        """使缓存失效"""
        if key is None:
            self.cache.clear()
        elif key in self.cache:
            del self.cache[key]

# 全局缓存实例
_query_cache = QueryCache()

async def cached_query(query: str, params: List = None, ttl: int = 60):
    """
    带缓存的查询函数
    
    参数:
        query: SQL查询
        params: 查询参数
        ttl: 缓存生存时间(秒)
    
    返回:
        查询结果
    """
    if _POOL is None:
        raise ValueError("连接池未初始化")
    
    params = params or []
    
    # 使用查询和参数作为缓存键
    cache_key = f"{query}:{str(params)}"
    cached_result = _query_cache.get(cache_key)
    
    if cached_result is not None:
        return cached_result
    
    # 缓存未命中，执行查询
    start_time = time.time()
    async with _POOL.acquire() as conn:
        result = await conn.fetch(query, *params)
    
    query_time = time.time() - start_time
    
    # 记录慢查询
    if query_time > SLOW_QUERY_THRESHOLD:
        logger.warning(f"慢查询 ({query_time:.2f}s): {query}")
    
    # 缓存结果
    _query_cache.set(cache_key, result)
    
    return result

async def force_query(query: str, params: List = None):
    """
    强制查询数据库，不使用缓存
    适用于需要绝对最新数据的场景
    
    参数:
        query: SQL查询
        params: 查询参数
    
    返回:
        查询结果
    """
    if _POOL is None:
        raise ValueError("连接池未初始化")
    
    params = params or []
    
    # 直接执行查询，跳过缓存
    start_time = time.time()
    async with _POOL.acquire() as conn:
        result = await conn.fetch(query, *params)
    
    query_time = time.time() - start_time
    
    # 记录慢查询
    if query_time > SLOW_QUERY_THRESHOLD:
        logger.warning(f"强制查询 ({query_time:.2f}s): {query}")
    
    return result

# 查询统计
_QUERY_STATS = {
    "total_queries": 0,
    "slow_queries": 0,
    "query_times": {}  # 查询 -> 平均执行时间
}

async def monitored_query(query: str, params: List = None):
    """
    带监控的查询函数
    
    参数:
        query: SQL查询
        params: 查询参数
    
    返回:
        查询结果
    """
    if _POOL is None:
        raise ValueError("连接池未初始化")
    
    params = params or []
    
    # 更新统计信息
    global _QUERY_STATS
    _QUERY_STATS["total_queries"] += 1
    
    # 执行查询并计时
    start_time = time.time()
    async with _POOL.acquire() as conn:
        result = await conn.fetch(query, *params)
    
    query_time = time.time() - start_time
    
    # 记录查询时间
    query_key = query.strip()
    if query_key in _QUERY_STATS["query_times"]:
        # 计算移动平均值
        old_avg = _QUERY_STATS["query_times"][query_key]["avg_time"]
        count = _QUERY_STATS["query_times"][query_key]["count"]
        new_avg = (old_avg * count + query_time) / (count + 1)
        
        _QUERY_STATS["query_times"][query_key] = {
            "avg_time": new_avg,
            "count": count + 1,
            "last_time": query_time
        }
    else:
        _QUERY_STATS["query_times"][query_key] = {
            "avg_time": query_time,
            "count": 1,
            "last_time": query_time
        }
    
    # 记录慢查询
    if query_time > SLOW_QUERY_THRESHOLD:
        _QUERY_STATS["slow_queries"] += 1
        logger.warning(f"慢查询 ({query_time:.2f}s): {query}")
    
    return result

def get_query_stats():
    """获取查询统计信息"""
    return _QUERY_STATS

def reset_query_stats():
    """重置查询统计信息"""
    global _QUERY_STATS
    _QUERY_STATS = {
        "total_queries": 0,
        "slow_queries": 0,
        "query_times": {}
    }


# 物化视图
MATERIALIZED_VIEWS = {
    "create_user_stats_view": """
    CREATE MATERIALIZED VIEW IF NOT EXISTS xiuxian_user_stats AS
    SELECT 
        level,
        COUNT(*) as user_count,
        AVG(exp) as avg_exp,
        MAX(exp) as max_exp,
        MIN(exp) as min_exp,
        AVG(power) as avg_power
    FROM xiuxian_user
    GROUP BY level
    WITH DATA;
    
    CREATE UNIQUE INDEX IF NOT EXISTS idx_xiuxian_user_stats_level ON xiuxian_user_stats(level);
    """,
    
    "create_top_users_view": """
    CREATE MATERIALIZED VIEW IF NOT EXISTS xiuxian_top_users AS
    SELECT 
        user_id, 
        user_name, 
        level, 
        exp, 
        power,
        ROW_NUMBER() OVER (ORDER BY exp DESC) as rank
    FROM xiuxian_user
    WITH DATA;
    
    CREATE UNIQUE INDEX IF NOT EXISTS idx_xiuxian_top_users_rank ON xiuxian_top_users(rank);
    CREATE INDEX IF NOT EXISTS idx_xiuxian_top_users_user_id ON xiuxian_top_users(user_id);
    """
}

async def create_materialized_views():
    """创建物化视图"""
    if _POOL is None:
        raise ValueError("连接池未初始化")
        
    async with _POOL.acquire() as conn:
        for view_sql in MATERIALIZED_VIEWS.values():
            await conn.execute(view_sql)

async def refresh_materialized_view(view_name: str):
    """刷新物化视图"""
    if _POOL is None:
        raise ValueError("连接池未初始化")
        
    async with _POOL.acquire() as conn:
        await conn.execute(f"REFRESH MATERIALIZED VIEW {view_name}")

# 常用视图查询
async def get_user_stats():
    """获取用户统计数据"""
    query = "SELECT * FROM xiuxian_user_stats ORDER BY level"
    async with _POOL.acquire() as conn:
        return await conn.fetch(query)

async def get_user_rank(user_id: int):
    """获取用户排名"""
    query = "SELECT rank FROM xiuxian_top_users WHERE user_id = $1"
    async with _POOL.acquire() as conn:
        result = await conn.fetchval(query, user_id)
        return result 