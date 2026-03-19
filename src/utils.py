"""
Utility functions for the geopolitical risk analysis project
"""

import numpy as np
import pandas as pd
from typing import Tuple, Optional
import warnings
warnings.filterwarnings('ignore')


def log_returns(prices: pd.Series) -> pd.Series:
    """
    Tính lợi suất logarit từ chuỗi giá
    
    Parameters:
    -----------
    prices : pd.Series
        Chuỗi giá đóng cửa
        
    Returns:
    --------
    pd.Series
        Chuỗi lợi suất logarit
    """
    return np.log(prices / prices.shift(1)).dropna()


def first_differences(series: pd.Series) -> pd.Series:
    """
    Tính sai phân bậc 1 (first differences)
    
    Parameters:
    -----------
    series : pd.Series
        Chuỗi thời gian gốc
        
    Returns:
    --------
    pd.Series
        Chuỗi sai phân bậc 1
    """
    return series.diff().dropna()


def align_dataframes(*dfs: pd.DataFrame) -> Tuple[pd.DataFrame, ...]:
    """
    Căn chỉnh các DataFrame theo index chung
    
    Parameters:
    -----------
    *dfs : pd.DataFrame
        Các DataFrame cần căn chỉnh
        
    Returns:
    --------
    Tuple[pd.DataFrame, ...]
        Các DataFrame đã được căn chỉnh
    """
    common_index = dfs[0].index
    for df in dfs[1:]:
        common_index = common_index.intersection(df.index)
    
    return tuple(df.loc[common_index] for df in dfs)


def remove_outliers(series: pd.Series, method: str = 'iqr', factor: float = 3.0) -> pd.Series:
    """
    Loại bỏ outliers sử dụng phương pháp IQR hoặc Z-score
    
    Parameters:
    -----------
    series : pd.Series
        Chuỗi dữ liệu
    method : str
        Phương pháp: 'iqr' hoặc 'zscore'
    factor : float
        Hệ số nhân cho ngưỡng (default: 3.0)
        
    Returns:
    --------
    pd.Series
        Chuỗi đã loại bỏ outliers
    """
    if method == 'iqr':
        Q1 = series.quantile(0.25)
        Q3 = series.quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - factor * IQR
        upper_bound = Q3 + factor * IQR
        return series[(series >= lower_bound) & (series <= upper_bound)]
    
    elif method == 'zscore':
        z_scores = np.abs((series - series.mean()) / series.std())
        return series[z_scores < factor]
    
    else:
        raise ValueError(f"Unknown method: {method}")


def check_stationarity(series: pd.Series, test: str = 'adf') -> dict:
    """
    Kiểm tra tính dừng của chuỗi thời gian
    
    Parameters:
    -----------
    series : pd.Series
        Chuỗi cần kiểm tra
    test : str
        Loại test: 'adf' (Augmented Dickey-Fuller)
        
    Returns:
    --------
    dict
        Kết quả test
    """
    from statsmodels.tsa.stattools import adfuller
    
    if test == 'adf':
        result = adfuller(series.dropna())
        return {
            'adf_statistic': result[0],
            'p_value': result[1],
            'critical_values': result[4],
            'is_stationary': result[1] < 0.05
        }
    else:
        raise ValueError(f"Unknown test: {test}")


def create_lag_matrix(data: pd.DataFrame, max_lags: int = 5) -> pd.DataFrame:
    """
    Tạo ma trận lag cho phân tích lead-lag
    
    Parameters:
    -----------
    data : pd.DataFrame
        Dữ liệu gốc
    max_lags : int
        Số lag tối đa
        
    Returns:
    --------
    pd.DataFrame
        Ma trận với các cột lag
    """
    lagged_data = data.copy()
    for col in data.columns:
        for lag in range(1, max_lags + 1):
            lagged_data[f'{col}_lag{lag}'] = data[col].shift(lag)
    
    return lagged_data.dropna()

