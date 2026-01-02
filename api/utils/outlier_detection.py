"""
Outlier Detection Utilities
이상치 탐지 및 제거 기능
"""

import pandas as pd
import numpy as np

# ============================================
# 이상치 제거 방법
# ============================================

def remove_outliers_iqr(data, column, multiplier=1.5):
    """
    IQR(Interquartile Range) 방법으로 이상치 제거
    
    Parameters:
    - data: DataFrame
    - column: 이상치를 탐지할 컬럼명
    - multiplier: IQR 배수 (기본값: 1.5)
    
    Returns:
    - filtered_data: 이상치가 제거된 DataFrame
    - outliers_removed: 제거된 이상치 개수
    """
    if len(data) < 4:
        return data, 0
    
    Q1 = data[column].quantile(0.25)
    Q3 = data[column].quantile(0.75)
    IQR = Q3 - Q1
    
    lower_bound = Q1 - multiplier * IQR
    upper_bound = Q3 + multiplier * IQR
    
    filtered_data = data[
        (data[column] >= lower_bound) & 
        (data[column] <= upper_bound)
    ]
    
    outliers_removed = len(data) - len(filtered_data)
    
    return filtered_data, outliers_removed

def remove_outliers_zscore(data, column, threshold=3):
    """
    Z-Score 방법으로 이상치 제거
    
    Parameters:
    - data: DataFrame
    - column: 이상치를 탐지할 컬럼명
    - threshold: Z-Score 임계값 (기본값: 3)
    
    Returns:
    - filtered_data: 이상치가 제거된 DataFrame
    - outliers_removed: 제거된 이상치 개수
    """
    if len(data) < 2:
        return data, 0
    
    mean = data[column].mean()
    std = data[column].std()
    
    if std == 0:
        return data, 0
    
    z_scores = np.abs((data[column] - mean) / std)
    filtered_data = data[z_scores < threshold]
    
    outliers_removed = len(data) - len(filtered_data)
    
    return filtered_data, outliers_removed

def remove_outliers_percentile(data, column, lower_percentile=5, upper_percentile=95):
    """
    백분위수(Percentile) 방법으로 이상치 제거
    
    Parameters:
    - data: DataFrame
    - column: 이상치를 탐지할 컬럼명
    - lower_percentile: 하위 백분위수 (기본값: 5)
    - upper_percentile: 상위 백분위수 (기본값: 95)
    
    Returns:
    - filtered_data: 이상치가 제거된 DataFrame
    - outliers_removed: 제거된 이상치 개수
    """
    lower_bound = data[column].quantile(lower_percentile / 100)
    upper_bound = data[column].quantile(upper_percentile / 100)
    
    filtered_data = data[
        (data[column] >= lower_bound) & 
        (data[column] <= upper_bound)
    ]
    
    outliers_removed = len(data) - len(filtered_data)
    
    return filtered_data, outliers_removed

def remove_outliers_isolation_forest(data, column, contamination=0.1):
    """
    Isolation Forest 방법으로 이상치 제거 (고급)
    
    Parameters:
    - data: DataFrame
    - column: 이상치를 탐지할 컬럼명
    - contamination: 예상 이상치 비율 (기본값: 0.1)
    
    Returns:
    - filtered_data: 이상치가 제거된 DataFrame
    - outliers_removed: 제거된 이상치 개수
    
    Note: sklearn이 제거되어 IQR 방법으로 대체됩니다.
    """
    # sklearn 의존성 제거 - IQR로 대체
    return remove_outliers_iqr(data, column)

# ============================================
# 통합 함수
# ============================================

OUTLIER_METHODS = {
    'iqr': {
        'name': 'IQR 방법',
        'func': remove_outliers_iqr,
        'description': '사분위수 범위 기반 (통계적으로 안정적)'
    },
    'zscore': {
        'name': 'Z-Score 방법',
        'func': remove_outliers_zscore,
        'description': '표준편차 기반 (정규분포 가정)'
    },
    'percentile': {
        'name': '백분위수 방법',
        'func': remove_outliers_percentile,
        'description': '상하위 백분위 제거'
    },
    'isolation_forest': {
        'name': 'Isolation Forest',
        'func': remove_outliers_isolation_forest,
        'description': '머신러닝 기반 (고급)'
    }
}

def remove_outliers(data, column, method='iqr', **kwargs):
    """
    지정된 방법으로 이상치 제거
    
    Parameters:
    - data: DataFrame
    - column: 이상치를 탐지할 컬럼명
    - method: 방법 ('iqr', 'zscore', 'percentile', 'isolation_forest')
    - **kwargs: 각 방법별 추가 파라미터
    
    Returns:
    - filtered_data: 이상치가 제거된 DataFrame
    - outliers_removed: 제거된 이상치 개수
    """
    if method not in OUTLIER_METHODS:
        method = 'iqr'
    
    func = OUTLIER_METHODS[method]['func']
    return func(data, column, **kwargs)
