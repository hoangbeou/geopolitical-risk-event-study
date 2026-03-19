"""
Tao bao cao tong hop ve ACT/THREAT analysis
"""

import pandas as pd
import numpy as np
import json
from pathlib import Path

def main():
    print("="*80)
    print("TAO BAO CAO TONG HOP ACT/THREAT")
    print("="*80)
    
    # Load data
    car_path = Path('results/event_study/event_classification.csv')
    car_df = pd.read_csv(car_path)
    car_df['Date'] = pd.to_datetime(car_df['Date'])
    
    events_path = Path('results/event_study/identified_events.json')
    with open(events_path, 'r', encoding='utf-8') as f:
        events_dict = json.load(f)
    
    # Merge ACT/THREAT
    car_df['act_threat'] = car_df['Event'].map(
        lambda x: events_dict.get(x, {}).get('identified', {}).get('act_threat', 'unknown')
    )
    car_df['category'] = car_df['Event'].map(
        lambda x: events_dict.get(x, {}).get('identified', {}).get('category', 0)
    )
    car_df['category_name'] = car_df['Event'].map(
        lambda x: events_dict.get(x, {}).get('identified', {}).get('category_name', 'unknown')
    )
    
    # Filter
    car_df = car_df[car_df['act_threat'] != 'unknown']
    
    assets = ['BTC', 'GOLD', 'OIL']
    
    # Create summary
    summary = []
    summary.append("="*80)
    summary.append("BAO CAO TONG HOP: ACT vs THREAT")
    summary.append("="*80)
    summary.append("")
    
    summary.append("1. TONG QUAN:")
    summary.append("-"*80)
    for asset in assets:
        asset_data = car_df[car_df['Asset'] == asset]
        act_data = asset_data[asset_data['act_threat'] == 'ACT']
        threat_data = asset_data[asset_data['act_threat'] == 'THREAT']
        
        summary.append(f"\n{asset}:")
        summary.append(f"  ACTS (GPRA): {len(act_data)} events")
        if len(act_data) > 0:
            summary.append(f"    - Mean CAR: {act_data['CAR_pct'].mean():+.2f}%")
            summary.append(f"    - Std CAR: {act_data['CAR_pct'].std():.2f}%")
            summary.append(f"    - Positive rate: {(act_data['CAR_pct'] > 0).sum() / len(act_data) * 100:.1f}%")
        
        summary.append(f"  THREATS (GPRT): {len(threat_data)} events")
        if len(threat_data) > 0:
            summary.append(f"    - Mean CAR: {threat_data['CAR_pct'].mean():+.2f}%")
            summary.append(f"    - Std CAR: {threat_data['CAR_pct'].std():.2f}%")
            summary.append(f"    - Positive rate: {(threat_data['CAR_pct'] > 0).sum() / len(threat_data) * 100:.1f}%")
    
    summary.append("\n" + "="*80)
    summary.append("2. SO SANH ACT vs THREAT:")
    summary.append("-"*80)
    summary.append(f"{'Asset':<8} | {'ACT Mean':<12} | {'THREAT Mean':<12} | {'Difference':<12}")
    summary.append("-"*80)
    
    for asset in assets:
        asset_data = car_df[car_df['Asset'] == asset]
        act_data = asset_data[asset_data['act_threat'] == 'ACT']
        threat_data = asset_data[asset_data['act_threat'] == 'THREAT']
        
        act_mean = act_data['CAR_pct'].mean() if len(act_data) > 0 else 0
        threat_mean = threat_data['CAR_pct'].mean() if len(threat_data) > 0 else 0
        diff = act_mean - threat_mean
        
        summary.append(f"{asset:<8} | {act_mean:+11.2f}% | {threat_mean:+11.2f}% | {diff:+11.2f}%")
    
    summary.append("\n" + "="*80)
    summary.append("3. PHAN TICH THEO CATEGORY:")
    summary.append("-"*80)
    
    category_names = {
        1: 'War Threats',
        3: 'Military Buildups',
        4: 'Nuclear Threats',
        6: 'Beginning of War',
        7: 'Escalation of War',
        8: 'Terror Acts'
    }
    
    for asset in assets:
        summary.append(f"\n{asset}:")
        asset_data = car_df[car_df['Asset'] == asset]
        
        for cat in sorted(asset_data['category'].unique()):
            if cat == 0:
                continue
            cat_data = asset_data[asset_data['category'] == cat]
            if len(cat_data) > 0:
                mean_car = cat_data['CAR_pct'].mean()
                std_car = cat_data['CAR_pct'].std()
                count = len(cat_data)
                summary.append(f"  {category_names.get(cat, f'Category {cat}'):<25}: "
                              f"n={count}, Mean={mean_car:+.2f}%, Std={std_car:.2f}%")
    
    summary.append("\n" + "="*80)
    summary.append("4. KET LUAN:")
    summary.append("-"*80)
    
    for asset in assets:
        asset_data = car_df[car_df['Asset'] == asset]
        act_data = asset_data[asset_data['act_threat'] == 'ACT']
        threat_data = asset_data[asset_data['act_threat'] == 'THREAT']
        
        if len(act_data) > 0 and len(threat_data) > 0:
            act_mean = act_data['CAR_pct'].mean()
            threat_mean = threat_data['CAR_pct'].mean()
            
            if abs(act_mean) > abs(threat_mean):
                stronger = "ACTS"
                value = act_mean
            else:
                stronger = "THREATS"
                value = threat_mean
            
            summary.append(f"\n{asset}:")
            summary.append(f"  - {stronger} co tac dong manh hon ({value:+.2f}%)")
    
    # Save report
    output_dir = Path('results/event_study/act_threat_analysis')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    report_text = "\n".join(summary)
    with open(output_dir / 'summary_report.txt', 'w', encoding='utf-8') as f:
        f.write(report_text)
    
    print(report_text)
    print(f"\n✓ Da luu bao cao vao: {output_dir / 'summary_report.txt'}")


if __name__ == '__main__':
    main()

