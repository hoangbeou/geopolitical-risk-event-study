"""
Script đơn giản để phân tích CAR theo Region
Copy-paste và chạy trực tiếp trong Python hoặc terminal
"""
import pandas as pd
import numpy as np

# Bước 1: Load dữ liệu
print("="*70)
print("PHÂN TÍCH CAR THEO REGION")
print("="*70)

events_df = pd.read_csv('ket_qua_wiki_with_regions.csv')
events_df['Date'] = pd.to_datetime(events_df['Date'])

car_df = pd.read_csv('results/event_study/detected_events_with_car.csv')
car_df['Date'] = pd.to_datetime(car_df['Date'])

# Bước 2: Merge
merged = pd.merge(
    events_df[['Event_Number', 'Date', 'Region', 'Secondary_Regions', 'GPR_Value']],
    car_df[['Date', 'CAR_BTC', 'CAR_GOLD', 'CAR_OIL']],
    on='Date',
    how='inner'
)

print(f"\n✓ Đã merge {len(merged)} events")

# Bước 3: Loại bỏ UNKNOWN và MULTI_REGION
df_clean = merged[~merged['Region'].isin(['UNKNOWN', 'MULTI_REGION'])].copy()
print(f"✓ Sau khi loại bỏ UNKNOWN/MULTI_REGION: {len(df_clean)} events")

# Bước 4: Phân tích theo region
print("\n" + "="*70)
print("PHÂN BỐ EVENTS THEO REGION")
print("="*70)
region_counts = df_clean['Region'].value_counts()
for region, count in region_counts.items():
    pct = count / len(df_clean) * 100
    print(f"  {region:20s}: {count:3d} events ({pct:5.1f}%)")

# Bước 5: Tính average CAR theo region
print("\n" + "="*70)
print("AVERAGE CAR (%) THEO REGION")
print("="*70)

results = []
for region in sorted(df_clean['Region'].unique()):
    region_data = df_clean[df_clean['Region'] == region]
    n = len(region_data)
    
    if n < 2:
        continue
    
    # Loại bỏ NaN
    btc_data = region_data['CAR_BTC'].dropna()
    gold_data = region_data['CAR_GOLD'].dropna()
    oil_data = region_data['CAR_OIL'].dropna()
    
    if len(btc_data) == 0 or len(gold_data) == 0 or len(oil_data) == 0:
        continue
    
    btc_mean = btc_data.mean() * 100  # Convert to percentage
    gold_mean = gold_data.mean() * 100
    oil_mean = oil_data.mean() * 100
    
    btc_std = btc_data.std() * 100
    gold_std = gold_data.std() * 100
    oil_std = oil_data.std() * 100
    
    results.append({
        'Region': region,
        'N': n,
        'BTC_Mean': btc_mean,
        'BTC_Std': btc_std,
        'GOLD_Mean': gold_mean,
        'GOLD_Std': gold_std,
        'OIL_Mean': oil_mean,
        'OIL_Std': oil_std
    })
    
    print(f"\n{region} (N={n}):")
    print(f"  BTC:  {btc_mean:7.2f}% (std: {btc_std:.2f}%)")
    print(f"  GOLD: {gold_mean:7.2f}% (std: {gold_std:.2f}%)")
    print(f"  OIL:  {oil_mean:7.2f}% (std: {oil_std:.2f}%)")

# Bước 6: Export
results_df = pd.DataFrame(results)
results_df = results_df.sort_values('N', ascending=False)

import os
os.makedirs('results/region_analysis', exist_ok=True)
results_df.to_csv('results/region_analysis/car_by_region_summary.csv', index=False)

# Export full data
df_export = merged[['Event_Number', 'Date', 'Region', 'Secondary_Regions',
                     'GPR_Value', 'CAR_BTC', 'CAR_GOLD', 'CAR_OIL']]
df_export.to_csv('results/region_analysis/events_with_region_and_car.csv', index=False)

print("\n" + "="*70)
print("✓ Đã lưu kết quả:")
print("  - results/region_analysis/car_by_region_summary.csv")
print("  - results/region_analysis/events_with_region_and_car.csv")
print("="*70)

# In bảng markdown
print("\n" + "="*70)
print("BẢNG MARKDOWN CHO KHÓA LUẬN:")
print("="*70)
print("\n| Region | N Events | BTC CAR | GOLD CAR | OIL CAR |")
print("|--------|----------|---------|----------|---------|")
for _, row in results_df.iterrows():
    print(f"| {row['Region']} | {int(row['N'])} | {row['BTC_Mean']:.2f}% | {row['GOLD_Mean']:.2f}% | {row['OIL_Mean']:.2f}% |")

