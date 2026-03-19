"""
Phan tich lai ket qua Event Study theo ACT/THREAT
So sanh tac dong cua THREATS vs ACTS
"""

import pandas as pd
import numpy as np
import json
import matplotlib.pyplot as plt
from pathlib import Path
from collections import defaultdict
import sys
import io

# Fix encoding
if hasattr(sys.stdout, 'buffer'):
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    except:
        pass

# Set font
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['font.size'] = 10

def load_data():
    """Load all necessary data"""
    # Load CAR data
    car_path = Path('results/event_study/event_classification.csv')
    car_df = pd.read_csv(car_path)
    car_df['Date'] = pd.to_datetime(car_df['Date'])
    
    # Load events với phân loại ACT/THREAT
    events_path = Path('results/event_study/identified_events.json')
    with open(events_path, 'r', encoding='utf-8') as f:
        events_dict = json.load(f)
    
    # Merge ACT/THREAT vào car_df
    car_df['act_threat'] = car_df['Event'].map(
        lambda x: events_dict.get(x, {}).get('identified', {}).get('act_threat', 'unknown')
    )
    car_df['category'] = car_df['Event'].map(
        lambda x: events_dict.get(x, {}).get('identified', {}).get('category', 0)
    )
    car_df['category_name'] = car_df['Event'].map(
        lambda x: events_dict.get(x, {}).get('identified', {}).get('category_name', 'unknown')
    )
    car_df['region'] = car_df['Event'].map(
        lambda x: events_dict.get(x, {}).get('identified', {}).get('region', 'unknown')
    )
    
    return car_df, events_dict


def analyze_act_vs_threat(car_df):
    """Phan tich so sanh ACT vs THREAT"""
    print("="*80)
    print("PHAN TICH ACT vs THREAT")
    print("="*80)
    
    assets = ['BTC', 'GOLD', 'OIL']
    results = {}
    
    for asset in assets:
        print(f"\n--- {asset} ---")
        asset_data = car_df[car_df['Asset'] == asset].copy()
        
        # Filter
        act_data = asset_data[asset_data['act_threat'] == 'ACT']
        threat_data = asset_data[asset_data['act_threat'] == 'THREAT']
        
        print(f"\nACTS (GPRA):")
        print(f"  - Số lượng: {len(act_data)} events")
        if len(act_data) > 0:
            print(f"  - CAR trung bình: {act_data['CAR_pct'].mean():+.2f}%")
            print(f"  - CAR median: {act_data['CAR_pct'].median():+.2f}%")
            print(f"  - Std CAR: {act_data['CAR_pct'].std():.2f}%")
            print(f"  - Min CAR: {act_data['CAR_pct'].min():+.2f}%")
            print(f"  - Max CAR: {act_data['CAR_pct'].max():+.2f}%")
            print(f"  - Tỷ lệ tích cực: {(act_data['CAR_pct'] > 0).sum() / len(act_data) * 100:.1f}%")
        
        print(f"\nTHREATS (GPRT):")
        print(f"  - Số lượng: {len(threat_data)} events")
        if len(threat_data) > 0:
            print(f"  - CAR trung bình: {threat_data['CAR_pct'].mean():+.2f}%")
            print(f"  - CAR median: {threat_data['CAR_pct'].median():+.2f}%")
            print(f"  - Std CAR: {threat_data['CAR_pct'].std():.2f}%")
            print(f"  - Min CAR: {threat_data['CAR_pct'].min():+.2f}%")
            print(f"  - Max CAR: {threat_data['CAR_pct'].max():+.2f}%")
            print(f"  - Tỷ lệ tích cực: {(threat_data['CAR_pct'] > 0).sum() / len(threat_data) * 100:.1f}%")
        
        # Statistical test (simplified)
        if len(act_data) > 0 and len(threat_data) > 0:
            act_mean = act_data['CAR_pct'].mean()
            threat_mean = threat_data['CAR_pct'].mean()
            act_std = act_data['CAR_pct'].std()
            threat_std = threat_data['CAR_pct'].std()
            n_act = len(act_data)
            n_threat = len(threat_data)
            
            # Simplified t-test
            pooled_std = np.sqrt(((n_act - 1) * act_std**2 + (n_threat - 1) * threat_std**2) / (n_act + n_threat - 2))
            se_diff = pooled_std * np.sqrt(1/n_act + 1/n_threat)
            t_stat = (act_mean - threat_mean) / se_diff if se_diff > 0 else 0
            
            print(f"\nT-test ACT vs THREAT:")
            print(f"  - T-statistic: {t_stat:.3f}")
            print(f"  - Mean difference: {act_mean - threat_mean:+.2f}%")
            if abs(t_stat) > 1.96:
                print(f"  - Kết luận: Khác biệt có ý nghĩa thống kê (|t| > 1.96)")
            else:
                print(f"  - Kết luận: Không có khác biệt có ý nghĩa thống kê")
        
        results[asset] = {
            'ACT': act_data,
            'THREAT': threat_data
        }
    
    return results


