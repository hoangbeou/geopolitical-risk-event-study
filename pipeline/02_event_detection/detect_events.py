"""
Tự động phát hiện các sự kiện địa chính trị quan trọng từ GPR index
Phương pháp: Phát hiện GPR spike (đột ngột tăng) và tìm ngày GPR cao nhất
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import sys
import io

# Fix encoding for Windows (only if needed)
if hasattr(sys.stdout, 'buffer') and not hasattr(sys.stdout, '_encoding_set'):
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stdout._encoding_set = True
    except (AttributeError, ValueError):
        pass

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.preprocessing import DataPreprocessor


class GPREventDetector:
    """Tự động phát hiện events từ GPR index"""
    
    def __init__(self, data: pd.DataFrame, gpr_col: str = None):
        """
        Initialize GPR Event Detector
        
        Parameters:
        -----------
        data : pd.DataFrame
            Data với columns: BTC, GOLD, OIL, GPR, ...
        gpr_col : str
            Tên cột GPR (nếu None, tự động tìm)
        """
        self.data = data
        
        # Tự động tìm GPR column
        if gpr_col is None:
            if 'GPRD' in data.columns:
                self.gpr_col = 'GPRD'
            elif 'GPR' in data.columns:
                self.gpr_col = 'GPR'
            elif 'GPR_TOTAL' in data.columns:
                self.gpr_col = 'GPR_TOTAL'
            else:
                raise ValueError("Khong tim thay cot GPR")
        else:
            self.gpr_col = gpr_col
        
        # Filter date range
        start_date = pd.Timestamp('2015-01-01')
        end_date = pd.Timestamp('2025-11-11')
        self.data = self.data[(self.data.index >= start_date) & (self.data.index <= end_date)]
        
        # Calculate GPR changes
        self.gpr = self.data[self.gpr_col]
        self.gpr_diff = self.gpr.diff()
        self.gpr_pct_change = self.gpr.pct_change() * 100
    
    def _filter_by_separation(self, events_with_dates, min_separation_days, 
                             compare_func=None):
        """
        Helper function: Filter events để đảm bảo cách nhau ít nhất min_separation_days
        
        Parameters:
        -----------
        events_with_dates : list
            List of tuples (date, event_data) hoặc list of dates
        min_separation_days : int
            Số ngày tối thiểu giữa các events
        compare_func : callable, optional
            Function để so sánh khi quá gần: (event1, event2) -> bool
            Nếu True, giữ event1; nếu False, giữ event2
            Nếu None, bỏ qua event mới (giữ event cũ)
        
        Returns:
        --------
        list
            Filtered events (dates hoặc event_data tùy input)
        """
        if len(events_with_dates) == 0:
            return []
        
        # Normalize: convert to list of (date, event_data) tuples
        normalized = []
        for item in events_with_dates:
            if isinstance(item, tuple) and len(item) == 2:
                date, data = item
            elif isinstance(item, pd.Timestamp):
                date = item
                data = item
            elif isinstance(item, dict) and 'date' in item:
                date = item['date']
                data = item
            else:
                date = item
                data = item
            normalized.append((date, data))
        
        # Sort by date
        normalized.sort(key=lambda x: x[0])
        
        filtered = []
        last_date = None
        
        for date, event_data in normalized:
            if last_date is None:
                filtered.append(event_data)
                last_date = date
            else:
                days_diff = (date - last_date).days
                if days_diff >= min_separation_days:
                    # Đủ xa → giữ lại
                    filtered.append(event_data)
                    last_date = date
                elif compare_func is not None:
                    # Quá gần → so sánh và giữ event tốt hơn
                    if compare_func(event_data, filtered[-1]):
                        filtered[-1] = event_data
                        last_date = date
                    # Nếu không tốt hơn, giữ event cũ (không làm gì)
        
        return filtered
    
    def detect_spikes(self, threshold_percentile: float = 95, 
                     min_spike_size: float = None, 
                     window_days: int = 30):
        """
        Phát hiện GPR spikes (đột ngột tăng)
        
        Parameters:
        -----------
        threshold_percentile : float
            Percentile để xác định spike (95 = top 5%)
        min_spike_size : float
            Minimum spike size (nếu None, dùng percentile)
        window_days : int
            Số ngày tối thiểu giữa các spikes
        
        Returns:
        --------
        pd.DataFrame
            DataFrame với các spikes được phát hiện
        """
        # Calculate spike threshold
        if min_spike_size is None:
            threshold = np.percentile(self.gpr_diff.dropna(), threshold_percentile)
        else:
            threshold = min_spike_size
        
        # Find spikes (GPR_diff > threshold)
        spikes = self.gpr_diff[self.gpr_diff > threshold].dropna()
        
        if len(spikes) == 0:
            print(f"Khong tim thay spike nao voi threshold = {threshold:.2f}")
            return pd.DataFrame()
        
        # Filter spikes by separation (keep larger if too close)
        spike_dates = spikes.index.sort_values().tolist()
        compare_func = lambda date1, date2: spikes[date1] > spikes[date2]
        filtered_spike_dates = self._filter_by_separation(
            spike_dates, window_days, compare_func=compare_func
        )
        
        # Create results DataFrame
        results = []
        for spike_date in filtered_spike_dates:
            spike_value = spikes[spike_date]
            gpr_value = self.gpr[spike_date]
            pct_change = self.gpr_pct_change[spike_date]
            
            results.append({
                'date': spike_date,
                'gpr_value': gpr_value,
                'gpr_diff': spike_value,
                'gpr_pct_change': pct_change,
                'method': 'spike'
            })
        
        return pd.DataFrame(results)
    
    def detect_high_periods(self, threshold_percentile: float = 90, 
                           min_duration_days: int = 5,
                           min_separation_days: int = 30,
                           require_increase: bool = True):
        """
        Phát hiện các giai đoạn GPR cao (sustained high GPR)
        
        Parameters:
        -----------
        threshold_percentile : float
            Percentile để xác định GPR cao (90 = top 10%)
        min_duration_days : int
            Số ngày tối thiểu để coi là period
        min_separation_days : int
            Số ngày tối thiểu giữa các periods
        require_increase : bool
            Nếu True, chỉ lấy periods có GPR_diff > 0 vào ngày peak (chỉ lấy GPR tăng)
        
        Returns:
        --------
        pd.DataFrame
            DataFrame với các high periods được phát hiện
        """
        # Calculate threshold
        threshold = np.percentile(self.gpr.dropna(), threshold_percentile)
        
        # Find high GPR periods
        high_gpr = self.gpr[self.gpr > threshold]
        
        if len(high_gpr) == 0:
            return pd.DataFrame()
        
        # Group consecutive days
        high_periods = []
        current_period_start = None
        current_period_end = None
        
        sorted_dates = high_gpr.index.sort_values()
        
        for date in sorted_dates:
            if current_period_start is None:
                current_period_start = date
                current_period_end = date
            else:
                days_diff = (date - current_period_end).days
                if days_diff <= 7:  # Within 7 days, continue period
                    current_period_end = date
                else:
                    # End current period
                    period_duration = (current_period_end - current_period_start).days + 1
                    if period_duration >= min_duration_days:
                        # Find event date: ngày có GPR_diff lớn nhất trong period
                        # (ngày tăng mạnh nhất = ngày event thực sự xảy ra)
                        period_gpr_diff = self.gpr_diff.loc[current_period_start:current_period_end]
                        
                        if len(period_gpr_diff) > 0 and period_gpr_diff.max() > 0:
                            # Ngày có GPR_diff lớn nhất (tăng mạnh nhất)
                            event_date = period_gpr_diff.idxmax()
                            event_gpr_diff = period_gpr_diff.max()
                            event_gpr_value = self.gpr[event_date]
                            
                            # Check if GPR increased (if required)
                            if require_increase:
                                if event_gpr_diff <= 0:  # Không tăng → Skip
                                    # Start new period
                                    current_period_start = date
                                    current_period_end = date
                                    continue
                            
                            high_periods.append({
                                'date': event_date,  # Ngày event thực sự (GPR_diff max)
                                'gpr_value': event_gpr_value,
                                'gpr_diff': event_gpr_diff,
                                'start_date': current_period_start,
                                'end_date': current_period_end,
                                'duration_days': period_duration,
                                'method': 'high_period'
                            })
                        else:
                            # Không có GPR_diff > 0 trong period → Skip
                            pass
                    
                    # Start new period
                    current_period_start = date
                    current_period_end = date
        
        # Handle last period
        if current_period_start is not None:
            period_duration = (current_period_end - current_period_start).days + 1
            if period_duration >= min_duration_days:
                # Find event date: ngày có GPR_diff lớn nhất trong period
                # (ngày tăng mạnh nhất = ngày event thực sự xảy ra)
                period_gpr_diff = self.gpr_diff.loc[current_period_start:current_period_end]
                
                if len(period_gpr_diff) > 0 and period_gpr_diff.max() > 0:
                    # Ngày có GPR_diff lớn nhất (tăng mạnh nhất)
                    event_date = period_gpr_diff.idxmax()
                    event_gpr_diff = period_gpr_diff.max()
                    event_gpr_value = self.gpr[event_date]
                    
                    # Check if GPR increased (if required)
                    if require_increase:
                        if event_gpr_diff <= 0:  # Không tăng → Skip
                            pass  # Skip this period
                        else:
                            high_periods.append({
                                'date': event_date,  # Ngày event thực sự (GPR_diff max)
                                'gpr_value': event_gpr_value,
                                'gpr_diff': event_gpr_diff,
                                'start_date': current_period_start,
                                'end_date': current_period_end,
                                'duration_days': period_duration,
                                'method': 'high_period'
                            })
                    else:
                        high_periods.append({
                            'date': event_date,  # Ngày event thực sự (GPR_diff max)
                            'gpr_value': event_gpr_value,
                            'gpr_diff': event_gpr_diff,
                            'start_date': current_period_start,
                            'end_date': current_period_end,
                            'duration_days': period_duration,
                            'method': 'high_period'
                        })
        
        # Filter by minimum separation
        filtered_periods = self._filter_by_separation(
            high_periods, min_separation_days, compare_func=None
        )
        
        return pd.DataFrame(filtered_periods)
    
    def detect_all_events(self, spike_percentile: float = 95,
                         high_period_percentile: float = 95,
                         combine: bool = True,
                         require_gpr_increase: bool = True):
        """
        Phát hiện tất cả events bằng cả 2 phương pháp
        
        Parameters:
        -----------
        spike_percentile : float
            Percentile cho spike detection
        high_period_percentile : float
            Percentile cho high period detection
        combine : bool
            Có combine 2 phương pháp không (nếu True, loại bỏ duplicates)
        require_gpr_increase : bool
            Nếu True, chỉ lấy events làm GPR tăng (GPR_diff > 0)
        
        Returns:
        --------
        pd.DataFrame
            DataFrame với tất cả events
        """
        # Detect spikes (luôn chỉ lấy GPR tăng)
        # Giữ window_days = 30 ngày
        spike_events = self.detect_spikes(threshold_percentile=spike_percentile, window_days=30)
        
        # Detect high periods (có thể filter chỉ lấy GPR tăng)
        period_events = self.detect_high_periods(
            threshold_percentile=high_period_percentile,
            require_increase=require_gpr_increase
        )
        
        # Combine
        if combine:
            # Add spike events
            all_events = spike_events.to_dict('records')
            all_dates = {row['date'] for row in all_events}
            
            # Filter period events: only add if not too close to existing events
            # Giữ khoảng cách tối thiểu = 7 ngày
            period_events_list = period_events.to_dict('records')
            filtered_periods = []
            for period in period_events_list:
                date = period['date']
                is_far_enough = all(
                    abs((date - existing_date).days) >= 7 
                    for existing_date in all_dates
                )
                if is_far_enough:
                    filtered_periods.append(period)
                    all_dates.add(date)
            
            # Combine and sort
            all_events.extend(filtered_periods)
            all_events.sort(key=lambda x: x['date'])
            
            return pd.DataFrame(all_events)
        else:
            # Return separately
            return {
                'spikes': spike_events,
                'high_periods': period_events
            }
    
    def plot_detection_results(self, events: pd.DataFrame, output_dir: str = 'results'):
        """Plot GPR và highlight detected events"""
        Path(output_dir).mkdir(exist_ok=True)
        
        fig, axes = plt.subplots(2, 1, figsize=(16, 10))
        
        # Plot 1: GPR time series với events
        axes[0].plot(self.gpr.index, self.gpr.values, linewidth=1.5, alpha=0.7, label='GPR')
        
        # Highlight events
        if len(events) > 0:
            event_dates = events['date'].tolist()
            event_values = events['gpr_value'].tolist()
            
            axes[0].scatter(event_dates, event_values, color='red', s=100, 
                          zorder=5, label='Detected Events', marker='v')
            
            # Annotate events
            for _, row in events.iterrows():
                axes[0].annotate(
                    row['date'].strftime('%Y-%m-%d'),
                    xy=(row['date'], row['gpr_value']),
                    xytext=(10, 10), textcoords='offset points',
                    fontsize=8, bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.7),
                    arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0')
                )
        
        axes[0].set_xlabel('Date', fontsize=12)
        axes[0].set_ylabel('GPR Index', fontsize=12)
        axes[0].set_title('GPR Index with Detected Events', fontsize=14)
        axes[0].legend()
        axes[0].grid(True, alpha=0.3)
        
        # Plot 2: GPR changes với spikes
        axes[1].plot(self.gpr_diff.index, self.gpr_diff.values, linewidth=1, alpha=0.5, label='GPR Change')
        axes[1].axhline(y=0, color='black', linestyle='--', linewidth=1)
        
        # Highlight spikes
        if len(events) > 0:
            spike_events = events[events['method'] == 'spike']
            if len(spike_events) > 0:
                spike_dates = spike_events['date'].tolist()
                spike_values = spike_events['gpr_diff'].tolist()
                
                axes[1].scatter(spike_dates, spike_values, color='red', s=100, 
                              zorder=5, label='GPR Spikes', marker='^')
        
        axes[1].set_xlabel('Date', fontsize=12)
        axes[1].set_ylabel('GPR Change', fontsize=12)
        axes[1].set_title('GPR Changes with Detected Spikes', fontsize=14)
        axes[1].legend()
        axes[1].grid(True, alpha=0.3)
        
        plt.suptitle('Automatic GPR Event Detection', fontsize=16, y=0.995)
        plt.tight_layout()
        plt.savefig(f'{output_dir}/GPR_Event_Detection.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def identify_known_events(self, events: pd.DataFrame):
        """
        Add simple identification for events (all auto-detected)
        
        Parameters:
        -----------
        events : pd.DataFrame
            Detected events
        
        Returns:
        --------
        pd.DataFrame
            Events với identification
        """
        # Simply add auto-detected label for all events
        events_with_id = events.copy()
        events_with_id['identified_event'] = events_with_id['date'].apply(
            lambda x: f'GPR Event {x.strftime("%Y-%m-%d")}'
        )
        events_with_id['identification_method'] = 'auto_detected'
        
        return events_with_id
    
    def save_events_csv(self, events: pd.DataFrame, output_dir: str = 'results'):
        """Save events to CSV file for further processing"""
        Path(output_dir).mkdir(exist_ok=True)
        
        # Identify events first
        events_with_id = self.identify_known_events(events)
        
        # Save to CSV
        csv_path = Path(output_dir) / 'detected_events.csv'
        events_with_id.to_csv(csv_path, index=False, encoding='utf-8-sig')
        print(f"Events saved to {csv_path}")
        
        return events_with_id
    
    def generate_summary(self, events: pd.DataFrame, output_dir: str = 'results'):
        """Generate summary report"""
        Path(output_dir).mkdir(exist_ok=True)
        
        summary_path = Path(output_dir) / 'gpr_event_detection_summary.txt'
        
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("GPR EVENT DETECTION - SUMMARY\n")
            f.write("=" * 80 + "\n\n")
            
            f.write(f"Tong so events duoc phat hien: {len(events)}\n\n")
            
            f.write("Chi tiet cac events:\n")
            f.write("-" * 80 + "\n\n")
            
            # Identify known events
            events_with_id = self.identify_known_events(events)
            
            for idx, row in events_with_id.iterrows():
                f.write(f"{idx+1}. {row['identified_event']}\n")
                f.write(f"   Date: {row['date'].strftime('%Y-%m-%d')}\n")
                f.write(f"   GPR Value: {row['gpr_value']:.2f}\n")
                if 'gpr_diff' in row and pd.notna(row['gpr_diff']):
                    f.write(f"   GPR Change: {row['gpr_diff']:.2f}\n")
                if 'duration_days' in row and pd.notna(row['duration_days']):
                    f.write(f"   Duration: {row['duration_days']} days\n")
                f.write(f"   Method: {row['method']}\n")
                f.write(f"   Identification: {row['identification_method']}\n")
                f.write("\n")
            
            # Statistics
            f.write("\n" + "=" * 80 + "\n")
            f.write("THONG KE\n")
            f.write("-" * 80 + "\n\n")
            
            f.write(f"Total events: {len(events)}\n")
            f.write(f"Spike events: {len(events[events['method'] == 'spike'])}\n")
            f.write(f"High period events: {len(events[events['method'] == 'high_period'])}\n")
            f.write(f"All events auto-detected from GPR data\n")
        
        print(f"\nSummary saved to {summary_path}")
        
        return events_with_id


def main():
    """Run GPR Event Detection"""
    print("=" * 80)
    print("GPR EVENT DETECTION")
    print("=" * 80)
    print("\nPhuong phap tu dong phat hien su kien dia chinh tri tu GPR index\n")
    print("1. Spike Detection: Phat hien GPR tang dot ngot (percentile 95)\n")
    print("2. High Period Detection: Phat hien giai doan GPR cao (percentile 95)\n")
    
    # Load data
    preprocessor = DataPreprocessor()
    data_path = Path('data/raw/data.csv')
    if not data_path.exists():
        print("Error: data/raw/data.csv khong ton tai!")
        print("Vui long kiem tra lai duong dan file du lieu.")
        return
    data = preprocessor.load_data(str(data_path))
    
    # Initialize detector
    detector = GPREventDetector(data)
    
    # Detect all events
    print("Dang phat hien events...\n")
    events = detector.detect_all_events(
        spike_percentile=95,
        high_period_percentile=95,
        combine=True,
        require_gpr_increase=True  # chỉ lấy GPR tăng
    )
    
    print(f"Phat hien duoc {len(events)} events\n")
    
    # Identify known events
    events_with_id = detector.identify_known_events(events)
    
    # Save events to CSV
    print("Dang luu events vao CSV...\n")
    events_with_id = detector.save_events_csv(events, output_dir='results')
    
    # Plot results
    print("Dang tao bieu do...\n")
    detector.plot_detection_results(events, output_dir='results')
    
    # Generate summary
    print("Dang tao bao cao tong hop...\n")
    events_final = detector.generate_summary(events, output_dir='results')
    
    # Print results
    print("\n" + "=" * 80)
    print("KET QUA PHAT HIEN EVENTS")
    print("=" * 80 + "\n")
    
    for idx, row in events_final.iterrows():
        print(f"{idx+1}. {row['identified_event']}")
        print(f"   Date: {row['date'].strftime('%Y-%m-%d')}")
        print(f"   GPR Value: {row['gpr_value']:.2f}")
        print()
    
    print("\n" + "=" * 80)
    print("HOAN THANH EVENT DETECTION")
    print("=" * 80)
    print("\nKiem tra thu muc results/ de xem:")
    print("- GPR_Event_Detection.png: Bieu do GPR voi events")
    print("- gpr_event_detection_summary.txt: Bao cao tong hop")
    print("\nCo the su dung danh sach events nay cho Event Study!")
    print("\n")


if __name__ == '__main__':
    main()

