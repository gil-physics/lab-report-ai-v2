from fastapi import FastAPI
import os
import sys

# 경로 문제 진단을 위한 정보 수집
current_dir = os.path.dirname(os.path.abspath(__file__))
sys_path = sys.path

app = FastAPI()

@app.get("/api/health")
def health_check():
    return {
        "status": "ok",
        "message": "Python is running!",
        "debug": {
            "current_dir": current_dir,
            "sys_path_head": sys_path[0] if sys_path else "empty"
        }
    }

# Vercel ASGI Handler (Native Support)
# Mangum 대신 Vercel 네이티브 호환 핸들러 사용
async def handler(scope, receive, send):
    await app(scope, receive, send)