def analyze_by_category(car_df):
    """Phan tich theo tung category"""
    print("\n" + "="*80)
    print("PHAN TICH THEO CATEGORY")
    print("="*80)
    
    assets = ['BTC', 'GOLD', 'OIL']
    category_names = {
        1: 'War Threats',
        3: 'Military Buildups',
        4: 'Nuclear Threats',
        5: 'Terror Threats',
        6: 'Beginning of War',
        7: 'Escalation of War',
        8: 'Terror Acts'
    }
    
    for asset in assets:
        print(f"\n--- {asset} ---")
        asset_data = car_df[car_df['Asset'] == asset].copy()
        
        print(f"\n{'Category':<25} | {'Count':<8} | {'Mean CAR':<12} | {'Std CAR':<12} | {'Risk Level':<12}")
        print("-" * 80)
        
        for cat in sorted(asset_data['category'].unique()):
            if cat == 0:
                continue
            cat_data = asset_data[asset_data['category'] == cat]
            if len(cat_data) > 0:
                mean_car = cat_data['CAR_pct'].mean()
                std_car = cat_data['CAR_pct'].std()
                count = len(cat_data)
                
                # Risk level
                if abs(mean_car) > 10 and std_car > 15:
                    risk_level = "Rất Cao"
                elif abs(mean_car) > 5 and std_car > 10:
                    risk_level = "Cao"
                elif abs(mean_car) > 2 and std_car > 5:
                    risk_level = "Trung bình"
                else:
                    risk_level = "Thấp"
                
                print(f"{category_names.get(cat, f'Category {cat}'):<25} | {count:<8} | "
                      f"{mean_car:+11.2f}% | {std_car:11.2f}% | {risk_level:<12}")


