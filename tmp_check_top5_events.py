import pandas as pd
import numpy as np

# Load data
df = pd.read_csv('results/events_complete.csv')
df['date'] = pd.to_datetime(df['date'])

# Filter out 2025 events (not in study period 2015-2024)
df = df[df['date'].dt.year <= 2024]

print("="*100)
print("TOP 5 EVENTS BY CAR FOR EACH ASSET")
print("="*100)
print(f"\nTotal events (2015-2024): {len(df)}")
print(f"Date range: {df['date'].min().strftime('%Y-%m-%d')} to {df['date'].max().strftime('%Y-%m-%d')}")

# BTC Top 5 positive and negative
print("\n" + "="*100)
print("BITCOIN (BTC) - Top 5 Positive CAR:")
print("="*100)
btc_pos = df.nlargest(5, 'BTC_CAR')[['date', 'BTC_CAR', 'Event_Name']]
for idx, (i, row) in enumerate(btc_pos.iterrows(), 1):
    print(f"{idx}. {row['date'].strftime('%Y-%m-%d')} | CAR: {row['BTC_CAR']*100:+.2f}% | {row['Event_Name'][:60]}")

print("\n" + "="*100)
print("BITCOIN (BTC) - Top 5 Negative CAR:")
print("="*100)
btc_neg = df.nsmallest(5, 'BTC_CAR')[['date', 'BTC_CAR', 'Event_Name']]
for idx, (i, row) in enumerate(btc_neg.iterrows(), 1):
    print(f"{idx}. {row['date'].strftime('%Y-%m-%d')} | CAR: {row['BTC_CAR']*100:+.2f}% | {row['Event_Name'][:60]}")

# GOLD Top 5 positive and negative
print("\n" + "="*100)
print("GOLD - Top 5 Positive CAR:")
print("="*100)
gold_pos = df.nlargest(5, 'GOLD_CAR')[['date', 'GOLD_CAR', 'Event_Name']]
for idx, (i, row) in enumerate(gold_pos.iterrows(), 1):
    print(f"{idx}. {row['date'].strftime('%Y-%m-%d')} | CAR: {row['GOLD_CAR']*100:+.2f}% | {row['Event_Name'][:60]}")

print("\n" + "="*100)
print("GOLD - Top 5 Negative CAR:")
print("="*100)
gold_neg = df.nsmallest(5, 'GOLD_CAR')[['date', 'GOLD_CAR', 'Event_Name']]
for idx, (i, row) in enumerate(gold_neg.iterrows(), 1):
    print(f"{idx}. {row['date'].strftime('%Y-%m-%d')} | CAR: {row['GOLD_CAR']*100:+.2f}% | {row['Event_Name'][:60]}")

# OIL Top 5 positive and negative
print("\n" + "="*100)
print("OIL - Top 5 Positive CAR:")
print("="*100)
oil_pos = df.nlargest(5, 'OIL_CAR')[['date', 'OIL_CAR', 'Event_Name']]
for idx, (i, row) in enumerate(oil_pos.iterrows(), 1):
    print(f"{idx}. {row['date'].strftime('%Y-%m-%d')} | CAR: {row['OIL_CAR']*100:+.2f}% | {row['Event_Name'][:60]}")

print("\n" + "="*100)
print("OIL - Top 5 Negative CAR:")
print("="*100)
oil_neg = df.nsmallest(5, 'OIL_CAR')[['date', 'OIL_CAR', 'Event_Name']]
for idx, (i, row) in enumerate(oil_neg.iterrows(), 1):
    print(f"{idx}. {row['date'].strftime('%Y-%m-%d')} | CAR: {row['OIL_CAR']*100:+.2f}% | {row['Event_Name'][:60]}")

