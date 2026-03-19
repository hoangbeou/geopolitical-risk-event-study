"""
Classify events into ACT vs THREAT based on GPR_ACT and GPR_THREAT
Then analyze CAR differences between the two types
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# Load data
print("="*100)
print("CLASSIFYING EVENTS: ACT vs THREAT")
print("="*100)
print()

# Load raw data to get GPR_ACT and GPR_THREAT
raw_data = pd.read_csv('data/raw/data.csv', index_col=0, parse_dates=True, dayfirst=True)
if not isinstance(raw_data.index, pd.DatetimeIndex):
    raw_data.index = pd.to_datetime(raw_data.index, dayfirst=True, format='mixed')

# Load events with CAR
events_df = pd.read_csv('results/events_complete.csv')
events_df['date'] = pd.to_datetime(events_df['date'])

print(f"Loaded {len(events_df)} events")
print(f"Raw data columns: {raw_data.columns.tolist()}")
print()

# Merge to get GPR_ACT and GPR_THREAT for each event
events_with_act_threat = []

for idx, row in events_df.iterrows():
    event_date = row['date']
    
    # Find closest date in raw data
    if event_date in raw_data.index:
        gpr_act = raw_data.loc[event_date, 'GPRD_ACT']
        gpr_threat = raw_data.loc[event_date, 'GPRD_THREAT']
    else:
        # Find nearest date
        nearest_idx = raw_data.index.get_indexer([event_date], method='nearest')[0]
        nearest_date = raw_data.index[nearest_idx]
        gpr_act = raw_data.loc[nearest_date, 'GPRD_ACT']
        gpr_threat = raw_data.loc[nearest_date, 'GPRD_THREAT']
    
    # Classify based on which is higher
    if pd.notna(gpr_act) and pd.notna(gpr_threat):
        if gpr_act > gpr_threat:
            event_type = 'ACT'
            dominant_value = gpr_act
        elif gpr_threat > gpr_act:
            event_type = 'THREAT'
            dominant_value = gpr_threat
        else:
            event_type = 'EQUAL'
            dominant_value = gpr_act
        
        act_threat_ratio = gpr_act / (gpr_threat + 1e-6)  # Avoid division by zero
    else:
        event_type = 'UNKNOWN'
        dominant_value = np.nan
        act_threat_ratio = np.nan
    
    events_with_act_threat.append({
        **row.to_dict(),
        'GPR_ACT': gpr_act,
        'GPR_THREAT': gpr_threat,
        'Event_Type': event_type,
        'Dominant_Value': dominant_value,
        'ACT_THREAT_Ratio': act_threat_ratio
    })

# Create new dataframe
df_classified = pd.DataFrame(events_with_act_threat)

# Save
output_path = Path('results/events_classified_act_threat.csv')
df_classified.to_csv(output_path, index=False, encoding='utf-8-sig')
print(f"✓ Saved classified events to {output_path}")
print()

# Statistics
print("="*100)
print("CLASSIFICATION STATISTICS")
print("="*100)
print()

type_counts = df_classified['Event_Type'].value_counts()
print("Event Type Distribution:")
for event_type, count in type_counts.items():
    print(f"  {event_type}: {count} events ({count/len(df_classified)*100:.1f}%)")
print()

# Compare CAR between ACT and THREAT
print("="*100)
print("CAR COMPARISON: ACT vs THREAT")
print("="*100)
print()

for asset in ['BTC', 'GOLD', 'OIL']:
    car_col = f'{asset}_CAR'
    
    print(f"{asset}:")
    
    act_events = df_classified[df_classified['Event_Type'] == 'ACT']
    threat_events = df_classified[df_classified['Event_Type'] == 'THREAT']
    
    if len(act_events) > 0:
        act_mean = act_events[car_col].mean()
        act_median = act_events[car_col].median()
        act_std = act_events[car_col].std()
        print(f"  ACT events ({len(act_events)}):")
        print(f"    Mean CAR: {act_mean:.6f} ({act_mean*100:+.2f}%)")
        print(f"    Median CAR: {act_median:.6f} ({act_median*100:+.2f}%)")
        print(f"    Std Dev: {act_std:.6f}")
    
    if len(threat_events) > 0:
        threat_mean = threat_events[car_col].mean()
        threat_median = threat_events[car_col].median()
        threat_std = threat_events[car_col].std()
        print(f"  THREAT events ({len(threat_events)}):")
        print(f"    Mean CAR: {threat_mean:.6f} ({threat_mean*100:+.2f}%)")
        print(f"    Median CAR: {threat_median:.6f} ({threat_median*100:+.2f}%)")
        print(f"    Std Dev: {threat_std:.6f}")
    
    # T-test for difference
    if len(act_events) > 0 and len(threat_events) > 0:
        from scipy import stats
        act_data = act_events[car_col].dropna()
        threat_data = threat_events[car_col].dropna()
        
        if len(act_data) > 1 and len(threat_data) > 1:
            t_stat, p_value = stats.ttest_ind(act_data, threat_data)
            print(f"  T-test: t={t_stat:.3f}, p={p_value:.4f}", end="")
            if p_value < 0.05:
                print(" ***")
            elif p_value < 0.10:
                print(" *")
            else:
                print()
    
    print()

# Visualize
print("Creating visualizations...")
output_dir = Path('results/act_threat_analysis')
output_dir.mkdir(parents=True, exist_ok=True)

# Box plot comparison
fig, axes = plt.subplots(1, 3, figsize=(18, 6))

for idx, asset in enumerate(['BTC', 'GOLD', 'OIL']):
    car_col = f'{asset}_CAR'
    
    # Prepare data for box plot
    act_data = df_classified[df_classified['Event_Type'] == 'ACT'][car_col].dropna()
    threat_data = df_classified[df_classified['Event_Type'] == 'THREAT'][car_col].dropna()
    
    data_to_plot = [act_data, threat_data]
    labels = ['ACT', 'THREAT']
    
    bp = axes[idx].boxplot(data_to_plot, labels=labels, patch_artist=True)
    
    # Color boxes
    colors = ['lightblue', 'lightcoral']
    for patch, color in zip(bp['boxes'], colors):
        patch.set_facecolor(color)
    
    axes[idx].set_title(f'{asset} - CAR Distribution', fontsize=12, fontweight='bold')
    axes[idx].set_ylabel('CAR')
    axes[idx].axhline(y=0, color='black', linestyle='-', linewidth=0.5)
    axes[idx].grid(True, alpha=0.3)

plt.suptitle('CAR Comparison: ACT vs THREAT Events', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig(output_dir / 'act_vs_threat_boxplot.png', dpi=300, bbox_inches='tight')
plt.close()

print(f"✓ Saved: {output_dir / 'act_vs_threat_boxplot.png'}")

# Bar plot - mean comparison
fig, ax = plt.subplots(figsize=(12, 6))

act_means = []
threat_means = []
assets = ['BTC', 'GOLD', 'OIL']

for asset in assets:
    car_col = f'{asset}_CAR'
    act_mean = df_classified[df_classified['Event_Type'] == 'ACT'][car_col].mean()
    threat_mean = df_classified[df_classified['Event_Type'] == 'THREAT'][car_col].mean()
    act_means.append(act_mean)
    threat_means.append(threat_mean)

x = np.arange(len(assets))
width = 0.35

ax.bar(x - width/2, act_means, width, label='ACT', alpha=0.8, color='lightblue')
ax.bar(x + width/2, threat_means, width, label='THREAT', alpha=0.8, color='lightcoral')

ax.set_xlabel('Asset', fontsize=12, fontweight='bold')
ax.set_ylabel('Mean CAR', fontsize=12, fontweight='bold')
ax.set_title('Mean CAR Comparison: ACT vs THREAT Events', fontsize=14, fontweight='bold')
ax.set_xticks(x)
ax.set_xticklabels(assets)
ax.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
ax.legend()
ax.grid(True, alpha=0.3, axis='y')

plt.tight_layout()
plt.savefig(output_dir / 'act_vs_threat_mean_comparison.png', dpi=300, bbox_inches='tight')
plt.close()

print(f"✓ Saved: {output_dir / 'act_vs_threat_mean_comparison.png'}")

print()
print("="*100)
print("✅ ACT vs THREAT ANALYSIS COMPLETE!")
print("="*100)
print()
print("Key files created:")
print("  - results/events_classified_act_threat.csv")
print("  - results/act_threat_analysis/act_vs_threat_boxplot.png")
print("  - results/act_threat_analysis/act_vs_threat_mean_comparison.png")
print()

