from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import sys
import os

# 현재 디렉토리를 sys.path에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.curve_fitting import smart_curve_fitting

app = FastAPI()

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AnalysisRequest(BaseModel):
    x: List[float]
    y: List[float]

@app.post("/api/analyze")
async def analyze(request: AnalysisRequest):
    try:
        x_data = request.x
        y_data = request.y
        
        if len(x_data) != len(y_data):
            raise HTTPException(status_code=400, detail="X and Y data must have the same length")
        
        if len(x_data) < 3:
            raise HTTPException(status_code=400, detail="At least 3 data points are required")
        
        result = smart_curve_fitting(x_data, y_data)
        
        if result is None:
            raise HTTPException(status_code=500, detail="Curve fitting failed")
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Vercel Serverless Function handler
from mangum import Mangum
handler = Mangum(app, lifespan="off")
