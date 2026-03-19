"""
Tính toán CAR trung bình theo Region và Type để điền vào Bảng 3.8 và 3.9
"""

import json
import pandas as pd
import numpy as np
from pathlib import Path

# Load event patterns (có đầy đủ region, type, CAR)
patterns_path = Path('results/event_study/event_patterns.json')
with open(patterns_path, 'r', encoding='utf-8') as f:
    patterns = json.load(f)


# Tạo DataFrame từ tất cả events
all_events = {}
for direction in ['BTC_increase', 'BTC_decrease', 'GOLD_increase', 'GOLD_decrease', 'OIL_increase', 'OIL_decrease']:
    if direction in patterns:
        for event in patterns[direction]['events']:
            event_id = event['event']
            if event_id not in all_events:
                all_events[event_id] = {
                    'event': event_id,
                    'date': event.get('date', ''),
                    'region': event.get('region', 'Unknown'),
                    'type': event.get('type', 'Unknown')
                }
            
            # Lấy CAR cho từng asset
            asset = direction.split('_')[0]
            all_events[event_id][f'{asset}_car'] = event.get('car', np.nan)

df = pd.DataFrame(list(all_events.values()))

# Map region names
region_mapping = {
    'middle_east': 'Trung Đông',
    'asia': 'Châu Á',
    'europe': 'Châu Âu',
    'americas': 'Bắc Mỹ',
    'global': 'Toàn cầu'
}

df['region_display'] = df['region'].map(region_mapping).fillna(df['region'])

# Map type names
type_mapping = {
    'war': 'War',
    'political': 'Political',
    'mixed': 'Mixed'
}

df['type_display'] = df['type'].map(type_mapping).fillna(df['type'])

print("="*80)
print("BẢNG 3.8: CAR TRUNG BÌNH THEO VÙNG ĐỊA LÝ")
print("="*80)
print()

regional_stats = df.groupby('region_display').agg({
    'event': 'count',
    'BTC_car': ['mean', 'std'],
    'GOLD_car': ['mean', 'std'],
    'OIL_car': ['mean', 'std']
}).round(4)

print("| Vùng | Số lượng | BTC CAR TB | BTC Std | GOLD CAR TB | GOLD Std | OIL CAR TB | OIL Std |")
print("|------|----------|------------|---------|-------------|----------|------------|---------|")

for region in regional_stats.index:
    count = int(regional_stats.loc[region, ('event', 'count')])
    btc_mean = regional_stats.loc[region, ('BTC_car', 'mean')]
    btc_std = regional_stats.loc[region, ('BTC_car', 'std')]
    gold_mean = regional_stats.loc[region, ('GOLD_car', 'mean')]
    gold_std = regional_stats.loc[region, ('GOLD_car', 'std')]
    oil_mean = regional_stats.loc[region, ('OIL_car', 'mean')]
    oil_std = regional_stats.loc[region, ('OIL_car', 'std')]
    
    print(f"| {region} | {count} | {btc_mean*100:.2f}% | {btc_std*100:.2f}% | {gold_mean*100:.2f}% | {gold_std*100:.2f}% | {oil_mean*100:.2f}% | {oil_std*100:.2f}% |")

print()
print("="*80)
print("CHI TIẾT THEO VÙNG:")
print("="*80)
for region in df['region_display'].unique():
    if pd.notna(region):
        region_df = df[df['region_display'] == region]
        print(f"\n{region}: {len(region_df)} events")
        print(f"  BTC CAR: {region_df['BTC_car'].mean()*100:.2f}% (std: {region_df['BTC_car'].std()*100:.2f}%)")
        print(f"  GOLD CAR: {region_df['GOLD_car'].mean()*100:.2f}% (std: {region_df['GOLD_car'].std()*100:.2f}%)")
        print(f"  OIL CAR: {region_df['OIL_car'].mean()*100:.2f}% (std: {region_df['OIL_car'].std()*100:.2f}%)")

