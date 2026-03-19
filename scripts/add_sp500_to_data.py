# -*- coding: utf-8 -*-
"""
Script để thêm S&P 500 vào dataset
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import pandas as pd
import numpy as np
from pathlib import Path
import yfinance as yf
from datetime import datetime

def add_sp500_to_data():
    """Thêm S&P 500 vào dataset"""
    
    print("="*80)
    print("THEM S&P 500 VAO DATASET")
    print("="*80)
    
    # Load data hiện tại
    data_path = Path("data/raw/data.csv")
    if not data_path.exists():
        print(f"ERROR: Khong tim thay {data_path}")
        return
    
    print(f"\n1. Loading data tu {data_path}...")
    # Try to read with different date formats
    try:
        data = pd.read_csv(data_path, index_col=0, parse_dates=True, dayfirst=True)
    except:
        data = pd.read_csv(data_path, index_col=0)
        # Try to parse dates manually
        if data.index.dtype == 'object':
            data.index = pd.to_datetime(data.index, dayfirst=True, errors='coerce')
    
    print(f"   Data loaded: {len(data)} observations")
    print(f"   Date range: {data.index.min()} to {data.index.max()}")
    
    # Download S&P 500 data
    print("\n2. Downloading S&P 500 data tu yfinance...")
    start_date = pd.Timestamp(data.index.min())
    end_date = pd.Timestamp(data.index.max())
    
    # Convert to string format for yfinance
    start_str = start_date.strftime('%Y-%m-%d')
    end_str = end_date.strftime('%Y-%m-%d')
    
    print(f"   Downloading from {start_str} to {end_str}...")
    try:
        sp500 = yf.download('^GSPC', start=start_str, end=end_str, progress=False, auto_adjust=False)
        if sp500.empty:
            print("   ERROR: Khong tai duoc du lieu S&P 500")
            return
        
        # Lấy Close price
        if isinstance(sp500.columns, pd.MultiIndex):
            sp500_close = sp500['Close']['^GSPC'] if ('Close', '^GSPC') in sp500.columns else sp500.iloc[:, 0]
        else:
            sp500_close = sp500['Close'] if 'Close' in sp500.columns else sp500.iloc[:, 0]
        
        sp500_close = pd.DataFrame({'SP500': sp500_close})
        sp500_close.index.name = None
        sp500_close.index = pd.to_datetime(sp500_close.index)
        
        print(f"   S&P 500 data downloaded: {len(sp500_close)} observations")
        print(f"   Date range: {sp500_close.index.min()} to {sp500_close.index.max()}")
        
    except Exception as e:
        print(f"   ERROR: {e}")
        return
    
    # Merge với data hiện tại
    print("\n3. Merging S&P 500 voi data hien tai...")
    data_merged = data.merge(sp500_close, left_index=True, right_index=True, how='left')
    
    # Tính log returns cho S&P 500
    print("\n4. Calculating log returns cho S&P 500...")
    data_merged['SP500_ret'] = np.log(data_merged['SP500'] / data_merged['SP500'].shift(1))
    
    # Kiểm tra số lượng missing values
    missing_before = data_merged['SP500'].isna().sum()
    missing_after = data_merged['SP500_ret'].isna().sum()
    print(f"   Missing values trong SP500: {missing_before}")
    print(f"   Missing values trong SP500_ret: {missing_after}")
    
    # Save
    output_path = Path("data/raw/data_with_sp500.csv")
    data_merged.to_csv(output_path)
    print(f"\n5. Saved to: {output_path}")
    
    # Backup file cũ
    backup_path = Path("data/raw/data_backup.csv")
    if not backup_path.exists():
        data.to_csv(backup_path)
        print(f"   Backup saved to: {backup_path}")
    
    print("\n" + "="*80)
    print("HOÀN THÀNH!")
    print("="*80)
    print(f"\nFile mới: {output_path}")
    print(f"File gốc đã được backup: {backup_path}")
    
    return data_merged

if __name__ == '__main__':
    add_sp500_to_data()

