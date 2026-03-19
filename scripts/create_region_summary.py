"""
Tạo summary phân tích region và tích hợp vào khóa luận
"""
import pandas as pd
import numpy as np
import os

print("="*70)
print("PHÂN TÍCH CAR THEO REGION")
print("="*70)

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

print(f"\nTổng số events sau merge: {len(merged)}")

# Loại bỏ UNKNOWN và MULTI_REGION
df_clean = merged[~merged['Region'].isin(['UNKNOWN', 'MULTI_REGION'])].copy()
print(f"Sau khi loại bỏ UNKNOWN/MULTI_REGION: {len(df_clean)}")

# Phân tích theo region
print("\n" + "="*70)
print("PHÂN BỐ EVENTS THEO REGION")
print("="*70)
region_counts = df_clean['Region'].value_counts()
for region, count in region_counts.items():
    pct = count / len(df_clean) * 100
    print(f"  {region:20s}: {count:3d} events ({pct:5.1f}%)")

# Tính average CAR theo region
print("\n" + "="*70)
print("AVERAGE CAR (%) THEO REGION")
print("="*70)

results = []
for region in df_clean['Region'].unique():
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
    
    btc_mean = btc_data.mean()
    gold_mean = gold_data.mean()
    oil_mean = oil_data.mean()
    
    btc_std = btc_data.std()
    gold_std = gold_data.std()
    oil_std = oil_data.std()
    
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
    print(f"  BTC:  {btc_mean:7.2f}% (std: {btc_std:.2f})")
    print(f"  GOLD: {gold_mean:7.2f}% (std: {gold_std:.2f})")
    print(f"  OIL:  {oil_mean:7.2f}% (std: {oil_std:.2f})")

# Export
results_df = pd.DataFrame(results)
results_df = results_df.sort_values('N', ascending=False)

os.makedirs('results/region_analysis', exist_ok=True)
results_df.to_csv('results/region_analysis/car_by_region_summary.csv', index=False)

# Export full data
df_export = merged[['Event_Number', 'Date', 'Region', 'Secondary_Regions',
                     'GPR_Value', 'CAR_BTC', 'CAR_GOLD', 'CAR_OIL']]
df_export.to_csv('results/region_analysis/events_with_region_and_car.csv', index=False)

print("\n" + "="*70)
print("✓ Đã lưu kết quả vào results/region_analysis/")
print("="*70)

# Tạo markdown summary cho khóa luận
markdown_content = f"""
## PHÂN TÍCH CAR THEO REGION

### Phân bố Events theo Region

| Region | Số lượng Events | Tỷ lệ |
|--------|-----------------|-------|
"""
for region, count in region_counts.items():
    pct = count / len(df_clean) * 100
    markdown_content += f"| {region} | {count} | {pct:.1f}% |\n"

markdown_content += f"""

### Average CAR (%) theo Region

| Region | N | BTC CAR | GOLD CAR | OIL CAR |
|--------|---|---------|----------|---------|
"""
for _, row in results_df.iterrows():
    markdown_content += f"| {row['Region']} | {int(row['N'])} | {row['BTC_Mean']:.2f}% | {row['GOLD_Mean']:.2f}% | {row['OIL_Mean']:.2f}% |\n"

markdown_content += """

### Kết luận chính

"""

# Tìm region có CAR cao nhất/thấp nhất
for asset in ['BTC', 'GOLD', 'OIL']:
    mean_col = f'{asset}_Mean'
    max_idx = results_df[mean_col].idxmax()
    min_idx = results_df[mean_col].idxmin()
    
    max_region = results_df.loc[max_idx, 'Region']
    max_car = results_df.loc[max_idx, mean_col]
    min_region = results_df.loc[min_idx, 'Region']
    min_car = results_df.loc[min_idx, mean_col]
    
    markdown_content += f"- **{asset}**: Region có CAR cao nhất là {max_region} ({max_car:.2f}%), thấp nhất là {min_region} ({min_car:.2f}%)\n"

with open('results/region_analysis/region_analysis_summary.md', 'w', encoding='utf-8') as f:
    f.write(markdown_content)

print("\n✓ Đã tạo markdown summary: results/region_analysis/region_analysis_summary.md")

