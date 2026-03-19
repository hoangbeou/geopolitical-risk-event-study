#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tạo các file đầu vào cần thiết từ Event Study results"""
import sys
import json
import pandas as pd
from pathlib import Path
import io

# Fix encoding
if hasattr(sys.stdout, 'buffer') and not hasattr(sys.stdout, '_encoding_set'):
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stdout._encoding_set = True
    except (AttributeError, ValueError):
        pass

sys.path.insert(0, str(Path(__file__).parent))

from scripts.run_qqr import GeopoliticalRiskAnalysis
from scripts.run_event_study import EventStudy
from scripts.detect_events import GPREventDetector

def create_missing_files():
    """Tạo các file JSON/CSV cần thiết"""
    print("=" * 80)
    print("TẠO CÁC FILE ĐẦU VÀO CẦN THIẾT")
    print("=" * 80)
    print()
    
    # Load data
    print("Loading data...")
    analysis = GeopoliticalRiskAnalysis('data/data_optimized.csv', max_scale=9)
    data = analysis.preprocessor.load_data('data/data_optimized.csv')
    
    # Initialize Event Study
    event_study = EventStudy(data, assets=['BTC', 'GOLD', 'OIL'])
    
    # Analyze all events với auto-detection (71 events)
    print("Analyzing events với auto-detection...")
    results = event_study.analyze_all_events(use_auto_detection=True)
    results = event_study._reindex_results(results)
    
    # Lấy events từ results để tạo identified_events.json
    events = {}
    for event_name, event_data in results.items():
        events[event_name] = event_data['event_info']
    
    # Create output directory
    output_dir = Path('results/event_study')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Create identified_events.json
    print("Creating identified_events.json...")
    identified_events = {}
    for event_name, event_data in events.items():
        event_info = event_data
        identified_events[event_name] = {
            'date': event_info['date'].strftime('%Y-%m-%d'),
            'description': event_info.get('description', event_name),
            'window': event_info.get('window', [-10, 10])
        }
    
    with open(output_dir / 'identified_events.json', 'w', encoding='utf-8') as f:
        json.dump(identified_events, f, indent=2, ensure_ascii=False)
    print(f"  ✓ Created identified_events.json with {len(identified_events)} events")
    
    # 2. Create event_classification.csv
    print("Creating event_classification.csv...")
    car_data = []
    for event_name, event_data in results.items():
        event_info = event_data['event_info']
        asset_results = event_data['results']
        
        for asset, result in asset_results.items():
            car_data.append({
                'Event': event_name,
                'Date': event_info['date'].strftime('%Y-%m-%d'),
                'Asset': asset,
                'CAR': result['car_final'],
                'CAR_pct': result['car_final'] * 100,
                'T_stat': result['t_stat'],
                'Description': event_info.get('description', event_name)
            })
    
    car_df = pd.DataFrame(car_data)
    car_df.to_csv(output_dir / 'event_classification.csv', index=False, encoding='utf-8')
    print(f"  ✓ Created event_classification.csv with {len(car_df)} rows")
    
    # 3. Create event_patterns.json
    print("Creating event_patterns.json...")
    patterns = {
        'BTC_increase': {'events': []},
        'BTC_decrease': {'events': []},
        'GOLD_increase': {'events': []},
        'GOLD_decrease': {'events': []}
    }
    
    for event_name, event_data in results.items():
        event_info = event_data['event_info']
        asset_results = event_data['results']
        
        for asset, result in asset_results.items():
            car = result['car_final']
            if asset == 'BTC':
                if car > 0:
                    patterns['BTC_increase']['events'].append({
                        'event': event_name,
                        'date': event_info['date'].strftime('%Y-%m-%d'),
                        'car': car,
                        'car_pct': car * 100,
                        'description': event_info.get('description', event_name)
                    })
                else:
                    patterns['BTC_decrease']['events'].append({
                        'event': event_name,
                        'date': event_info['date'].strftime('%Y-%m-%d'),
                        'car': car,
                        'car_pct': car * 100,
                        'description': event_info.get('description', event_name)
                    })
            elif asset == 'GOLD':
                if car > 0:
                    patterns['GOLD_increase']['events'].append({
                        'event': event_name,
                        'date': event_info['date'].strftime('%Y-%m-%d'),
                        'car': car,
                        'car_pct': car * 100,
                        'description': event_info.get('description', event_name)
                    })
                else:
                    patterns['GOLD_decrease']['events'].append({
                        'event': event_name,
                        'date': event_info['date'].strftime('%Y-%m-%d'),
                        'car': car,
                        'car_pct': car * 100,
                        'description': event_info.get('description', event_name)
                    })
    
    with open(output_dir / 'event_patterns.json', 'w', encoding='utf-8') as f:
        json.dump(patterns, f, indent=2, ensure_ascii=False)
    print(f"  ✓ Created event_patterns.json")
    
    # 4. Create gpr_act_threat_analysis.json (simplified - using same patterns)
    print("Creating gpr_act_threat_analysis.json...")
    act_threat = {
        'BTC_increase': patterns['BTC_increase']['events'],
        'BTC_decrease': patterns['BTC_decrease']['events'],
        'GOLD_increase': patterns['GOLD_increase']['events'],
        'GOLD_decrease': patterns['GOLD_decrease']['events']
    }
    
    with open(output_dir / 'gpr_act_threat_analysis.json', 'w', encoding='utf-8') as f:
        json.dump(act_threat, f, indent=2, ensure_ascii=False)
    print(f"  ✓ Created gpr_act_threat_analysis.json")
    
    print()
    print("=" * 80)
    print("HOÀN THÀNH TẠO CÁC FILE ĐẦU VÀO")
    print("=" * 80)

if __name__ == '__main__':
    create_missing_files()

