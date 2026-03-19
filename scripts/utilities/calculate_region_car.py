import pandas as pd
import numpy as np

# Load data
events_df = pd.read_csv('ket_qua_wiki_with_regions.csv')
events_df['Date'] = pd.to_datetime(events_df['Date'])

car_df = pd.read_csv('results/event_study/detected_events_with_car.csv')
car_df['Date'] = pd.to_datetime(car_df['Date'])

# Merge
merged = pd.merge(
    events_df[['Event_Number', 'Date', 'Region', 'Secondary_Regions', 'GPR_Value']],
    car_df[['Date', 'CAR_BTC', 'CAR_GOLD', 'CAR_OIL']],
    on='Date',
    how='inner'
)

# Loại bỏ UNKNOWN và MULTI_REGION
df_clean = merged[~merged['Region'].isin(['UNKNOWN', 'MULTI_REGION'])].copy()

# Tính average CAR theo region
results = []
for region in sorted(df_clean['Region'].unique()):
    region_data = df_clean[df_clean['Region'] == region]
    n = len(region_data)
    
    if n < 2:
        continue
    
    btc_data = region_data['CAR_BTC'].dropna()
    gold_data = region_data['CAR_GOLD'].dropna()
    oil_data = region_data['CAR_OIL'].dropna()
    
    if len(btc_data) == 0 or len(gold_data) == 0 or len(oil_data) == 0:
        continue
    
    results.append({
        'Region': region,
        'N': n,
        'BTC_Mean': btc_data.mean() * 100,
        'GOLD_Mean': gold_data.mean() * 100,
        'OIL_Mean': oil_data.mean() * 100
    })

results_df = pd.DataFrame(results)
results_df = results_df.sort_values('N', ascending=False)

# Export
import os
os.makedirs('results/region_analysis', exist_ok=True)
results_df.to_csv('results/region_analysis/car_by_region_summary.csv', index=False)

# Print markdown table
print("\n| Region | N Events | BTC CAR | GOLD CAR | OIL CAR |")
print("|--------|----------|---------|----------|---------|")
for _, row in results_df.iterrows():
    print(f"| {row['Region']} | {int(row['N'])} | {row['BTC_Mean']:.2f}% | {row['GOLD_Mean']:.2f}% | {row['OIL_Mean']:.2f}% |")

print(f"\n✓ Đã lưu: results/region_analysis/car_by_region_summary.csv")

