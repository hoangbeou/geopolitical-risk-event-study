"""
Phân tích kết quả từ Advanced Visualizations:
1. Candlestick Charts - Phân tích bối cảnh kỹ thuật tại thời điểm sự kiện
2. Box Plots - Phân tích phân phối rủi ro theo type và region
"""

import pandas as pd
import numpy as np
import json
from pathlib import Path
from collections import defaultdict

def load_data():
    """Load all necessary data"""
    print("Loading data...")
    
    # Load CAR data
    car_path = Path('results/event_study/event_classification.csv')
    car_df = pd.read_csv(car_path)
    car_df['Date'] = pd.to_datetime(car_df['Date'])
    
    # Load events
    events_path = Path('results/event_study/identified_events.json')
    with open(events_path, 'r', encoding='utf-8') as f:
        events_dict = json.load(f)
    
    return car_df, events_dict


def analyze_candlestick_insights(car_df, events_dict):
    """
    Phân tích insights từ candlestick charts:
    - Top events và bối cảnh kỹ thuật
    - Phân loại theo type và region
    """
    print("\n" + "="*80)
    print("PHÂN TÍCH CANDLESTICK CHARTS - BỐI CẢNH KỸ THUẬT")
    print("="*80)
    
    assets = ['BTC', 'GOLD', 'OIL']
    results = {}
    
    for asset in assets:
        print(f"\n--- {asset} ---")
        asset_car = car_df[car_df['Asset'] == asset].copy()
        asset_car['abs_car'] = asset_car['CAR'].abs()
        top_5 = asset_car.nlargest(5, 'abs_car')
        
        print(f"\nTop 5 Events có CAR lớn nhất:")
        print("-" * 80)
        
        type_dist = defaultdict(int)
        region_dist = defaultdict(int)
        car_by_type = defaultdict(list)
        car_by_region = defaultdict(list)
        
        for idx, row in top_5.iterrows():
            event_id = row['Event']
            car_pct = row['CAR_pct']
            t_stat = row['T_stat']
            
            event_info = events_dict.get(event_id, {})
            event_name = event_info.get('identified', {}).get('name', 'Unknown')
            event_type = event_info.get('identified', {}).get('type', 'unknown')
            event_region = event_info.get('identified', {}).get('region', 'unknown')
            
            type_dist[event_type] += 1
            region_dist[event_region] += 1
            car_by_type[event_type].append(car_pct)
            car_by_region[event_region].append(car_pct)
            
            significance = ""
            if abs(t_stat) > 1.96:
                significance = "***"
            elif abs(t_stat) > 1.65:
                significance = "**"
            elif abs(t_stat) > 1.28:
                significance = "*"
            
            print(f"{event_id:12} | {event_name[:40]:40} | CAR: {car_pct:+7.2f}% | "
                  f"ACT/THREAT: {act_threat:10} | Region: {event_region:12} | {significance}")
        
        # Phân tích phân bố
        print(f"\nPhân bố theo Type:")
        for act_threat, count in type_dist.items():
            if act_threat in ['ACT', 'THREAT'] and len(car_by_type[act_threat]) > 0:
                avg_car = np.mean(car_by_type[act_threat])
                print(f"  {act_threat:12}: {count} events, CAR trung bình: {avg_car:+.2f}%")
        
        print(f"\nPhân bố theo Region:")
        for region, count in region_dist.items():
            avg_car = np.mean(car_by_region[region])
            print(f"  {region:12}: {count} events, CAR trung bình: {avg_car:+.2f}%")
        
        results[asset] = {
            'top_5': top_5,
            'type_dist': dict(type_dist),
            'region_dist': dict(region_dist),
            'car_by_type': {k: np.mean(v) for k, v in car_by_type.items()},
            'car_by_region': {k: np.mean(v) for k, v in car_by_region.items()}
        }
    
    return results


