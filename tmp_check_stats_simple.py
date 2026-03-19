import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

# Load data
data = pd.read_csv('data/raw/data.csv', index_col=0, parse_dates=True, dayfirst=True)
if not isinstance(data.index, pd.DatetimeIndex):
    data.index = pd.to_datetime(data.index, dayfirst=True, format='mixed')

# Filter
data = data[(data.index >= '2015-01-01') & (data.index <= '2025-11-11')]
data = data[data.index.dayofweek < 5]

print("="*80)
print("BẢNG 3.1: THỐNG KÊ MÔ TẢ TỶ SUẤT SINH LỢI")
print("="*80)
print(f"{'Tài sản':<10} {'Mean (%)':<12} {'Std Dev (%)':<15} {'Min (%)':<12} {'Max (%)':<12} {'Kurtosis':<12} {'Skewness':<12}")
print("-"*80)

for col in ['BTC', 'GOLD', 'OIL']:
    if col not in data.columns:
        continue
    
    prices = data[col].dropna()
    prices = prices[prices > 0]
    ret = np.log(prices / prices.shift(1)).dropna()
    
    if len(ret) == 0:
        continue
    
    mean_pct = ret.mean() * 100
    std_pct = ret.std() * 100
    min_pct = ret.min() * 100
    max_pct = ret.max() * 100
    kurtosis = ret.kurtosis()
    skewness = ret.skew()
    
    print(f"{col:<10} {mean_pct:>11.4f}  {std_pct:>13.4f}  {min_pct:>11.2f}  {max_pct:>11.2f}  {kurtosis:>11.2f}  {skewness:>11.4f}")

print("\n" + "="*80)
print("SO SÁNH VỚI BẢNG 3.1 TRONG CHAPTER 3:")
print("="*80)

chapter3 = {
    'BTC': {'mean': 0.1883, 'std': 4.1873, 'min': -46.47, 'max': 22.51, 'kurtosis': 10.37, 'skewness': -0.6671},
    'GOLD': {'mean': 0.0436, 'std': 0.9557, 'min': -5.91, 'max': 5.78, 'kurtosis': 3.84, 'skewness': -0.1983},
    'OIL': {'mean': 0.0619, 'std': 2.8485, 'min': -28.22, 'max': 31.96, 'kurtosis': 23.18, 'skewness': 0.1282}
}

for col in ['BTC', 'GOLD', 'OIL']:
    if col not in data.columns:
        continue
    
    prices = data[col].dropna()
    prices = prices[prices > 0]
    ret = np.log(prices / prices.shift(1)).dropna()
    
    if len(ret) == 0:
        continue
    
    mean_pct = ret.mean() * 100
    std_pct = ret.std() * 100
    min_pct = ret.min() * 100
    max_pct = ret.max() * 100
    kurtosis = ret.kurtosis()
    skewness = ret.skew()
    
    ch3 = chapter3[col]
    
    print(f"\n{col}:")
    print(f"  Mean:    {mean_pct:.4f}% (Chapter 3: {ch3['mean']:.4f}%) - {'✓' if abs(mean_pct - ch3['mean']) < 0.01 else '✗'}")
    print(f"  Std:     {std_pct:.4f}% (Chapter 3: {ch3['std']:.4f}%) - {'✓' if abs(std_pct - ch3['std']) < 0.01 else '✗'}")
    print(f"  Min:     {min_pct:.2f}% (Chapter 3: {ch3['min']:.2f}%) - {'✓' if abs(min_pct - ch3['min']) < 0.1 else '✗'}")
    print(f"  Max:     {max_pct:.2f}% (Chapter 3: {ch3['max']:.2f}%) - {'✓' if abs(max_pct - ch3['max']) < 0.1 else '✗'}")
    print(f"  Kurtosis: {kurtosis:.2f} (Chapter 3: {ch3['kurtosis']:.2f}) - {'✓' if abs(kurtosis - ch3['kurtosis']) < 0.5 else '✗'}")
    print(f"  Skewness: {skewness:.4f} (Chapter 3: {ch3['skewness']:.4f}) - {'✓' if abs(skewness - ch3['skewness']) < 0.1 else '✗'}")




