"""
Generate insights from ACT/THREAT analysis
"""

import pandas as pd
import numpy as np
import json
from pathlib import Path

def main():
    print("="*80)
    print("INSIGHTS TU PHAN TICH ACT/THREAT")
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
    car_df['region'] = car_df['Event'].map(
        lambda x: events_dict.get(x, {}).get('identified', {}).get('region', 'unknown')
    )
    
    car_df = car_df[car_df['act_threat'] != 'unknown']
    
    assets = ['BTC', 'GOLD', 'OIL']
    
    print("\n" + "="*80)
    print("INSIGHT 1: ACT vs THREAT - TAC DONG KHAC NHAU")
    print("="*80)
    
    for asset in assets:
        asset_data = car_df[car_df['Asset'] == asset]
        act_data = asset_data[asset_data['act_threat'] == 'ACT']
        threat_data = asset_data[asset_data['act_threat'] == 'THREAT']
        
        if len(act_data) > 0 and len(threat_data) > 0:
            act_mean = act_data['CAR_pct'].mean()
            threat_mean = threat_data['CAR_pct'].mean()
            act_std = act_data['CAR_pct'].std()
            threat_std = threat_data['CAR_pct'].std()
            
            print(f"\n{asset}:")
            print(f"  ACTS (GPRA): Mean={act_mean:+.2f}%, Std={act_std:.2f}%, n={len(act_data)}")
            print(f"  THREATS (GPRT): Mean={threat_mean:+.2f}%, Std={threat_std:.2f}%, n={len(threat_data)}")
            print(f"  Chenh lech: {act_mean - threat_mean:+.2f}%")
            
            if abs(act_mean) > abs(threat_mean):
                print(f"  -> ACTS co tac dong MANH HON")
            else:
                print(f"  -> THREATS co tac dong MANH HON")
    
    print("\n" + "="*80)
    print("INSIGHT 2: PHAN TICH THEO CATEGORY")
    print("="*80)
    
    category_names = {
        1: 'War Threats',
        3: 'Military Buildups',
        4: 'Nuclear Threats',
        6: 'Beginning of War',
        7: 'Escalation of War',
        8: 'Terror Acts'
    }
    
    for asset in assets:
        print(f"\n{asset}:")
        asset_data = car_df[car_df['Asset'] == asset]
        
        for cat in sorted(asset_data['category'].unique()):
            if cat == 0:
                continue
            cat_data = asset_data[asset_data['category'] == cat]
            if len(cat_data) > 0:
                mean_car = cat_data['CAR_pct'].mean()
                std_car = cat_data['CAR_pct'].std()
                count = len(cat_data)
                pos_rate = (cat_data['CAR_pct'] > 0).sum() / count * 100
                
                print(f"  {category_names.get(cat, f'Cat {cat}'):<25}: "
                      f"n={count:2d}, Mean={mean_car:+7.2f}%, Std={std_car:6.2f}%, "
                      f"Pos={pos_rate:5.1f}%")
    
    print("\n" + "="*80)
    print("INSIGHT 3: TOP EVENTS THEO ACT/THREAT")
    print("="*80)
    
    for asset in assets:
        print(f"\n{asset} - Top 5 ACTS:")
        asset_data = car_df[car_df['Asset'] == asset]
        act_data = asset_data[asset_data['act_threat'] == 'ACT'].copy()
        act_data['abs_car'] = act_data['CAR_pct'].abs()
        top_acts = act_data.nlargest(5, 'abs_car')
        
        for idx, row in top_acts.iterrows():
            event_id = row['Event']
            car_pct = row['CAR_pct']
            cat_name = row['category_name']
            event_name = events_dict.get(event_id, {}).get('identified', {}).get('name', 'Unknown')
            print(f"  {event_id:12} | {car_pct:+7.2f}% | {cat_name:20} | {event_name[:40]}")
        
        print(f"\n{asset} - Top 5 THREATS:")
        threat_data = asset_data[asset_data['act_threat'] == 'THREAT'].copy()
        threat_data['abs_car'] = threat_data['CAR_pct'].abs()
        top_threats = threat_data.nlargest(5, 'abs_car')
        
        for idx, row in top_threats.iterrows():
            event_id = row['Event']
            car_pct = row['CAR_pct']
            cat_name = row['category_name']
            event_name = events_dict.get(event_id, {}).get('identified', {}).get('name', 'Unknown')
            print(f"  {event_id:12} | {car_pct:+7.2f}% | {cat_name:20} | {event_name[:40]}")
    
    print("\n" + "="*80)
    print("INSIGHT 4: KET LUAN CHINH")
    print("="*80)
    
    insights = []
    
    # Insight 1: ACT vs THREAT
    for asset in assets:
        asset_data = car_df[car_df['Asset'] == asset]
        act_data = asset_data[asset_data['act_threat'] == 'ACT']
        threat_data = asset_data[asset_data['act_threat'] == 'THREAT']
        
        if len(act_data) > 0 and len(threat_data) > 0:
            act_mean = act_data['CAR_pct'].mean()
            threat_mean = threat_data['CAR_pct'].mean()
            
            if asset == 'BTC':
                if act_mean > threat_mean:
                    insights.append(f"{asset}: ACTS co tac dong TICH CUC hon THREATS "
                                  f"({act_mean:+.2f}% vs {threat_mean:+.2f}%)")
                else:
                    insights.append(f"{asset}: THREATS co tac dong TICH CUC hon ACTS "
                                  f"({threat_mean:+.2f}% vs {act_mean:+.2f}%)")
            elif asset == 'GOLD':
                if act_mean > threat_mean:
                    insights.append(f"{asset}: ACTS co tac dong TICH CUC hon THREATS "
                                  f"({act_mean:+.2f}% vs {threat_mean:+.2f}%)")
                else:
                    insights.append(f"{asset}: THREATS co tac dong TICH CUC hon ACTS "
                                  f"({threat_mean:+.2f}% vs {act_mean:+.2f}%)")
            else:  # OIL
                insights.append(f"{asset}: Phan ung YEU voi ca ACTS va THREATS "
                              f"(ACT: {act_mean:+.2f}%, THREAT: {threat_mean:+.2f}%)")
    
    # Insight 2: Category analysis
    for asset in assets:
        asset_data = car_df[car_df['Asset'] == asset]
        
        # Find strongest category
        max_mean = 0
        strongest_cat = None
        for cat in asset_data['category'].unique():
            if cat == 0:
                continue
            cat_data = asset_data[asset_data['category'] == cat]
            if len(cat_data) > 0:
                mean_car = abs(cat_data['CAR_pct'].mean())
                if mean_car > max_mean:
                    max_mean = mean_car
                    strongest_cat = (cat, category_names.get(cat, f'Cat {cat}'))
        
        if strongest_cat:
            cat_data = asset_data[asset_data['category'] == strongest_cat[0]]
            mean_car = cat_data['CAR_pct'].mean()
            insights.append(f"{asset}: Category manh nhat la '{strongest_cat[1]}' "
                          f"(Mean CAR: {mean_car:+.2f}%)")
    
    for insight in insights:
        print(f"  - {insight}")
    
    # Save insights
    output_dir = Path('results/event_study/act_threat_analysis')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(output_dir / 'insights.txt', 'w', encoding='utf-8') as f:
        f.write("INSIGHTS TU PHAN TICH ACT/THREAT\n")
        f.write("="*80 + "\n\n")
        for insight in insights:
            f.write(f"- {insight}\n")
    
    print(f"\n✓ Da luu insights vao: {output_dir / 'insights.txt'}")


if __name__ == '__main__':
    main()

