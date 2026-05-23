from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional
from engine import HuntingEngine
from pathlib import Path
import uvicorn
import os

app = FastAPI(title="认知狩猎 API")

# 从 VERSION 文件读取项目版本号
def _read_version() -> str:
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(base_dir, "VERSION")) as f:
            return f.read().strip()
    except Exception:
        return "0.0.0"

__version__ = _read_version()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

engine = HuntingEngine()

# 启动后台 iCloud 同步（每 5 分钟）
engine.start_icloud_sync(interval=300)

class CaptureRequest(BaseModel):
    content: str
    tags: Optional[List[str]] = []
    folder: str = "Inbox"

class ExchangeRequest(BaseModel):
    amount: float

class ContentVerifyRequest(BaseModel):
    url: str

class ReviewSubmitRequest(BaseModel):
    file_path: str
    insight: str

class ExchangePathRequest(BaseModel):
    path: str

@app.get("/api/version")
async def get_version():
    """返回项目版本号"""
    return {"version": __version__}

@app.post("/api/capture")
async def capture(request: CaptureRequest):
    try:
        result = engine.process_daily_capture(
            content=request.content,
            tags=request.tags,
            folder=request.folder
        )
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/status")
async def get_status():
    try:
        return engine.get_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/content/verify")
async def content_verify(request: ContentVerifyRequest):
    try:
        result = engine.process_publish(url=request.url)
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ========== 兑换相关 API ==========

@app.post("/api/exchange/path")
async def set_exchange_path(request: ExchangePathRequest):
    try:
        result = engine.set_exchange_path(path=request.path)
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/exchange/coupon")
async def exchange_coupon(request: ExchangeRequest):
    try:
        result = engine.exchange_coupon(amount=request.amount)
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/exchange/fund")
async def exchange_fund(request: ExchangeRequest):
    try:
        result = engine.exchange_fund(amount=request.amount)
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ========== 回顾与战报 API ==========

@app.get("/api/projection")
async def get_projection(days: int = 180):
    """长期推演计算，基于当前速度预测未来状态"""
    try:
        result = engine.calculate_long_term_projection(days=days)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/review/weekly")
async def weekly_review():
    """生成上周素材文件，返回文件路径和内容预览"""
    try:
        result = engine.generate_weekly_review()
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/review/weekly/submit")
async def weekly_review_submit(request: ReviewSubmitRequest):
    """提交周回顾总结，写入素材文件并添加 #周回顾 标签，发放星点"""
    try:
        result = engine.submit_weekly_review(
            file_path=request.file_path,
            insight=request.insight
        )
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/report/monthly")
async def monthly_report():
    """生成上月素材文件，返回文件路径和内容预览"""
    try:
        result = engine.generate_monthly_report()
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/report/monthly/submit")
async def monthly_report_submit(request: ReviewSubmitRequest):
    """提交月度战报总结，写入素材文件并添加 #月回顾 标签，发放星点"""
    try:
        result = engine.submit_monthly_report(
            file_path=request.file_path,
            insight=request.insight
        )
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/report/monthly/draft")
async def get_monthly_draft():
    try:
        return engine.get_monthly_draft()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ========== 标签相关 API ==========

@app.get("/api/tags")
async def get_tags():
    """获取标签云数据"""
    try:
        return engine.get_tag_cloud_data()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/notes/by-tag")
async def get_notes_by_tag(tag: str):
    """按标签查询笔记摘要"""
    try:
        return engine.get_notes_by_tag(tag=tag)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ========== 勋章相关 API ==========

@app.get("/api/medals")
async def get_medals():
    """获取所有勋章定义和状态"""
    try:
        return {"medals": engine.get_all_medals()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class MedalCheckRequest(BaseModel):
    trigger_type: Optional[str] = None

@app.post("/api/medals/check")
async def check_medals(request: MedalCheckRequest = None):
    """触发勋章检查（通常由系统自动调用，也可手动触发）"""
    try:
        trigger_type = request.trigger_type if request else None
        newly_earned = engine._check_medals(trigger_type=trigger_type)
        return {
            "checked": len(engine.get_all_medals()),
            "newly_earned": newly_earned
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ========== 赛季相关 API ==========

@app.get("/api/season/current")
async def get_current_season():
    """获取当前赛季信息"""
    try:
        return engine.get_current_season()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/season/history")
async def get_season_history():
    """获取赛季历史记录"""
    try:
        return {"history": engine.get_season_history()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/income/history")
async def get_income_history():
    """获取星点获取记录"""
    try:
        return {"records": engine.get_star_income_history()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/season/check")
async def check_season_end():
    """检查赛季是否结束并自动开启新赛季"""
    try:
        result = engine.check_season_end()
        if result:
            return {
                "season_changed": True,
                "old_season": result["old_season"],
                "new_season": result["new_season"]
            }
        return {"season_changed": False}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/season/start")
async def start_new_season():
    """手动开启新赛季"""
    try:
        result = engine.start_new_season()
        return {
            "old_season": result["old_season"],
            "new_season": result["new_season"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ========== 配置相关 API ==========

@app.get("/api/config")
async def get_config():
    try:
        return engine.get_config()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/config")
async def update_config(config: dict):
    try:
        return engine.update_config(config)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ========== 备份与同步 API ==========

@app.post("/api/backup")
async def backup_data():
    """备份 inspire 数据目录"""
    try:
        result = engine.backup()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/backup/list")
async def list_backups():
    """列出所有备份"""
    try:
        backup_root = Path.home() / "Documents" / "hunterhunter_backups"
        if not backup_root.exists():
            return {"backups": []}
        backups = sorted(backup_root.glob("inspire_backup_*"), reverse=True)
        return {
            "backups": [
                {
                    "name": b.name,
                    "path": str(b),
                    "size": sum(f.stat().st_size for f in b.rglob("*") if f.is_file()),
                    "file_count": sum(1 for _ in b.rglob("*") if _.is_file())
                }
                for b in backups
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/sync/icloud")
async def sync_to_icloud():
    """手动触发同步：本地 → iCloud Obsidian Vault（只写不删）"""
    try:
        result = engine.sync_to_icloud()
        if not result["success"]:
            raise HTTPException(status_code=500, detail=result.get("error", "同步失败"))
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ========== 调试相关 API ==========

@app.post("/api/reset")
async def reset_state():
    """调试用：重置游戏状态到初始值，清理回顾/战报素材文件"""
    try:
        return engine.reset_all()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/reset/daily")
async def reset_daily_flags():
    """重置每日/每周/每月标志"""
    try:
        engine.reset_daily_flags()
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if not os.path.exists("static"):
    os.makedirs("static")

app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8003)