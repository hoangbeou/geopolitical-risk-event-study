"""
Phân tích GPRD_ACT và GPRD_THREAT tại các war events
Kiểm chứng giả thuyết: Threats → BTC tăng, Actions → BTC giảm
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

def load_gpr_data():
    """Load GPR data với ACT và THREAT"""
    gpr_path = Path('data/data_gpr_daily_recent.xls')
    if not gpr_path.exists():
        raise FileNotFoundError(f"Không tìm thấy file {gpr_path}")
    
    df = pd.read_excel(gpr_path)
    
    # Convert DAY to datetime
    if 'DAY' in df.columns:
        df['date'] = pd.to_datetime(df['DAY'], format='%Y%m%d', errors='coerce')
        df = df.set_index('date')
    
    # Ensure we have the columns we need
    required_cols = ['GPRD', 'GPRD_ACT', 'GPRD_THREAT']
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Không tìm thấy cột {col} trong file")
    
    return df[required_cols]

def analyze_events_with_gpr():
    """Phân tích events với GPRD_ACT và GPRD_THREAT"""
    print("=" * 80)
    print("PHÂN TÍCH GPRD_ACT vs GPRD_THREAT TẠI WAR EVENTS")
    print("=" * 80)
    print()
    
    # Load GPR data
    print("Đang đọc GPR data...")
    gpr_data = load_gpr_data()
    print(f"✓ Đã đọc GPR data: {len(gpr_data)} ngày")
    print(f"  Date range: {gpr_data.index.min()} đến {gpr_data.index.max()}")
    print()
    
    # Load patterns
    print("Đang đọc event patterns...")
    patterns_path = Path('results/event_study/event_patterns.json')
    with open(patterns_path, 'r', encoding='utf-8') as f:
        patterns = json.load(f)
    print("✓ Đã đọc event patterns")
    print()
    
    # Extract war events
    btc_increase_war = [e for e in patterns['BTC_increase']['events'] if e['type'] == 'war']
    btc_decrease_war = [e for e in patterns['BTC_decrease']['events'] if e['type'] == 'war']
    
    print(f"War events làm BTC TĂNG: {len(btc_increase_war)}")
    print(f"War events làm BTC GIẢM: {len(btc_decrease_war)}")
    print()
    
    # Analyze each event
    results = {
        'BTC_increase': [],
        'BTC_decrease': []
    }
    
    for event in btc_increase_war:
        event_date = pd.Timestamp(event['date'])
        
        # Get GPR values at event date
        if event_date in gpr_data.index:
            gpr_row = gpr_data.loc[event_date]
            gpr_total = gpr_row['GPRD']
            gpr_act = gpr_row['GPRD_ACT']
            gpr_threat = gpr_row['GPRD_THREAT']
            
            # Calculate ratios
            act_ratio = gpr_act / gpr_total if gpr_total > 0 else np.nan
            threat_ratio = gpr_threat / gpr_total if gpr_total > 0 else np.nan
            
            results['BTC_increase'].append({
                'event': event['event'],
                'date': event['date'],
                'name': event['name'],
                'car': event['car'],
                'gpr_total': gpr_total,
                'gpr_act': gpr_act,
                'gpr_threat': gpr_threat,
                'act_ratio': act_ratio,
                'threat_ratio': threat_ratio
            })
        else:
            print(f"⚠ Không tìm thấy GPR data cho {event['event']} ({event['date']})")
    
    for event in btc_decrease_war:
        event_date = pd.Timestamp(event['date'])
        
        # Get GPR values at event date
        if event_date in gpr_data.index:
            gpr_row = gpr_data.loc[event_date]
            gpr_total = gpr_row['GPRD']
            gpr_act = gpr_row['GPRD_ACT']
            gpr_threat = gpr_row['GPRD_THREAT']
            
            # Calculate ratios
            act_ratio = gpr_act / gpr_total if gpr_total > 0 else np.nan
            threat_ratio = gpr_threat / gpr_total if gpr_total > 0 else np.nan
            
            results['BTC_decrease'].append({
                'event': event['event'],
                'date': event['date'],
                'name': event['name'],
                'car': event['car'],
                'gpr_total': gpr_total,
                'gpr_act': gpr_act,
                'gpr_threat': gpr_threat,
                'act_ratio': act_ratio,
                'threat_ratio': threat_ratio
            })
        else:
            print(f"⚠ Không tìm thấy GPR data cho {event['event']} ({event['date']})")
    
    # Calculate statistics
    print("=" * 80)
    print("THỐNG KÊ GPRD_ACT vs GPRD_THREAT")
    print("=" * 80)
    print()
    
    inc_df = pd.DataFrame(results['BTC_increase'])
    dec_df = pd.DataFrame(results['BTC_decrease'])
    
    if len(inc_df) > 0:
        print("WAR EVENTS LÀM BTC TĂNG:")
        print("-" * 80)
        print(f"Average GPRD_ACT: {inc_df['gpr_act'].mean():.2f}")
        print(f"Average GPRD_THREAT: {inc_df['gpr_threat'].mean():.2f}")
        print(f"Average ACT Ratio: {inc_df['act_ratio'].mean():.3f}")
        print(f"Average THREAT Ratio: {inc_df['threat_ratio'].mean():.3f}")
        print()
    
    if len(dec_df) > 0:
        print("WAR EVENTS LÀM BTC GIẢM:")
        print("-" * 80)
        print(f"Average GPRD_ACT: {dec_df['gpr_act'].mean():.2f}")
        print(f"Average GPRD_THREAT: {dec_df['gpr_threat'].mean():.2f}")
        print(f"Average ACT Ratio: {dec_df['act_ratio'].mean():.3f}")
        print(f"Average THREAT Ratio: {dec_df['threat_ratio'].mean():.3f}")
        print()
    
    # Save detailed results
    output_dir = Path('results/event_study')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save JSON
    json_path = output_dir / 'gpr_act_threat_analysis.json'
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False, default=str)
    print(f"✓ Đã lưu JSON: {json_path}")
    
    # Save text report
    txt_path = output_dir / 'gpr_act_threat_analysis.txt'
    with open(txt_path, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("PHÂN TÍCH GPRD_ACT vs GPRD_THREAT TẠI WAR EVENTS\n")
        f.write("=" * 80 + "\n\n")
        
        f.write("GIẢ THUYẾT: Threats → BTC tăng, Actions → BTC giảm\n\n")
        
        f.write("=" * 80 + "\n")
        f.write("WAR EVENTS LÀM BTC TĂNG\n")
        f.write("=" * 80 + "\n\n")
        
        for event in sorted(results['BTC_increase'], key=lambda x: x['car'], reverse=True):
            f.write(f"{event['event']} ({event['date']}): {event['car']*100:.2f}%\n")
            f.write(f"  {event['name']}\n")
            f.write(f"  GPRD_ACT: {event['gpr_act']:.2f} (Ratio: {event['act_ratio']:.3f})\n")
            f.write(f"  GPRD_THREAT: {event['gpr_threat']:.2f} (Ratio: {event['threat_ratio']:.3f})\n")
            f.write(f"  GPRD Total: {event['gpr_total']:.2f}\n")
            f.write("\n")
        
        f.write("\n" + "=" * 80 + "\n")
        f.write("WAR EVENTS LÀM BTC GIẢM\n")
        f.write("=" * 80 + "\n\n")
        
        for event in sorted(results['BTC_decrease'], key=lambda x: x['car']):
            f.write(f"{event['event']} ({event['date']}): {event['car']*100:.2f}%\n")
            f.write(f"  {event['name']}\n")
            f.write(f"  GPRD_ACT: {event['gpr_act']:.2f} (Ratio: {event['act_ratio']:.3f})\n")
            f.write(f"  GPRD_THREAT: {event['gpr_threat']:.2f} (Ratio: {event['threat_ratio']:.3f})\n")
            f.write(f"  GPRD Total: {event['gpr_total']:.2f}\n")
            f.write("\n")
        
        # Statistics
        f.write("\n" + "=" * 80 + "\n")
        f.write("THỐNG KÊ\n")
        f.write("=" * 80 + "\n\n")
        
        if len(inc_df) > 0:
            f.write("BTC TĂNG:\n")
            f.write(f"  Average GPRD_ACT: {inc_df['gpr_act'].mean():.2f}\n")
            f.write(f"  Average GPRD_THREAT: {inc_df['gpr_threat'].mean():.2f}\n")
            f.write(f"  Average ACT Ratio: {inc_df['act_ratio'].mean():.3f}\n")
            f.write(f"  Average THREAT Ratio: {inc_df['threat_ratio'].mean():.3f}\n")
            f.write("\n")
        
        if len(dec_df) > 0:
            f.write("BTC GIẢM:\n")
            f.write(f"  Average GPRD_ACT: {dec_df['gpr_act'].mean():.2f}\n")
            f.write(f"  Average GPRD_THREAT: {dec_df['gpr_threat'].mean():.2f}\n")
            f.write(f"  Average ACT Ratio: {dec_df['act_ratio'].mean():.3f}\n")
            f.write(f"  Average THREAT Ratio: {dec_df['threat_ratio'].mean():.3f}\n")
            f.write("\n")
        
        # Comparison
        if len(inc_df) > 0 and len(dec_df) > 0:
            f.write("SO SÁNH:\n")
            f.write(f"  ACT Ratio: Tăng ({inc_df['act_ratio'].mean():.3f}) vs Giảm ({dec_df['act_ratio'].mean():.3f})\n")
            f.write(f"  THREAT Ratio: Tăng ({inc_df['threat_ratio'].mean():.3f}) vs Giảm ({dec_df['threat_ratio'].mean():.3f})\n")
            f.write("\n")
            
            if inc_df['threat_ratio'].mean() > dec_df['threat_ratio'].mean():
                f.write("✓ GIẢ THUYẾT ĐƯỢC XÁC NHẬN: Events làm BTC tăng có THREAT ratio cao hơn!\n")
            else:
                f.write("✗ GIẢ THUYẾT KHÔNG ĐƯỢC XÁC NHẬN: Cần phân tích thêm\n")
            
            if dec_df['act_ratio'].mean() > inc_df['act_ratio'].mean():
                f.write("✓ GIẢ THUYẾT ĐƯỢC XÁC NHẬN: Events làm BTC giảm có ACT ratio cao hơn!\n")
            else:
                f.write("✗ GIẢ THUYẾT KHÔNG ĐƯỢC XÁC NHẬN: Cần phân tích thêm\n")
    
    print(f"✓ Đã tạo report: {txt_path}")
    print()
    
    # Print summary
    if len(inc_df) > 0 and len(dec_df) > 0:
        print("=" * 80)
        print("KẾT QUẢ KIỂM CHỨNG GIẢ THUYẾT")
        print("=" * 80)
        print()
        print(f"THREAT Ratio:")
        print(f"  BTC TĂNG: {inc_df['threat_ratio'].mean():.3f}")
        print(f"  BTC GIẢM: {dec_df['threat_ratio'].mean():.3f}")
        print()
        print(f"ACT Ratio:")
        print(f"  BTC TĂNG: {inc_df['act_ratio'].mean():.3f}")
        print(f"  BTC GIẢM: {dec_df['act_ratio'].mean():.3f}")
        print()
        
        if inc_df['threat_ratio'].mean() > dec_df['threat_ratio'].mean():
            print("✓ THREAT hypothesis: ĐƯỢC XÁC NHẬN!")
            print("  → Events làm BTC tăng có THREAT ratio cao hơn")
        else:
            print("✗ THREAT hypothesis: KHÔNG được xác nhận")
        
        if dec_df['act_ratio'].mean() > inc_df['act_ratio'].mean():
            print("✓ ACT hypothesis: ĐƯỢC XÁC NHẬN!")
            print("  → Events làm BTC giảm có ACT ratio cao hơn")
        else:
            print("✗ ACT hypothesis: KHÔNG được xác nhận")


if __name__ == '__main__':
    analyze_events_with_gpr()


















