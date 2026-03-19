import pandas as pd
import numpy as np

# Load data
print("Loading data...")
data = pd.read_csv('data/raw/data.csv', index_col=0, parse_dates=True, dayfirst=True)
print(f"Data shape: {data.shape}")
print(f"Date range: {data.index.min()} to {data.index.max()}")
print(f"Columns: {data.columns.tolist()}")

# Ensure index is DatetimeIndex
if not isinstance(data.index, pd.DatetimeIndex):
    data.index = pd.to_datetime(data.index, dayfirst=True, format='mixed')

# Filter date range
data = data[(data.index >= '2015-01-01') & (data.index <= '2025-11-11')]
print(f"\nAfter date filter: {data.shape}")

# Filter weekdays
if isinstance(data.index, pd.DatetimeIndex):
    data = data[data.index.dayofweek < 5]
    print(f"After weekday filter: {data.shape}")

# Calculate log returns for each asset
print("\n" + "="*80)
print("THỐNG KÊ MÔ TẢ TỶ SUẤT SINH LỢI")
print("="*80)

for col in ['BTC', 'GOLD', 'OIL']:
    if col not in data.columns:
        print(f"\n{col}: Column not found!")
        continue
    
    # Get price series
    prices = data[col].dropna()
    print(f"\n{col}:")
    print(f"  Total observations: {len(prices)}")
    print(f"  Missing values: {prices.isna().sum()}")
    
    if len(prices) < 2:
        print(f"  ERROR: Not enough data!")
        continue
    
    # Calculate log returns (handle zeros and negatives)
    prices_clean = prices[prices > 0]  # Remove zeros and negatives
    ret = np.log(prices_clean / prices_clean.shift(1)).dropna()
    
    if len(ret) == 0:
        print(f"  ERROR: No valid returns calculated!")
        continue
    
    # Calculate statistics
    mean_pct = ret.mean() * 100
    std_pct = ret.std() * 100
    min_pct = ret.min() * 100
    max_pct = ret.max() * 100
    kurtosis = ret.kurtosis()
    skewness = ret.skew()
    
    print(f"  Mean: {mean_pct:.4f}%")
    print(f"  Std Dev: {std_pct:.4f}%")
    print(f"  Min: {min_pct:.2f}%")
    print(f"  Max: {max_pct:.2f}%")
    print(f"  Kurtosis: {kurtosis:.2f}")
    print(f"  Skewness: {skewness:.4f}")
    
    # Compare with Chapter 3
    print(f"\n  So sánh với Bảng 3.1:")
    chapter3_values = {
        'BTC': {'mean': 0.1883, 'std': 4.1873, 'min': -46.47, 'max': 22.51, 'kurtosis': 10.37, 'skewness': -0.6671},
        'GOLD': {'mean': 0.0436, 'std': 0.9557, 'min': -5.91, 'max': 5.78, 'kurtosis': 3.84, 'skewness': -0.1983},
        'OIL': {'mean': 0.0619, 'std': 2.8485, 'min': -28.22, 'max': 31.96, 'kurtosis': 23.18, 'skewness': 0.1282}
    }
    
    if col in chapter3_values:
        ch3 = chapter3_values[col]
        print(f"    Mean: {mean_pct:.4f}% vs {ch3['mean']:.4f}% (diff: {abs(mean_pct - ch3['mean']):.4f}%)")
        print(f"    Std: {std_pct:.4f}% vs {ch3['std']:.4f}% (diff: {abs(std_pct - ch3['std']):.4f}%)")
        print(f"    Min: {min_pct:.2f}% vs {ch3['min']:.2f}% (diff: {abs(min_pct - ch3['min']):.2f}%)")
        print(f"    Max: {max_pct:.2f}% vs {ch3['max']:.2f}% (diff: {abs(max_pct - ch3['max']):.2f}%)")
        print(f"    Kurtosis: {kurtosis:.2f} vs {ch3['kurtosis']:.2f} (diff: {abs(kurtosis - ch3['kurtosis']):.2f})")
        print(f"    Skewness: {skewness:.4f} vs {ch3['skewness']:.4f} (diff: {abs(skewness - ch3['skewness']):.4f})")

