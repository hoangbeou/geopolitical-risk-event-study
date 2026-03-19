"""
Phân tích pattern chi tiết: GPRD_ACT vs GPRD_THREAT
Tìm điểm khác biệt giữa war events làm BTC tăng vs giảm
"""

import pandas as pd
import json
from pathlib import Path
import numpy as np
import sys
import io

# Fix encoding
if hasattr(sys.stdout, 'buffer') and not hasattr(sys.stdout, '_encoding_set'):
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stdout._encoding_set = True
    except (AttributeError, ValueError):
        pass

def main():
    """Main function"""
    print("=" * 80)
    print("PHÂN TÍCH PATTERN: GPRD_ACT vs GPRD_THREAT")
    print("=" * 80)
    print()
    
    # Load analysis results
    analysis_path = Path('results/event_study/gpr_act_threat_analysis.json')
    with open(analysis_path, 'r', encoding='utf-8') as f:
        analysis = json.load(f)
    
    btc_inc = pd.DataFrame(analysis['BTC_increase'])
    btc_dec = pd.DataFrame(analysis['BTC_decrease'])
    
    print(f"War events làm BTC TĂNG: {len(btc_inc)}")
    print(f"War events làm BTC GIẢM: {len(btc_dec)}")
    print()
    
    # Phân loại theo pattern ACT/THREAT
    print("=" * 80)
    print("PHÂN LOẠI THEO PATTERN ACT/THREAT")
    print("=" * 80)
    print()
    
    # Define thresholds
    act_threshold = 1.0  # ACT ratio > 1.0 = ACT dominant
    threat_threshold = 1.0  # THREAT ratio > 1.0 = THREAT dominant
    
    # BTC TĂNG
    print("BTC TĂNG - Phân loại:")
    print("-" * 80)
    
    inc_high_threat_low_act = btc_inc[(btc_inc['threat_ratio'] > threat_threshold) & (btc_inc['act_ratio'] < act_threshold)]
    inc_high_act_low_threat = btc_inc[(btc_inc['act_ratio'] > act_threshold) & (btc_inc['threat_ratio'] < threat_threshold)]
    inc_both_high = btc_inc[(btc_inc['act_ratio'] > act_threshold) & (btc_inc['threat_ratio'] > threat_threshold)]
    inc_both_low = btc_inc[(btc_inc['act_ratio'] < act_threshold) & (btc_inc['threat_ratio'] < threat_threshold)]
    
    print(f"1. THREAT cao, ACT thấp: {len(inc_high_threat_low_act)} events")
    if len(inc_high_threat_low_act) > 0:
        avg_car = inc_high_threat_low_act['car'].mean() * 100
        print(f"   Average CAR: {avg_car:.2f}%")
        print("   Events:")
        for _, row in inc_high_threat_low_act.iterrows():
            print(f"     - {row['event']} ({row['date']}): {row['car']*100:.2f}% - {row['name']}")
    print()
    
    print(f"2. ACT cao, THREAT thấp: {len(inc_high_act_low_threat)} events")
    if len(inc_high_act_low_threat) > 0:
        avg_car = inc_high_act_low_threat['car'].mean() * 100
        print(f"   Average CAR: {avg_car:.2f}%")
        print("   Events:")
        for _, row in inc_high_act_low_threat.iterrows():
            print(f"     - {row['event']} ({row['date']}): {row['car']*100:.2f}% - {row['name']}")
    print()
    
    print(f"3. Cả ACT và THREAT đều cao: {len(inc_both_high)} events")
    if len(inc_both_high) > 0:
        avg_car = inc_both_high['car'].mean() * 100
        print(f"   Average CAR: {avg_car:.2f}%")
        print("   Events:")
        for _, row in inc_both_high.iterrows():
            print(f"     - {row['event']} ({row['date']}): {row['car']*100:.2f}% - {row['name']}")
    print()
    
    print(f"4. Cả ACT và THREAT đều thấp: {len(inc_both_low)} events")
    if len(inc_both_low) > 0:
        avg_car = inc_both_low['car'].mean() * 100
        print(f"   Average CAR: {avg_car:.2f}%")
        print("   Events:")
        for _, row in inc_both_low.iterrows():
            print(f"     - {row['event']} ({row['date']}): {row['car']*100:.2f}% - {row['name']}")
    print()
    
    # BTC GIẢM
    print("BTC GIẢM - Phân loại:")
    print("-" * 80)
    
    dec_high_threat_low_act = btc_dec[(btc_dec['threat_ratio'] > threat_threshold) & (btc_dec['act_ratio'] < act_threshold)]
    dec_high_act_low_threat = btc_dec[(btc_dec['act_ratio'] > act_threshold) & (btc_dec['threat_ratio'] < threat_threshold)]
    dec_both_high = btc_dec[(btc_dec['act_ratio'] > act_threshold) & (btc_dec['threat_ratio'] > threat_threshold)]
    dec_both_low = btc_dec[(btc_dec['act_ratio'] < act_threshold) & (btc_dec['threat_ratio'] < threat_threshold)]
    
    print(f"1. THREAT cao, ACT thấp: {len(dec_high_threat_low_act)} events")
    if len(dec_high_threat_low_act) > 0:
        avg_car = dec_high_threat_low_act['car'].mean() * 100
        print(f"   Average CAR: {avg_car:.2f}%")
        print("   Events:")
        for _, row in dec_high_threat_low_act.iterrows():
            print(f"     - {row['event']} ({row['date']}): {row['car']*100:.2f}% - {row['name']}")
    print()
    
    print(f"2. ACT cao, THREAT thấp: {len(dec_high_act_low_threat)} events")
    if len(dec_high_act_low_threat) > 0:
        avg_car = dec_high_act_low_threat['car'].mean() * 100
        print(f"   Average CAR: {avg_car:.2f}%")
        print("   Events:")
        for _, row in dec_high_act_low_threat.iterrows():
            print(f"     - {row['event']} ({row['date']}): {row['car']*100:.2f}% - {row['name']}")
    print()
    
    print(f"3. Cả ACT và THREAT đều cao: {len(dec_both_high)} events")
    if len(dec_both_high) > 0:
        avg_car = dec_both_high['car'].mean() * 100
        print(f"   Average CAR: {avg_car:.2f}%")
        print("   Events:")
        for _, row in dec_both_high.iterrows():
            print(f"     - {row['event']} ({row['date']}): {row['car']*100:.2f}% - {row['name']}")
    print()
    
    print(f"4. Cả ACT và THREAT đều thấp: {len(dec_both_low)} events")
    if len(dec_both_low) > 0:
        avg_car = dec_both_low['car'].mean() * 100
        print(f"   Average CAR: {avg_car:.2f}%")
        print("   Events:")
        for _, row in dec_both_low.iterrows():
            print(f"     - {row['event']} ({row['date']}): {row['car']*100:.2f}% - {row['name']}")
    print()
    
    # So sánh
    print("=" * 80)
    print("SO SÁNH PATTERNS")
    print("=" * 80)
    print()
    
    print("THREAT cao, ACT thấp:")
    print(f"  BTC TĂNG: {len(inc_high_threat_low_act)} events (avg CAR: {inc_high_threat_low_act['car'].mean()*100:.2f}%)")
    print(f"  BTC GIẢM: {len(dec_high_threat_low_act)} events (avg CAR: {dec_high_threat_low_act['car'].mean()*100:.2f}%)")
    print()
    
    print("ACT cao, THREAT thấp:")
    print(f"  BTC TĂNG: {len(inc_high_act_low_threat)} events (avg CAR: {inc_high_act_low_threat['car'].mean()*100:.2f}%)")
    print(f"  BTC GIẢM: {len(dec_high_act_low_threat)} events (avg CAR: {dec_high_act_low_threat['car'].mean()*100:.2f}%)")
    print()
    
    # Save detailed analysis
    output_path = Path('results/event_study/act_threat_pattern_analysis.txt')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("PHÂN TÍCH PATTERN: ACT vs THREAT\n")
        f.write("=" * 80 + "\n\n")
        
        f.write("THRESHOLD: ACT ratio > 1.0 = ACT dominant, THREAT ratio > 1.0 = THREAT dominant\n\n")
        
        f.write("=" * 80 + "\n")
        f.write("BTC TĂNG - THREAT cao, ACT thấp\n")
        f.write("=" * 80 + "\n\n")
        for _, row in inc_high_threat_low_act.iterrows():
            f.write(f"{row['event']} ({row['date']}): {row['car']*100:.2f}%\n")
            f.write(f"  {row['name']}\n")
            f.write(f"  ACT Ratio: {row['act_ratio']:.3f}, THREAT Ratio: {row['threat_ratio']:.3f}\n")
            f.write("\n")
        
        f.write("\n" + "=" * 80 + "\n")
        f.write("BTC GIẢM - ACT cao, THREAT thấp\n")
        f.write("=" * 80 + "\n\n")
        for _, row in dec_high_act_low_threat.iterrows():
            f.write(f"{row['event']} ({row['date']}): {row['car']*100:.2f}%\n")
            f.write(f"  {row['name']}\n")
            f.write(f"  ACT Ratio: {row['act_ratio']:.3f}, THREAT Ratio: {row['threat_ratio']:.3f}\n")
            f.write("\n")
        
        f.write("\n" + "=" * 80 + "\n")
        f.write("KẾT LUẬN\n")
        f.write("=" * 80 + "\n\n")
        
        if len(inc_high_threat_low_act) > len(dec_high_threat_low_act):
            f.write("✓ THREAT cao + ACT thấp → Chủ yếu làm BTC TĂNG\n")
        else:
            f.write("✗ THREAT cao + ACT thấp → Không có pattern rõ ràng\n")
        
        if len(dec_high_act_low_threat) > len(inc_high_act_low_threat):
            f.write("✓ ACT cao + THREAT thấp → Chủ yếu làm BTC GIẢM\n")
        else:
            f.write("✗ ACT cao + THREAT thấp → Không có pattern rõ ràng\n")
    
    print(f"✓ Đã lưu phân tích: {output_path}")


if __name__ == '__main__':
    main()


















