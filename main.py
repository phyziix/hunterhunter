from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional
from engine import HuntingEngine
import uvicorn
import os

app = FastAPI(title="认知狩猎 API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

engine = HuntingEngine()

class CaptureRequest(BaseModel):
    content: str
    tags: Optional[List[str]] = []
    folder: str = "Inbox"

class ExchangeRequest(BaseModel):
    type: str
    amount: float

class ContentVerifyRequest(BaseModel):
    url: str

class ReviewSubmitRequest(BaseModel):
    file_path: str
    insight: str

@app.post("/api/capture")
async def capture(request: CaptureRequest):
    try:
        result = engine.process_daily_capture(
            content=request.content,
            tags=request.tags,
            folder=request.folder
        )
        return result
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

@app.post("/api/exchange")
async def exchange(request: ExchangeRequest):
    try:
        result = engine.exchange(type_=request.type, amount=request.amount)
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        return result
    except HTTPException:
        raise
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

@app.post("/api/reset")
async def reset_state():
    """调试用：重置游戏状态到初始值，清理回顾/战报素材文件"""
    try:
        return engine.reset_all()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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

if not os.path.exists("static"):
    os.makedirs("static")

app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
