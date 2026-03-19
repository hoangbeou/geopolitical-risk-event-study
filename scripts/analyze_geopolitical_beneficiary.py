"""
Phân tích định tính: Ai được lợi từ mỗi war event?
Giả thuyết: Nước có lợi → BTC tăng/giảm?
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

def analyze_beneficiary(event_name: str, event_date: str, region: str) -> dict:
    """
    Phân tích ai được lợi từ event (định tính)
    Returns: {'beneficiary': 'US/West', 'Russia/China', 'Regional', 'Neutral', 'Unknown'}
    """
    name_lower = event_name.lower()
    date = pd.Timestamp(event_date)
    
    # US/West beneficial events
    if any(keyword in name_lower for keyword in [
        'us-north korea tensions', 'north korea icbm',  # US pressure on NK
        'afghanistan withdrawal',  # US withdrawal (có thể là positive cho US)
        'iran missile strikes on us bases',  # US response expected
        'syria chemical attack / us response',  # US action
        'russia sanctions',  # US/West sanctions
        'us-russia sanctions',  # US action
        'wagner mutiny',  # Internal Russia problem → US/West benefit
    ]):
        return {'beneficiary': 'US/West', 'reason': 'US/West action or opponent weakness'}
    
    # Russia/China beneficial events
    if any(keyword in name_lower for keyword in [
        'russia-ukraine war / avdiivka',  # Russia tactical victory
        'russia-ukraine war / donbas',  # Russia gains
        'russia-ukraine war / kharkiv',  # Russia offensive
        'russia-ukraine war / mariupol',  # Russia capture
        'russia airstrikes in syria begin',  # Russia intervention
        'yemen civil war / saudi intervention',  # Regional power (Saudi)
        'china-india border conflict',  # China assertiveness
    ]):
        return {'beneficiary': 'Russia/China', 'reason': 'Russia/China action or gains'}
    
    # Regional conflicts (không rõ ai lợi)
    if any(keyword in name_lower for keyword in [
        'israel-palestine', 'israel-iran', 'gulf of oman', 'red sea', 'houthis',
        'turkey-syria', 'azerbaijan-armenia', 'beirut explosion',
        'saudi oil facility attack',  # Regional conflict
    ]):
        return {'beneficiary': 'Regional', 'reason': 'Middle East regional conflict'}
    
    # Neutral/Mixed
    if any(keyword in name_lower for keyword in [
        'russia-ukraine war / recent development',  # Unclear
        'russia-ukraine war / mobilization',  # Preparation, unclear outcome
        'russia-ukraine war / kherson',  # Mixed (retreat/capture)
        'middle east tensions',  # General tension
    ]):
        return {'beneficiary': 'Neutral', 'reason': 'Unclear or mixed outcome'}
    
    # Terrorism (generally negative for all)
    if any(keyword in name_lower for keyword in [
        'terrorist attacks', 'paris', 'brussels', 'uk parliament attack',
    ]):
        return {'beneficiary': 'Neutral', 'reason': 'Terrorism - negative for all'}
    
    return {'beneficiary': 'Unknown', 'reason': 'Need manual classification'}

def main():
    """Main function"""
    print("=" * 80)
    print("PHÂN TÍCH ĐỊNH TÍNH: AI ĐƯỢC LỢI TỪ WAR EVENTS?")
    print("=" * 80)
    print()
    
    # Load patterns
    patterns_path = Path('results/event_study/event_patterns.json')
    with open(patterns_path, 'r', encoding='utf-8') as f:
        patterns = json.load(f)
    
    # Extract war events
    btc_inc_war = [e for e in patterns['BTC_increase']['events'] if e['type'] == 'war']
    btc_dec_war = [e for e in patterns['BTC_decrease']['events'] if e['type'] == 'war']
    
    # Analyze beneficiaries
    results_inc = []
    for event in btc_inc_war:
        beneficiary = analyze_beneficiary(event['name'], event['date'], event['region'])
        results_inc.append({
            'event': event['event'],
            'date': event['date'],
            'name': event['name'],
            'car': event['car'],
            'beneficiary': beneficiary['beneficiary'],
            'reason': beneficiary['reason']
        })
    
    results_dec = []
    for event in btc_dec_war:
        beneficiary = analyze_beneficiary(event['name'], event['date'], event['region'])
        results_dec.append({
            'event': event['event'],
            'date': event['date'],
            'name': event['name'],
            'car': event['car'],
            'beneficiary': beneficiary['beneficiary'],
            'reason': beneficiary['reason']
        })
    
    # Analyze patterns
    print("=" * 80)
    print("PHÂN LOẠI THEO BENEFICIARY")
    print("=" * 80)
    print()
    
    inc_df = pd.DataFrame(results_inc)
    dec_df = pd.DataFrame(results_dec)
    
    print("BTC TĂNG - Phân loại theo Beneficiary:")
    print("-" * 80)
    inc_beneficiary_counts = inc_df['beneficiary'].value_counts()
    for beneficiary in ['US/West', 'Russia/China', 'Regional', 'Neutral', 'Unknown']:
        if beneficiary in inc_beneficiary_counts.index:
            events = inc_df[inc_df['beneficiary'] == beneficiary]
            avg_car = events['car'].mean() * 100
            print(f"\n{beneficiary}: {len(events)} events (avg CAR: {avg_car:.2f}%)")
            for _, row in events.iterrows():
                print(f"  - {row['event']} ({row['date']}): {row['car']*100:.2f}%")
                print(f"    {row['name']}")
                print(f"    Reason: {row['reason']}")
    
    print("\n" + "=" * 80)
    print("BTC GIẢM - Phân loại theo Beneficiary:")
    print("-" * 80)
    dec_beneficiary_counts = dec_df['beneficiary'].value_counts()
    for beneficiary in ['US/West', 'Russia/China', 'Regional', 'Neutral', 'Unknown']:
        if beneficiary in dec_beneficiary_counts.index:
            events = dec_df[dec_df['beneficiary'] == beneficiary]
            avg_car = events['car'].mean() * 100
            print(f"\n{beneficiary}: {len(events)} events (avg CAR: {avg_car:.2f}%)")
            for _, row in events.iterrows():
                print(f"  - {row['event']} ({row['date']}): {row['car']*100:.2f}%")
                print(f"    {row['name']}")
                print(f"    Reason: {row['reason']}")
    
    # Save analysis
    output_path = Path('results/event_study/geopolitical_beneficiary_analysis.txt')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("PHÂN TÍCH ĐỊNH TÍNH: AI ĐƯỢC LỢI TỪ WAR EVENTS?\n")
        f.write("=" * 80 + "\n\n")
        
        f.write("GIẢ THUYẾT: Nước có lợi từ event → Ảnh hưởng đến BTC?\n\n")
        
        f.write("=" * 80 + "\n")
        f.write("BTC TĂNG - Phân loại theo Beneficiary\n")
        f.write("=" * 80 + "\n\n")
        
        for beneficiary in ['US/West', 'Russia/China', 'Regional', 'Neutral', 'Unknown']:
            events = inc_df[inc_df['beneficiary'] == beneficiary]
            if len(events) > 0:
                avg_car = events['car'].mean() * 100
                f.write(f"{beneficiary}: {len(events)} events (avg CAR: {avg_car:.2f}%)\n")
                f.write("-" * 80 + "\n")
                for _, row in events.iterrows():
                    f.write(f"{row['event']} ({row['date']}): {row['car']*100:.2f}%\n")
                    f.write(f"  {row['name']}\n")
                    f.write(f"  Reason: {row['reason']}\n")
                    f.write("\n")
        
        f.write("\n" + "=" * 80 + "\n")
        f.write("BTC GIẢM - Phân loại theo Beneficiary\n")
        f.write("=" * 80 + "\n\n")
        
        for beneficiary in ['US/West', 'Russia/China', 'Regional', 'Neutral', 'Unknown']:
            events = dec_df[dec_df['beneficiary'] == beneficiary]
            if len(events) > 0:
                avg_car = events['car'].mean() * 100
                f.write(f"{beneficiary}: {len(events)} events (avg CAR: {avg_car:.2f}%)\n")
                f.write("-" * 80 + "\n")
                for _, row in events.iterrows():
                    f.write(f"{row['event']} ({row['date']}): {row['car']*100:.2f}%\n")
                    f.write(f"  {row['name']}\n")
                    f.write(f"  Reason: {row['reason']}\n")
                    f.write("\n")
        
        # Summary
        f.write("\n" + "=" * 80 + "\n")
        f.write("TÓM TẮT VÀ GIẢ THUYẾT\n")
        f.write("=" * 80 + "\n\n")
        
        f.write("BTC TĂNG:\n")
        for beneficiary in ['US/West', 'Russia/China', 'Regional', 'Neutral', 'Unknown']:
            events = inc_df[inc_df['beneficiary'] == beneficiary]
            if len(events) > 0:
                avg_car = events['car'].mean() * 100
                f.write(f"  {beneficiary}: {len(events)} events (avg CAR: {avg_car:.2f}%)\n")
        
        f.write("\nBTC GIẢM:\n")
        for beneficiary in ['US/West', 'Russia/China', 'Regional', 'Neutral', 'Unknown']:
            events = dec_df[dec_df['beneficiary'] == beneficiary]
            if len(events) > 0:
                avg_car = events['car'].mean() * 100
                f.write(f"  {beneficiary}: {len(events)} events (avg CAR: {avg_car:.2f}%)\n")
        
        f.write("\n" + "=" * 80 + "\n")
        f.write("GIẢ THUYẾT CẦN KIỂM CHỨNG\n")
        f.write("=" * 80 + "\n\n")
        
        f.write("1. US/West beneficial events → BTC tăng? (BTC là asset của phương Tây)\n")
        f.write("2. Russia/China beneficial events → BTC giảm? (Đối thủ của phương Tây)\n")
        f.write("3. Regional conflicts → Mixed? (Tùy context)\n")
        f.write("4. Neutral/Terrorism → Mixed? (Không rõ pattern)\n")
    
    print(f"\n✓ Đã lưu phân tích: {output_path}")
    print()
    
    # Print summary
    print("=" * 80)
    print("TÓM TẮT")
    print("=" * 80)
    print()
    
    print("BTC TĂNG:")
    for beneficiary in ['US/West', 'Russia/China', 'Regional', 'Neutral', 'Unknown']:
        events = inc_df[inc_df['beneficiary'] == beneficiary]
        if len(events) > 0:
            avg_car = events['car'].mean() * 100
            print(f"  {beneficiary}: {len(events)} events (avg CAR: {avg_car:.2f}%)")
    
    print("\nBTC GIẢM:")
    for beneficiary in ['US/West', 'Russia/China', 'Regional', 'Neutral', 'Unknown']:
        events = dec_df[dec_df['beneficiary'] == beneficiary]
        if len(events) > 0:
            avg_car = events['car'].mean() * 100
            print(f"  {beneficiary}: {len(events)} events (avg CAR: {avg_car:.2f}%)")


if __name__ == '__main__':
    main()


















