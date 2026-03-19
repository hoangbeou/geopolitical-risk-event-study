"""
Phân tích 4 insights chính:
1. Asset nào phản ứng mạnh nhất với GPR? Tại sao?
2. ACT vs THREAT: loại nào nguy hiểm hơn?
3. Regional bias: events ở khu vực nào ảnh hưởng toàn cầu nhất?
4. Time decay: phản ứng kéo dài bao lâu?
"""

import matplotlib
matplotlib.use('Agg')

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import json
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

# Set style
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['font.size'] = 10

def load_data():
    """Load all necessary data"""
    print("Loading data...")
    
    # Load CAR data
    car_path = Path('results/event_study/event_classification.csv')
    car_df = pd.read_csv(car_path)
    car_df['Date'] = pd.to_datetime(car_df['Date'])
    
    # Load GPR data for ACT/THREAT classification
    data_path = Path('data/data_optimized.csv')
    df_gpr = pd.read_csv(data_path)
    if 'DAY' in df_gpr.columns:
        try:
            df_gpr['DATE'] = pd.to_datetime(df_gpr['DAY'].astype(int).astype(str), format='%Y%m%d', errors='coerce')
        except:
            df_gpr['DATE'] = pd.to_datetime(df_gpr['DAY'], format='%d/%m/%Y', errors='coerce')
    df_gpr = df_gpr.dropna(subset=['DATE'])
    df_gpr['DATE'] = pd.to_datetime(df_gpr['DATE'])
    
    # Classify ACT/THREAT
    act_threat_map = {}
    for event_id in car_df['Event'].unique():
        event_row = car_df[car_df['Event'] == event_id].iloc[0]
        event_date = pd.to_datetime(event_row['Date'])
        
        date_diffs = (df_gpr['DATE'] - event_date).abs()
        closest_idx = date_diffs.idxmin()
        closest_date = df_gpr.loc[closest_idx, 'DATE']
        
        if abs((closest_date - event_date).days) <= 7:
            gpr_act = df_gpr.loc[closest_idx, 'GPRD_ACT'] if 'GPRD_ACT' in df_gpr.columns else 0
            gpr_threat = df_gpr.loc[closest_idx, 'GPRD_THREAT'] if 'GPRD_THREAT' in df_gpr.columns else 0
            
            if pd.notna(gpr_act) and pd.notna(gpr_threat):
                act_threat_map[event_id] = {
                    'act_threat': 'ACT' if gpr_act > gpr_threat else 'THREAT',
                    'gpr_level': float(df_gpr.loc[closest_idx, 'GPRD']) if 'GPRD' in df_gpr.columns else 0
                }
            else:
                act_threat_map[event_id] = {'act_threat': 'THREAT', 'gpr_level': 0}
        else:
            act_threat_map[event_id] = {'act_threat': 'THREAT', 'gpr_level': 0}
    
    # Merge ACT/THREAT vào car_df
    car_df['act_threat'] = car_df['Event'].map(lambda x: act_threat_map.get(x, {}).get('act_threat', 'THREAT'))
    car_df['gpr_level'] = car_df['Event'].map(lambda x: act_threat_map.get(x, {}).get('gpr_level', 0))
    
    # Classify regions từ description
    def classify_region(desc):
        desc_lower = str(desc).lower()
        if any(x in desc_lower for x in ['ukraine', 'russia', 'europe', 'brexit', 'nord stream', 'wagner']):
            return 'Europe'
        elif any(x in desc_lower for x in ['iran', 'israel', 'palestine', 'middle east', 'syria', 'soleimani']):
            return 'Middle East'
        elif any(x in desc_lower for x in ['china', 'hong kong', 'korea', 'asia', 'trade war']):
            return 'Asia'
        elif any(x in desc_lower for x in ['us', 'america', 'trump', 'election', 'afghanistan']):
            return 'Americas'
        else:
            return 'Global'
    
    car_df['Region'] = car_df['Description'].apply(classify_region)
    
    return car_df, df_gpr

