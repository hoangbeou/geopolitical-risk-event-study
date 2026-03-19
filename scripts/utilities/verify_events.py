"""Verify event detection counts"""
from scripts.detect_events import GPREventDetector
from src.preprocessing import DataPreprocessor

# Load data
pre = DataPreprocessor()
data = pre.load_data('data/data.csv')
detector = GPREventDetector(data)

# Detect separately
spikes = detector.detect_spikes(threshold_percentile=95, window_days=30)
periods = detector.detect_high_periods(
    threshold_percentile=95, 
    min_separation_days=30, 
    require_increase=False
)

# Detect combined
all_events = detector.detect_all_events(
    spike_percentile=95,
    high_period_percentile=95,
    combine=True,
    require_gpr_increase=False
)

print("=" * 80)
print("EVENT DETECTION VERIFICATION")
print("=" * 80)
print(f"\nSpike events (95th percentile): {len(spikes)}")
print(f"High period events (95th percentile): {len(periods)}")
print(f"\nCombined events (after deduplication): {len(all_events)}")
print(f"\nBreakdown by method:")
print(all_events['method'].value_counts())

print(f"\nFirst 10 events:")
print(all_events[['date', 'method', 'gpr_value']].head(10).to_string())

print(f"\nDate range: {all_events['date'].min()} to {all_events['date'].max()}")


from scripts.detect_events import GPREventDetector
from src.preprocessing import DataPreprocessor

# Load data
pre = DataPreprocessor()
data = pre.load_data('data/data.csv')
detector = GPREventDetector(data)

# Detect separately
spikes = detector.detect_spikes(threshold_percentile=95, window_days=30)
periods = detector.detect_high_periods(
    threshold_percentile=95, 
    min_separation_days=30, 
    require_increase=False
)

# Detect combined
all_events = detector.detect_all_events(
    spike_percentile=95,
    high_period_percentile=95,
    combine=True,
    require_gpr_increase=False
)

print("=" * 80)
print("EVENT DETECTION VERIFICATION")
print("=" * 80)
print(f"\nSpike events (95th percentile): {len(spikes)}")
print(f"High period events (95th percentile): {len(periods)}")
print(f"\nCombined events (after deduplication): {len(all_events)}")
print(f"\nBreakdown by method:")
print(all_events['method'].value_counts())

print(f"\nFirst 10 events:")
print(all_events[['date', 'method', 'gpr_value']].head(10).to_string())

print(f"\nDate range: {all_events['date'].min()} to {all_events['date'].max()}")

