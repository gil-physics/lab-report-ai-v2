import sys
import os
import traceback

# 1. 가장 기초적인 것만 먼저 import 합니다. (절대 실패하지 않음)
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from mangum import Mangum

app = FastAPI()

# CORS 설정 (이건 무조건 실행되어야 함)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. 에러 보관함
startup_error = None

# 3. [위험 구간] 무거운 라이브러리와 내 파일들을 "조심스럽게" 불러옵니다.
try:
    # 경로 설정 (아까 했던 것)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(current_dir)
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    if root_dir not in sys.path:
        sys.path.insert(0, root_dir)

    # 🚨 여기서 에러가 나면 catch 블록으로 점프합니다!
    import numpy as np
    import pandas as pd
    from scipy.optimize import curve_fit
    from utils.curve_fitting import smart_curve_fitting
    
    # 성공하면 플래그 설정
    print("✅ All imports successful")

except Exception as e:
    # 에러가 나면 서버를 죽이지 말고, 에러 내용을 변수에 담아둡니다.
    startup_error = {
        "error_type": type(e).__name__,
        "message": str(e),
        "traceback": traceback.format_exc(),
        "location": "Module Import / Startup Phase"
    }
    print(f"❌ Startup Error: {e}")


# 4. 요청 모델 정의 (이건 에러 안 남)
class AnalysisRequest(BaseModel):
    data: dict
    options: dict = None


# 5. 엔드포인트 정의
@app.post("/api/analyze")
@app.post("/")
async def analyze(request: AnalysisRequest):
    # 🕵️‍♂️ 사용자가 접속했을 때, 아까 담아둔 에러가 있다면 바로 보여줍니다.
    if startup_error:
        return {
            "status": "error",
            "detail": {
                "error": "서버 초기화 실패 (Startup Failed)",
                "message": startup_error["message"],
                "solution": "requirements.txt나 파일 경로를 확인하세요.",
                "debug_info": startup_error["traceback"]
            }
        }
    
    # 에러가 없다면 정상 로직 실행 (지금은 테스트를 위해 간단한 응답만)
    return {
        "status": "success", 
        "message": "서버가 정상적으로 라이브러리를 로드했습니다!", 
        "data_received": len(request.data.get('x', []))
    }

# Vercel용 핸들러
handler = Mangum(app)
