"""
Robustness Check: So sánh Mean Adjusted Model vs Market Model
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.run_event_study import EventStudy
from scripts.detect_events import GPREventDetector
from src.preprocessing import DataPreprocessor

def run_robustness_check():
    """Chạy robustness check so sánh Mean Adjusted Model và Market Model"""
    
    print("=" * 80)
    print("ROBUSTNESS CHECK: MEAN ADJUSTED MODEL vs MARKET MODEL")
    print("=" * 80)
    
    # Load data
    print("\n1. Loading data...")
    # Try different possible paths
    possible_paths = [
        Path("data/raw/data.csv"),
        Path("data/merged_data.csv"),
        Path("data/data.csv")
    ]
    
    data_path = None
    for path in possible_paths:
        if path.exists():
            data_path = path
            break
    
    if data_path is None:
        print(f"ERROR: Khong tim thay file data. Da thu:")
        for p in possible_paths:
            print(f"  - {p}")
        return
    
    # Load data using preprocessor (same as run_event_study.py)
    preprocessor = DataPreprocessor()
    data = preprocessor.load_data(str(data_path))
    print(f"   Data loaded: {len(data)} observations")
    print(f"   Date range: {data.index.min()} to {data.index.max()}")
    
    # Preprocess data
    print("\n2. Preprocessing data...")
    processed = preprocessor.preprocess_data(data)
    data_processed = processed['returns']
    print(f"   Processed data: {len(data_processed)} observations")
    
    # Detect events (cần dùng data gốc có GPR)
    print("\n3. Detecting events...")
    detector = GPREventDetector(data)
    events = detector.detect_all_events()
    print(f"   Detected {len(events)} events")
    
    # Run Event Study với Mean Adjusted Model
    print("\n4. Running Event Study với Mean Adjusted Model...")
    event_study_mean = EventStudy(
        data=data,  # Dùng data gốc, không phải data_processed
        assets=['BTC', 'GOLD', 'OIL'],
        event_window=(-10, 10),
        estimation_window=120,
        model='mean'
    )
    # Load events using load_events_from_detector (sẽ tạo đúng format)
    events_dict_mean = event_study_mean.load_events_from_detector(events)
    results_mean = event_study_mean.analyze_all_events(events=events_dict_mean, use_auto_detection=False)
    
    # Run Event Study với Market Model
    print("\n5. Running Event Study với Market Model...")
    event_study_market = EventStudy(
        data=data,  # Dùng data gốc, không phải data_processed
        assets=['BTC', 'GOLD', 'OIL'],
        event_window=(-10, 10),
        estimation_window=120,
        model='market'
    )
    # Load events using load_events_from_detector (sẽ tạo đúng format)
    events_dict_market = event_study_market.load_events_from_detector(events)
    results_market = event_study_market.analyze_all_events(events=events_dict_market, use_auto_detection=False)
    
    # Tính toán CAAR cho cả hai mô hình
    print("\n6. Computing CAAR comparison...")
    
    stats_mean = event_study_mean.compute_aggregate_statistics(results_mean)
    stats_market = event_study_market.compute_aggregate_statistics(results_market)
    
    # So sánh CAAR tại T+10 (cuối cửa sổ sự kiện)
    comparison_data = []
    
    for asset in ['BTC', 'GOLD', 'OIL']:
        if asset in stats_mean and asset in stats_market:
            # CAAR tại T+10
            caar_mean = stats_mean[asset]['CAAR'][-1]  # Giá trị cuối cùng
            caar_market = stats_market[asset]['CAAR'][-1]
            
            # Tính Std Dev của CAAR (từ CAR của từng sự kiện)
            car_mean_list = []
            car_market_list = []
            
            for event_id, event_data in results_mean.items():
                if asset in event_data['results']:
                    car_mean = event_data['results'][asset]['car'].iloc[-1] if 'car' in event_data['results'][asset] else np.nan
                    if not np.isnan(car_mean):
                        car_mean_list.append(car_mean)
            
            for event_id, event_data in results_market.items():
                if asset in event_data['results']:
                    car_market = event_data['results'][asset]['car'].iloc[-1] if 'car' in event_data['results'][asset] else np.nan
                    if not np.isnan(car_market):
                        car_market_list.append(car_market)
            
            std_mean = np.std(car_mean_list) if car_mean_list else np.nan
            std_market = np.std(car_market_list) if car_market_list else np.nan
            
            # Tính Patell Z-stat (từ CAAR_Z)
            z_mean = stats_mean[asset]['CAAR_Z'][-1] if 'CAAR_Z' in stats_mean[asset] else np.nan
            z_market = stats_market[asset]['CAAR_Z'][-1] if 'CAAR_Z' in stats_market[asset] else np.nan
            
            # Chênh lệch
            diff = caar_mean - caar_market
            diff_pct = (diff / abs(caar_market) * 100) if caar_market != 0 else np.nan
            
            comparison_data.append({
                'Asset': asset,
                'CAAR_Mean': caar_mean * 100,  # Convert to percentage
                'CAAR_Market': caar_market * 100,
                'Difference': diff * 100,
                'Difference_%': diff_pct,
                'StdDev_Mean': std_mean * 100,
                'StdDev_Market': std_market * 100,
                'Z_Mean': z_mean,
                'Z_Market': z_market,
                'Num_Events': len(car_mean_list)
            })
    
    # Tạo DataFrame
    comparison_df = pd.DataFrame(comparison_data)
    
    # Lưu kết quả
    output_dir = Path("results")
    output_dir.mkdir(exist_ok=True)
    
    output_file = output_dir / "robustness_check_comparison.csv"
    comparison_df.to_csv(output_file, index=False)
    print(f"\n7. Results saved to: {output_file}")
    
    # In kết quả
    print("\n" + "=" * 80)
    print("KẾT QUẢ SO SÁNH")
    print("=" * 80)
    print(comparison_df.to_string(index=False))
    
    # Tính toán correlation
    print("\n" + "=" * 80)
    print("PHÂN TÍCH BỔ SUNG")
    print("=" * 80)
    
    # Tính correlation giữa CAR của từng sự kiện
    for asset in ['BTC', 'GOLD', 'OIL']:
        car_mean_list = []
        car_market_list = []
        event_ids = []
        
        for event_id in results_mean.keys():
            if event_id in results_market:
                if asset in results_mean[event_id]['results'] and asset in results_market[event_id]['results']:
                    car_mean = results_mean[event_id]['results'][asset]['car'].iloc[-1] if 'car' in results_mean[event_id]['results'][asset] else np.nan
                    car_market = results_market[event_id]['results'][asset]['car'].iloc[-1] if 'car' in results_market[event_id]['results'][asset] else np.nan
                    
                    if not (np.isnan(car_mean) or np.isnan(car_market)):
                        car_mean_list.append(car_mean)
                        car_market_list.append(car_market)
                        event_ids.append(event_id)
        
        if len(car_mean_list) > 1:
            correlation = np.corrcoef(car_mean_list, car_market_list)[0, 1]
            print(f"\n{asset}:")
            print(f"  Correlation giữa CAR (Mean) và CAR (Market): {correlation:.4f}")
            print(f"  Số sự kiện so sánh: {len(car_mean_list)}")
    
    print("\n" + "=" * 80)
    print("KẾT LUẬN")
    print("=" * 80)
    print("Nếu CAAR giữa hai mô hình gần giống nhau (chênh lệch < 5%) và correlation cao (> 0.95),")
    print("thì Mean Adjusted Model là phù hợp và kết quả là robust.")
    print("\nHoàn thành!")
    
    return comparison_df

if __name__ == '__main__':
    comparison_df = run_robustness_check()

