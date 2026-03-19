"""
Phân tích Context của war events: Bắt đầu vs Escalation
Tìm điểm khác biệt về timing của war
"""

import pandas as pd
import json
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

def classify_war_context(event_name: str, event_date: str) -> str:
    """
    Phân loại context của war event
    Returns: 'start', 'escalation', 'continuation', 'withdrawal', 'tension'
    """
    name_lower = event_name.lower()
    date = pd.Timestamp(event_date)
    
    # War bắt đầu
    if any(keyword in name_lower for keyword in ['begin', 'start', 'strikes begin', 'conflict (gaza)', 'tensions escalate']):
        # Check if it's really the start
        if 'israel-palestine conflict (gaza)' in name_lower and date == pd.Timestamp('2023-10-06'):
            return 'start'  # Israel-Palestine conflict bắt đầu
        if 'russia airstrikes in syria begin' in name_lower:
            return 'start'
        if 'russia-ukraine tensions escalate' in name_lower and date == pd.Timestamp('2021-12-30'):
            return 'start'  # Pre-war escalation
        if 'us-north korea tensions escalate' in name_lower:
            return 'tension'  # Tension, chưa phải war
    
    # War escalation
    if any(keyword in name_lower for keyword in ['escalation', 'escalate', 'major battle', 'siege', 'kharkiv', 'mariupol']):
        return 'escalation'
    
    # War continuation/development
    if any(keyword in name_lower for keyword in ['development', 'recent', 'donbas', 'avdiivka', 'kherson', 'mobilization', 'crimea']):
        return 'continuation'
    
    # Withdrawal
    if 'withdrawal' in name_lower or 'withdraw' in name_lower:
        return 'withdrawal'
    
    # Tension (chưa phải war)
    if 'tension' in name_lower or 'tensions' in name_lower:
        return 'tension'
    
    # Attacks/Strikes (có thể là start hoặc continuation)
    if any(keyword in name_lower for keyword in ['attack', 'strikes', 'missile']):
        # Check context
        if 'iran missile strikes' in name_lower:
            return 'escalation'  # Direct action trong conflict đang diễn ra
        if 'gulf of oman tanker' in name_lower:
            return 'escalation'  # Attack trong context conflict
        if 'saudi oil facility attack' in name_lower:
            return 'escalation'  # Major attack
        if 'paris terrorist attacks' in name_lower or 'brussels' in name_lower or 'uk parliament' in name_lower:
            return 'escalation'  # Terrorist attack
    
    # Civil war / Full-scale conflict
    if 'civil war' in name_lower or 'nagorno-karabakh' in name_lower:
        return 'escalation'  # Full-scale conflict
    
    # Default: continuation
    return 'continuation'

