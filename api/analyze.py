from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import sys
import os
import logging

# ---------------------------------------------------------
# [핵심 수정] Vercel 경로 문제 해결 코드
# ---------------------------------------------------------
# 1. 현재 파일(analyze.py)이 위치한 폴더(api 폴더)의 절대 경로를 구합니다.
current_dir = os.path.dirname(os.path.abspath(__file__))

# 2. 시스템 경로(sys.path)의 맨 앞(0번째)에 이 폴더를 강제로 추가합니다.
#    이렇게 해야 파이썬이 바로 옆에 있는 'utils' 폴더를 볼 수 있습니다.
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# 3. 이제 안전하게 utils를 불러올 수 있습니다.
from utils.curve_fitting import smart_curve_fitting
# ---------------------------------------------------------

# 로깅 설정 (기존과 동일)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ▼▼▼ 이 아래부터는 기존의 app = FastAPI() 코드가 이어지면 됩니다 ▼▼▼

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

@app.post("/api/analyze")
@app.post("/")
async def analyze(request: AnalysisRequest):
    try:
        logger.info("📊 Analysis request received")
        x_data = request.data.x
        y_data = request.data.y
        
        logger.info(f"Data received: X={len(x_data)} points, Y={len(y_data)} points")
        
        # 데이터 길이 검증
        if len(x_data) != len(y_data):
            logger.warning(f"Data length mismatch: X={len(x_data)}, Y={len(y_data)}")
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "데이터 길이 불일치",
                    "message": f"X축 데이터({len(x_data)}개)와 Y축 데이터({len(y_data)}개)의 개수가 다릅니다.",
                    "solution": "CSV 파일에서 빈 셀을 제거하거나 데이터를 동일한 개수로 맞춰주세요."
                }
            )
        
        # 최소 데이터 포인트 검증
        if len(x_data) < 3:
            logger.warning(f"Insufficient data points: {len(x_data)}")
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "데이터 부족",
                    "message": f"회귀 분석을 위해서는 최소 3개 이상의 데이터가 필요합니다. (현재: {len(x_data)}개)",
                    "solution": "더 많은 데이터를 추가하거나 측정값을 늘려주세요."
                }
            )
        
        # Convert to numpy arrays
        import numpy as np
        try:
            x_array = np.array(x_data, dtype=float)
            y_array = np.array(y_data, dtype=float)
        except (ValueError, TypeError) as e:
            logger.error(f"Data conversion failed: {str(e)}")
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "잘못된 데이터 형식",
                    "message": "데이터에 숫자가 아닌 값이 포함되어 있습니다.",
                    "solution": "CSV 파일에서 텍스트나 특수문자를 제거하고 숫자만 포함되도록 해주세요."
                }
            )
        
        # NaN/Inf 체크
        if np.any(np.isnan(x_array)) or np.any(np.isnan(y_array)):
            logger.warning("NaN values detected in data")
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "유효하지 않은 데이터",
                    "message": "데이터에 빈 값(NaN)이 포함되어 있습니다.",
                    "solution": "CSV 파일에서 빈 셀을 채우거나 해당 행을 삭제해주세요."
                }
            )
        
        if np.any(np.isinf(x_array)) or np.any(np.isinf(y_array)):
            logger.warning("Infinite values detected in data")
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "극단적인 값 발견",
                    "message": "데이터에 무한대 값이 포함되어 있습니다.",
                    "solution": "데이터 범위를 확인하고 극단적으로 큰 값을 제거해주세요."
                }
            )
        
        logger.info(f"Data validation passed. Range: X=[{x_array.min():.2f}, {x_array.max():.2f}], Y=[{y_array.min():.2f}, {y_array.max():.2f}]")
        
        # Call smart curve fitting
        logger.info("Starting curve fitting...")
        result = smart_curve_fitting(x_array, y_array)
        
        if result is None:
            logger.error("Curve fitting returned None - no suitable model found")
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "회귀 분석 실패",
                    "message": "데이터에 적합한 수학 모델을 찾을 수 없습니다.",
                    "solution": "데이터의 패턴을 확인하거나 이상치를 제거한 후 다시 시도해주세요."
                }
            )
        
        logger.info(f"✅ Best model found: {result['model_key']} (R²={result['r_squared']:.4f})")
        
        # Calculate y_predicted for chart
        if request.options and request.options.return_chart_data:
            y_pred = result['func'](x_array, *result['params'])
            result['y_predicted'] = y_pred.tolist()
        
        # Calculate residuals
        y_pred = result['func'](x_array, *result['params'])
        residuals = y_array - y_pred
        
        logger.info(f"Analysis completed successfully. Residuals: mean={residuals.mean():.4f}, std={residuals.std():.4f}")
        
        return {
            "status": "success",
            "best_model": {
                "name": result['name'],
                "model_key": result['model_key'],
                "r_squared": result['r_squared'],
                "adj_r_squared": result.get('adj_r_squared', result['r_squared']),
                "aic": result.get('aic', 0),
                "equation": result['equation'],
                "latex": result.get('equation', ''),
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
        
    except HTTPException:
        # HTTPException은 그대로 전달 (이미 포맷팅됨)
        raise
    except Exception as e:
        # 예상치 못한 에러
        logger.error(f"❌ Unexpected error: {type(e).__name__}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "서버 내부 오류",
                "message": f"예상치 못한 오류가 발생했습니다: {type(e).__name__}",
                "solution": "잠시 후 다시 시도해주세요. 문제가 계속되면 관리자에게 문의해주세요.",
                "debug_info": str(e)
            }
        )


# Vercel Serverless Function handler
from mangum import Mangum
handler = Mangum(app)

