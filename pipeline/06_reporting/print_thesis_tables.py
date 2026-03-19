
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from src.preprocessing import DataPreprocessor

def print_descriptive_stats():
    print("="*80)
    print("BẢNG 3.1: THỐNG KÊ MÔ TẢ TỶ SUẤT SINH LỢI HÀNG NGÀY")
    print("="*80)
    
    # Load data
    preprocessor = DataPreprocessor()
    data = preprocessor.load_data('data/raw/data.csv')
    
    # Calculate log returns
    returns = pd.DataFrame()
    for asset in ['BTC', 'GOLD', 'OIL']:
        if asset in data.columns:
            returns[asset] = np.log(data[asset] / data[asset].shift(1))
    
    returns = returns.dropna()
    
    # Calculate stats
    stats = returns.describe().T
    stats['kurtosis'] = returns.kurtosis()
    stats['skewness'] = returns.skew()
    
    # Format and print
    print(f"{'Tài sản':<10} | {'Mean (%)':<10} | {'Std Dev (%)':<12} | {'Min (%)':<10} | {'Max (%)':<10} | {'Kurtosis':<10} | {'Skewness':<10}")
    print("-" * 90)
    
    for asset in stats.index:
        mean = stats.loc[asset, 'mean'] * 100
        std = stats.loc[asset, 'std'] * 100
        min_val = stats.loc[asset, 'min'] * 100
        max_val = stats.loc[asset, 'max'] * 100
        kurt = stats.loc[asset, 'kurtosis']
        skew = stats.loc[asset, 'skewness']
        
        print(f"{asset:<10} | {mean:10.4f} | {std:12.4f} | {min_val:10.2f} | {max_val:10.2f} | {kurt:10.2f} | {skew:10.4f}")
    print()

def print_top_events():
    print("="*80)
    print("BẢNG 3.2: TOP 5 SỰ KIỆN TÁC ĐỘNG MẠNH NHẤT (THEO TỪNG TÀI SẢN)")
    print("="*80)
    
    try:
        # Load from analysis output (or re-run logic if needed, here we simulate reading from previous known output logic)
        # Better to read from events_complete.csv and sort
        df = pd.read_csv('results/events_complete.csv')
        
        for asset in ['BTC', 'GOLD', 'OIL']:
            col = f'{asset}_CAR'
            if col not in df.columns:
                continue
                
            print(f"\n--- {asset} ---")
            
            # Top 5 Increases
            top_increase = df.nlargest(5, col)
            print("Top 5 Tăng giá mạnh nhất:")
            print(f"{'Ngày':<12} | {'CAR (%)':<10} | {'Sự kiện':<40}")
            print("-" * 70)
            for _, row in top_increase.iterrows():
                car = row[col] * 100
                event_name = str(row.get('Event_Name', 'N/A'))[:38]
                # Try both date formats
                date = str(row.get('date', row.get('Date', 'N/A')))[:10]
                print(f"{date:<12} | {car:+10.2f} | {event_name:<40}")
            
            # Top 5 Decreases
            top_decrease = df.nsmallest(5, col)
            print("\nTop 5 Giảm giá mạnh nhất:")
            print(f"{'Ngày':<12} | {'CAR (%)':<10} | {'Sự kiện':<40}")
            print("-" * 70)
            for _, row in top_decrease.iterrows():
                car = row[col] * 100
                event_name = str(row.get('Event_Name', 'N/A'))[:38]
                # Try both date formats
                date = str(row.get('date', row.get('Date', 'N/A')))[:10]
                print(f"{date:<12} | {car:+10.2f} | {event_name:<40}")
                
    except Exception as e:
        print(f"Error reading events file: {e}")

if __name__ == "__main__":
    print_descriptive_stats()
    print_top_events()

