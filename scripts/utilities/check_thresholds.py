"""Check spike and high period thresholds"""
from scripts.detect_events import GPREventDetector
from src.preprocessing import DataPreprocessor
import numpy as np
import pandas as pd

# Load data
pre = DataPreprocessor()
data = pre.load_data('data/data.csv')
detector = GPREventDetector(data)

# Calculate thresholds
gpr_diff = detector.gpr_diff.dropna()
gpr_level = detector.gpr.dropna()

spike_thresh_95 = np.percentile(gpr_diff, 95)
spike_thresh_90 = np.percentile(gpr_diff, 90)
spike_thresh_85 = np.percentile(gpr_diff, 85)

high_thresh_95 = np.percentile(gpr_level, 95)
high_thresh_90 = np.percentile(gpr_level, 90)
high_thresh_85 = np.percentile(gpr_level, 85)

print("=" * 80)
print("THRESHOLD ANALYSIS")
print("=" * 80)
print(f"\nData range: {data.index.min()} to {data.index.max()}")
print(f"Total observations: {len(data)}")
print(f"GPR_diff observations: {len(gpr_diff)}")
print(f"GPR_level observations: {len(gpr_level)}")

print("\n" + "=" * 80)
print("SPIKE THRESHOLDS (GPR_diff)")
print("=" * 80)
print(f"  95th percentile: {spike_thresh_95:.4f} (top 5%)")
print(f"  90th percentile: {spike_thresh_90:.4f} (top 10%)")
print(f"  85th percentile: {spike_thresh_85:.4f} (top 15%)")
print(f"\n  Current setting: 95th percentile = {spike_thresh_95:.4f}")
print(f"  Meaning: GPR_diff > {spike_thresh_95:.4f} is considered a spike")

print("\n" + "=" * 80)
print("HIGH PERIOD THRESHOLDS (GPR level)")
print("=" * 80)
print(f"  95th percentile: {high_thresh_95:.4f} (top 5%)")
print(f"  90th percentile: {high_thresh_90:.4f} (top 10%)")
print(f"  85th percentile: {high_thresh_85:.4f} (top 15%)")
print(f"\n  Current setting: 95th percentile = {high_thresh_95:.4f}")
print(f"  Meaning: GPR > {high_thresh_95:.4f} is considered high period")

# Count how many would be detected
spikes_95 = (gpr_diff > spike_thresh_95).sum()
spikes_90 = (gpr_diff > spike_thresh_90).sum()
high_95 = (gpr_level > high_thresh_95).sum()
high_90 = (gpr_level > high_thresh_90).sum()

print("\n" + "=" * 80)
print("CANDIDATE COUNTS")
print("=" * 80)
print(f"  Spike candidates (95th): {spikes_95} days")
print(f"  Spike candidates (90th): {spikes_90} days")
print(f"  High period candidates (95th): {high_95} days")
print(f"  High period candidates (90th): {high_90} days")


from scripts.detect_events import GPREventDetector
from src.preprocessing import DataPreprocessor
import numpy as np
import pandas as pd

# Load data
pre = DataPreprocessor()
data = pre.load_data('data/data.csv')
detector = GPREventDetector(data)

# Calculate thresholds
gpr_diff = detector.gpr_diff.dropna()
gpr_level = detector.gpr.dropna()

spike_thresh_95 = np.percentile(gpr_diff, 95)
spike_thresh_90 = np.percentile(gpr_diff, 90)
spike_thresh_85 = np.percentile(gpr_diff, 85)

high_thresh_95 = np.percentile(gpr_level, 95)
high_thresh_90 = np.percentile(gpr_level, 90)
high_thresh_85 = np.percentile(gpr_level, 85)

print("=" * 80)
print("THRESHOLD ANALYSIS")
print("=" * 80)
print(f"\nData range: {data.index.min()} to {data.index.max()}")
print(f"Total observations: {len(data)}")
print(f"GPR_diff observations: {len(gpr_diff)}")
print(f"GPR_level observations: {len(gpr_level)}")

print("\n" + "=" * 80)
print("SPIKE THRESHOLDS (GPR_diff)")
print("=" * 80)
print(f"  95th percentile: {spike_thresh_95:.4f} (top 5%)")
print(f"  90th percentile: {spike_thresh_90:.4f} (top 10%)")
print(f"  85th percentile: {spike_thresh_85:.4f} (top 15%)")
print(f"\n  Current setting: 95th percentile = {spike_thresh_95:.4f}")
print(f"  Meaning: GPR_diff > {spike_thresh_95:.4f} is considered a spike")

print("\n" + "=" * 80)
print("HIGH PERIOD THRESHOLDS (GPR level)")
print("=" * 80)
print(f"  95th percentile: {high_thresh_95:.4f} (top 5%)")
print(f"  90th percentile: {high_thresh_90:.4f} (top 10%)")
print(f"  85th percentile: {high_thresh_85:.4f} (top 15%)")
print(f"\n  Current setting: 95th percentile = {high_thresh_95:.4f}")
print(f"  Meaning: GPR > {high_thresh_95:.4f} is considered high period")

# Count how many would be detected
spikes_95 = (gpr_diff > spike_thresh_95).sum()
spikes_90 = (gpr_diff > spike_thresh_90).sum()
high_95 = (gpr_level > high_thresh_95).sum()
high_90 = (gpr_level > high_thresh_90).sum()

print("\n" + "=" * 80)
print("CANDIDATE COUNTS")
print("=" * 80)
print(f"  Spike candidates (95th): {spikes_95} days")
print(f"  Spike candidates (90th): {spikes_90} days")
print(f"  High period candidates (95th): {high_95} days")
print(f"  High period candidates (90th): {high_90} days")

