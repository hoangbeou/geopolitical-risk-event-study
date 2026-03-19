"""Debug script to check why only 12 events are plotted"""
from scripts.detect_events import GPREventDetector
from src.preprocessing import DataPreprocessor
from scripts.run_event_study import EventStudy
import pandas as pd

# Load data
pre = DataPreprocessor()
data = pre.load_data('data/data.csv')
print(f"Data loaded: {len(data)} rows, {data.index.min()} to {data.index.max()}")

# Detect events
detector = GPREventDetector(data)
events_df = detector.detect_all_events(
    spike_percentile=95,
    high_period_percentile=95,
    combine=True,
    require_gpr_increase=False
)
print(f"\nDetected {len(events_df)} events")
print(f"Date range: {events_df['date'].min()} to {events_df['date'].max()}")

# Load events into EventStudy format
event_study = EventStudy(data, assets=['BTC', 'GOLD', 'OIL'])
events_dict = event_study.load_events_from_detector(events_df)
print(f"\nLoaded {len(events_dict)} events into EventStudy format")

# Check how many can be analyzed
results = {}
skipped = []
for event_name, event_info in events_dict.items():
    event_date = event_info['date']
    window = event_info['window']
    
    event_results = {}
    for asset in ['BTC', 'GOLD', 'OIL']:
        if asset in data.columns:
            returns = event_study.calculate_returns(data[asset])
            car_result = event_study.calculate_car(returns, event_date, window)
            if car_result is not None:
                event_results[asset] = car_result
    
    if event_results:
        results[event_name] = {
            'event_info': event_info,
            'results': event_results
        }
    else:
        skipped.append((event_name, event_date))

print(f"\nEvents with valid CAR: {len(results)}")
print(f"Events skipped: {len(skipped)}")

if skipped:
    print("\nFirst 10 skipped events:")
    for name, date in skipped[:10]:
        print(f"  {name}: {date}")