def create_visualizations(car_df):
    """Tao visualizations moi theo ACT/THREAT"""
    print("\n" + "="*80)
    print("TAO VISUALIZATIONS THEO ACT/THREAT")
    print("="*80)
    
    output_dir = Path('results/event_study/act_threat_analysis')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    assets = ['BTC', 'GOLD', 'OIL']
    
    # 1. Box plot: ACT vs THREAT
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    
    for idx, asset in enumerate(assets):
        ax = axes[idx]
        asset_data = car_df[car_df['Asset'] == asset].copy()
        
        act_cars = asset_data[asset_data['act_threat'] == 'ACT']['CAR_pct'].values
        threat_cars = asset_data[asset_data['act_threat'] == 'THREAT']['CAR_pct'].values
        
        data = [act_cars, threat_cars]
        bp = ax.boxplot(data, labels=['ACTS (GPRA)', 'THREATS (GPRT)'], 
                       patch_artist=True, showmeans=True, meanline=True)
        
        # Colors
        colors = ['#e74c3c', '#3498db']  # Red for ACT, Blue for THREAT
        for patch, color in zip(bp['boxes'], colors):
            patch.set_facecolor(color)
            patch.set_alpha(0.7)
            patch.set_edgecolor('black')
            patch.set_linewidth(1.5)
        
        ax.set_ylabel('CAR (%)', fontsize=12, fontweight='bold')
        ax.set_title(f'{asset} CAR Distribution: ACT vs THREAT', 
                    fontsize=13, fontweight='bold')
        ax.grid(True, alpha=0.3, axis='y')
        ax.axhline(y=0, color='black', linestyle='--', linewidth=1, alpha=0.5)
        
        # Stats
        if len(act_cars) > 0 and len(threat_cars) > 0:
            act_mean = np.mean(act_cars)
            threat_mean = np.mean(threat_cars)
            textstr = f"ACT Mean: {act_mean:+.2f}%\nTHREAT Mean: {threat_mean:+.2f}%"
            props = dict(boxstyle='round', facecolor='wheat', alpha=0.8)
            ax.text(0.02, 0.98, textstr, transform=ax.transAxes, fontsize=9,
                   verticalalignment='top', bbox=props)
    
    plt.tight_layout()
    plt.savefig(output_dir / 'boxplot_act_vs_threat.png', dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {output_dir / 'boxplot_act_vs_threat.png'}")
    plt.close()
    
    # 2. Bar chart: Mean CAR by ACT/THREAT
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    
    for idx, asset in enumerate(assets):
        ax = axes[idx]
        asset_data = car_df[car_df['Asset'] == asset].copy()
        
        act_mean = asset_data[asset_data['act_threat'] == 'ACT']['CAR_pct'].mean()
        threat_mean = asset_data[asset_data['act_threat'] == 'THREAT']['CAR_pct'].mean()
        
        x = ['ACTS\n(GPRA)', 'THREATS\n(GPRT)']
        y = [act_mean, threat_mean]
        colors = ['#e74c3c', '#3498db']
        
        bars = ax.bar(x, y, color=colors, alpha=0.7, edgecolor='black', linewidth=1.5)
        
        # Add value labels
        for bar, val in zip(bars, y):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{val:+.2f}%', ha='center', va='bottom' if val > 0 else 'top',
                   fontsize=11, fontweight='bold')
        
        ax.set_ylabel('Mean CAR (%)', fontsize=12, fontweight='bold')
        ax.set_title(f'{asset} Mean CAR: ACT vs THREAT', fontsize=13, fontweight='bold')
        ax.grid(True, alpha=0.3, axis='y')
        ax.axhline(y=0, color='black', linestyle='-', linewidth=1)
    
    plt.tight_layout()
    plt.savefig(output_dir / 'barchart_act_vs_threat.png', dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {output_dir / 'barchart_act_vs_threat.png'}")
    plt.close()
    
    # 3. Scatter plot: ACT vs THREAT
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    
    for idx, asset in enumerate(assets):
        ax = axes[idx]
        asset_data = car_df[car_df['Asset'] == asset].copy()
        
        act_data = asset_data[asset_data['act_threat'] == 'ACT']
        threat_data = asset_data[asset_data['act_threat'] == 'THREAT']
        
        if len(act_data) > 0:
            ax.scatter(act_data['category'], act_data['CAR_pct'], 
                     c='#e74c3c', label='ACTS (GPRA)', s=100, alpha=0.6, 
                     edgecolors='black', linewidths=1)
        
        if len(threat_data) > 0:
            ax.scatter(threat_data['category'], threat_data['CAR_pct'], 
                     c='#3498db', label='THREATS (GPRT)', s=100, alpha=0.6,
                     edgecolors='black', linewidths=1)
        
        ax.set_xlabel('Category', fontsize=12, fontweight='bold')
        ax.set_ylabel('CAR (%)', fontsize=12, fontweight='bold')
        ax.set_title(f'{asset} CAR by Category', fontsize=13, fontweight='bold')
        ax.legend()
        ax.grid(True, alpha=0.3)
        ax.axhline(y=0, color='black', linestyle='--', linewidth=1, alpha=0.5)
        
        # Category labels
        category_labels = {
            1: 'War\nThreats', 3: 'Military\nBuildups', 4: 'Nuclear\nThreats',
            6: 'Beginning\nof War', 7: 'Escalation\nof War', 8: 'Terror\nActs'
        }
        ax.set_xticks(list(category_labels.keys()))
        ax.set_xticklabels([category_labels.get(x, f'Cat {x}') for x in category_labels.keys()], 
                          rotation=45, ha='right')
    
    plt.tight_layout()
    plt.savefig(output_dir / 'scatter_act_vs_threat.png', dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {output_dir / 'scatter_act_vs_threat.png'}")
    plt.close()


def generate_summary_report(car_df, results):
    """Tao bao cao tong hop"""
    print("\n" + "="*80)
    print("BAO CAO TONG HOP")
    print("="*80)
    
    assets = ['BTC', 'GOLD', 'OIL']
    
    print("\n1. SO SÁNH ACT vs THREAT:")
    print("-" * 80)
    print(f"{'Asset':<8} | {'ACT Mean':<12} | {'THREAT Mean':<12} | {'Difference':<12} | {'ACT Std':<12} | {'THREAT Std':<12}")
    print("-" * 80)
    
    for asset in assets:
        act_data = results[asset]['ACT']
        threat_data = results[asset]['THREAT']
        
        act_mean = act_data['CAR_pct'].mean() if len(act_data) > 0 else 0
        threat_mean = threat_data['CAR_pct'].mean() if len(threat_data) > 0 else 0
        act_std = act_data['CAR_pct'].std() if len(act_data) > 0 else 0
        threat_std = threat_data['CAR_pct'].std() if len(threat_data) > 0 else 0
        diff = act_mean - threat_mean
        
        print(f"{asset:<8} | {act_mean:+11.2f}% | {threat_mean:+11.2f}% | "
              f"{diff:+11.2f}% | {act_std:11.2f}% | {threat_std:11.2f}%")
    
    print("\n2. KẾT LUẬN CHÍNH:")
    print("-" * 80)
    
    for asset in assets:
        act_data = results[asset]['ACT']
        threat_data = results[asset]['THREAT']
        
        if len(act_data) > 0 and len(threat_data) > 0:
            act_mean = act_data['CAR_pct'].mean()
            threat_mean = threat_data['CAR_pct'].mean()
            act_std = act_data['CAR_pct'].std()
            threat_std = threat_data['CAR_pct'].std()
            
            if abs(act_mean) > abs(threat_mean):
                stronger = "ACTS"
            else:
                stronger = "THREATS"
            
            print(f"\n{asset}:")
            print(f"  - ACTS có tác động: {act_mean:+.2f}% (Std: {act_std:.2f}%)")
            print(f"  - THREATS có tác động: {threat_mean:+.2f}% (Std: {threat_std:.2f}%)")
            print(f"  - {stronger} có tác động mạnh hơn")


def main():
    """Main function"""
    print("="*80)
    print("PHAN TICH KET QUA THEO ACT/THREAT")
    print("="*80)
    
    # Load data
    car_df, events_dict = load_data()
    
    # 1. Phân tích ACT vs THREAT
    results = analyze_act_vs_threat(car_df)
    
    # 2. Phân tích theo category
    analyze_by_category(car_df)
    
    # 3. Tạo visualizations
    create_visualizations(car_df)
    
    # 4. Báo cáo tổng hợp
    generate_summary_report(car_df, results)
    
    print("\n" + "="*80)
    print("✓ Hoàn thành phân tích!")
    print("="*80)


if __name__ == '__main__':
    main()