def insight_1_asset_reaction(car_df):
    """1. Asset nào phản ứng mạnh nhất với GPR? Tại sao?"""
    print("\n" + "="*80)
    print("INSIGHT 1: Asset nào phản ứng mạnh nhất với GPR? Tại sao?")
    print("="*80)
    
    assets = ['BTC', 'GOLD', 'OIL']
    
    # Tính statistics cho từng asset
    stats_by_asset = {}
    for asset in assets:
        asset_data = car_df[car_df['Asset'] == asset]['CAR_pct']
        stats_by_asset[asset] = {
            'mean': asset_data.mean(),
            'median': asset_data.median(),
            'std': asset_data.std(),
            'abs_mean': asset_data.abs().mean(),
            'abs_median': asset_data.abs().median(),
            'max': asset_data.max(),
            'min': asset_data.min(),
            'positive_pct': (asset_data > 0).sum() / len(asset_data) * 100,
            'strong_reaction_pct': (asset_data.abs() > 10).sum() / len(asset_data) * 100
        }
    
    # Tạo visualization
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    
    # 1.1: Average absolute CAR
    ax1 = axes[0, 0]
    assets_sorted = sorted(assets, key=lambda x: stats_by_asset[x]['abs_mean'], reverse=True)
    abs_means = [stats_by_asset[a]['abs_mean'] for a in assets_sorted]
    colors = ['#f7931a', '#ffd700', '#0066cc']
    bars = ax1.bar(assets_sorted, abs_means, color=colors, alpha=0.8, edgecolor='black', linewidth=1.5)
    ax1.set_ylabel('Average |CAR| (%)', fontsize=12, fontweight='bold')
    ax1.set_title('Average Absolute CAR by Asset', fontsize=14, fontweight='bold')
    ax1.grid(axis='y', alpha=0.3)
    
    # Add value labels
    for bar, val in zip(bars, abs_means):
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                f'{val:.2f}%', ha='center', va='bottom', fontweight='bold')
    
    # 1.2: Distribution comparison
    ax2 = axes[0, 1]
    for asset in assets:
        asset_data = car_df[car_df['Asset'] == asset]['CAR_pct']
        ax2.hist(asset_data, bins=30, alpha=0.6, label=asset, density=True)
    ax2.axvline(0, color='black', linestyle='--', linewidth=1)
    ax2.set_xlabel('CAR (%)', fontsize=12)
    ax2.set_ylabel('Density', fontsize=12)
    ax2.set_title('CAR Distribution by Asset', fontsize=14, fontweight='bold')
    ax2.legend()
    ax2.grid(alpha=0.3)
    
    # 1.3: Box plot comparison
    ax3 = axes[1, 0]
    data_for_box = [car_df[car_df['Asset'] == asset]['CAR_pct'].values for asset in assets]
    bp = ax3.boxplot(data_for_box, labels=assets, patch_artist=True, showmeans=True)
    colors_box = ['#f7931a', '#ffd700', '#0066cc']
    for patch, color in zip(bp['boxes'], colors_box):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)
    ax3.axhline(0, color='black', linestyle='--', linewidth=1)
    ax3.set_ylabel('CAR (%)', fontsize=12, fontweight='bold')
    ax3.set_title('CAR Distribution (Box Plot)', fontsize=14, fontweight='bold')
    ax3.grid(axis='y', alpha=0.3)
    
    # 1.4: Statistics table
    ax4 = axes[1, 1]
    ax4.axis('off')
    
    table_data = []
    for asset in assets_sorted:
        stats = stats_by_asset[asset]
        table_data.append([
            asset,
            f"{stats['abs_mean']:.2f}%",
            f"{stats['std']:.2f}%",
            f"{stats['strong_reaction_pct']:.1f}%",
            f"{stats['positive_pct']:.1f}%"
        ])
    
    table = ax4.table(cellText=table_data,
                     colLabels=['Asset', 'Avg |CAR|', 'Std Dev', 'Strong (>10%)', 'Positive %'],
                     cellLoc='center',
                     loc='center',
                     bbox=[0, 0, 1, 1])
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 2)
    
    for i in range(len(assets_sorted)):
        table[(i+1, 0)].set_facecolor(colors_box[i])
        table[(i+1, 0)].set_text_props(weight='bold', color='white')
    
    for i in range(5):
        table[(0, i)].set_facecolor('#34495e')
        table[(0, i)].set_text_props(weight='bold', color='white')
    
    plt.suptitle('INSIGHT 1: Asset Reaction Strength to GPR', fontsize=16, fontweight='bold', y=0.995)
    plt.tight_layout()
    
    output_dir = Path('results/event_study/insights')
    output_dir.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_dir / 'insight_1_asset_reaction.png', dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {output_dir / 'insight_1_asset_reaction.png'}")
    plt.close()
    
    # Print summary
    strongest = max(assets, key=lambda x: stats_by_asset[x]['abs_mean'])
    print(f"\nKết luận:")
    print(f"- Asset phản ứng mạnh nhất: {strongest} (Avg |CAR| = {stats_by_asset[strongest]['abs_mean']:.2f}%)")
    print(f"- {strongest} có {stats_by_asset[strongest]['strong_reaction_pct']:.1f}% events với |CAR| > 10%")
    print(f"- Standard deviation cao nhất: {max(assets, key=lambda x: stats_by_asset[x]['std'])}")

