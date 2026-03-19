"""
Phân tích độ mạnh (magnitude) của GPR impact lên các assets
"""

import pandas as pd
import numpy as np
import json
from pathlib import Path

# Load event classification
classification_path = Path('results/event_study/event_classification.json')
with open(classification_path, 'r', encoding='utf-8') as f:
    classification = json.load(f)

# Load event study summary
summary_path = Path('results/event_study/event_study_summary.txt')
events_data = []

with open(summary_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        if line.startswith('Event_') and line.endswith(':'):
            event_name = line[:-1]
            event_info = {'event': event_name}
            
            i += 1
            if i < len(lines) and 'Date:' in lines[i]:
                date_str = lines[i].split('Date:')[1].strip()
                event_info['date'] = date_str
            
            i += 1
            while i < len(lines) and not lines[i].strip().startswith('Event_') and not lines[i].strip().startswith('==='):
                line = lines[i].strip()
                
                if line in ['BTC:', 'GOLD:', 'OIL:']:
                    asset = line[:-1]
                    car_final = np.nan
                    t_stat = np.nan
                    
                    i += 1
                    if i < len(lines) and 'CAR (final):' in lines[i]:
                        car_str = lines[i].split('CAR (final):')[1].strip()
                        car_str = car_str.replace('***', '').replace('**', '').replace('*', '').strip()
                        try:
                            car_final = float(car_str)
                        except:
                            pass
                    
                    i += 1
                    if i < len(lines) and 'T-statistic:' in lines[i]:
                        t_stat_str = lines[i].split('T-statistic:')[1].strip()
                        try:
                            t_stat = float(t_stat_str)
                        except:
                            pass
                    
                    event_info[f'{asset}_car'] = car_final
                    event_info[f'{asset}_tstat'] = t_stat
                
                i += 1
            
            events_data.append(event_info)
            continue
        
        i += 1

df = pd.DataFrame(events_data)

print("="*80)
print("PHÂN TÍCH ĐỘ MẠNH (MAGNITUDE) CỦA GPR IMPACT")
print("="*80)

for asset in ['BTC', 'GOLD', 'OIL']:
    print(f"\n{'='*80}")
    print(f"{asset} - PHÂN TÍCH MAGNITUDE")
    print(f"{'='*80}")
    
    car_col = f'{asset}_car'
    tstat_col = f'{asset}_tstat'
    
    asset_df = df[[car_col, tstat_col, 'event', 'date']].dropna()
    
    if len(asset_df) == 0:
        print("No data available")
        continue
    
    car_values = asset_df[car_col].values
    
    # 1. Overall statistics
    print(f"\n1. OVERALL STATISTICS (Tất cả {len(asset_df)} events):")
    print("-"*80)
    print(f"   Mean CAR: {np.mean(car_values):.4f} ({np.mean(car_values)*100:.2f}%)")
    print(f"   Median CAR: {np.median(car_values):.4f} ({np.median(car_values)*100:.2f}%)")
    print(f"   Std CAR: {np.std(car_values):.4f} ({np.std(car_values)*100:.2f}%)")
    print(f"   Min CAR: {np.min(car_values):.4f} ({np.min(car_values)*100:.2f}%)")
    print(f"   Max CAR: {np.max(car_values):.4f} ({np.max(car_values)*100:.2f}%)")
    
    # 2. Significant events
    significant_5pct = asset_df[abs(asset_df[tstat_col]) > 1.96]
    print(f"\n2. SIGNIFICANT EVENTS (|t-stat| > 1.96): {len(significant_5pct)} events ({len(significant_5pct)/len(asset_df)*100:.1f}%)")
    print("-"*80)
    if len(significant_5pct) > 0:
        sig_cars = significant_5pct[car_col].values
        print(f"   Mean CAR: {np.mean(sig_cars):.4f} ({np.mean(sig_cars)*100:.2f}%)")
        print(f"   Median CAR: {np.median(sig_cars):.4f} ({np.median(sig_cars)*100:.2f}%)")
        print(f"   Min CAR: {np.min(sig_cars):.4f} ({np.min(sig_cars)*100:.2f}%)")
        print(f"   Max CAR: {np.max(sig_cars):.4f} ({np.max(sig_cars)*100:.2f}%)")
        
        # Positive vs Negative
        pos_sig = significant_5pct[significant_5pct[tstat_col] > 1.96]
        neg_sig = significant_5pct[significant_5pct[tstat_col] < -1.96]
        if len(pos_sig) > 0:
            print(f"\n   Positive significant ({len(pos_sig)} events):")
            print(f"     Mean CAR: {pos_sig[car_col].mean():.4f} ({pos_sig[car_col].mean()*100:.2f}%)")
            print(f"     Range: [{pos_sig[car_col].min():.4f}, {pos_sig[car_col].max():.4f}]")
        if len(neg_sig) > 0:
            print(f"\n   Negative significant ({len(neg_sig)} events):")
            print(f"     Mean CAR: {neg_sig[car_col].mean():.4f} ({neg_sig[car_col].mean()*100:.2f}%)")
            print(f"     Range: [{neg_sig[car_col].min():.4f}, {neg_sig[car_col].max():.4f}]")
    
    # 3. Large magnitude events (|CAR| > 5%)
    large_magnitude = asset_df[abs(asset_df[car_col]) > 0.05]
    print(f"\n3. LARGE MAGNITUDE EVENTS (|CAR| > 5%): {len(large_magnitude)} events ({len(large_magnitude)/len(asset_df)*100:.1f}%)")
    print("-"*80)
    if len(large_magnitude) > 0:
        large_cars = large_magnitude[car_col].values
        print(f"   Mean CAR: {np.mean(large_cars):.4f} ({np.mean(large_cars)*100:.2f}%)")
        print(f"   Median CAR: {np.median(large_cars):.4f} ({np.median(large_cars)*100:.2f}%)")
        print(f"   Min CAR: {np.min(large_cars):.4f} ({np.min(large_cars)*100:.2f}%)")
        print(f"   Max CAR: {np.max(large_cars):.4f} ({np.max(large_cars)*100:.2f}%)")
        
        # Top 5 largest magnitude
        print(f"\n   Top 5 Largest Magnitude Events:")
        sorted_large = large_magnitude.sort_values(by=car_col, key=lambda x: abs(x), ascending=False)
        for idx, row in sorted_large.head(5).iterrows():
            date_str = str(row['date'])[:10] if len(str(row['date'])) > 10 else str(row['date'])
            print(f"     {row['event']:<15} {date_str:<15} CAR: {row[car_col]:>8.4f} ({row[car_col]*100:>6.2f}%)")
    
    # 4. Medium magnitude events (2% < |CAR| < 5%)
    medium_magnitude = asset_df[(abs(asset_df[car_col]) > 0.02) & (abs(asset_df[car_col]) <= 0.05)]
    print(f"\n4. MEDIUM MAGNITUDE EVENTS (2% < |CAR| < 5%): {len(medium_magnitude)} events ({len(medium_magnitude)/len(asset_df)*100:.1f}%)")
    print("-"*80)
    if len(medium_magnitude) > 0:
        med_cars = medium_magnitude[car_col].values
        print(f"   Mean CAR: {np.mean(med_cars):.4f} ({np.mean(med_cars)*100:.2f}%)")
    
    # 5. Small magnitude events (|CAR| < 2%)
    small_magnitude = asset_df[abs(asset_df[car_col]) <= 0.02]
    print(f"\n5. SMALL MAGNITUDE EVENTS (|CAR| < 2%): {len(small_magnitude)} events ({len(small_magnitude)/len(asset_df)*100:.1f}%)")
    print("-"*80)
    if len(small_magnitude) > 0:
        small_cars = small_magnitude[car_col].values
        print(f"   Mean CAR: {np.mean(small_cars):.4f} ({np.mean(small_cars)*100:.2f}%)")
    
    # 6. Distribution by magnitude
    print(f"\n6. DISTRIBUTION BY MAGNITUDE:")
    print("-"*80)
    print(f"   |CAR| > 10%: {len(asset_df[abs(asset_df[car_col]) > 0.10])} events ({len(asset_df[abs(asset_df[car_col]) > 0.10])/len(asset_df)*100:.1f}%)")
    print(f"   5% < |CAR| < 10%: {len(asset_df[(abs(asset_df[car_col]) > 0.05) & (abs(asset_df[car_col]) <= 0.10)])} events ({len(asset_df[(abs(asset_df[car_col]) > 0.05) & (abs(asset_df[car_col]) <= 0.10)])/len(asset_df)*100:.1f}%)")
    print(f"   2% < |CAR| < 5%: {len(medium_magnitude)} events ({len(medium_magnitude)/len(asset_df)*100:.1f}%)")
    print(f"   |CAR| < 2%: {len(small_magnitude)} events ({len(small_magnitude)/len(asset_df)*100:.1f}%)")

# Summary comparison
print("\n" + "="*80)
print("SO SÁNH GIỮA CÁC ASSETS")
print("="*80)

summary_data = []
for asset in ['BTC', 'GOLD', 'OIL']:
    car_col = f'{asset}_car'
    tstat_col = f'{asset}_tstat'
    
    asset_df = df[[car_col, tstat_col]].dropna()
    
    if len(asset_df) == 0:
        continue
    
    car_values = asset_df[car_col].values
    significant_5pct = asset_df[abs(asset_df[tstat_col]) > 1.96]
    large_magnitude = asset_df[abs(asset_df[car_col]) > 0.05]
    
    summary_data.append({
        'Asset': asset,
        'Mean CAR (%)': f"{np.mean(car_values)*100:.2f}%",
        'Median CAR (%)': f"{np.median(car_values)*100:.2f}%",
        'Std CAR (%)': f"{np.std(car_values)*100:.2f}%",
        'Max CAR (%)': f"{np.max(car_values)*100:.2f}%",
        'Min CAR (%)': f"{np.min(car_values)*100:.2f}%",
        'Significant Events': f"{len(significant_5pct)} ({len(significant_5pct)/len(asset_df)*100:.1f}%)",
        'Mean CAR (Sig Only) (%)': f"{significant_5pct[car_col].mean()*100:.2f}%" if len(significant_5pct) > 0 else "N/A",
        'Large Mag Events': f"{len(large_magnitude)} ({len(large_magnitude)/len(asset_df)*100:.1f}%)",
        'Mean CAR (Large Mag) (%)': f"{large_magnitude[car_col].mean()*100:.2f}%" if len(large_magnitude) > 0 else "N/A"
    })

summary_df = pd.DataFrame(summary_data)
print("\n" + summary_df.to_string(index=False))

print("\n" + "="*80)
print("KẾT LUẬN")
print("="*80)
print("""
1. GPR TÁC ĐỘNG MẠNH NHƯNG KHÔNG NHẤT QUÁN:

   ✓ CÓ TÁC ĐỘNG MẠNH:
   - Một số events có impact rất lớn (10-45%)
   - Mean CAR của significant events cao hơn nhiều so với average
   - Large magnitude events chiếm một tỷ lệ đáng kể
   
   ✗ KHÔNG NHẤT QUÁN:
   - Chỉ 1.6-11.5% events có significant response
   - Responses rất khác nhau giữa các events
   - Có events tăng mạnh, có events giảm mạnh → cancel out khi tính average

2. ĐỘ MẠNH CỤ THỂ:

   BTC:
   - Mean CAR (all): 0.73%
   - Mean CAR (significant only): ~17%
   - Mean CAR (large magnitude): ~15-20%
   - Max impact: ~45%
   
   GOLD:
   - Mean CAR (all): 1.39%
   - Mean CAR (significant only): ~-29% (chỉ 1 event)
   - Mean CAR (large magnitude): ~10-15%
   - Max impact: ~29%
   
   OIL:
   - Mean CAR (all): -0.01% (gần như 0)
   - Mean CAR (significant only): ~-2.5%
   - Mean CAR (large magnitude): ~-3%
   - Max impact: ~-6%

3. IMPLICATION:

   - GPR events CÓ thể gây ra movements lớn (10-45%)
   - Nhưng không thể dự đoán trước event nào sẽ có impact
   - Cần phân tích context của từng event để hiểu tại sao
""")

