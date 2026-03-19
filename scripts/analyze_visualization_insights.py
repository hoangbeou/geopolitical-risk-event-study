"""
Analyze insights from the 3 priority visualizations
"""

import sys
sys.path.append('.')
from scripts.create_priority_visualizations import load_all_event_data
import pandas as pd
import numpy as np

df = load_all_event_data()

print("=" * 60)
print("PHAN TICH INSIGHTS TU 3 BIEU DO")
print("=" * 60)

# 1. ACT/THREAT vs BTC CAR
print("\n1. ACT/THREAT vs BTC CAR ANALYSIS:")
print("-" * 60)
act_df = df[(df['act_ratio'].notna()) & (df['BTC_car'].notna())]
print(f"Events with both ACT/THREAT and BTC CAR: {len(act_df)}")

if len(act_df) > 0:
    act_low = act_df[act_df['act_ratio'] < 1.0]  # ACT < THREAT
    act_high = act_df[act_df['act_ratio'] >= 1.0]  # ACT >= THREAT
    
    print(f"\nACT < THREAT (Threat-dominated): {len(act_low)} events")
    if len(act_low) > 0:
        print(f"  Average BTC CAR: {act_low['BTC_car'].mean()*100:.2f}%")
        print(f"  Positive CAR: {len(act_low[act_low['BTC_car'] > 0])} events ({len(act_low[act_low['BTC_car'] > 0])/len(act_low)*100:.1f}%)")
    
    print(f"\nACT >= THREAT (Action-dominated): {len(act_high)} events")
    if len(act_high) > 0:
        print(f"  Average BTC CAR: {act_high['BTC_car'].mean()*100:.2f}%")
        print(f"  Positive CAR: {len(act_high[act_high['BTC_car'] > 0])} events ({len(act_high[act_high['BTC_car'] > 0])/len(act_high)*100:.1f}%)")
    
    # Correlation
    corr = act_df['act_ratio'].corr(act_df['BTC_car'])
    print(f"\nCorrelation (ACT/THREAT ratio vs BTC CAR): {corr:.3f}")

# 2. Temporal Evolution
print("\n\n2. TEMPORAL EVOLUTION ANALYSIS:")
print("-" * 60)
yearly = df.groupby('year').agg({
    'BTC_car': ['mean', 'std', 'count'],
    'GOLD_car': ['mean', 'std', 'count'],
    'OIL_car': ['mean', 'std', 'count']
}).round(4)
print(yearly)

# Trend analysis
if len(yearly) > 1:
    btc_trend = np.polyfit(range(len(yearly)), yearly[('BTC_car', 'mean')].values, 1)[0]
    gold_trend = np.polyfit(range(len(yearly)), yearly[('GOLD_car', 'mean')].values, 1)[0]
    print(f"\nTrend (slope):")
    print(f"  BTC: {btc_trend*100:.2f}% per year")
    print(f"  GOLD: {gold_trend*100:.2f}% per year")

# 3. Pattern Distribution
print("\n\n3. PATTERN DISTRIBUTION:")
print("-" * 60)
df['pattern'] = df.apply(lambda r: 
    'BTC_UP_GOLD_UP' if (pd.notna(r['BTC_car']) and pd.notna(r['GOLD_car']) and r['BTC_car'] > 0 and r['GOLD_car'] > 0) else
    ('BTC_DOWN_GOLD_DOWN' if (pd.notna(r['BTC_car']) and pd.notna(r['GOLD_car']) and r['BTC_car'] < 0 and r['GOLD_car'] < 0) else
    ('BTC_UP_GOLD_DOWN' if (pd.notna(r['BTC_car']) and pd.notna(r['GOLD_car']) and r['BTC_car'] > 0 and r['GOLD_car'] < 0) else
    ('BTC_DOWN_GOLD_UP' if (pd.notna(r['BTC_car']) and pd.notna(r['GOLD_car']) and r['BTC_car'] < 0 and r['GOLD_car'] > 0) else 'Unknown'))), axis=1)

pattern_counts = df['pattern'].value_counts()
print(pattern_counts)
print(f"\nPercentage:")
for pattern, count in pattern_counts.items():
    print(f"  {pattern}: {count/len(df)*100:.1f}%")

# Pattern by type
print("\nPattern by Event Type:")
pattern_type = pd.crosstab(df['pattern'], df['type'], margins=True)
print(pattern_type)

# Average CAR by pattern
print("\nAverage CAR by Pattern:")
pattern_car = df.groupby('pattern').agg({
    'BTC_car': 'mean',
    'GOLD_car': 'mean',
    'OIL_car': 'mean'
}) * 100
print(pattern_car.round(2))

print("\n" + "=" * 60)
print("ANALYSIS COMPLETE")
print("=" * 60)

