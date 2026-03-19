# -*- coding: utf-8 -*-
"""
Robustness Check: So sánh Mean Adjusted Model vs Market Model (DXY) vs Market Model (S&P 500)
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

class EventStudyWithMarketProxy(EventStudy):
    """EventStudy với khả năng chọn market proxy"""
    
    def __init__(self, *args, market_proxy='DXY', **kwargs):
        super().__init__(*args, **kwargs)
        # Override market series
        self.market_series = market_proxy
        self.market_returns = self._prepare_market_returns()

def run_robustness_check_with_sp500():
    """Chạy robustness check với cả DXY và S&P 500"""
    
    print("=" * 80)
    print("ROBUSTNESS CHECK: MEAN vs MARKET (DXY) vs MARKET (S&P 500)")
    print("=" * 80)
    
    # Load data
    print("\n1. Loading data...")
    possible_paths = [
        Path("data/raw/data_with_sp500.csv"),
        Path("data/raw/data.csv"),
        Path("data/merged_data.csv"),
    ]
    
    data_path = None
    for path in possible_paths:
        if path.exists():
            data_path = path
            break
    
    if data_path is None:
        print(f"ERROR: Khong tim thay file data")
        return
    
    preprocessor = DataPreprocessor()
    try:
        data = preprocessor.load_data(str(data_path))
    except:
        # Fallback: read directly
        data = pd.read_csv(data_path, index_col=0, parse_dates=True, dayfirst=True)
        if not isinstance(data.index, pd.DatetimeIndex):
            data.index = pd.to_datetime(data.index, dayfirst=True, errors='coerce')
    
    print(f"   Data loaded: {len(data)} observations")
    print(f"   Date range: {data.index.min()} to {data.index.max()}")
    print(f"   Columns: {list(data.columns)}")
    
    # Check if SP500 exists
    has_sp500 = 'SP500' in data.columns or 'SP500_ret' in data.columns
    print(f"   Has SP500: {has_sp500}")
    
    # Detect events
    print("\n2. Detecting events...")
    detector = GPREventDetector(data)
    events = detector.detect_all_events()
    print(f"   Detected {len(events)} events")
    
    # Run Event Study với Mean Adjusted Model
    print("\n3. Running Event Study với Mean Adjusted Model...")
    event_study_mean = EventStudy(
        data=data,
        assets=['BTC', 'GOLD', 'OIL'],
        event_window=(-10, 10),
        estimation_window=120,
        model='mean'
    )
    events_dict_mean = event_study_mean.load_events_from_detector(events)
    results_mean = event_study_mean.analyze_all_events(events=events_dict_mean, use_auto_detection=False)
    
    # Run Event Study với Market Model (DXY)
    print("\n4. Running Event Study với Market Model (DXY)...")
    event_study_dxy = EventStudyWithMarketProxy(
        data=data,
        assets=['BTC', 'GOLD', 'OIL'],
        event_window=(-10, 10),
        estimation_window=120,
        model='market',
        market_proxy='DXY'
    )
    events_dict_dxy = event_study_dxy.load_events_from_detector(events)
    results_dxy = event_study_dxy.analyze_all_events(events=events_dict_dxy, use_auto_detection=False)
    
    # Run Event Study với Market Model (S&P 500) - nếu có
    results_sp500 = None
    if has_sp500:
        print("\n5. Running Event Study với Market Model (S&P 500)...")
        # Check column name
        sp500_col = 'SP500' if 'SP500' in data.columns else 'SP500_ret'
        if sp500_col == 'SP500_ret':
            # Need to create SP500 price column from returns
            print("   Warning: SP500_ret found but SP500 price not found. Skipping S&P 500 model.")
            has_sp500 = False
        else:
            try:
                event_study_sp500 = EventStudyWithMarketProxy(
                    data=data,
                    assets=['BTC', 'GOLD', 'OIL'],
                    event_window=(-10, 10),
                    estimation_window=120,
                    model='market',
                    market_proxy='SP500'
                )
                events_dict_sp500 = event_study_sp500.load_events_from_detector(events)
                results_sp500 = event_study_sp500.analyze_all_events(events=events_dict_sp500, use_auto_detection=False)
            except Exception as e:
                print(f"   ERROR running S&P 500 model: {e}")
                has_sp500 = False
    
    # Tính toán CAAR
    print("\n6. Computing CAAR comparison...")
    
    stats_mean = event_study_mean.compute_aggregate_statistics(results_mean)
    stats_dxy = event_study_dxy.compute_aggregate_statistics(results_dxy)
    
    comparison_data = []
    
    for asset in ['BTC', 'GOLD', 'OIL']:
        if asset in stats_mean and asset in stats_dxy:
            # CAAR tại T+10
            caar_mean = stats_mean[asset]['CAAR'][-1]
            caar_dxy = stats_dxy[asset]['CAAR'][-1]
            
            # Tính Std Dev
            car_mean_list = []
            car_dxy_list = []
            
            for event_id, event_data in results_mean.items():
                if asset in event_data['results']:
                    car_mean = event_data['results'][asset]['car'].iloc[-1] if 'car' in event_data['results'][asset] else np.nan
                    if not np.isnan(car_mean):
                        car_mean_list.append(car_mean)
            
            for event_id, event_data in results_dxy.items():
                if asset in event_data['results']:
                    car_dxy = event_data['results'][asset]['car'].iloc[-1] if 'car' in event_data['results'][asset] else np.nan
                    if not np.isnan(car_dxy):
                        car_dxy_list.append(car_dxy)
            
            std_mean = np.std(car_mean_list) if car_mean_list else np.nan
            std_dxy = np.std(car_dxy_list) if car_dxy_list else np.nan
            
            # Correlation
            car_mean_aligned = []
            car_dxy_aligned = []
            for event_id in results_mean.keys():
                if event_id in results_dxy:
                    if asset in results_mean[event_id]['results'] and asset in results_dxy[event_id]['results']:
                        car_mean = results_mean[event_id]['results'][asset]['car'].iloc[-1] if 'car' in results_mean[event_id]['results'][asset] else np.nan
                        car_dxy = results_dxy[event_id]['results'][asset]['car'].iloc[-1] if 'car' in results_dxy[event_id]['results'][asset] else np.nan
                        if not (np.isnan(car_mean) or np.isnan(car_dxy)):
                            car_mean_aligned.append(car_mean)
                            car_dxy_aligned.append(car_dxy)
            
            correlation_dxy = np.corrcoef(car_mean_aligned, car_dxy_aligned)[0, 1] if len(car_mean_aligned) > 1 else np.nan
            
            row = {
                'Asset': asset,
                'CAAR_Mean': caar_mean * 100,
                'CAAR_Market_DXY': caar_dxy * 100,
                'Difference_DXY': (caar_mean - caar_dxy) * 100,
                'Correlation_DXY': correlation_dxy,
                'StdDev_Mean': std_mean * 100,
                'StdDev_DXY': std_dxy * 100,
                'Num_Events': len(car_mean_list)
            }
            
            # Add S&P 500 if available
            if has_sp500 and results_sp500:
                stats_sp500 = event_study_sp500.compute_aggregate_statistics(results_sp500)
                if asset in stats_sp500:
                    caar_sp500 = stats_sp500[asset]['CAAR'][-1]
                    car_sp500_list = []
                    for event_id, event_data in results_sp500.items():
                        if asset in event_data['results']:
                            car_sp500 = event_data['results'][asset]['car'].iloc[-1] if 'car' in event_data['results'][asset] else np.nan
                            if not np.isnan(car_sp500):
                                car_sp500_list.append(car_sp500)
                    
                    std_sp500 = np.std(car_sp500_list) if car_sp500_list else np.nan
                    
                    # Correlation với S&P 500
                    car_sp500_aligned = []
                    car_mean_sp500 = []
                    for event_id in results_mean.keys():
                        if event_id in results_sp500:
                            if asset in results_mean[event_id]['results'] and asset in results_sp500[event_id]['results']:
                                car_mean = results_mean[event_id]['results'][asset]['car'].iloc[-1] if 'car' in results_mean[event_id]['results'][asset] else np.nan
                                car_sp500 = results_sp500[event_id]['results'][asset]['car'].iloc[-1] if 'car' in results_sp500[event_id]['results'][asset] else np.nan
                                if not (np.isnan(car_mean) or np.isnan(car_sp500)):
                                    car_mean_sp500.append(car_mean)
                                    car_sp500_aligned.append(car_sp500)
                    
                    correlation_sp500 = np.corrcoef(car_mean_sp500, car_sp500_aligned)[0, 1] if len(car_mean_sp500) > 1 else np.nan
                    
                    row['CAAR_Market_SP500'] = caar_sp500 * 100
                    row['Difference_SP500'] = (caar_mean - caar_sp500) * 100
                    row['Correlation_SP500'] = correlation_sp500
                    row['StdDev_SP500'] = std_sp500 * 100
            
            comparison_data.append(row)
    
    # Tạo DataFrame
    comparison_df = pd.DataFrame(comparison_data)
    
    # Lưu kết quả
    output_dir = Path("results")
    output_dir.mkdir(exist_ok=True)
    
    output_file = output_dir / "robustness_check_with_sp500.csv"
    comparison_df.to_csv(output_file, index=False)
    print(f"\n7. Results saved to: {output_file}")
    
    # In kết quả
    print("\n" + "=" * 80)
    print("KET QUA SO SANH")
    print("=" * 80)
    print(comparison_df.to_string(index=False))
    
    print("\n" + "=" * 80)
    print("KET LUAN")
    print("=" * 80)
    print("Neu CAAR giua cac mo hinh gan giong nhau va correlation cao (> 0.90),")
    print("thi Mean Adjusted Model la phu hop va ket qua la robust.")
    
    return comparison_df

if __name__ == '__main__':
    comparison_df = run_robustness_check_with_sp500()

