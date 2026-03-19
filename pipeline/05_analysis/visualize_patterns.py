"""
Visualize 4 patterns để làm rõ sự khác biệt
"""

import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend

import json
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
import sys
import io

# Fix encoding
if hasattr(sys.stdout, 'buffer') and not hasattr(sys.stdout, '_encoding_set'):
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stdout._encoding_set = True
    except (AttributeError, ValueError):
        pass

# Set font for Vietnamese
plt.rcParams['font.family'] = 'DejaVu Sans'

def main():
    """Main function"""
    print("=" * 80)
    print("TẠO VISUALIZATION CHO PATTERNS (BTC, GOLD, OIL)")
    print("=" * 80)
    print()
    
    # Load data từ event_classification.csv (đầy đủ 3 assets)
    car_path = Path('results/event_study/event_classification.csv')
    car_df = pd.read_csv(car_path)
    car_df['Date'] = pd.to_datetime(car_df['Date'])
    
    # Load ACT/THREAT từ GPR data
    data_path = Path('data/data_optimized.csv')
    df_gpr = pd.read_csv(data_path)
    if 'DAY' in df_gpr.columns:
        try:
            df_gpr['DATE'] = pd.to_datetime(df_gpr['DAY'].astype(int).astype(str), format='%Y%m%d', errors='coerce')
        except:
            df_gpr['DATE'] = pd.to_datetime(df_gpr['DAY'], format='%d/%m/%Y', errors='coerce')
    df_gpr = df_gpr.dropna(subset=['DATE'])
    df_gpr['DATE'] = pd.to_datetime(df_gpr['DATE'])
    
    # Tạo lookup cho từng asset
    assets = ['BTC', 'GOLD', 'OIL']
    asset_data = {}
    for asset in assets:
        asset_df = car_df[car_df['Asset'] == asset].copy()
        asset_data[asset] = {
            'increase': {row['Event']: {'car': row['CAR'], 'car_pct': row['CAR_pct'], 'date': row['Date']} 
                         for _, row in asset_df.iterrows() if row['CAR'] > 0},
            'decrease': {row['Event']: {'car': row['CAR'], 'car_pct': row['CAR_pct'], 'date': row['Date']} 
                         for _, row in asset_df.iterrows() if row['CAR'] <= 0}
        }
    
    # Tạo ACT/THREAT mapping
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
                    'act_ratio': float(gpr_act) if pd.notna(gpr_act) else 0,
                    'threat_ratio': float(gpr_threat) if pd.notna(gpr_threat) else 0
                }
            else:
                act_threat_map[event_id] = {'act_threat': 'THREAT', 'act_ratio': 0, 'threat_ratio': 0}
        else:
            act_threat_map[event_id] = {'act_threat': 'THREAT', 'act_ratio': 0, 'threat_ratio': 0}
    
    # Phân loại patterns dựa trên cả 3 assets
    # Patterns: 8 combinations (2^3)
    pattern_data = {
        'all_inc': {'btc_car': [], 'gold_car': [], 'oil_car': [], 'act_ratio': [], 'threat_ratio': [], 'events': []},
        'all_dec': {'btc_car': [], 'gold_car': [], 'oil_car': [], 'act_ratio': [], 'threat_ratio': [], 'events': []},
        'btc_inc_others_dec': {'btc_car': [], 'gold_car': [], 'oil_car': [], 'act_ratio': [], 'threat_ratio': [], 'events': []},
        'gold_inc_others_dec': {'btc_car': [], 'gold_car': [], 'oil_car': [], 'act_ratio': [], 'threat_ratio': [], 'events': []},
        'oil_inc_others_dec': {'btc_car': [], 'gold_car': [], 'oil_car': [], 'act_ratio': [], 'threat_ratio': [], 'events': []},
        'btc_gold_inc_oil_dec': {'btc_car': [], 'gold_car': [], 'oil_car': [], 'act_ratio': [], 'threat_ratio': [], 'events': []},
        'btc_oil_inc_gold_dec': {'btc_car': [], 'gold_car': [], 'oil_car': [], 'act_ratio': [], 'threat_ratio': [], 'events': []},
        'gold_oil_inc_btc_dec': {'btc_car': [], 'gold_car': [], 'oil_car': [], 'act_ratio': [], 'threat_ratio': [], 'events': []}
    }
    
    all_events = set(car_df['Event'].unique())
    
    for event_id in all_events:
        btc_inc = event_id in asset_data['BTC']['increase']
        gold_inc = event_id in asset_data['GOLD']['increase']
        oil_inc = event_id in asset_data['OIL']['increase']
        
        btc_info = asset_data['BTC']['increase'].get(event_id) or asset_data['BTC']['decrease'].get(event_id, {'car': 0, 'car_pct': 0})
        gold_info = asset_data['GOLD']['increase'].get(event_id) or asset_data['GOLD']['decrease'].get(event_id, {'car': 0, 'car_pct': 0})
        oil_info = asset_data['OIL']['increase'].get(event_id) or asset_data['OIL']['decrease'].get(event_id, {'car': 0, 'car_pct': 0})
        act_threat_info = act_threat_map.get(event_id, {'act_ratio': 0, 'threat_ratio': 0})
        
        # Phân loại pattern
        if btc_inc and gold_inc and oil_inc:
            pattern = 'all_inc'
        elif not btc_inc and not gold_inc and not oil_inc:
            pattern = 'all_dec'
        elif btc_inc and not gold_inc and not oil_inc:
            pattern = 'btc_inc_others_dec'
        elif not btc_inc and gold_inc and not oil_inc:
            pattern = 'gold_inc_others_dec'
        elif not btc_inc and not gold_inc and oil_inc:
            pattern = 'oil_inc_others_dec'
        elif btc_inc and gold_inc and not oil_inc:
            pattern = 'btc_gold_inc_oil_dec'
        elif btc_inc and not gold_inc and oil_inc:
            pattern = 'btc_oil_inc_gold_dec'
        elif not btc_inc and gold_inc and oil_inc:
            pattern = 'gold_oil_inc_btc_dec'
        else:
            continue  # Skip nếu không match pattern nào
        
        pattern_data[pattern]['btc_car'].append(btc_info.get('car', 0))
        pattern_data[pattern]['gold_car'].append(gold_info.get('car', 0))
        pattern_data[pattern]['oil_car'].append(oil_info.get('car', 0))
        pattern_data[pattern]['act_ratio'].append(act_threat_info.get('act_ratio', 0))
        pattern_data[pattern]['threat_ratio'].append(act_threat_info.get('threat_ratio', 0))
        pattern_data[pattern]['events'].append(event_id)
    
    # Create output directory
    output_dir = Path('results/event_study/pattern_visualizations')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Lọc patterns có dữ liệu
    patterns_with_data = [p for p in pattern_data.keys() if len(pattern_data[p]['events']) > 0]
    
    if len(patterns_with_data) == 0:
        print("  ✗ Không có dữ liệu patterns")
        return
    
    # Pattern labels
    pattern_labels_map = {
        'all_inc': 'All\nIncrease',
        'all_dec': 'All\nDecrease',
        'btc_inc_others_dec': 'BTC↑\nOthers↓',
        'gold_inc_others_dec': 'GOLD↑\nOthers↓',
        'oil_inc_others_dec': 'OIL↑\nOthers↓',
        'btc_gold_inc_oil_dec': 'BTC↑GOLD↑\nOIL↓',
        'btc_oil_inc_gold_dec': 'BTC↑OIL↑\nGOLD↓',
        'gold_oil_inc_btc_dec': 'GOLD↑OIL↑\nBTC↓'
    }
    
    # 1. Bar chart: Average CAR by pattern (3 assets)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
    
    pattern_labels = [pattern_labels_map.get(p, p) for p in patterns_with_data]
    
    btc_avg = [np.mean(pattern_data[p]['btc_car'])*100 if len(pattern_data[p]['btc_car']) > 0 else 0 for p in patterns_with_data]
    gold_avg = [np.mean(pattern_data[p]['gold_car'])*100 if len(pattern_data[p]['gold_car']) > 0 else 0 for p in patterns_with_data]
    oil_avg = [np.mean(pattern_data[p]['oil_car'])*100 if len(pattern_data[p]['oil_car']) > 0 else 0 for p in patterns_with_data]
    
    x = np.arange(len(patterns_with_data))
    width = 0.25
    
    ax1.bar(x - width, btc_avg, width, label='BTC', color='#f7931a', alpha=0.8)
    ax1.bar(x, gold_avg, width, label='GOLD', color='#ffd700', alpha=0.8)
    ax1.bar(x + width, oil_avg, width, label='OIL', color='#0066cc', alpha=0.8)
    ax1.set_xlabel('Pattern', fontsize=12)
    ax1.set_ylabel('Average CAR (%)', fontsize=12)
    ax1.set_title('Average CAR by Pattern (BTC, GOLD, OIL)', fontsize=14, fontweight='bold')
    ax1.set_xticks(x)
    ax1.set_xticklabels(pattern_labels, rotation=45, ha='right')
    ax1.legend()
    ax1.grid(axis='y', alpha=0.3)
    ax1.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
    
    # 2. ACT/THREAT ratios
    act_avg = [np.mean(pattern_data[p]['act_ratio']) if len(pattern_data[p]['act_ratio']) > 0 else 0 for p in patterns_with_data]
    threat_avg = [np.mean(pattern_data[p]['threat_ratio']) if len(pattern_data[p]['threat_ratio']) > 0 else 0 for p in patterns_with_data]
    
    ax2.bar(x - width/2, act_avg, width, label='ACT Ratio', color='#e74c3c', alpha=0.8)
    ax2.bar(x + width/2, threat_avg, width, label='THREAT Ratio', color='#3498db', alpha=0.8)
    ax2.set_xlabel('Pattern', fontsize=12)
    ax2.set_ylabel('Average Ratio', fontsize=12)
    ax2.set_title('GPR ACT/THREAT Ratios by Pattern', fontsize=14, fontweight='bold')
    ax2.set_xticks(x)
    ax2.set_xticklabels(pattern_labels, rotation=45, ha='right')
    ax2.legend()
    ax2.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_dir / 'pattern_comparison.png', dpi=300, bbox_inches='tight')
    print(f"✓ Đã tạo: {output_dir / 'pattern_comparison.png'}")
    plt.close()
    
    # 3. Scatter plot: 3D-like visualization với 3 assets
    fig = plt.figure(figsize=(14, 10))
    
    # Subplot 1: BTC vs GOLD
    ax1 = fig.add_subplot(2, 2, 1)
    colors_map = {
        'all_inc': '#2ecc71', 'all_dec': '#e74c3c',
        'btc_inc_others_dec': '#f39c12', 'gold_inc_others_dec': '#3498db', 'oil_inc_others_dec': '#9b59b6',
        'btc_gold_inc_oil_dec': '#e67e22', 'btc_oil_inc_gold_dec': '#1abc9c', 'gold_oil_inc_btc_dec': '#34495e'
    }
    
    for pattern in patterns_with_data:
        if len(pattern_data[pattern]['btc_car']) > 0:
            btc_cars = np.array(pattern_data[pattern]['btc_car']) * 100
            gold_cars = np.array(pattern_data[pattern]['gold_car']) * 100
            ax1.scatter(btc_cars, gold_cars, c=colors_map.get(pattern, '#95a5a6'), 
                       label=pattern_labels_map.get(pattern, pattern), 
                       alpha=0.6, s=100, edgecolors='black', linewidth=0.5)
    
    ax1.axhline(y=0, color='black', linestyle='--', linewidth=0.5)
    ax1.axvline(x=0, color='black', linestyle='--', linewidth=0.5)
    ax1.set_xlabel('BTC CAR (%)', fontsize=11)
    ax1.set_ylabel('GOLD CAR (%)', fontsize=11)
    ax1.set_title('BTC vs GOLD CAR', fontsize=12, fontweight='bold')
    ax1.legend(fontsize=8)
    ax1.grid(alpha=0.3)
    
    # Subplot 2: BTC vs OIL
    ax2 = fig.add_subplot(2, 2, 2)
    for pattern in patterns_with_data:
        if len(pattern_data[pattern]['btc_car']) > 0:
            btc_cars = np.array(pattern_data[pattern]['btc_car']) * 100
            oil_cars = np.array(pattern_data[pattern]['oil_car']) * 100
            ax2.scatter(btc_cars, oil_cars, c=colors_map.get(pattern, '#95a5a6'), 
                       label=pattern_labels_map.get(pattern, pattern), 
                       alpha=0.6, s=100, edgecolors='black', linewidth=0.5)
    
    ax2.axhline(y=0, color='black', linestyle='--', linewidth=0.5)
    ax2.axvline(x=0, color='black', linestyle='--', linewidth=0.5)
    ax2.set_xlabel('BTC CAR (%)', fontsize=11)
    ax2.set_ylabel('OIL CAR (%)', fontsize=11)
    ax2.set_title('BTC vs OIL CAR', fontsize=12, fontweight='bold')
    ax2.legend(fontsize=8)
    ax2.grid(alpha=0.3)
    
    # Subplot 3: GOLD vs OIL
    ax3 = fig.add_subplot(2, 2, 3)
    for pattern in patterns_with_data:
        if len(pattern_data[pattern]['gold_car']) > 0:
            gold_cars = np.array(pattern_data[pattern]['gold_car']) * 100
            oil_cars = np.array(pattern_data[pattern]['oil_car']) * 100
            ax3.scatter(gold_cars, oil_cars, c=colors_map.get(pattern, '#95a5a6'), 
                       label=pattern_labels_map.get(pattern, pattern), 
                       alpha=0.6, s=100, edgecolors='black', linewidth=0.5)
    
    ax3.axhline(y=0, color='black', linestyle='--', linewidth=0.5)
    ax3.axvline(x=0, color='black', linestyle='--', linewidth=0.5)
    ax3.set_xlabel('GOLD CAR (%)', fontsize=11)
    ax3.set_ylabel('OIL CAR (%)', fontsize=11)
    ax3.set_title('GOLD vs OIL CAR', fontsize=12, fontweight='bold')
    ax3.legend(fontsize=8)
    ax3.grid(alpha=0.3)
    
    # Subplot 4: Summary statistics
    ax4 = fig.add_subplot(2, 2, 4)
    ax4.axis('off')
    
    summary_text = "Pattern Summary:\n\n"
    total_events = sum(len(pattern_data[p]['events']) for p in patterns_with_data)
    for pattern in patterns_with_data:
        count = len(pattern_data[pattern]['events'])
        pct = count / total_events * 100 if total_events > 0 else 0
        summary_text += f"{pattern_labels_map.get(pattern, pattern)}: {count} ({pct:.1f}%)\n"
    
    ax4.text(0.1, 0.5, summary_text, fontsize=10, verticalalignment='center',
             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
    
    plt.suptitle('CAR Relationships Across Assets (BTC, GOLD, OIL)', fontsize=14, fontweight='bold', y=0.98)
    plt.tight_layout()
    plt.savefig(output_dir / 'btc_gold_scatter.png', dpi=300, bbox_inches='tight')
    print(f"✓ Đã tạo: {output_dir / 'btc_gold_scatter.png'}")
    plt.close()
    
    # 4. ACT/THREAT distribution
    fig, ax = plt.subplots(figsize=(14, 6))
    
    act_threat_counts = {}
    for pattern in patterns_with_data:
        act_threat_counts[pattern] = {'ACT': 0, 'THREAT': 0}
        for event_id in pattern_data[pattern].get('events', []):
            act_threat_info = act_threat_map.get(event_id, {})
            act_threat = act_threat_info.get('act_threat', 'THREAT')
            if act_threat in ['ACT', 'THREAT']:
                act_threat_counts[pattern][act_threat] += 1
    
    act_threats = ['ACT', 'THREAT']
    x = np.arange(len(act_threats))
    width = 0.8 / len(patterns_with_data)
    
    for i, pattern in enumerate(patterns_with_data):
        counts = [act_threat_counts[pattern].get(at, 0) for at in act_threats]
        ax.bar(x + i*width, counts, width, label=pattern_labels_map.get(pattern, pattern), 
               color=colors_map.get(pattern, '#95a5a6'), alpha=0.8)
    
    ax.set_xlabel('ACT/THREAT', fontsize=12)
    ax.set_ylabel('Number of Events', fontsize=12)
    ax.set_title('ACT/THREAT Distribution by Pattern', fontsize=14, fontweight='bold')
    ax.set_xticks(x + width * (len(patterns_with_data) - 1) / 2)
    ax.set_xticklabels(act_threats)
    ax.legend(fontsize=9, ncol=2)
    ax.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_dir / 'act_threat_distribution.png', dpi=300, bbox_inches='tight')
    print(f"✓ Đã tạo: {output_dir / 'act_threat_distribution.png'}")
    plt.close()
    
    # 5. Summary table visualization
    fig, ax = plt.subplots(figsize=(16, 10))
    ax.axis('tight')
    ax.axis('off')
    
    total_events = sum(len(pattern_data[p]['events']) for p in patterns_with_data)
    table_data = []
    for pattern in patterns_with_data:
        count = len(pattern_data[pattern]['events'])
        btc_avg = np.mean(pattern_data[pattern]['btc_car'])*100 if len(pattern_data[pattern]['btc_car']) > 0 else 0
        gold_avg = np.mean(pattern_data[pattern]['gold_car'])*100 if len(pattern_data[pattern]['gold_car']) > 0 else 0
        oil_avg = np.mean(pattern_data[pattern]['oil_car'])*100 if len(pattern_data[pattern]['oil_car']) > 0 else 0
        act_avg = np.mean(pattern_data[pattern]['act_ratio']) if len(pattern_data[pattern]['act_ratio']) > 0 else 0
        threat_avg = np.mean(pattern_data[pattern]['threat_ratio']) if len(pattern_data[pattern]['threat_ratio']) > 0 else 0
        
        act_count = sum(1 for eid in pattern_data[pattern]['events'] 
                       if act_threat_map.get(eid, {}).get('act_threat') == 'ACT')
        act_pct = act_count / count * 100 if count > 0 else 0
        
        table_data.append([
            pattern_labels_map.get(pattern, pattern),
            f"{count} ({count/total_events*100:.1f}%)",
            f"{btc_avg:+.2f}%",
            f"{gold_avg:+.2f}%",
            f"{oil_avg:+.2f}%",
            f"{act_avg:.1f}",
            f"{threat_avg:.1f}",
            f"{act_pct:.1f}%"
        ])
    
    table = ax.table(cellText=table_data,
                    colLabels=['Pattern', 'Count', 'BTC CAR', 'GOLD CAR', 'OIL CAR',
                              'ACT Ratio', 'THREAT Ratio', 'ACT %'],
                    cellLoc='center',
                    loc='center',
                    bbox=[0, 0, 1, 1])
    
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1, 1.8)
    
    # Color code
    for i, pattern in enumerate(patterns_with_data):
        table[(i+1, 0)].set_facecolor(colors_map.get(pattern, '#95a5a6'))
        table[(i+1, 0)].set_text_props(weight='bold', color='white')
    
    for i in range(len(table_data[0])):
        table[(0, i)].set_facecolor('#34495e')
        table[(0, i)].set_text_props(weight='bold', color='white')
    
    plt.title('Pattern Characteristics Summary (BTC, GOLD, OIL)', fontsize=16, fontweight='bold', pad=20)
    plt.savefig(output_dir / 'pattern_summary_table.png', dpi=300, bbox_inches='tight')
    print(f"✓ Đã tạo: {output_dir / 'pattern_summary_table.png'}")
    plt.close()
    
    print(f"\n✓ Đã tạo tất cả visualizations trong: {output_dir}", flush=True)
    print(f"  - pattern_comparison.png", flush=True)
    print(f"  - btc_gold_scatter.png (3 assets)", flush=True)
    print(f"  - act_threat_distribution.png", flush=True)
    print(f"  - pattern_summary_table.png (BTC, GOLD, OIL)", flush=True)


if __name__ == '__main__':
    main()


