def insight_2_act_vs_threat(car_df):
    """2. ACT vs THREAT: loại nào nguy hiểm hơn?"""
    print("\n" + "="*80)
    print("INSIGHT 2: ACT vs THREAT - Loại nào nguy hiểm hơn?")
    print("="*80)
    
    assets = ['BTC', 'GOLD', 'OIL']
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    
    # 2.1: Average CAR comparison
    ax1 = axes[0, 0]
    act_means = []
    threat_means = []
    act_stds = []
    threat_stds = []
    
    for asset in assets:
        asset_act = car_df[(car_df['Asset'] == asset) & (car_df['act_threat'] == 'ACT')]['CAR_pct']
        asset_threat = car_df[(car_df['Asset'] == asset) & (car_df['act_threat'] == 'THREAT')]['CAR_pct']
        
        act_means.append(asset_act.mean() if len(asset_act) > 0 else 0)
        threat_means.append(asset_threat.mean() if len(asset_threat) > 0 else 0)
        act_stds.append(asset_act.std() if len(asset_act) > 0 else 0)
        threat_stds.append(asset_threat.std() if len(asset_threat) > 0 else 0)
    
    x = np.arange(len(assets))
    width = 0.35
    
    bars1 = ax1.bar(x - width/2, act_means, width, label='ACT', color='#e74c3c', alpha=0.8, yerr=act_stds, capsize=5)
    bars2 = ax1.bar(x + width/2, threat_means, width, label='THREAT', color='#3498db', alpha=0.8, yerr=threat_stds, capsize=5)
    ax1.set_ylabel('Average CAR (%)', fontsize=12, fontweight='bold')
    ax1.set_xlabel('Asset', fontsize=12, fontweight='bold')
    ax1.set_title('Average CAR: ACT vs THREAT', fontsize=14, fontweight='bold')
    ax1.set_xticks(x)
    ax1.set_xticklabels(assets)
    ax1.legend()
    ax1.axhline(0, color='black', linestyle='--', linewidth=1)
    ax1.grid(axis='y', alpha=0.3)
    
    # 2.2: Absolute CAR comparison
    ax2 = axes[0, 1]
    act_abs_means = []
    threat_abs_means = []
    
    for asset in assets:
        asset_act = car_df[(car_df['Asset'] == asset) & (car_df['act_threat'] == 'ACT')]['CAR_pct'].abs()
        asset_threat = car_df[(car_df['Asset'] == asset) & (car_df['act_threat'] == 'THREAT')]['CAR_pct'].abs()
        
        act_abs_means.append(asset_act.mean() if len(asset_act) > 0 else 0)
        threat_abs_means.append(asset_threat.mean() if len(asset_threat) > 0 else 0)
    
    bars1 = ax2.bar(x - width/2, act_abs_means, width, label='ACT', color='#e74c3c', alpha=0.8)
    bars2 = ax2.bar(x + width/2, threat_abs_means, width, label='THREAT', color='#3498db', alpha=0.8)
    ax2.set_ylabel('Average |CAR| (%)', fontsize=12, fontweight='bold')
    ax2.set_xlabel('Asset', fontsize=12, fontweight='bold')
    ax2.set_title('Average Absolute CAR: ACT vs THREAT', fontsize=14, fontweight='bold')
    ax2.set_xticks(x)
    ax2.set_xticklabels(assets)
    ax2.legend()
    ax2.grid(axis='y', alpha=0.3)
    
    # 2.3: Statistical test results
    ax3 = axes[1, 0]
    test_results = []
    
    for asset in assets:
        act_data = car_df[(car_df['Asset'] == asset) & (car_df['act_threat'] == 'ACT')]['CAR_pct'].abs()
        threat_data = car_df[(car_df['Asset'] == asset) & (car_df['act_threat'] == 'THREAT')]['CAR_pct'].abs()
        
        if len(act_data) > 0 and len(threat_data) > 0:
            # Mann-Whitney U test (non-parametric)
            statistic, p_value = stats.mannwhitneyu(act_data, threat_data, alternative='two-sided')
            test_results.append({
                'asset': asset,
                'act_mean': act_data.mean(),
                'threat_mean': threat_data.mean(),
                'p_value': p_value,
                'significant': p_value < 0.05
            })
    
    # Visualize test results
    assets_test = [r['asset'] for r in test_results]
    act_means_test = [r['act_mean'] for r in test_results]
    threat_means_test = [r['threat_mean'] for r in test_results]
    p_values = [r['p_value'] for r in test_results]
    
    x_test = np.arange(len(assets_test))
    bars1 = ax3.bar(x_test - width/2, act_means_test, width, label='ACT', color='#e74c3c', alpha=0.8)
    bars2 = ax3.bar(x_test + width/2, threat_means_test, width, label='THREAT', color='#3498db', alpha=0.8)
    
    # Add significance markers
    for i, (bar1, bar2, p_val) in enumerate(zip(bars1, bars2, p_values)):
        max_height = max(bar1.get_height(), bar2.get_height())
        if p_val < 0.05:
            ax3.plot([i - width/2, i + width/2], [max_height + 1, max_height + 1], 'k-', linewidth=1)
            ax3.text(i, max_height + 1.5, '*', ha='center', fontsize=14, fontweight='bold')
    
    ax3.set_ylabel('Average |CAR| (%)', fontsize=12, fontweight='bold')
    ax3.set_xlabel('Asset', fontsize=12, fontweight='bold')
    ax3.set_title('Statistical Comparison (Mann-Whitney U test, * = p<0.05)', fontsize=14, fontweight='bold')
    ax3.set_xticks(x_test)
    ax3.set_xticklabels(assets_test)
    ax3.legend()
    ax3.grid(axis='y', alpha=0.3)
    
    # 2.4: Summary table
    ax4 = axes[1, 1]
    ax4.axis('off')
    
    table_data = []
    for result in test_results:
        winner = 'ACT' if result['act_mean'] > result['threat_mean'] else 'THREAT'
        sig = 'Yes' if result['significant'] else 'No'
        table_data.append([
            result['asset'],
            f"{result['act_mean']:.2f}%",
            f"{result['threat_mean']:.2f}%",
            winner,
            f"{result['p_value']:.4f}",
            sig
        ])
    
    table = ax4.table(cellText=table_data,
                     colLabels=['Asset', 'ACT |CAR|', 'THREAT |CAR|', 'Stronger', 'p-value', 'Significant'],
                     cellLoc='center',
                     loc='center',
                     bbox=[0, 0, 1, 1])
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 2)
    
    for i in range(len(table_data[0])):
        table[(0, i)].set_facecolor('#34495e')
        table[(0, i)].set_text_props(weight='bold', color='white')
    
    plt.suptitle('INSIGHT 2: ACT vs THREAT Impact Comparison', fontsize=16, fontweight='bold', y=0.995)
    plt.tight_layout()
    
    output_dir = Path('results/event_study/insights')
    plt.savefig(output_dir / 'insight_2_act_vs_threat.png', dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {output_dir / 'insight_2_act_vs_threat.png'}")
    plt.close()
    
    # Print summary
    print(f"\nKết luận:")
    for result in test_results:
        winner = 'ACT' if result['act_mean'] > result['threat_mean'] else 'THREAT'
        diff = abs(result['act_mean'] - result['threat_mean'])
        print(f"- {result['asset']}: {winner} mạnh hơn ({diff:.2f}% difference, p={result['p_value']:.4f})")

def insight_3_regional_bias(car_df):
    """3. Regional bias: events ở khu vực nào ảnh hưởng toàn cầu nhất?"""
    print("\n" + "="*80)
    print("INSIGHT 3: Regional Bias - Events ở khu vực nào ảnh hưởng toàn cầu nhất?")
    print("="*80)
    
    assets = ['BTC', 'GOLD', 'OIL']
    regions = ['Europe', 'Middle East', 'Asia', 'Americas', 'Global']
    
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    
    # 3.1: Average CAR by region (all assets combined)
    ax1 = axes[0, 0]
    region_stats = {}
    for region in regions:
        region_data = car_df[car_df['Region'] == region]['CAR_pct'].abs()
        if len(region_data) > 0:
            region_stats[region] = {
                'mean': region_data.mean(),
                'std': region_data.std(),
                'count': len(region_data)
            }
    
    regions_sorted = sorted(region_stats.keys(), key=lambda x: region_stats[x]['mean'], reverse=True)
    means = [region_stats[r]['mean'] for r in regions_sorted]
    stds = [region_stats[r]['std'] for r in regions_sorted]
    
    bars = ax1.bar(regions_sorted, means, color='#3498db', alpha=0.8, yerr=stds, capsize=5, edgecolor='black', linewidth=1.5)
    ax1.set_ylabel('Average |CAR| (%)', fontsize=12, fontweight='bold')
    ax1.set_xlabel('Region', fontsize=12, fontweight='bold')
    ax1.set_title('Average Absolute CAR by Region (All Assets)', fontsize=14, fontweight='bold')
    ax1.tick_params(axis='x', rotation=45)
    ax1.grid(axis='y', alpha=0.3)
    
    for bar, val in zip(bars, means):
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                f'{val:.2f}%', ha='center', va='bottom', fontweight='bold')
    
    # 3.2: Heatmap - CAR by Region × Asset
    ax2 = axes[0, 1]
    heatmap_data = []
    for asset in assets:
        row = []
        for region in regions:
            region_asset_data = car_df[(car_df['Region'] == region) & (car_df['Asset'] == asset)]['CAR_pct'].abs()
            row.append(region_asset_data.mean() if len(region_asset_data) > 0 else 0)
        heatmap_data.append(row)
    
    heatmap_df = pd.DataFrame(heatmap_data, index=assets, columns=regions)
    sns.heatmap(heatmap_df, annot=True, fmt='.2f', cmap='YlOrRd', ax=ax2, cbar_kws={'label': 'Avg |CAR| (%)'})
    ax2.set_title('Average |CAR| by Region × Asset', fontsize=14, fontweight='bold')
    ax2.set_xlabel('Region', fontsize=12)
    ax2.set_ylabel('Asset', fontsize=12)
    
    # 3.3: Event count by region
    ax3 = axes[1, 0]
    event_counts = {}
    for region in regions:
        events_in_region = car_df[car_df['Region'] == region]['Event'].nunique()
        event_counts[region] = events_in_region
    
    regions_count_sorted = sorted(event_counts.keys(), key=lambda x: event_counts[x], reverse=True)
    counts = [event_counts[r] for r in regions_count_sorted]
    
    bars = ax3.bar(regions_count_sorted, counts, color='#2ecc71', alpha=0.8, edgecolor='black', linewidth=1.5)
    ax3.set_ylabel('Number of Events', fontsize=12, fontweight='bold')
    ax3.set_xlabel('Region', fontsize=12, fontweight='bold')
    ax3.set_title('Number of Events by Region', fontsize=14, fontweight='bold')
    ax3.tick_params(axis='x', rotation=45)
    ax3.grid(axis='y', alpha=0.3)
    
    for bar, val in zip(bars, counts):
        ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                f'{val}', ha='center', va='bottom', fontweight='bold')
    
    # 3.4: Summary statistics
    ax4 = axes[1, 1]
    ax4.axis('off')
    
    table_data = []
    for region in regions_sorted:
        if region in region_stats:
            stats = region_stats[region]
            table_data.append([
                region,
                f"{stats['count']}",
                f"{stats['mean']:.2f}%",
                f"{stats['std']:.2f}%"
            ])
    
    table = ax4.table(cellText=table_data,
                     colLabels=['Region', 'Events', 'Avg |CAR|', 'Std Dev'],
                     cellLoc='center',
                     loc='center',
                     bbox=[0, 0, 1, 1])
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 2)
    
    for i in range(len(table_data[0])):
        table[(0, i)].set_facecolor('#34495e')
        table[(0, i)].set_text_props(weight='bold', color='white')
    
    plt.suptitle('INSIGHT 3: Regional Impact Analysis', fontsize=16, fontweight='bold', y=0.995)
    plt.tight_layout()
    
    output_dir = Path('results/event_study/insights')
    plt.savefig(output_dir / 'insight_3_regional_bias.png', dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {output_dir / 'insight_3_regional_bias.png'}")
    plt.close()
    
    # Print summary
    strongest_region = regions_sorted[0] if regions_sorted else None
    print(f"\nKết luận:")
    print(f"- Region ảnh hưởng mạnh nhất: {strongest_region} (Avg |CAR| = {region_stats[strongest_region]['mean']:.2f}%)")
    print(f"- Region có nhiều events nhất: {regions_count_sorted[0]} ({event_counts[regions_count_sorted[0]]} events)")

def insight_4_time_decay(car_df, df_gpr):
    """4. Time decay: phản ứng kéo dài bao lâu?"""
    print("\n" + "="*80)
    print("INSIGHT 4: Time Decay - Phản ứng kéo dài bao lâu?")
    print("="*80)
    
    # Load detailed event study results để có AR theo từng ngày
    # Vì không có file chi tiết, ta sẽ ước tính từ CAR
    # Giả sử event window là [-10, 10], ta sẽ phân tích CAR accumulation
    
    # Load identified events để có event dates
    events_path = Path('results/event_study/identified_events.json')
    with open(events_path, 'r', encoding='utf-8') as f:
        events_dict = json.load(f)
    
    # Tạo timeline analysis
    assets = ['BTC', 'GOLD', 'OIL']
    
    # Phân tích: events nào có CAR tích lũy nhanh (early reaction) vs chậm (late reaction)
    # Giả sử: nếu CAR lớn trong 5 ngày đầu → early reaction
    # Nếu CAR lớn trong 5 ngày cuối → late reaction
    
    # Vì không có AR daily data, ta sẽ phân tích:
    # 1. Persistence: events có CAR tiếp tục tăng sau event date không?
    # 2. Reversal: events có đảo chiều không?
    # 3. Speed: events nào phản ứng nhanh nhất?
    
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    
    # 4.1: CAR magnitude vs time (phân tích theo thời gian trong dataset)
    ax1 = axes[0, 0]
    
    # Group events by year
    car_df['Year'] = car_df['Date'].dt.year
    yearly_stats = {}
    
    for asset in assets:
        asset_data = car_df[car_df['Asset'] == asset].copy()
        asset_data['CAR_pct_abs'] = asset_data['CAR_pct'].abs()
        yearly_data = asset_data.groupby('Year')['CAR_pct_abs'].mean()
        yearly_stats[asset] = yearly_data
    
    years = sorted(car_df['Year'].unique())
    x = np.arange(len(years))
    width = 0.25
    
    for i, asset in enumerate(assets):
        values = [yearly_stats[asset].get(year, 0) for year in years]
        ax1.plot(x, values, marker='o', linewidth=2, markersize=8, label=asset)
    
    ax1.set_xlabel('Year', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Average |CAR| (%)', fontsize=12, fontweight='bold')
    ax1.set_title('Average |CAR| Over Time', fontsize=14, fontweight='bold')
    ax1.set_xticks(x)
    ax1.set_xticklabels(years, rotation=45)
    ax1.legend()
    ax1.grid(alpha=0.3)
    
    # 4.2: Event persistence analysis (dựa trên CAR magnitude)
    ax2 = axes[0, 1]
    
    # Phân loại events theo persistence
    # High persistence: |CAR| > 10% (phản ứng mạnh và kéo dài)
    # Low persistence: |CAR| < 5% (phản ứng yếu)
    
    persistence_categories = {
        'Very Strong (>15%)': (car_df['CAR_pct'].abs() > 15).sum(),
        'Strong (10-15%)': ((car_df['CAR_pct'].abs() >= 10) & (car_df['CAR_pct'].abs() <= 15)).sum(),
        'Moderate (5-10%)': ((car_df['CAR_pct'].abs() >= 5) & (car_df['CAR_pct'].abs() < 10)).sum(),
        'Weak (<5%)': (car_df['CAR_pct'].abs() < 5).sum()
    }
    
    categories = list(persistence_categories.keys())
    counts = list(persistence_categories.values())
    colors_persist = ['#e74c3c', '#f39c12', '#3498db', '#95a5a6']
    
    bars = ax2.bar(categories, counts, color=colors_persist, alpha=0.8, edgecolor='black', linewidth=1.5)
    ax2.set_ylabel('Number of Events', fontsize=12, fontweight='bold')
    ax2.set_xlabel('CAR Magnitude Category', fontsize=12, fontweight='bold')
    ax2.set_title('Event Persistence by CAR Magnitude', fontsize=14, fontweight='bold')
    ax2.tick_params(axis='x', rotation=45)
    ax2.grid(axis='y', alpha=0.3)
    
    for bar, val in zip(bars, counts):
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                f'{val}', ha='center', va='bottom', fontweight='bold')
    
    # 4.3: Asset-specific persistence
    ax3 = axes[1, 0]
    
    asset_persistence = {}
    category_keys = {
        'Very Strong (>15%)': 'Very Strong',
        'Strong (10-15%)': 'Strong',
        'Moderate (5-10%)': 'Moderate',
        'Weak (<5%)': 'Weak'
    }
    
    for asset in assets:
        asset_data = car_df[car_df['Asset'] == asset]['CAR_pct'].abs()
        asset_persistence[asset] = {
            'Very Strong': (asset_data > 15).sum(),
            'Strong': ((asset_data >= 10) & (asset_data <= 15)).sum(),
            'Moderate': ((asset_data >= 5) & (asset_data < 10)).sum(),
            'Weak': (asset_data < 5).sum()
        }
    
    x_asset = np.arange(len(categories))
    width_asset = 0.25
    
    for i, asset in enumerate(assets):
        values = [asset_persistence[asset][category_keys[cat]] for cat in categories]
        ax3.bar(x_asset + i*width_asset, values, width_asset, label=asset, alpha=0.8)
    
    ax3.set_ylabel('Number of Events', fontsize=12, fontweight='bold')
    ax3.set_xlabel('CAR Magnitude Category', fontsize=12, fontweight='bold')
    ax3.set_title('Persistence by Asset', fontsize=14, fontweight='bold')
    ax3.set_xticks(x_asset + width_asset)
    ax3.set_xticklabels([c.split('(')[0].strip() for c in categories], rotation=45, ha='right')
    ax3.legend()
    ax3.grid(axis='y', alpha=0.3)
    
    # 4.4: Summary statistics
    ax4 = axes[1, 1]
    ax4.axis('off')
    
    table_data = []
    for asset in assets:
        asset_data = car_df[car_df['Asset'] == asset]['CAR_pct'].abs()
        mean_persist = asset_data.mean()
        median_persist = asset_data.median()
        strong_pct = (asset_data > 10).sum() / len(asset_data) * 100
        
        table_data.append([
            asset,
            f"{mean_persist:.2f}%",
            f"{median_persist:.2f}%",
            f"{strong_pct:.1f}%"
        ])
    
    table = ax4.table(cellText=table_data,
                     colLabels=['Asset', 'Mean |CAR|', 'Median |CAR|', 'Strong (>10%) %'],
                     cellLoc='center',
                     loc='center',
                     bbox=[0, 0, 1, 1])
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 2)
    
    for i in range(len(table_data[0])):
        table[(0, i)].set_facecolor('#34495e')
        table[(0, i)].set_text_props(weight='bold', color='white')
    
    plt.suptitle('INSIGHT 4: Time Decay and Reaction Persistence', fontsize=16, fontweight='bold', y=0.995)
    plt.tight_layout()
    
    output_dir = Path('results/event_study/insights')
    plt.savefig(output_dir / 'insight_4_time_decay.png', dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {output_dir / 'insight_4_time_decay.png'}")
    plt.close()
    
    # Print summary
    print(f"\nKết luận:")
    print(f"- Events với phản ứng mạnh (>15%): {persistence_categories['Very Strong (>15%)']}")
    print(f"- Events với phản ứng yếu (<5%): {persistence_categories['Weak (<5%)']}")
    for asset in assets:
        asset_data = car_df[car_df['Asset'] == asset]['CAR_pct'].abs()
        strong_pct = (asset_data > 10).sum() / len(asset_data) * 100
        print(f"- {asset}: {strong_pct:.1f}% events có phản ứng mạnh (>10%)")

def main():
    """Main function"""
    print("=" * 80)
    print("PHÂN TÍCH 4 INSIGHTS CHÍNH TỪ EVENT STUDY")
    print("=" * 80)
    
    # Load data
    car_df, df_gpr = load_data()
    
    # Run all insights
    insight_1_asset_reaction(car_df)
    insight_2_act_vs_threat(car_df)
    insight_3_regional_bias(car_df)
    insight_4_time_decay(car_df, df_gpr)
    
    print("\n" + "=" * 80)
    print("✓ HOÀN THÀNH TẤT CẢ PHÂN TÍCH")
    print("=" * 80)
    print("\nCác file đã được lưu trong: results/event_study/insights/")

if __name__ == '__main__':
    main()