def analyze_boxplot_insights(car_df, events_dict):
    """
    Phân tích insights từ box plots:
    - Phân phối rủi ro theo event type
    - Phân phối rủi ro theo region
    """
    print("\n" + "="*80)
    print("PHÂN TÍCH BOX PLOTS - PHÂN PHỐI RỦI RO")
    print("="*80)
    
    # Merge ACT/THREAT và region vào car_df
    car_df['act_threat'] = car_df['Event'].map(
        lambda x: events_dict.get(x, {}).get('identified', {}).get('act_threat', 'unknown')
    )
    car_df['Region'] = car_df['Event'].map(
        lambda x: events_dict.get(x, {}).get('identified', {}).get('region', 'unknown')
    )
    
    car_df = car_df[car_df['act_threat'] != 'unknown']
    car_df = car_df[car_df['Region'] != 'unknown']
    
    assets = ['BTC', 'GOLD', 'OIL']
    
    # Phân tích theo ACT/THREAT
    print("\n--- PHÂN TÍCH THEO ACT/THREAT ---")
    print("="*80)
    
    for asset in assets:
        print(f"\n{asset}:")
        asset_data = car_df[car_df['Asset'] == asset].copy()
        
        act_threats = ['ACT', 'THREAT']
        print(f"\n{'ACT/THREAT':<12} | {'Count':<8} | {'Mean CAR':<12} | {'Median CAR':<12} | "
              f"{'Std CAR':<12} | {'Min CAR':<12} | {'Max CAR':<12} | {'Risk Level':<12}")
        print("-" * 100)
        
        for at in act_threats:
            type_data = asset_data[asset_data['act_threat'] == at]['CAR_pct']
            if len(type_data) > 0:
                mean_car = type_data.mean()
                median_car = type_data.median()
                std_car = type_data.std()
                min_car = type_data.min()
                max_car = type_data.max()
                count = len(type_data)
                
                # Đánh giá mức độ rủi ro
                if abs(mean_car) > 10 and std_car > 15:
                    risk_level = "Rất Cao"
                elif abs(mean_car) > 5 and std_car > 10:
                    risk_level = "Cao"
                elif abs(mean_car) > 2 and std_car > 5:
                    risk_level = "Trung bình"
                else:
                    risk_level = "Thấp"
                
                print(f"{t:<12} | {count:<8} | {mean_car:+11.2f}% | {median_car:+11.2f}% | "
                      f"{std_car:11.2f}% | {min_car:+11.2f}% | {max_car:+11.2f}% | {risk_level:<12}")
    
    # Phân tích theo Region
    print("\n\n--- PHÂN TÍCH THEO REGION ---")
    print("="*80)
    
    region_map = {
        'asia': 'Asia',
        'europe': 'Europe',
        'middle_east': 'Middle East',
        'americas': 'Americas',
        'global': 'Global'
    }
    car_df['Region'] = car_df['Region'].map(region_map).fillna(car_df['Region'])
    
    for asset in assets:
        print(f"\n{asset}:")
        asset_data = car_df[car_df['Asset'] == asset].copy()
        
        regions = ['Asia', 'Europe', 'Middle East', 'Americas', 'Global']
        print(f"\n{'Region':<15} | {'Count':<8} | {'Mean CAR':<12} | {'Median CAR':<12} | "
              f"{'Std CAR':<12} | {'Risk Level':<12}")
        print("-" * 90)
        
        for r in regions:
            region_data = asset_data[asset_data['Region'] == r]['CAR_pct']
            if len(region_data) > 0:
                mean_car = region_data.mean()
                median_car = region_data.median()
                std_car = region_data.std()
                count = len(region_data)
                
                # Đánh giá mức độ rủi ro
                if abs(mean_car) > 10 and std_car > 15:
                    risk_level = "Rất Cao"
                elif abs(mean_car) > 5 and std_car > 10:
                    risk_level = "Cao"
                elif abs(mean_car) > 2 and std_car > 5:
                    risk_level = "Trung bình"
                else:
                    risk_level = "Thấp"
                
                print(f"{r:<15} | {count:<8} | {mean_car:+11.2f}% | {median_car:+11.2f}% | "
                      f"{std_car:11.2f}% | {risk_level:<12}")


