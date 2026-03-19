"""Export detected events with CAR statistics to CSV"""
from scripts.detect_events import GPREventDetector
from scripts.run_event_study import EventStudy
from src.preprocessing import DataPreprocessor
import pandas as pd
import numpy as np

# Load data
pre = DataPreprocessor()
data = pre.load_data('data/data.csv')

# Detect all events
detector = GPREventDetector(data)
detected_events = detector.detect_all_events(
    spike_percentile=95,
    high_period_percentile=95,
    combine=True,
    require_gpr_increase=False
)

# Sort by date
detected_events = detected_events.sort_values('date').reset_index(drop=True)

# Run Event Study to get CAR results
print("Running Event Study analysis...")
event_study = EventStudy(data, assets=['BTC', 'GOLD', 'OIL'])
results = event_study.analyze_all_events(use_auto_detection=True)

# Create DataFrame from detected events
events_df = detected_events.copy()
events_df['event_number'] = range(1, len(events_df) + 1)

# Create a mapping from event date to results
# Results are already sorted by date and reindexed as Event_1, Event_2, ...
results_by_date = {}
for event_name, event_data in sorted(results.items(), key=lambda x: x[1]['event_info']['date']):
    event_date = event_data['event_info']['date']
    results_by_date[event_date] = event_data['results']

# Add CAR data for each asset
assets = ['BTC', 'GOLD', 'OIL']
for asset in assets:
    car_values = []
    t_stats = []
    car_finals = []
    
    for idx, row in events_df.iterrows():
        event_date = row['date']
        
        # Match by date
        if event_date in results_by_date:
            asset_results = results_by_date[event_date]
            if asset in asset_results:
                car_result = asset_results[asset]
                # car_final is already the final CAR value
                car_final_val = car_result['car_final']
                car_values.append(car_final_val)
                t_stats.append(car_result['t_stat'])
                car_finals.append(car_final_val)  # Same as car_final
            else:
                car_values.append(np.nan)
                t_stats.append(np.nan)
                car_finals.append(np.nan)
        else:
            car_values.append(np.nan)
            t_stats.append(np.nan)
            car_finals.append(np.nan)
    
    # CAR_Final is the final CAR value (same as CAR, so we only keep one)
    events_df[f'CAR_{asset}'] = car_finals
    events_df[f'Tstat_{asset}'] = t_stats

# Reorder and rename columns
columns_order = [
    'event_number', 'date', 'method', 'gpr_value', 'gpr_diff', 'gpr_pct_change',
    'CAR_BTC', 'Tstat_BTC',
    'CAR_GOLD', 'Tstat_GOLD',
    'CAR_OIL', 'Tstat_OIL'
]

events_df = events_df[columns_order]

# Rename columns for clarity
events_df.columns = [
    'Event_Number', 'Date', 'Detection_Method', 'GPR_Value', 'GPR_Diff', 'GPR_Pct_Change',
    'CAR_BTC', 'Tstat_BTC',
    'CAR_GOLD', 'Tstat_GOLD',
    'CAR_OIL', 'Tstat_OIL'
]

# Format date
events_df['Date'] = pd.to_datetime(events_df['Date']).dt.strftime('%Y-%m-%d')

# Round numeric columns
numeric_cols = ['GPR_Value', 'GPR_Diff', 'GPR_Pct_Change', 
                'CAR_BTC', 'Tstat_BTC',
                'CAR_GOLD', 'Tstat_GOLD',
                'CAR_OIL', 'Tstat_OIL']

for col in numeric_cols:
    if col in events_df.columns:
        if col.startswith('GPR_Pct_Change'):
            events_df[col] = events_df[col].apply(lambda x: round(x * 100, 2) if pd.notna(x) else x)
        else:
            events_df[col] = events_df[col].round(4)

# Save to CSV
output_path = 'results/event_study/detected_events_with_car.csv'
events_df.to_csv(output_path, index=False, encoding='utf-8-sig')

print("\n" + "=" * 80)
print("EXPORTED EVENTS WITH CAR STATISTICS TO CSV")
print("=" * 80)
print(f"\nFile saved to: {output_path}")
print(f"Total events: {len(events_df)}")

# Count events with valid CAR
for asset in assets:
    valid_count = events_df[f'CAR_{asset}'].notna().sum()
    print(f"  Events with valid CAR for {asset}: {valid_count}/{len(events_df)}")

print(f"\nDate range: {events_df['Date'].min()} to {events_df['Date'].max()}")
print(f"\nFirst 5 events:")
print(events_df.head(5).to_string(index=False))
print(f"\nSummary statistics:")
print(events_df[['CAR_BTC', 'CAR_GOLD', 'CAR_OIL']].describe())


