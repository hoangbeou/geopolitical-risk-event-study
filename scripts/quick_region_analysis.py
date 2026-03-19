"""
Quick analysis: Merge region data với CAR và tạo summary
"""
import pandas as pd
import numpy as np

# Load data
print("Loading data...")
events_df = pd.read_csv('ket_qua_wiki_with_regions.csv')
events_df['Date'] = pd.to_datetime(events_df['Date'])

car_df = pd.read_csv('results/event_study/detected_events_with_car.csv')
car_df['Date'] = pd.to_datetime(car_df['Date'])

print(f"Events with region: {len(events_df)}")
print(f"Events with CAR: {len(car_df)}")

# Merge
merged = pd.merge(
    events_df[['Event_Number', 'Date', 'Region', 'Secondary_Regions', 'GPR_Value']],
    car_df[['Date', 'CAR_BTC', 'CAR_GOLD', 'CAR_OIL']],
    on='Date',
    how='inner'
)

print(f"\nMerged events: {len(merged)}")

# Loại bỏ UNKNOWN và MULTI_REGION
df_clean = merged[~merged['Region'].isin(['UNKNOWN', 'MULTI_REGION'])].copy()
print(f"After removing UNKNOWN/MULTI_REGION: {len(df_clean)}")

# Phân tích theo region
print("\n" + "="*70)
print("AVERAGE CAR (%) THEO REGION")
print("="*70)

regions = df_clean['Region'].unique()
results = []

for region in regions:
    region_data = df_clean[df_clean['Region'] == region]
    n = len(region_data)
    
    if n < 2:
        continue
    
    btc_mean = region_data['CAR_BTC'].mean()
    gold_mean = region_data['CAR_GOLD'].mean()
    oil_mean = region_data['CAR_OIL'].mean()
    
    results.append({
        'Region': region,
        'N': n,
        'BTC_CAR': btc_mean,
        'GOLD_CAR': gold_mean,
        'OIL_CAR': oil_mean
    })
    
    print(f"\n{region} (N={n}):")
    print(f"  BTC:  {btc_mean:7.2f}%")
    print(f"  GOLD: {gold_mean:7.2f}%")
    print(f"  OIL:  {oil_mean:7.2f}%")

# Export
results_df = pd.DataFrame(results)
results_df = results_df.sort_values('N', ascending=False)
results_df.to_csv('results/region_analysis/car_by_region_summary.csv', index=False)

# Export full data
df_export = merged[['Event_Number', 'Date', 'Region', 'Secondary_Regions',
                     'GPR_Value', 'CAR_BTC', 'CAR_GOLD', 'CAR_OIL']]
df_export.to_csv('results/region_analysis/events_with_region_and_car.csv', index=False)

print("\n" + "="*70)
print("✓ Đã lưu kết quả vào results/region_analysis/")
print("="*70)

