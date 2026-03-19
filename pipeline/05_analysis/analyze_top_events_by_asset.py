"""
Analyze top events by asset - separate for increases and decreases
"""

import pandas as pd
import numpy as np

# Load data
df = pd.read_csv('results/events_complete.csv')
df['date'] = pd.to_datetime(df['date'])

print("="*100)
print("TOP EVENTS ANALYSIS - BY ASSET AND DIRECTION")
print("="*100)
print()


def analyze_asset_extremes(df, asset, top_n=10):
    """Analyze top increases and decreases for an asset"""
    car_col = f'{asset}_CAR'
    
    print("="*100)
    print(f"{asset} - TOP {top_n} INCREASES")
    print("="*100)
    print()
    
    top_increases = df.nlargest(top_n, car_col)
    
    for idx, (i, row) in enumerate(top_increases.iterrows(), 1):
        print(f"#{idx}. {row['date'].strftime('%Y-%m-%d')} - CAR: {row[car_col]*100:+.2f}%")
        print(f"    Event: {row['Event_Name'][:80]}")
        print(f"    Location: {row['Detected_Locations']}")
        print(f"    GPR: {row['gpr_value']:.0f} (diff: {row['gpr_diff']:.0f})")
        print()
    
    print()
    print("="*100)
    print(f"{asset} - TOP {top_n} DECREASES")
    print("="*100)
    print()
    
    top_decreases = df.nsmallest(top_n, car_col)
    
    for idx, (i, row) in enumerate(top_decreases.iterrows(), 1):
        print(f"#{idx}. {row['date'].strftime('%Y-%m-%d')} - CAR: {row[car_col]*100:+.2f}%")
        print(f"    Event: {row['Event_Name'][:80]}")
        print(f"    Location: {row['Detected_Locations']}")
        print(f"    GPR: {row['gpr_value']:.0f} (diff: {row['gpr_diff']:.0f})")
        print()
    
    print()
    print("-"*100)
    print(f"{asset} - INSIGHTS FROM EXTREMES")
    print("-"*100)
    print()
    
    # Analyze patterns
    top_inc_years = top_increases['date'].dt.year.value_counts()
    top_dec_years = top_decreases['date'].dt.year.value_counts()
    
    print(f"Top increases by year:")
    for year, count in top_inc_years.items():
        print(f"  {year}: {count} events")
    print()
    
    print(f"Top decreases by year:")
    for year, count in top_dec_years.items():
        print(f"  {year}: {count} events")
    print()
    
    # Analyze locations
    inc_locations = []
    dec_locations = []
    
    for _, row in top_increases.iterrows():
        locs = str(row['Detected_Locations'])
        if locs != 'nan':
            inc_locations.extend([l.strip() for l in locs.split(',')])
    
    for _, row in top_decreases.iterrows():
        locs = str(row['Detected_Locations'])
        if locs != 'nan':
            dec_locations.extend([l.strip() for l in locs.split(',')])
    
    if inc_locations:
        from collections import Counter
        top_inc_locs = Counter(inc_locations).most_common(5)
        print(f"Top locations in increases:")
        for loc, count in top_inc_locs:
            print(f"  {loc}: {count} times")
        print()
    
    if dec_locations:
        from collections import Counter
        top_dec_locs = Counter(dec_locations).most_common(5)
        print(f"Top locations in decreases:")
        for loc, count in top_dec_locs:
            print(f"  {loc}: {count} times")
        print()
    
    print()


# Analyze each asset
for asset in ['BTC', 'GOLD', 'OIL']:
    analyze_asset_extremes(df, asset, top_n=10)

print("="*100)
print("CROSS-ASSET INSIGHTS")
print("="*100)
print()

# Find events where all 3 assets moved in same direction
all_up = df[(df['BTC_CAR'] > 0) & (df['GOLD_CAR'] > 0) & (df['OIL_CAR'] > 0)]
all_down = df[(df['BTC_CAR'] < 0) & (df['GOLD_CAR'] < 0) & (df['OIL_CAR'] < 0)]

print(f"Events where ALL 3 assets increased: {len(all_up)}")
if len(all_up) > 0:
    print("Examples:")
    for _, row in all_up.head(5).iterrows():
        print(f"  - {row['date'].strftime('%Y-%m-%d')}: {row['Event_Name'][:60]}")
print()

print(f"Events where ALL 3 assets decreased: {len(all_down)}")
if len(all_down) > 0:
    print("Examples:")
    for _, row in all_down.head(5).iterrows():
        print(f"  - {row['date'].strftime('%Y-%m-%d')}: {row['Event_Name'][:60]}")
print()

# Find events where BTC and GOLD moved opposite
opposite = df[((df['BTC_CAR'] > 0) & (df['GOLD_CAR'] < 0)) | ((df['BTC_CAR'] < 0) & (df['GOLD_CAR'] > 0))]
print(f"Events where BTC and GOLD moved OPPOSITE: {len(opposite)}")
print()

print("="*100)
print("ANALYSIS COMPLETE")
print("="*100)

