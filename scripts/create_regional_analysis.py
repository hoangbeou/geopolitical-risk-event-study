"""
Create Comprehensive Regional Pattern Analysis Visualizations with ACT/THREAT
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import json
import warnings
warnings.filterwarnings('ignore')

# Set style
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

REGION_NAMES = {
    'middle_east': 'Middle East',
    'asia': 'Asia',
    'europe': 'Europe',
    'americas': 'Americas',
    'global': 'Global'
}

ACT_THREAT_COLORS = {
    'ACT': '#e74c3c',
    'THREAT': '#3498db'
}


def load_all_event_data():
    """Load all event data with ACT/THREAT classification"""
    # Load CAR data
    car_path = Path('results/event_study/event_classification.csv')
    car_df = pd.read_csv(car_path)
    car_df['Date'] = pd.to_datetime(car_df['Date'])
    
    # Load events
    events_path = Path('results/event_study/identified_events.json')
    with open(events_path, 'r', encoding='utf-8') as f:
        events_dict = json.load(f)
    
    # Merge BTC and GOLD CARs
    btc_cars = car_df[car_df['Asset'] == 'BTC'][['Event', 'Date', 'CAR', 'CAR_pct']].rename(
        columns={'CAR': 'BTC_car', 'CAR_pct': 'BTC_car_pct'})
    gold_cars = car_df[car_df['Asset'] == 'GOLD'][['Event', 'Date', 'CAR', 'CAR_pct']].rename(
        columns={'CAR': 'GOLD_car', 'CAR_pct': 'GOLD_car_pct'})
    
    # Merge
    merged = pd.merge(btc_cars, gold_cars, on=['Event', 'Date'], how='outer', suffixes=('', '_gold'))
    
    # Add event info
    merged['name'] = merged['Event'].map(
        lambda x: events_dict.get(x, {}).get('identified', {}).get('name', 'Unknown'))
    merged['region'] = merged['Event'].map(
        lambda x: events_dict.get(x, {}).get('identified', {}).get('region', 'unknown'))
    merged['act_threat'] = merged['Event'].map(
        lambda x: events_dict.get(x, {}).get('identified', {}).get('act_threat', 'unknown'))
    merged['category'] = merged['Event'].map(
        lambda x: events_dict.get(x, {}).get('identified', {}).get('category', 0))
    merged['category_name'] = merged['Event'].map(
        lambda x: events_dict.get(x, {}).get('identified', {}).get('category_name', 'unknown'))
    merged['date'] = merged['Date']
    
    return merged


def prepare_data(df):
    """Prepare data with pattern classification"""
    df['pattern'] = df.apply(lambda r: 
        'BTC_UP_GOLD_UP' if (pd.notna(r['BTC_car']) and pd.notna(r['GOLD_car']) and r['BTC_car'] > 0 and r['GOLD_car'] > 0) else
        ('BTC_DOWN_GOLD_DOWN' if (pd.notna(r['BTC_car']) and pd.notna(r['GOLD_car']) and r['BTC_car'] < 0 and r['GOLD_car'] < 0) else
        ('BTC_UP_GOLD_DOWN' if (pd.notna(r['BTC_car']) and pd.notna(r['GOLD_car']) and r['BTC_car'] > 0 and r['GOLD_car'] < 0) else
        ('BTC_DOWN_GOLD_UP' if (pd.notna(r['BTC_car']) and pd.notna(r['GOLD_car']) and r['BTC_car'] < 0 and r['GOLD_car'] > 0) else 'Unknown'))), axis=1)
    return df


def create_regional_car_comparison(df, output_dir):
    """Compare average CAR by region for BTC and GOLD"""
    
    plot_df = df[(df['region'].notna()) & (df['pattern'] != 'Unknown')]
    
    # Calculate average CAR by region
    regional_stats = []
    for region in plot_df['region'].unique():
        region_df = plot_df[plot_df['region'] == region]
        regional_stats.append({
            'Region': REGION_NAMES.get(region, region.title()),
            'BTC_Mean': region_df['BTC_car'].mean() * 100,
            'BTC_Std': region_df['BTC_car'].std() * 100,
            'GOLD_Mean': region_df['GOLD_car'].mean() * 100,
            'GOLD_Std': region_df['GOLD_car'].std() * 100,
            'Count': len(region_df)
        })
    
    stats_df = pd.DataFrame(regional_stats).sort_values('BTC_Mean', ascending=False)
    
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))
    
    x_pos = np.arange(len(stats_df))
    width = 0.35
    
    # BTC CAR
    axes[0].bar(x_pos - width/2, stats_df['BTC_Mean'], width, 
               yerr=stats_df['BTC_Std'], label='BTC', color='#1f77b4', 
               alpha=0.8, capsize=5, edgecolor='black', linewidth=0.5)
    axes[0].axhline(y=0, color='gray', linestyle='-', linewidth=0.8)
    axes[0].set_xlabel('Region', fontsize=12, fontweight='bold')
    axes[0].set_ylabel('Average CAR (%)', fontsize=12, fontweight='bold')
    axes[0].set_title('Average BTC CAR by Region', fontsize=13, fontweight='bold')
    axes[0].set_xticks(x_pos)
    axes[0].set_xticklabels(stats_df['Region'], rotation=45, ha='right')
    axes[0].grid(True, alpha=0.3, axis='y')
    axes[0].legend(fontsize=10)
    
    # Add count annotations
    for i, (idx, row) in enumerate(stats_df.iterrows()):
        axes[0].text(i, row['BTC_Mean'] + row['BTC_Std'] + 1, f"n={int(row['Count'])}", 
                    ha='center', fontsize=9, alpha=0.7)
    
    # GOLD CAR
    axes[1].bar(x_pos - width/2, stats_df['GOLD_Mean'], width,
               yerr=stats_df['GOLD_Std'], label='GOLD', color='#ff7f0e',
               alpha=0.8, capsize=5, edgecolor='black', linewidth=0.5)
    axes[1].axhline(y=0, color='gray', linestyle='-', linewidth=0.8)
    axes[1].set_xlabel('Region', fontsize=12, fontweight='bold')
    axes[1].set_ylabel('Average CAR (%)', fontsize=12, fontweight='bold')
    axes[1].set_title('Average GOLD CAR by Region', fontsize=13, fontweight='bold')
    axes[1].set_xticks(x_pos)
    axes[1].set_xticklabels(stats_df['Region'], rotation=45, ha='right')
    axes[1].grid(True, alpha=0.3, axis='y')
    axes[1].legend(fontsize=10)
    
    # Add count annotations
    for i, (idx, row) in enumerate(stats_df.iterrows()):
        axes[1].text(i, row['GOLD_Mean'] + row['GOLD_Std'] + 1, f"n={int(row['Count'])}", 
                    ha='center', fontsize=9, alpha=0.7)
    
    plt.suptitle('Regional CAR Comparison: BTC vs GOLD', fontsize=14, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig(f'{output_dir}/regional_car_comparison.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    print("[OK] Regional CAR comparison saved")


def create_regional_act_threat_analysis(df, output_dir):
    """Analyze ACT/THREAT distribution by region"""
    
    plot_df = df[(df['region'].notna()) & (df['act_threat'].isin(['ACT', 'THREAT']))]
    
    # Create crosstab
    act_threat_region = pd.crosstab(plot_df['act_threat'], plot_df['region'], margins=False)
    act_threat_region.columns = [REGION_NAMES.get(c, c.title()) for c in act_threat_region.columns]
    
    # Also create percentage version
    act_threat_region_pct = act_threat_region.div(act_threat_region.sum(axis=0), axis=1) * 100
    
    fig, axes = plt.subplots(1, 2, figsize=(18, 6))
    
    # Count heatmap
    sns.heatmap(act_threat_region, annot=True, fmt='d', cmap='YlOrRd', 
               cbar_kws={'label': 'Number of Events'}, ax=axes[0], 
               linewidths=0.5, linecolor='gray')
    axes[0].set_title('ACT/THREAT Distribution by Region (Count)', 
                     fontsize=12, fontweight='bold', pad=15)
    axes[0].set_xlabel('Region', fontsize=11, fontweight='bold')
    axes[0].set_ylabel('ACT/THREAT', fontsize=11, fontweight='bold')
    
    # Percentage heatmap
    sns.heatmap(act_threat_region_pct, annot=True, fmt='.1f', cmap='YlOrRd', 
               cbar_kws={'label': 'Percentage (%)'}, ax=axes[1],
               linewidths=0.5, linecolor='gray')
    axes[1].set_title('ACT/THREAT Distribution by Region (Percentage)', 
                     fontsize=12, fontweight='bold', pad=15)
    axes[1].set_xlabel('Region', fontsize=11, fontweight='bold')
    axes[1].set_ylabel('ACT/THREAT', fontsize=11, fontweight='bold')
    
    plt.suptitle('Regional ACT/THREAT Distribution', fontsize=14, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig(f'{output_dir}/regional_act_threat_heatmap.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    print("[OK] Regional ACT/THREAT heatmap saved")


def create_regional_scatter(df, output_dir):
    """Scatter plot: BTC CAR vs GOLD CAR, colored by region"""
    
    plot_df = df[(df['region'].notna()) & 
                 (df['BTC_car'].notna()) & 
                 (df['GOLD_car'].notna())]
    
    if len(plot_df) == 0:
        print("Warning: No data for regional scatter")
        return
    
    fig, ax = plt.subplots(figsize=(14, 10))
    
    # Color map for regions
    region_colors = {
        'asia': '#2ca02c',
        'middle_east': '#d62728',
        'europe': '#1f77b4',
        'americas': '#ff7f0e',
        'global': '#9467bd'
    }
    
    for region in plot_df['region'].unique():
        region_df = plot_df[plot_df['region'] == region]
        color = region_colors.get(region, '#808080')
        
        # Size based on ACT/THREAT
        sizes = []
        for _, row in region_df.iterrows():
            if row.get('act_threat') == 'ACT':
                sizes.append(300)
            elif row.get('act_threat') == 'THREAT':
                sizes.append(200)
            else:
                sizes.append(150)
        
        ax.scatter(
            region_df['GOLD_car'] * 100,
            region_df['BTC_car'] * 100,
            s=sizes,
            c=color,
            label=REGION_NAMES.get(region, region.title()),
            alpha=0.6,
            edgecolors='black',
            linewidth=0.5
        )
    
    # Add quadrant lines
    ax.axhline(y=0, color='gray', linestyle='--', linewidth=0.8, alpha=0.5)
    ax.axvline(x=0, color='gray', linestyle='--', linewidth=0.8, alpha=0.5)
    
    # Add quadrant labels
    ax.text(0.02, 0.98, 'Quadrant I:\nBTC↑ GOLD↑', 
            transform=ax.transAxes, fontsize=10, verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.3))
    ax.text(0.98, 0.98, 'Quadrant II:\nBTC↓ GOLD↑', 
            transform=ax.transAxes, fontsize=10, verticalalignment='top', horizontalalignment='right',
            bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.3))
    ax.text(0.02, 0.02, 'Quadrant III:\nBTC↓ GOLD↓', 
            transform=ax.transAxes, fontsize=10, verticalalignment='bottom',
            bbox=dict(boxstyle='round', facecolor='lightcoral', alpha=0.3))
    ax.text(0.98, 0.02, 'Quadrant IV:\nBTC↑ GOLD↓', 
            transform=ax.transAxes, fontsize=10, verticalalignment='bottom', horizontalalignment='right',
            bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.3))
    
    ax.set_xlabel('GOLD Cumulative Abnormal Return (CAR, %)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Bitcoin Cumulative Abnormal Return (CAR, %)', fontsize=12, fontweight='bold')
    ax.set_title('Regional Regime Map: BTC vs GOLD Response by Region', 
                fontsize=14, fontweight='bold', pad=20)
    ax.legend(title='Region', fontsize=10, title_fontsize=11, loc='upper left')
    ax.text(0.02, 0.05, 'Point size: ACT (large), THREAT (medium)', 
            transform=ax.transAxes, fontsize=9, style='italic', alpha=0.7)
    ax.grid(True, alpha=0.3, linestyle=':')
    
    plt.tight_layout()
    plt.savefig(f'{output_dir}/regional_regime_map.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    print("[OK] Regional regime map saved")


def create_regional_detailed_analysis(df, output_dir):
    """Detailed analysis table for each region"""
    
    plot_df = df[(df['region'].notna()) & (df['pattern'] != 'Unknown')]
    
    analysis_data = []
    
    for region in plot_df['region'].unique():
        region_df = plot_df[plot_df['region'] == region]
        
        # Overall stats
        btc_mean = region_df['BTC_car'].mean() * 100
        gold_mean = region_df['GOLD_car'].mean() * 100
        count = len(region_df)
        
        # Pattern distribution
        pattern_counts = region_df['pattern'].value_counts()
        dominant_pattern = pattern_counts.index[0] if len(pattern_counts) > 0 else 'N/A'
        dominant_count = pattern_counts.iloc[0] if len(pattern_counts) > 0 else 0
        
        # ACT/THREAT distribution
        act_threat_counts = region_df[region_df['act_threat'].isin(['ACT', 'THREAT'])]['act_threat'].value_counts()
        dominant_act_threat = act_threat_counts.index[0] if len(act_threat_counts) > 0 else 'N/A'
        
        # Average CAR by pattern
        pattern_cars = {}
        for pattern in region_df['pattern'].unique():
            pattern_df = region_df[region_df['pattern'] == pattern]
            if len(pattern_df) > 0:
                pattern_cars[pattern] = {
                    'BTC': pattern_df['BTC_car'].mean() * 100,
                    'GOLD': pattern_df['GOLD_car'].mean() * 100,
                    'count': len(pattern_df)
                }
        
        analysis_data.append({
            'Region': REGION_NAMES.get(region, region.title()),
            'Total_Events': count,
            'Avg_BTC_CAR': btc_mean,
            'Avg_GOLD_CAR': gold_mean,
            'Dominant_Pattern': dominant_pattern.replace('_', ' ').replace('UP', '↑').replace('DOWN', '↓'),
            'Dominant_Pattern_Count': dominant_count,
            'Dominant_ACT_THREAT': dominant_act_threat,
            'Patterns': len(pattern_counts)
        })
    
    analysis_df = pd.DataFrame(analysis_data)
    analysis_df = analysis_df.sort_values('Avg_BTC_CAR', ascending=False)
    
    # Save to CSV
    analysis_df.to_csv(f'{output_dir}/regional_detailed_analysis.csv', index=False)
    
    # Create summary visualization
    fig, ax = plt.subplots(figsize=(12, 6))
    
    x_pos = np.arange(len(analysis_df))
    width = 0.35
    
    bars1 = ax.bar(x_pos - width/2, analysis_df['Avg_BTC_CAR'], width, 
                  label='BTC', color='#1f77b4', alpha=0.8, edgecolor='black', linewidth=0.5)
    bars2 = ax.bar(x_pos + width/2, analysis_df['Avg_GOLD_CAR'], width,
                  label='GOLD', color='#ff7f0e', alpha=0.8, edgecolor='black', linewidth=0.5)
    
    ax.axhline(y=0, color='gray', linestyle='-', linewidth=0.8)
    ax.set_xlabel('Region', fontsize=12, fontweight='bold')
    ax.set_ylabel('Average CAR (%)', fontsize=12, fontweight='bold')
    ax.set_title('Regional Summary: Average CAR by Region', fontsize=14, fontweight='bold', pad=20)
    ax.set_xticks(x_pos)
    ax.set_xticklabels(analysis_df['Region'], rotation=45, ha='right')
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3, axis='y')
    
    # Add annotations
    for i, (idx, row) in enumerate(analysis_df.iterrows()):
        ax.text(i, max(row['Avg_BTC_CAR'], row['Avg_GOLD_CAR']) + 2, 
               f"n={int(row['Total_Events'])}", ha='center', fontsize=9, alpha=0.7)
    
    plt.tight_layout()
    plt.savefig(f'{output_dir}/regional_summary.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    print("[OK] Regional detailed analysis saved")
    print(f"[OK] Analysis table saved to {output_dir}/regional_detailed_analysis.csv")


def create_regional_event_list(df, output_dir):
    """Create detailed event list for each region with top events"""
    
    plot_df = df[(df['region'].notna()) & (df['pattern'] != 'Unknown')]
    
    output_text = []
    output_text.append("=" * 80)
    output_text.append("REGIONAL PATTERN ANALYSIS - DETAILED EVENT LIST")
    output_text.append("=" * 80)
    output_text.append("")
    
    for region in sorted(plot_df['region'].unique()):
        region_df = plot_df[plot_df['region'] == region].copy()
        region_df = region_df.sort_values('BTC_car', ascending=False)
        
        output_text.append(f"\n{'=' * 80}")
        output_text.append(f"REGION: {REGION_NAMES.get(region, region.title()).upper()}")
        output_text.append(f"{'=' * 80}")
        output_text.append(f"Total Events: {len(region_df)}")
        output_text.append(f"Average BTC CAR: {region_df['BTC_car'].mean()*100:.2f}%")
        output_text.append(f"Average GOLD CAR: {region_df['GOLD_car'].mean()*100:.2f}%")
        output_text.append("")
        
        # Pattern breakdown
        output_text.append("Pattern Distribution:")
        pattern_counts = region_df['pattern'].value_counts()
        for pattern, count in pattern_counts.items():
            pct = count / len(region_df) * 100
            pattern_name = pattern.replace('_', ' ').replace('UP', '↑').replace('DOWN', '↓')
            output_text.append(f"  {pattern_name}: {count} events ({pct:.1f}%)")
        output_text.append("")
        
        # ACT/THREAT breakdown
        output_text.append("ACT/THREAT Distribution:")
        act_threat_counts = region_df[region_df['act_threat'].isin(['ACT', 'THREAT'])]['act_threat'].value_counts()
        for at, count in act_threat_counts.items():
            pct = count / len(region_df) * 100
            output_text.append(f"  {at}: {count} events ({pct:.1f}%)")
        output_text.append("")
        
        # Top 5 events
        output_text.append("Top 5 Events (by BTC CAR):")
        for idx, (_, row) in enumerate(region_df.head(5).iterrows(), 1):
            pattern_name = row['pattern'].replace('_', ' ').replace('UP', '↑').replace('DOWN', '↓')
            output_text.append(f"  {idx}. {row.get('name', row['Event'])}")
            output_text.append(f"     Date: {row.get('date', 'N/A')}")
            output_text.append(f"     Pattern: {pattern_name}")
            output_text.append(f"     ACT/THREAT: {row.get('act_threat', 'N/A')}")
            output_text.append(f"     BTC CAR: {row['BTC_car']*100:.2f}%, GOLD CAR: {row['GOLD_car']*100:.2f}%")
            output_text.append("")
    
    # Save to file
    output_file = Path(output_dir) / 'regional_event_list.txt'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(output_text))
    
    print(f"[OK] Regional event list saved to {output_file}")


def main():
    """Main function"""
    print("=" * 60)
    print("Creating Regional Pattern Analysis Visualizations with ACT/THREAT")
    print("=" * 60)
    
    output_dir = Path('results/event_study/advanced_visualizations')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("\nLoading data...")
    df = load_all_event_data()
    df = prepare_data(df)
    print(f"Loaded {len(df)} events")
    
    print("\n1. Creating regional CAR comparison...")
    create_regional_car_comparison(df, output_dir)
    
    print("\n2. Creating regional ACT/THREAT analysis...")
    create_regional_act_threat_analysis(df, output_dir)
    
    print("\n3. Creating regional regime map...")
    create_regional_scatter(df, output_dir)
    
    print("\n4. Creating regional detailed analysis...")
    create_regional_detailed_analysis(df, output_dir)
    
    print("\n5. Creating regional event list...")
    create_regional_event_list(df, output_dir)
    
    print("\n" + "=" * 60)
    print("All regional analysis visualizations complete!")
    print("=" * 60)


if __name__ == '__main__':
    main()
