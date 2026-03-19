"""Export detected events to CSV"""
from scripts.detect_events import GPREventDetector
from src.preprocessing import DataPreprocessor
import pandas as pd

# Load data
pre = DataPreprocessor()
data = pre.load_data('data/data.csv')
detector = GPREventDetector(data)

# Detect all events
all_events = detector.detect_all_events(
    spike_percentile=95,
    high_period_percentile=95,
    combine=True,
    require_gpr_increase=False
)

# Sort by date
all_events = all_events.sort_values('date').reset_index(drop=True)

# Add event number
all_events['event_number'] = range(1, len(all_events) + 1)

# Reorder columns
columns_order = ['event_number', 'date', 'method', 'gpr_value', 'gpr_diff', 'gpr_pct_change']
all_events = all_events[columns_order]

# Rename columns for clarity
all_events.columns = ['Event_Number', 'Date', 'Detection_Method', 'GPR_Value', 'GPR_Diff', 'GPR_Pct_Change']

# Format date
all_events['Date'] = pd.to_datetime(all_events['Date']).dt.strftime('%Y-%m-%d')

# Round numeric columns
all_events['GPR_Value'] = all_events['GPR_Value'].round(2)
all_events['GPR_Diff'] = all_events['GPR_Diff'].round(2)
all_events['GPR_Pct_Change'] = (all_events['GPR_Pct_Change'] * 100).round(2)

# Save to CSV
output_path = 'results/event_study/detected_events.csv'
all_events.to_csv(output_path, index=False, encoding='utf-8-sig')

print("=" * 80)
print("EXPORTED EVENTS TO CSV")
print("=" * 80)
print(f"\nFile saved to: {output_path}")
print(f"Total events: {len(all_events)}")
print(f"\nBreakdown:")
print(f"  Spike events: {(all_events['Detection_Method'] == 'spike').sum()}")
print(f"  High period events: {(all_events['Detection_Method'] == 'high_period').sum()}")
print(f"\nDate range: {all_events['Date'].min()} to {all_events['Date'].max()}")
print(f"\nFirst 10 events:")
print(all_events.head(10).to_string(index=False))
print(f"\nLast 10 events:")
print(all_events.tail(10).to_string(index=False))


from scripts.detect_events import GPREventDetector
from src.preprocessing import DataPreprocessor
import pandas as pd

# Load data
pre = DataPreprocessor()
data = pre.load_data('data/data.csv')
detector = GPREventDetector(data)

# Detect all events
all_events = detector.detect_all_events(
    spike_percentile=95,
    high_period_percentile=95,
    combine=True,
    require_gpr_increase=False
)

# Sort by date
all_events = all_events.sort_values('date').reset_index(drop=True)

# Add event number
all_events['event_number'] = range(1, len(all_events) + 1)

# Reorder columns
columns_order = ['event_number', 'date', 'method', 'gpr_value', 'gpr_diff', 'gpr_pct_change']
all_events = all_events[columns_order]

# Rename columns for clarity
all_events.columns = ['Event_Number', 'Date', 'Detection_Method', 'GPR_Value', 'GPR_Diff', 'GPR_Pct_Change']

# Format date
all_events['Date'] = pd.to_datetime(all_events['Date']).dt.strftime('%Y-%m-%d')

# Round numeric columns
all_events['GPR_Value'] = all_events['GPR_Value'].round(2)
all_events['GPR_Diff'] = all_events['GPR_Diff'].round(2)
all_events['GPR_Pct_Change'] = (all_events['GPR_Pct_Change'] * 100).round(2)

# Save to CSV
output_path = 'results/event_study/detected_events.csv'
all_events.to_csv(output_path, index=False, encoding='utf-8-sig')

print("=" * 80)
print("EXPORTED EVENTS TO CSV")
print("=" * 80)
print(f"\nFile saved to: {output_path}")
print(f"Total events: {len(all_events)}")
print(f"\nBreakdown:")
print(f"  Spike events: {(all_events['Detection_Method'] == 'spike').sum()}")
print(f"  High period events: {(all_events['Detection_Method'] == 'high_period').sum()}")
print(f"\nDate range: {all_events['Date'].min()} to {all_events['Date'].max()}")
print(f"\nFirst 10 events:")
print(all_events.head(10).to_string(index=False))
print(f"\nLast 10 events:")
print(all_events.tail(10).to_string(index=False))

