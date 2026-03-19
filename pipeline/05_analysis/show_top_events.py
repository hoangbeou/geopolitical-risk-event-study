"""
Show top events with largest impact
"""

import pandas as pd
import numpy as np

# Load data
df = pd.read_csv('results/events_complete.csv')
df['date'] = pd.to_datetime(df['date'])

# Calculate average absolute CAR
df['Avg_Abs_CAR'] = (
    abs(df['BTC_CAR'].fillna(0)) + 
    abs(df['GOLD_CAR'].fillna(0)) + 
    abs(df['OIL_CAR'].fillna(0))
) / 3

# Get top 10
top10 = df.nlargest(10, 'Avg_Abs_CAR')

print("="*100)
print("TOP 10 EVENTS BY IMPACT (Average Absolute CAR)")
print("="*100)
print()

for idx, (i, row) in enumerate(top10.iterrows(), 1):
    print(f"{'='*100}")
    print(f"RANK #{idx}")
    print(f"{'='*100}")
    print(f"Date: {row['date'].strftime('%Y-%m-%d')}")
    print(f"Event Name: {row['Event_Name']}")
    print()
    print(f"CAR Results:")
    print(f"  BTC:  {row['BTC_CAR']:.6f} ({row['BTC_CAR']*100:+.2f}%)")
    print(f"  GOLD: {row['GOLD_CAR']:.6f} ({row['GOLD_CAR']*100:+.2f}%)")
    print(f"  OIL:  {row['OIL_CAR']:.6f} ({row['OIL_CAR']*100:+.2f}%)")
    print(f"  Avg |CAR|: {row['Avg_Abs_CAR']:.6f}")
    print()
    print(f"GPR Info:")
    print(f"  GPR Value: {row['gpr_value']:.2f}")
    print(f"  GPR Diff: {row['gpr_diff']:.2f}")
    print(f"  Method: {row['method']}")
    print()
    print(f"Location: {row['Detected_Locations']}")
    print()
    print(f"Wiki Content (first 300 chars):")
    content = str(row['Wiki_Content'])[:300]
    print(f"  {content}...")
    print()
    print()

print("="*100)
print("ANALYSIS COMPLETE")
print("="*100)