def analyze_technical_context(car_df, events_dict):
    """
    Phân tích bối cảnh kỹ thuật:
    - Sự kiện nào xảy ra trong xu hướng tăng/giảm
    - Mức độ biến động tại thời điểm sự kiện
    """
    print("\n" + "="*80)
    print("PHÂN TÍCH BỐI CẢNH KỸ THUẬT")
    print("="*80)
    
    assets = ['BTC', 'GOLD', 'OIL']
    
    for asset in assets:
        print(f"\n--- {asset} ---")
        asset_car = car_df[car_df['Asset'] == asset].copy()
        asset_car['abs_car'] = asset_car['CAR'].abs()
        top_10 = asset_car.nlargest(10, 'abs_car')
        
        positive_events = top_10[top_10['CAR'] > 0]
        negative_events = top_10[top_10['CAR'] < 0]
        
        print(f"\nTop 10 Events:")
        print(f"  - Sự kiện tích cực (CAR > 0): {len(positive_events)} events")
        print(f"    CAR trung bình: {positive_events['CAR_pct'].mean():+.2f}%")
        print(f"    CAR lớn nhất: {positive_events['CAR_pct'].max():+.2f}%")
        
        print(f"  - Sự kiện tiêu cực (CAR < 0): {len(negative_events)} events")
        print(f"    CAR trung bình: {negative_events['CAR_pct'].mean():+.2f}%")
        print(f"    CAR nhỏ nhất: {negative_events['CAR_pct'].min():+.2f}%")
        
        # Phân tích theo ACT/THREAT
        print(f"\nPhân tích theo ACT/THREAT (Top 10):")
        for act_threat in ['ACT', 'THREAT']:
            at_events = top_10[top_10['Event'].map(
                lambda x: events_dict.get(x, {}).get('identified', {}).get('act_threat', '') == act_threat
            )]
            if len(at_events) > 0:
                print(f"  {act_threat:12}: {len(at_events)} events, "
                      f"CAR trung bình: {at_events['CAR_pct'].mean():+.2f}%")


def generate_summary_report(car_df, events_dict):
    """
    Tạo báo cáo tổng hợp
    """
    print("\n" + "="*80)
    print("BÁO CÁO TỔNG HỢP")
    print("="*80)
    
    # Merge ACT/THREAT và region
    car_df['act_threat'] = car_df['Event'].map(
        lambda x: events_dict.get(x, {}).get('identified', {}).get('act_threat', 'unknown')
    )
    car_df['Region'] = car_df['Event'].map(
        lambda x: events_dict.get(x, {}).get('identified', {}).get('region', 'unknown')
    )
    
    assets = ['BTC', 'GOLD', 'OIL']
    
    print("\n1. TỔNG QUAN RỦI RO THEO TÀI SẢN:")
    print("-" * 80)
    for asset in assets:
        asset_data = car_df[car_df['Asset'] == asset]['CAR_pct']
        print(f"{asset:6}: Mean={asset_data.mean():+7.2f}%, "
              f"Std={asset_data.std():7.2f}%, "
              f"Min={asset_data.min():+7.2f}%, "
              f"Max={asset_data.max():+7.2f}%")
    
    print("\n2. RỦI RO THEO ACT/THREAT:")
    print("-" * 80)
    act_threats = ['ACT', 'THREAT']
    for at in act_threats:
        type_data = car_df[car_df['act_threat'] == at]
        if len(type_data) > 0:
            print(f"\n{t.upper()}:")
            for asset in assets:
                asset_type_data = type_data[type_data['Asset'] == asset]['CAR_pct']
                if len(asset_type_data) > 0:
                    print(f"  {asset:6}: Mean={asset_type_data.mean():+7.2f}%, "
                          f"Std={asset_type_data.std():7.2f}%, "
                          f"Count={len(asset_type_data)}")
    
    print("\n3. KẾT LUẬN CHÍNH:")
    print("-" * 80)
    
    # Tìm loại sự kiện rủi ro nhất cho từng asset
    for asset in assets:
        asset_data = car_df[car_df['Asset'] == asset]
        max_std = 0
        riskiest_type = None
        for at in act_threats:
            type_data = asset_data[asset_data['act_threat'] == at]['CAR_pct']
            if len(type_data) > 0:
                std = type_data.std()
                if std > max_std:
                    max_std = std
                    riskiest_type = t
        
        if riskiest_type:
            print(f"  {asset}: Loại sự kiện rủi ro nhất là '{riskiest_type}' "
                  f"(Std={max_std:.2f}%)")


def main():
    """Main function"""
    print("="*80)
    print("PHÂN TÍCH KẾT QUẢ ADVANCED VISUALIZATIONS")
    print("="*80)
    
    # Load data
    car_df, events_dict = load_data()
    
    # 1. Phân tích candlestick insights
    candlestick_results = analyze_candlestick_insights(car_df, events_dict)
    
    # 2. Phân tích boxplot insights
    analyze_boxplot_insights(car_df, events_dict)
    
    # 3. Phân tích bối cảnh kỹ thuật
    analyze_technical_context(car_df, events_dict)
    
    # 4. Báo cáo tổng hợp
    generate_summary_report(car_df, events_dict)
    
    # Save report
    output_dir = Path('results/event_study/advanced_visualizations')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("\n" + "="*80)
    print("✓ Hoàn thành phân tích!")
    print(f"✓ Kết quả đã được hiển thị trên console")
    print("="*80)


if __name__ == '__main__':
    main()