from scripts.run_event_study import EventStudy
from src.preprocessing import DataPreprocessor
import pandas as pd
import numpy as np

# Load data
pre = DataPreprocessor()
data = pre.load_data('data/data.csv')

# Detect all events
detector = GPREventDetector(data)
detected_events = detector.detect_all_events(
    spike_percentile=95,
    high_period_percentile=95,
    combine=True,
    require_gpr_increase=False
)

# Sort by date
detected_events = detected_events.sort_values('date').reset_index(drop=True)

# Run Event Study to get CAR results
print("Running Event Study analysis...")
event_study = EventStudy(data, assets=['BTC', 'GOLD', 'OIL'])
results = event_study.analyze_all_events(use_auto_detection=True)

# Create DataFrame from detected events
events_df = detected_events.copy()
events_df['event_number'] = range(1, len(events_df) + 1)

# Create a mapping from event date to results
# Results are already sorted by date and reindexed as Event_1, Event_2, ...
results_by_date = {}
for event_name, event_data in sorted(results.items(), key=lambda x: x[1]['event_info']['date']):
    event_date = event_data['event_info']['date']
    results_by_date[event_date] = event_data['results']

# Add CAR data for each asset
assets = ['BTC', 'GOLD', 'OIL']
for asset in assets:
    car_values = []
    t_stats = []
    car_finals = []
    
    for idx, row in events_df.iterrows():
        event_date = row['date']
        
        # Match by date
        if event_date in results_by_date:
            asset_results = results_by_date[event_date]
            if asset in asset_results:
                car_result = asset_results[asset]
                # car_final is already the final CAR value
                car_final_val = car_result['car_final']
                car_values.append(car_final_val)
                t_stats.append(car_result['t_stat'])
                car_finals.append(car_final_val)  # Same as car_final
            else:
                car_values.append(np.nan)
                t_stats.append(np.nan)
                car_finals.append(np.nan)
        else:
            car_values.append(np.nan)
            t_stats.append(np.nan)
            car_finals.append(np.nan)
    
    # CAR_Final is the final CAR value (same as CAR, so we only keep one)
    events_df[f'CAR_{asset}'] = car_finals
    events_df[f'Tstat_{asset}'] = t_stats

# Reorder and rename columns
columns_order = [
    'event_number', 'date', 'method', 'gpr_value', 'gpr_diff', 'gpr_pct_change',
    'CAR_BTC', 'Tstat_BTC',
    'CAR_GOLD', 'Tstat_GOLD',
    'CAR_OIL', 'Tstat_OIL'
]

events_df = events_df[columns_order]

# Rename columns for clarity
events_df.columns = [
    'Event_Number', 'Date', 'Detection_Method', 'GPR_Value', 'GPR_Diff', 'GPR_Pct_Change',
    'CAR_BTC', 'Tstat_BTC',
    'CAR_GOLD', 'Tstat_GOLD',
    'CAR_OIL', 'Tstat_OIL'
]

# Format date
events_df['Date'] = pd.to_datetime(events_df['Date']).dt.strftime('%Y-%m-%d')

# Round numeric columns
numeric_cols = ['GPR_Value', 'GPR_Diff', 'GPR_Pct_Change', 
                'CAR_BTC', 'Tstat_BTC',
                'CAR_GOLD', 'Tstat_GOLD',
                'CAR_OIL', 'Tstat_OIL']

for col in numeric_cols:
    if col in events_df.columns:
        if col.startswith('GPR_Pct_Change'):
            events_df[col] = events_df[col].apply(lambda x: round(x * 100, 2) if pd.notna(x) else x)
        else:
            events_df[col] = events_df[col].round(4)

# Save to CSV
output_path = 'results/event_study/detected_events_with_car.csv'
events_df.to_csv(output_path, index=False, encoding='utf-8-sig')

print("\n" + "=" * 80)
print("EXPORTED EVENTS WITH CAR STATISTICS TO CSV")
print("=" * 80)
print(f"\nFile saved to: {output_path}")
print(f"Total events: {len(events_df)}")

# Count events with valid CAR
for asset in assets:
    valid_count = events_df[f'CAR_{asset}'].notna().sum()
    print(f"  Events with valid CAR for {asset}: {valid_count}/{len(events_df)}")

print(f"\nDate range: {events_df['Date'].min()} to {events_df['Date'].max()}")
print(f"\nFirst 5 events:")
print(events_df.head(5).to_string(index=False))
print(f"\nSummary statistics:")
print(events_df[['CAR_BTC', 'CAR_GOLD', 'CAR_OIL']].describe())

