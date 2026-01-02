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

class DataPayload(BaseModel):
    x: List[float]
    y: List[float]

class AnalysisOptions(BaseModel):
    remove_outliers: Optional[bool] = False
    manual_model: Optional[str] = None
    return_chart_data: Optional[bool] = False

class AnalysisRequest(BaseModel):
    data: DataPayload
    options: Optional[AnalysisOptions] = None

@app.post("/")
async def analyze(request: AnalysisRequest):
    try:
        x_data = request.data.x
        y_data = request.data.y
        
        if len(x_data) != len(y_data):
            raise HTTPException(status_code=400, detail="X and Y data must have the same length")
        
        if len(x_data) < 3:
            raise HTTPException(status_code=400, detail="At least 3 data points are required")
        
        # Convert to numpy arrays
        import numpy as np
        x_array = np.array(x_data)
        y_array = np.array(y_data)
        
        # Call smart curve fitting
        result = smart_curve_fitting(x_array, y_array)
        
        if result is None:
            raise HTTPException(status_code=500, detail="Curve fitting failed")
        
        # Calculate y_predicted for chart
        if request.options and request.options.return_chart_data:
            y_pred = result['func'](x_array, *result['params'])
            result['y_predicted'] = y_pred.tolist()
        
        # Calculate residuals
        y_pred = result['func'](x_array, *result['params'])
        residuals = y_array - y_pred
        
        return {
            "status": "success",
            "best_model": {
                "name": result['name'],
                "model_key": result['model_key'],
                "r_squared": result['r_squared'],
                "adj_r_squared": result.get('adj_r_squared', result['r_squared']),
                "aic": result.get('aic', 0),
                "equation": result['equation'],
                "latex": result.get('equation', ''),  # You may want to add proper LaTeX conversion
                "parameters": result['params'],
                "y_predicted": y_pred.tolist() if request.options and request.options.return_chart_data else None
            },
            "residuals": residuals.tolist(),
            "data_info": {
                "original_count": len(x_data),
                "used_count": len(x_data),
                "outliers_removed": 0
            },
            "alternative_models": result.get('all_results', [])
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Vercel Serverless Function handler
from mangum import Mangum
handler = Mangum(app, lifespan="off")
