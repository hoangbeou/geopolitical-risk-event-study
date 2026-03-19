"""
Tối ưu file data:
1. Bỏ các ngày thứ 7, chủ nhật không có data
2. Cắt data đến ngày cuối cùng có GPR data
"""

import pandas as pd
import numpy as np
from pathlib import Path

def optimize_data(input_file='data/data.csv', output_file='data/data_optimized.csv'):
    """
    Tối ưu file data
    
    Parameters:
    -----------
    input_file : str
        File input
    output_file : str
        File output
    """
    print("="*80)
    print("TOI UU FILE DATA")
    print("="*80)
    
    # Load data
    print(f"\n1. Loading data from {input_file}...")
    df = pd.read_csv(input_file, index_col=0)
    # Parse dates với format DD/MM/YYYY
    df.index = pd.to_datetime(df.index, format='%d/%m/%Y', errors='coerce')
    # Bỏ các dòng có index là NaT (không parse được)
    df = df[df.index.notna()]
    print(f"   [OK] Loaded: {len(df)} rows")
    print(f"   Date range: {df.index.min()} to {df.index.max()}")
    
    # Tìm ngày cuối cùng có GPR data
    print("\n2. Finding last date with GPR data...")
    gpr_cols = ['GPRD', 'GPRD_ACT', 'GPRD_THREAT']
    gpr_data = df[gpr_cols].notna().any(axis=1)
    last_gpr_date = df[gpr_data].index.max()
    print(f"   [OK] Last GPR date: {last_gpr_date}")
    
    # Cắt data đến ngày cuối cùng có GPR
    print("\n3. Filtering data to last GPR date...")
    df = df[df.index <= last_gpr_date]
    print(f"   [OK] After filtering: {len(df)} rows")
    print(f"   Date range: {df.index.min()} to {df.index.max()}")
    
    # Chỉ giữ thứ 2-6 (Monday-Friday), bỏ thứ 7 và chủ nhật
    # weekday: 0=Monday, 1=Tuesday, 2=Wednesday, 3=Thursday, 4=Friday, 5=Saturday, 6=Sunday
    print("\n4. Keeping only weekdays (Monday-Friday), removing weekends...")
    weekdays = df.index.weekday
    
    # Đếm số ngày cuối tuần
    weekends = weekdays.isin([5, 6])  # Saturday, Sunday
    weekend_count = weekends.sum()
    print(f"   Found {weekend_count} weekend days (Saturday & Sunday)")
    
    # Chỉ giữ thứ 2-6 (weekday 0-4)
    rows_before = len(df)
    df = df[weekdays.isin([0, 1, 2, 3, 4])]  # Chỉ giữ Monday-Friday
    rows_removed = rows_before - len(df)
    
    print(f"   [OK] Removed {rows_removed} weekend days")
    print(f"   After removal: {len(df)} rows (only Monday-Friday)")
    
    # Không cần xóa vì không tạo cột weekday
    
    # Sort lại theo date
    df = df.sort_index()
    
    # Save
    print(f"\n5. Saving optimized data to {output_file}...")
    df.to_csv(output_file, date_format='%d/%m/%Y')
    print(f"   [OK] Saved: {len(df)} rows")
    print(f"   Date range: {df.index.min()} to {df.index.max()}")
    
    # Thống kê
    print("\n" + "="*80)
    print("THONG KE")
    print("="*80)
    print(f"Total rows: {len(df)}")
    print(f"Date range: {df.index.min().strftime('%d/%m/%Y')} to {df.index.max().strftime('%d/%m/%Y')}")
    
    # Đếm số ngày có data cho từng cột
    print("\nData availability:")
    for col in ['BTC', 'GOLD', 'OIL', 'GPRD', 'DXY', 'DGS3MO', 'T10YIE']:
        if col in df.columns:
            count = df[col].notna().sum()
            pct = count / len(df) * 100
            print(f"  {col:8}: {count:5} days ({pct:5.1f}%)")
    
    # Kiểm tra ngày cuối tuần còn lại (nên = 0)
    weekends_remaining = df.index.weekday.isin([5, 6]).sum()
    weekdays_only = df.index.weekday.isin([0, 1, 2, 3, 4]).sum()
    print(f"\nWeekend days remaining: {weekends_remaining} (should be 0)")
    print(f"Weekdays (Mon-Fri): {weekdays_only} (should be {len(df)})")
    
    print("\n" + "="*80)
    print("COMPLETE!")
    print("="*80)
    
    return df


def main():
    """Main function"""
    # Optimize CSV - tạo file mới, giữ file gốc
    print("NOTE: Original file will be kept as data/data.csv")
    print("Optimized file will be saved as data/data_optimized.csv\n")
    
    df = optimize_data('data/data.csv', 'data/data_optimized.csv')
    
    # Also save Excel file mới
    print("\n6. Saving optimized Excel file...")
    df.to_excel('data/data_gpr_daily_recent_optimized.xlsx', index=True)
    print("   [OK] Saved: data/data_gpr_daily_recent_optimized.xlsx")
    print("\n   Original files kept:")
    print("   - data/data.csv")
    print("   - data/data_gpr_daily_recent.xlsx")


if __name__ == '__main__':
    main()

