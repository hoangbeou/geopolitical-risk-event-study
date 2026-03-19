"""
Phân tích đặc điểm của 4 patterns:
1. Cả BTC và GOLD tăng
2. Cả BTC và GOLD giảm
3. BTC tăng, GOLD giảm
4. BTC giảm, GOLD tăng (Flight-to-Quality)
"""

import json
import pandas as pd
from pathlib import Path
from collections import defaultdict
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
    print("PHÂN TÍCH ĐẶC ĐIỂM CỦA 4 PATTERNS")
    print("=" * 80)
    print()
    
    # Load patterns
    patterns_path = Path('results/event_study/event_patterns.json')
    with open(patterns_path, 'r', encoding='utf-8') as f:
        patterns = json.load(f)
    
    # Load ACT/THREAT analysis
    act_threat_path = Path('results/event_study/gpr_act_threat_analysis.json')
    with open(act_threat_path, 'r', encoding='utf-8') as f:
        act_threat = json.load(f)
    
    # Create lookup
    btc_inc = {e['event']: e for e in patterns['BTC_increase']['events']}
    btc_dec = {e['event']: e for e in patterns['BTC_decrease']['events']}
    gold_inc = {e['event']: e for e in patterns['GOLD_increase']['events']}
    gold_dec = {e['event']: e for e in patterns['GOLD_decrease']['events']}
    
    act_threat_inc = {e['event']: e for e in act_threat['BTC_increase']}
    act_threat_dec = {e['event']: e for e in act_threat['BTC_decrease']}
    
    # Categorize events
    pattern_events = {
        'both_inc': [],
        'both_dec': [],
        'btc_inc_gold_dec': [],
        'btc_dec_gold_inc': []
    }
    
    all_events = set(btc_inc.keys()) | set(btc_dec.keys())
    
    for event_id in all_events:
        btc_inc_flag = event_id in btc_inc
        gold_inc_flag = event_id in gold_inc
        
        if btc_inc_flag and gold_inc_flag:
            pattern_events['both_inc'].append(event_id)
        elif not btc_inc_flag and not gold_inc_flag:
            pattern_events['both_dec'].append(event_id)
        elif btc_inc_flag and not gold_inc_flag:
            pattern_events['btc_inc_gold_dec'].append(event_id)
        else:
            pattern_events['btc_dec_gold_inc'].append(event_id)
    
    # Analyze each pattern
    results = {}
    
    for pattern_name, event_ids in pattern_events.items():
        print("=" * 80)
        print(f"PATTERN: {pattern_name.upper()}")
        print("=" * 80)
        print(f"Số lượng: {len(event_ids)} events")
        print()
        
        # Get event details
        events_data = []
        for event_id in event_ids:
            btc_info = btc_inc.get(event_id) or btc_dec.get(event_id, {})
            gold_info = gold_inc.get(event_id) or gold_dec.get(event_id, {})
            
            # Get ACT/THREAT
            act_threat_info = act_threat_inc.get(event_id) or act_threat_dec.get(event_id, {})
            
            events_data.append({
                'event': event_id,
                'date': btc_info.get('date', ''),
                'name': btc_info.get('name', ''),
                'type': btc_info.get('type', ''),
                'region': btc_info.get('region', ''),
                'btc_car': btc_info.get('car', 0),
                'gold_car': gold_info.get('car', 0),
                'gpr_act_ratio': act_threat_info.get('act_ratio', 0),
                'gpr_threat_ratio': act_threat_info.get('threat_ratio', 0)
            })
        
        df = pd.DataFrame(events_data)
        
        # Statistics
        print("THỐNG KÊ:")
        print("-" * 80)
        print(f"Average BTC CAR: {df['btc_car'].mean()*100:.2f}%")
        print(f"Average GOLD CAR: {df['gold_car'].mean()*100:.2f}%")
        print(f"Average ACT Ratio: {df['gpr_act_ratio'].mean():.3f}")
        print(f"Average THREAT Ratio: {df['gpr_threat_ratio'].mean():.3f}")
        print()
        
        # Type distribution
        print("PHÂN LOẠI THEO TYPE:")
        print("-" * 80)
        type_counts = df['type'].value_counts()
        for event_type, count in type_counts.items():
            print(f"  {event_type}: {count} ({count/len(df)*100:.1f}%)")
        print()
        
        # Region distribution
        print("PHÂN LOẠI THEO REGION:")
        print("-" * 80)
        region_counts = df['region'].value_counts()
        for region, count in region_counts.items():
            print(f"  {region}: {count} ({count/len(df)*100:.1f}%)")
        print()
        
        # Top events
        print("TOP 5 EVENTS (theo BTC CAR):")
        print("-" * 80)
        top_events = df.nlargest(5, 'btc_car')
        for _, row in top_events.iterrows():
            print(f"  {row['event']} ({row['date']}): BTC {row['btc_car']*100:+.2f}%, GOLD {row['gold_car']*100:+.2f}%")
            print(f"    {row['name']}")
        print()
        
        results[pattern_name] = {
            'count': len(event_ids),
            'avg_btc_car': df['btc_car'].mean(),
            'avg_gold_car': df['gold_car'].mean(),
            'avg_act_ratio': df['gpr_act_ratio'].mean(),
            'avg_threat_ratio': df['gpr_threat_ratio'].mean(),
            'type_dist': df['type'].value_counts().to_dict(),
            'region_dist': df['region'].value_counts().to_dict(),
            'events': events_data
        }
    
    # Comparison
    print("=" * 80)
    print("SO SÁNH GIỮA CÁC PATTERNS")
    print("=" * 80)
    print()
    
    print("Average CAR:")
    print("-" * 80)
    for pattern_name, data in results.items():
        print(f"{pattern_name}:")
        print(f"  BTC CAR: {data['avg_btc_car']*100:+.2f}%")
        print(f"  GOLD CAR: {data['avg_gold_car']*100:+.2f}%")
    print()
    
    print("GPR ACT/THREAT Ratios:")
    print("-" * 80)
    for pattern_name, data in results.items():
        print(f"{pattern_name}:")
        print(f"  ACT Ratio: {data['avg_act_ratio']:.3f}")
        print(f"  THREAT Ratio: {data['avg_threat_ratio']:.3f}")
    print()
    
    print("Type Distribution:")
    print("-" * 80)
    for pattern_name, data in results.items():
        print(f"{pattern_name}:")
        for event_type, count in data['type_dist'].items():
            print(f"  {event_type}: {count} ({count/data['count']*100:.1f}%)")
    print()
    
    # Save detailed analysis
    output_path = Path('results/event_study/pattern_characteristics_analysis.txt')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("PHÂN TÍCH ĐẶC ĐIỂM CỦA 4 PATTERNS\n")
        f.write("=" * 80 + "\n\n")
        
        pattern_names = {
            'both_inc': '1. CẢ BTC VÀ GOLD TĂNG',
            'both_dec': '2. CẢ BTC VÀ GOLD GIẢM',
            'btc_inc_gold_dec': '3. BTC TĂNG, GOLD GIẢM',
            'btc_dec_gold_inc': '4. BTC GIẢM, GOLD TĂNG (Flight-to-Quality)'
        }
        
        for pattern_name, pattern_label in pattern_names.items():
            data = results[pattern_name]
            f.write("=" * 80 + "\n")
            f.write(f"{pattern_label}\n")
            f.write("=" * 80 + "\n\n")
            
            f.write(f"Số lượng: {data['count']} events ({data['count']/61*100:.1f}%)\n\n")
            
            f.write("THỐNG KÊ:\n")
            f.write("-" * 80 + "\n")
            f.write(f"Average BTC CAR: {data['avg_btc_car']*100:+.2f}%\n")
            f.write(f"Average GOLD CAR: {data['avg_gold_car']*100:+.2f}%\n")
            f.write(f"Average ACT Ratio: {data['avg_act_ratio']:.3f}\n")
            f.write(f"Average THREAT Ratio: {data['avg_threat_ratio']:.3f}\n\n")
            
            f.write("PHÂN LOẠI THEO TYPE:\n")
            f.write("-" * 80 + "\n")
            for event_type, count in data['type_dist'].items():
                f.write(f"  {event_type}: {count} ({count/data['count']*100:.1f}%)\n")
            f.write("\n")
            
            f.write("PHÂN LOẠI THEO REGION:\n")
            f.write("-" * 80 + "\n")
            for region, count in data['region_dist'].items():
                f.write(f"  {region}: {count} ({count/data['count']*100:.1f}%)\n")
            f.write("\n")
            
            f.write("DANH SÁCH EVENTS:\n")
            f.write("-" * 80 + "\n")
            for event in sorted(data['events'], key=lambda x: x['btc_car'], reverse=True):
                f.write(f"{event['event']} ({event['date']}): BTC {event['btc_car']*100:+.2f}%, GOLD {event['gold_car']*100:+.2f}%\n")
                f.write(f"  {event['name']}\n")
                f.write(f"  Type: {event['type']}, Region: {event['region']}\n")
                f.write(f"  ACT Ratio: {event['gpr_act_ratio']:.3f}, THREAT Ratio: {event['gpr_threat_ratio']:.3f}\n")
                f.write("\n")
            f.write("\n")
        
        # Summary comparison
        f.write("\n" + "=" * 80 + "\n")
        f.write("TÓM TẮT SO SÁNH\n")
        f.write("=" * 80 + "\n\n")
        
        f.write("Average CAR:\n")
        for pattern_name, pattern_label in pattern_names.items():
            data = results[pattern_name]
            f.write(f"  {pattern_label}: BTC {data['avg_btc_car']*100:+.2f}%, GOLD {data['avg_gold_car']*100:+.2f}%\n")
        
        f.write("\nGPR ACT/THREAT Ratios:\n")
        for pattern_name, pattern_label in pattern_names.items():
            data = results[pattern_name]
            f.write(f"  {pattern_label}: ACT {data['avg_act_ratio']:.3f}, THREAT {data['avg_threat_ratio']:.3f}\n")
        
        f.write("\nType Distribution:\n")
        for pattern_name, pattern_label in pattern_names.items():
            data = results[pattern_name]
            f.write(f"  {pattern_label}:\n")
            for event_type, count in data['type_dist'].items():
                f.write(f"    {event_type}: {count} ({count/data['count']*100:.1f}%)\n")
    
    print(f"✓ Đã lưu phân tích: {output_path}")


if __name__ == '__main__':
    main()


