def main():
    """Main function"""
    print("=" * 80)
    print("PHÂN TÍCH CONTEXT: WAR BẮT ĐẦU vs WAR ESCALATION")
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
    
    # Extract war events
    btc_inc_war = [e for e in patterns['BTC_increase']['events'] if e['type'] == 'war']
    btc_dec_war = [e for e in patterns['BTC_decrease']['events'] if e['type'] == 'war']
    
    # Create ACT/THREAT lookup
    act_threat_inc = {e['event']: e for e in act_threat['BTC_increase']}
    act_threat_dec = {e['event']: e for e in act_threat['BTC_decrease']}
    
    # Classify context
    results_inc = []
    for event in btc_inc_war:
        context = classify_war_context(event['name'], event['date'])
        act_threat_info = act_threat_inc.get(event['event'], {})
        results_inc.append({
            'event': event['event'],
            'date': event['date'],
            'name': event['name'],
            'car': event['car'],
            'context': context,
            'threat_ratio': act_threat_info.get('threat_ratio', np.nan),
            'act_ratio': act_threat_info.get('act_ratio', np.nan)
        })
    
    results_dec = []
    for event in btc_dec_war:
        context = classify_war_context(event['name'], event['date'])
        act_threat_info = act_threat_dec.get(event['event'], {})
        results_dec.append({
            'event': event['event'],
            'date': event['date'],
            'name': event['name'],
            'car': event['car'],
            'context': context,
            'threat_ratio': act_threat_info.get('threat_ratio', np.nan),
            'act_ratio': act_threat_info.get('act_ratio', np.nan)
        })
    
    # Analyze by context
    print("=" * 80)
    print("PHÂN LOẠI THEO CONTEXT")
    print("=" * 80)
    print()
    
    # BTC TĂNG
    print("BTC TĂNG - Phân loại theo Context:")
    print("-" * 80)
    inc_df = pd.DataFrame(results_inc)
    context_counts_inc = inc_df['context'].value_counts()
    
    for context in ['start', 'tension', 'continuation', 'escalation', 'withdrawal']:
        if context in context_counts_inc.index:
            events = inc_df[inc_df['context'] == context]
            avg_car = events['car'].mean() * 100
            print(f"\n{context.upper()}: {len(events)} events (avg CAR: {avg_car:.2f}%)")
            for _, row in events.iterrows():
                print(f"  - {row['event']} ({row['date']}): {row['car']*100:.2f}% - {row['name']}")
    
    print("\n" + "=" * 80)
    print("BTC GIẢM - Phân loại theo Context:")
    print("-" * 80)
    dec_df = pd.DataFrame(results_dec)
    context_counts_dec = dec_df['context'].value_counts()
    
    for context in ['start', 'tension', 'continuation', 'escalation', 'withdrawal']:
        if context in context_counts_dec.index:
            events = dec_df[dec_df['context'] == context]
            avg_car = events['car'].mean() * 100
            print(f"\n{context.upper()}: {len(events)} events (avg CAR: {avg_car:.2f}%)")
            for _, row in events.iterrows():
                print(f"  - {row['event']} ({row['date']}): {row['car']*100:.2f}% - {row['name']}")
    
    # Save detailed analysis
    output_path = Path('results/event_study/war_context_analysis.txt')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("PHÂN TÍCH CONTEXT: WAR BẮT ĐẦU vs ESCALATION\n")
        f.write("=" * 80 + "\n\n")
        
        f.write("=" * 80 + "\n")
        f.write("BTC TĂNG - Phân loại theo Context\n")
        f.write("=" * 80 + "\n\n")
        
        for context in ['start', 'tension', 'continuation', 'escalation', 'withdrawal']:
            events = inc_df[inc_df['context'] == context]
            if len(events) > 0:
                avg_car = events['car'].mean() * 100
                f.write(f"{context.upper()}: {len(events)} events (avg CAR: {avg_car:.2f}%)\n")
                f.write("-" * 80 + "\n")
                for _, row in events.iterrows():
                    f.write(f"{row['event']} ({row['date']}): {row['car']*100:.2f}%\n")
                    f.write(f"  {row['name']}\n")
                    f.write(f"  THREAT Ratio: {row['threat_ratio']:.3f}, ACT Ratio: {row['act_ratio']:.3f}\n")
                    f.write("\n")
        
        f.write("\n" + "=" * 80 + "\n")
        f.write("BTC GIẢM - Phân loại theo Context\n")
        f.write("=" * 80 + "\n\n")
        
        for context in ['start', 'tension', 'continuation', 'escalation', 'withdrawal']:
            events = dec_df[dec_df['context'] == context]
            if len(events) > 0:
                avg_car = events['car'].mean() * 100
                f.write(f"{context.upper()}: {len(events)} events (avg CAR: {avg_car:.2f}%)\n")
                f.write("-" * 80 + "\n")
                for _, row in events.iterrows():
                    f.write(f"{row['event']} ({row['date']}): {row['car']*100:.2f}%\n")
                    f.write(f"  {row['name']}\n")
                    f.write(f"  THREAT Ratio: {row['threat_ratio']:.3f}, ACT Ratio: {row['act_ratio']:.3f}\n")
                    f.write("\n")
        
        # Summary
        f.write("\n" + "=" * 80 + "\n")
        f.write("TÓM TẮT\n")
        f.write("=" * 80 + "\n\n")
        
        f.write("BTC TĂNG:\n")
        for context in ['start', 'tension', 'continuation', 'escalation', 'withdrawal']:
            events = inc_df[inc_df['context'] == context]
            if len(events) > 0:
                avg_car = events['car'].mean() * 100
                f.write(f"  {context}: {len(events)} events (avg CAR: {avg_car:.2f}%)\n")
        
        f.write("\nBTC GIẢM:\n")
        for context in ['start', 'tension', 'continuation', 'escalation', 'withdrawal']:
            events = dec_df[dec_df['context'] == context]
            if len(events) > 0:
                avg_car = events['car'].mean() * 100
                f.write(f"  {context}: {len(events)} events (avg CAR: {avg_car:.2f}%)\n")
    
    print(f"\n✓ Đã lưu phân tích: {output_path}")
    print()
    
    # Print summary
    print("=" * 80)
    print("TÓM TẮT")
    print("=" * 80)
    print()
    
    print("BTC TĂNG:")
    for context in ['start', 'tension', 'continuation', 'escalation', 'withdrawal']:
        events = inc_df[inc_df['context'] == context]
        if len(events) > 0:
            avg_car = events['car'].mean() * 100
            print(f"  {context}: {len(events)} events (avg CAR: {avg_car:.2f}%)")
    
    print("\nBTC GIẢM:")
    for context in ['start', 'tension', 'continuation', 'escalation', 'withdrawal']:
        events = dec_df[dec_df['context'] == context]
        if len(events) > 0:
            avg_car = events['car'].mean() * 100
            print(f"  {context}: {len(events)} events (avg CAR: {avg_car:.2f}%)")


if __name__ == '__main__':
    import numpy as np
    main()


















