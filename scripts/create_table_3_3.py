# -*- coding: utf-8 -*-
"""
Tạo Bảng 3.3: So sánh Kết quả giữa Mean Adjusted Model và Market Model (S&P 500)
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

def create_table_3_3():
    """Tạo Bảng 3.3 so sánh Mean Adjusted Model và Market Model (S&P 500)"""
    
    print("=" * 80)
    print("TẠO BẢNG 3.3: SO SÁNH KẾT QUẢ GIỮA CÁC MÔ HÌNH")
    print("=" * 80)
    
    # Load data
    print("\n1. Loading data...")
    data_path = Path("data/raw/data_with_sp500.csv")
    if not data_path.exists():
        data_path = Path("data/raw/data.csv")
    
    if not data_path.exists():
        print(f"ERROR: Khong tim thay file data")
        return
    
    preprocessor = DataPreprocessor()
    try:
        data = preprocessor.load_data(str(data_path))
    except:
        data = pd.read_csv(data_path, index_col=0, parse_dates=True, dayfirst=True)
        if not isinstance(data.index, pd.DatetimeIndex):
            data.index = pd.to_datetime(data.index, dayfirst=True, errors='coerce')
    
    print(f"   Data loaded: {len(data)} observations")
    print(f"   Date range: {data.index.min()} to {data.index.max()}")
    print(f"   Columns: {list(data.columns)}")
    
    # Check if SP500 exists
    has_sp500 = 'SP500' in data.columns
    if not has_sp500:
        print("   ERROR: SP500 not found in data. Please run add_sp500_to_data.py first.")
        return
    
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
    stats_mean = event_study_mean.compute_aggregate_statistics(results_mean)
    
    # Run Event Study với Market Model (S&P 500)
    print("\n4. Running Event Study với Market Model (S&P 500)...")
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
    stats_sp500 = event_study_sp500.compute_aggregate_statistics(results_sp500)
    
    # Tính toán so sánh
    print("\n5. Computing comparison statistics...")
    comparison_data = []
    
    for asset in ['BTC', 'GOLD', 'OIL']:
        if asset in stats_mean and asset in stats_sp500:
            # CAAR tại T+10
            caar_mean = stats_mean[asset]['CAAR'][-1]
            caar_sp500 = stats_sp500[asset]['CAAR'][-1]
            
            # Tính Std Dev từ AAR
            std_mean = stats_mean[asset]['AAR'].std()
            std_sp500 = stats_sp500[asset]['AAR'].std()
            
            # Z-stat từ CAAR_Z tại T+10
            z_mean = stats_mean[asset]['CAAR_Z'][-1] if 'CAAR_Z' in stats_mean[asset] else np.nan
            z_sp500 = stats_sp500[asset]['CAAR_Z'][-1] if 'CAAR_Z' in stats_sp500[asset] else np.nan
            
            # Tính correlation giữa CAR của từng sự kiện
            car_mean_list = []
            car_sp500_list = []
            
            for event_id in results_mean.keys():
                if event_id in results_sp500:
                    if asset in results_mean[event_id]['results'] and asset in results_sp500[event_id]['results']:
                        car_mean = results_mean[event_id]['results'][asset]['car'].iloc[-1] if 'car' in results_mean[event_id]['results'][asset] else np.nan
                        car_sp500 = results_sp500[event_id]['results'][asset]['car'].iloc[-1] if 'car' in results_sp500[event_id]['results'][asset] else np.nan
                        if not (np.isnan(car_mean) or np.isnan(car_sp500)):
                            car_mean_list.append(car_mean)
                            car_sp500_list.append(car_sp500)
            
            correlation = np.corrcoef(car_mean_list, car_sp500_list)[0, 1] if len(car_mean_list) > 1 else np.nan
            num_events = len(car_mean_list)
            
            # Chênh lệch
            diff = caar_mean - caar_sp500
            diff_pct = (diff / abs(caar_sp500) * 100) if caar_sp500 != 0 else np.nan
            
            comparison_data.append({
                'Asset': asset,
                'CAAR_Mean': caar_mean * 100,
                'CAAR_Market_SP500': caar_sp500 * 100,
                'Difference': diff * 100,
                'Difference_%': diff_pct,
                'StdDev_Mean': std_mean * 100,
                'StdDev_SP500': std_sp500 * 100,
                'Z_Mean': z_mean,
                'Z_SP500': z_sp500,
                'Correlation': correlation,
                'Num_Events': num_events
            })
    
    # Tạo DataFrame
    comparison_df = pd.DataFrame(comparison_data)
    
    # Lưu kết quả
    output_dir = Path("results")
    output_dir.mkdir(exist_ok=True)
    
    output_file = output_dir / "table_3_3_comparison.csv"
    comparison_df.to_csv(output_file, index=False)
    print(f"\n6. Results saved to: {output_file}")
    
    # Tạo bảng markdown
    print("\n" + "=" * 80)
    print("BẢNG 3.3: SO SÁNH KẾT QUẢ GIỮA CÁC MÔ HÌNH")
    print("=" * 80)
    print("\n| Tài sản | CAAR Mean (%) | CAAR Market (S&P 500) (%) | Chênh lệch (%) | Correlation | Std Dev Mean (%) | Std Dev SP500 (%) | Z Mean | Z SP500 | N |")
    print("|---------|---------------|--------------------------|----------------|-------------|------------------|-------------------|--------|---------|---|")
    
    for _, row in comparison_df.iterrows():
        asset_name = {'BTC': 'BTC', 'GOLD': 'GOLD', 'OIL': 'OIL'}.get(row['Asset'], row['Asset'])
        print(f"| {asset_name:7} | {row['CAAR_Mean']:13.2f} | {row['CAAR_Market_SP500']:26.2f} | {row['Difference']:14.2f} | {row['Correlation']:11.4f} | {row['StdDev_Mean']:17.2f} | {row['StdDev_SP500']:18.2f} | {row['Z_Mean']:6.2f} | {row['Z_SP500']:7.2f} | {int(row['Num_Events'])} |")
    
    # Lưu bảng markdown
    md_file = output_dir / "table_3_3_comparison.md"
    with open(md_file, 'w', encoding='utf-8') as f:
        f.write("**Bảng 3.3: So sánh Kết quả giữa Mean Adjusted Model và Market Model (S&P 500)**\n\n")
        f.write("| Tài sản | CAAR Mean (%) | CAAR Market (S&P 500) (%) | Chênh lệch (%) | Correlation | Std Dev Mean (%) | Std Dev SP500 (%) | Z Mean | Z SP500 | N |\n")
        f.write("|---------|---------------|--------------------------|----------------|-------------|------------------|-------------------|--------|---------|---|\n")
        for _, row in comparison_df.iterrows():
            asset_name = {'BTC': 'BTC', 'GOLD': 'GOLD', 'OIL': 'OIL'}.get(row['Asset'], row['Asset'])
            f.write(f"| {asset_name:7} | {row['CAAR_Mean']:13.2f} | {row['CAAR_Market_SP500']:26.2f} | {row['Difference']:14.2f} | {row['Correlation']:11.4f} | {row['StdDev_Mean']:17.2f} | {row['StdDev_SP500']:18.2f} | {row['Z_Mean']:6.2f} | {row['Z_SP500']:7.2f} | {int(row['Num_Events'])} |\n")
    
    print(f"\n7. Markdown table saved to: {md_file}")
    
    print("\n" + "=" * 80)
    print("HOÀN THÀNH!")
    print("=" * 80)
    
    return comparison_df

if __name__ == '__main__':
    df = create_table_3_3()

