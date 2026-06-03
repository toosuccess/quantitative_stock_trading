"""
个人专属交易系统 - FastAPI入口
"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from .api.routes import router
from app.database_config import MYSQL_CONFIG
import pymysql

scheduler = AsyncIOScheduler()

def init_database():
    """初始化数据库，确保必要字段存在"""
    print("检查数据库结构...")
    try:
        conn = pymysql.connect(**MYSQL_CONFIG)
        cursor = conn.cursor()
        
        # 检查 account_info 表是否有 initial_assets 字段
        cursor.execute("SHOW COLUMNS FROM account_info LIKE 'initial_assets'")
        result = cursor.fetchone()
        
        if not result:
            print("添加 initial_assets 字段...")
            try:
                cursor.execute("ALTER TABLE account_info ADD COLUMN initial_assets DECIMAL(20,2) DEFAULT 0.00 COMMENT '初始资金'")
                print("✓ initial_assets 字段添加成功")
            except Exception as e:
                print(f"  字段可能已存在: {e}")
            
            # 初始化 initial_assets 为当前 total_assets
            cursor.execute("SELECT account_id, total_assets FROM account_info")
            accounts = cursor.fetchall()
            for acc in accounts:
                if acc[1] and float(acc[1]) > 0:
                    cursor.execute(
                        "UPDATE account_info SET initial_assets = %s WHERE account_id = %s",
                        (acc[1], acc[0])
                    )
            conn.commit()
            print("✓ 初始化 initial_assets 完成")
        else:
            print("✓ initial_assets 字段已存在")
        
        conn.close()
    except Exception as e:
        print(f"数据库检查失败: {e}")

def init_scheduler():
    """初始化定时任务"""
    from app.services.price_updater import update_stock_prices
    from app.services.news_fetcher import update_all_news

    # 每5分钟更新股票价格
    scheduler.add_job(
        update_stock_prices,
        'interval',
        minutes=5,
        id='update_stock_prices',
        name='更新股票价格',
        replace_existing=True,
        max_instances=1
    )

    # 每30分钟更新新闻动态
    scheduler.add_job(
        update_all_news,
        'interval',
        minutes=30,
        id='update_market_news',
        name='更新市场新闻动态',
        replace_existing=True,
        max_instances=1
    )

    scheduler.start()
    print("✓ 定时任务已启动:")
    print("  - 股票价格更新: 每5分钟")
    print("  - 新闻动态更新: 每30分钟")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    print("初始化数据库...")
    init_database()
    print("启动定时任务：每5分钟更新股票价格...")
    init_scheduler()
    yield
    print("关闭定时任务...")
    scheduler.shutdown()

app = FastAPI(
    title="个人专属交易系统",
    description="去情绪化、可量化、可追溯、可重复、可迭代的交易系统",
    version="1.0.0",
    lifespan=lifespan
)

CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*').split(',')

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1")


@app.get("/")
async def root():
    return {"message": "个人专属交易系统API", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.get("/scheduler/status")
async def scheduler_status():
    """查看定时任务状态"""
    jobs = scheduler.get_jobs()
    return {
        "running": scheduler.running,
        "jobs": [{"id": job.id, "name": job.name, "next_run": str(job.next_run_time)} for job in jobs]
    }


@app.post("/scheduler/trigger/price-update")
async def trigger_price_update():
    """手动触发价格更新"""
    from app.services.price_updater import update_stock_prices
    import threading
    
    def run_update():
        try:
            update_stock_prices()
        except Exception as e:
            print(f"手动触发价格更新失败: {e}")
    
    thread = threading.Thread(target=run_update)
    thread.start()
    
    return {"message": "价格更新任务已触发", "status": "running"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
