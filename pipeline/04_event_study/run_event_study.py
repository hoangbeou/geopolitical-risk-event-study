"""
Event Study Analysis - Phân tích phản ứng của tài sản quanh các sự kiện địa chính trị lớn
"""

import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import sys
import io
from scipy import stats
import statsmodels.api as sm

# Fix encoding for Windows
if hasattr(sys.stdout, 'buffer') and not hasattr(sys.stdout, '_encoding_set'):
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stdout._encoding_set = True
    except (AttributeError, ValueError):
        pass

from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.preprocessing import DataPreprocessor

class EventStudy:
    """Event Study Analysis"""
    
    def __init__(
        self,
        data: pd.DataFrame,
        assets: list = ['BTC', 'GOLD', 'OIL'],
        event_window: tuple = (-10, 10),
        estimation_window: int = 120,
        estimation_gap: int = 1,  # tham chiếu workflow tham khảo
        model: str = 'mean',  # 'mean', 'market', 'factor'
        overlap_limit: int = 0  # Disable overlap filtering here - already done in detect_events with min_gap=30
    ):
        """
        Initialize Event Study
        
        Parameters:
        -----------
        data : pd.DataFrame
            Data với columns: BTC, GOLD, OIL, GPR, ...
        assets : list
            List of asset names
        """
        self.data = data
        self.assets = assets
        self.event_window = event_window
        self.estimation_window = estimation_window
        self.estimation_gap = estimation_gap
        self.model = model
        self.overlap_limit = overlap_limit

        # Prepare market/factor series
        self.market_series = 'DXY'
        self.market_returns = self._prepare_market_returns()
        self.factor_series = ['DGS3MO', 'T10YIE']
        self.factor_data = self._prepare_factor_data()

        # Storage for aggregate stats
        self.aggregate_stats = {}

    def _estimate_expected_returns(
        self,
        est_returns: pd.Series,
        event_returns: pd.Series,
        model: str,
        market_returns: pd.Series,
        factor_data: pd.DataFrame
    ) -> tuple[pd.Series, float, str]:
        """
        Estimate expected returns for event window.
        Returns expected_event (Series), sigma_hat, model_used.
        """
        model_used = model

        if model == 'mean' or market_returns.empty:
            mean_ret = est_returns.mean()
            sigma_hat = est_returns.std(ddof=1)
            expected_event = pd.Series(mean_ret, index=event_returns.index)
            return expected_event, sigma_hat, 'mean'

        regressors_est = pd.DataFrame(index=est_returns.index)
        regressors_event = pd.DataFrame(index=event_returns.index)

        if not market_returns.empty:
            regressors_est['market'] = market_returns.reindex(est_returns.index)
            regressors_event['market'] = market_returns.reindex(event_returns.index)

        if model == 'factor' and factor_data is not None and not factor_data.empty:
            regressors_est = regressors_est.join(factor_data.reindex(est_returns.index))
            regressors_event = regressors_event.join(factor_data.reindex(event_returns.index))

        regressors_est = regressors_est.dropna(axis=1, how='all')
        if regressors_est.empty:
            mean_ret = est_returns.mean()
            sigma_hat = est_returns.std(ddof=1)
            expected_event = pd.Series(mean_ret, index=event_returns.index)
            return expected_event, sigma_hat, 'mean'

        combined = pd.concat([est_returns, regressors_est], axis=1).dropna()
        if len(combined) < 30:
            mean_ret = est_returns.mean()
            sigma_hat = est_returns.std(ddof=1)
            expected_event = pd.Series(mean_ret, index=event_returns.index)
            return expected_event, sigma_hat, 'mean'

        y_est = combined.iloc[:, 0]
        X_est = combined.iloc[:, 1:]
        X_est = sm.add_constant(X_est)
        try:
            fit = sm.OLS(y_est.values, X_est.values).fit()
            sigma_hat = np.std(y_est.values - fit.predict(X_est.values), ddof=1)
            X_event = regressors_event.reindex(columns=X_est.columns[1:])
            X_event = X_event.ffill().bfill()
            X_event = sm.add_constant(X_event.reindex(event_returns.index).fillna(0))
            expected_vals = fit.predict(X_event.values)
            expected_event = pd.Series(expected_vals, index=event_returns.index)
            return expected_event, sigma_hat, model_used
        except Exception:
            mean_ret = est_returns.mean()
            sigma_hat = est_returns.std(ddof=1)
            expected_event = pd.Series(mean_ret, index=event_returns.index)
            return expected_event, sigma_hat, 'mean'

    def _prepare_market_returns(self) -> pd.Series:
        """Prepare market proxy returns (e.g., DXY)"""
        if self.market_series in self.data.columns:
            series = np.log(self.data[self.market_series] / self.data[self.market_series].shift(1)).dropna()
            return series
        return pd.Series(dtype=float)

    def _prepare_factor_data(self) -> pd.DataFrame:
        """Prepare additional factor differences"""
        factors = pd.DataFrame(index=self.data.index)
        for col in self.factor_series:
            if col in self.data.columns:
                if col.startswith('D'):
                    factors[f'{col}_diff'] = self.data[col].diff()
                else:
                    factors[f'{col}_ret'] = np.log(self.data[col] / self.data[col].shift(1))
        return factors.dropna(how='all')
        
    
    def load_events_from_detector(self, detector_events: pd.DataFrame):
        """
        Load events from auto detector
        
        Parameters:
        -----------
        detector_events : pd.DataFrame
            Events from GPREventDetector
        """
        events = {}
        
        for idx, row in detector_events.iterrows():
            event_date = row['date']
            identified = row.get('identified_event')
            description = identified if isinstance(identified, str) and identified.strip() else None
            events[f'AutoEvent_{idx+1}'] = {
                'date': event_date,
                'window': (-10, 10),
                'description': description if description else None,
                'identified_event': description,
                'gpr_value': row.get('gpr_value', None),
                'method': row.get('method', 'auto')
            }
        
        filtered = self._filter_overlapping_events(events)
        return self._rename_events_sequential(filtered)

    def _filter_overlapping_events(self, events: dict) -> dict:
        """Remove events that are too close to each other (overlap limit)"""
        if self.overlap_limit <= 0:
            return events

        sorted_events = sorted(events.items(), key=lambda x: x[1]['date'])
        filtered = []
        last_date = None
        for name, info in sorted_events:
            date = info['date']
            if last_date is None or (date - last_date).days > self.overlap_limit:
                filtered.append((name, info))
                last_date = date
        return dict(filtered)
    
    def _rename_events_sequential(self, events: dict) -> dict:
        """Ensure event keys are sequential (Event_1, Event_2, ...) after filtering"""
        sequential = {}
        for idx, (_, info) in enumerate(sorted(events.items(), key=lambda x: x[1]['date']), start=1):
            new_key = f'Event_{idx}'
            info_copy = info.copy()
            if not info_copy.get('description'):
                info_copy['description'] = new_key
            sequential[new_key] = info_copy
        return sequential
    
    def _reindex_results(self, results: dict) -> dict:
        """Rename result keys sequentially after filtering invalid events."""
        sequential = {}
        for idx, (_, data) in enumerate(sorted(results.items(), key=lambda x: x[1]['event_info']['date']), start=1):
            sequential[f'Event_{idx}'] = data
        return sequential
    
    def calculate_returns(self, prices: pd.Series) -> pd.Series:
        """Calculate log returns"""
        return np.log(prices / prices.shift(1)).dropna()
    
    def calculate_car(
        self,
        returns: pd.Series,
        event_date: pd.Timestamp,
        window: tuple = None,
        model: str = None,
    ) -> dict:
        """
        Calculate Cumulative Abnormal Returns (CAR)
        
        Parameters:
        -----------
        returns : pd.Series
            Returns series
        event_date : pd.Timestamp
            Event date
        window : tuple
            (days_before, days_after)
        model : str
            Expected return model
        
        Returns:
        --------
        dict
            Dictionary with CAR, AR, and statistics
        """
        if model is None:
            model = self.model
        if window is None:
            window = self.event_window

        # Check if event date in data
        if event_date not in returns.index:
            # Find closest date
            closest_idx = returns.index.get_indexer([event_date], method='nearest')[0]
            event_date = returns.index[closest_idx]
        
        # Get event index
        event_idx = returns.index.get_loc(event_date)
        
        # Event and estimation windows
        event_start_idx = event_idx + window[0]
        event_end_idx = event_idx + window[1] + 1
        event_start_idx = max(0, event_start_idx)
        event_end_idx = min(len(returns), event_end_idx)
        if event_end_idx <= event_start_idx:
            return None

        est_end_idx = event_start_idx - self.estimation_gap
        est_start_idx = est_end_idx - self.estimation_window
        est_start_idx = max(0, est_start_idx)
        # Accept events even if estimation window is shorter (at least 30 days needed)
        if est_end_idx <= est_start_idx:
            return None

        est_returns = returns.iloc[est_start_idx:est_end_idx]
        event_returns = returns.iloc[event_start_idx:event_end_idx]
        # Accept events with at least 30 days estimation (minimum for meaningful estimate)
        # and at least some event window data (even if not full [-10, +10])
        if len(est_returns) < 30 or event_returns.empty:
            return None

        expected_event, sigma_hat, model_used = self._estimate_expected_returns(
            est_returns,
            event_returns,
            model,
            self.market_returns,
            self.factor_data
        )

        if sigma_hat is None or sigma_hat <= 0:
            sigma_hat = est_returns.std(ddof=1)
        if sigma_hat is None or np.isnan(sigma_hat) or sigma_hat <= 0:
            sigma_hat = 1e-6

        ar = event_returns - expected_event
        sar = ar / sigma_hat
        car = ar.cumsum()

        t_stat = np.nan
        if len(sar) > 0:
            t_stat = np.sum(sar) / np.sqrt(len(sar))

        days = np.arange(window[0], window[0] + len(event_returns))

        return {
            'ar': ar,
            'car': car,
            'sar': sar,
            'days': days,
            'sigma_hat': sigma_hat,
            't_stat': t_stat,
            'car_final': car.iloc[-1] if len(car) > 0 else np.nan,
            'model': model_used
        }
    
    def analyze_all_events(self, events: dict = None, use_auto_detection: bool = True) -> dict:
        """
        Analyze all events for all assets
        
        Parameters:
        -----------
        events : dict
            Manual events dict (nếu None, sẽ dùng define_events)
        use_auto_detection : bool
            Nếu True, sẽ tự động phát hiện events từ GPR
        """
        if events is None:
            # Luôn dùng auto detection (bỏ manual list)
            from scripts.detect_events import GPREventDetector
            detector = GPREventDetector(self.data)
            detected_events = detector.detect_all_events(
                spike_percentile=95,
                high_period_percentile=95,
                combine=True,
                require_gpr_increase=True  # chỉ lấy GPR tăng (nhất quán với spike detection)
            )
            events = self.load_events_from_detector(detected_events)
            print(f"Da phat hien {len(events)} events tu GPR\n")
        
        results = {}
        
        # Calculate returns for all assets
        returns = {}
        for asset in self.assets:
            if asset in self.data.columns:
                returns[asset] = self.calculate_returns(self.data[asset])
        
        skipped_count = 0
        for event_name, event_info in events.items():
            event_date = event_info['date']
            window = event_info['window']
            
            event_results = {}
            
            for asset in self.assets:
                if asset in returns:
                    car_result = self.calculate_car(
                        returns[asset], event_date, window
                    )
                    
                    if car_result is not None:
                        event_results[asset] = car_result
            
            if event_results:
                results[event_name] = {
                    'event_info': event_info,
                    'results': event_results
                }
            else:
                skipped_count += 1
        
        print(f"  Total events analyzed: {len(events)}")
        print(f"  Events with valid CAR: {len(results)}")
        print(f"  Events skipped (no valid CAR): {skipped_count}\n")
        
        sequential_results = self._reindex_results(results)
        self.aggregate_stats = self.compute_aggregate_statistics(sequential_results)
        return sequential_results
    
    def plot_event_study(self, results: dict, output_dir: str = 'results', use_tight_layout: bool = False):
        """Plot event study results (optional tight_layout for spacing)"""
        # Tạo thư mục event_study
        event_dir = Path(output_dir) / 'event_study'
        event_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"  Bat dau tao bieu do cho {len(results)} events...")
        
        for idx, (event_name, event_data) in enumerate(results.items(), 1):
            try:
                event_info = event_data['event_info']
                asset_results = event_data['results']
                
                n_assets = len(asset_results)
                if n_assets == 0:
                    continue
                
                fig, axes = plt.subplots(n_assets, 1, figsize=(14, 4 * n_assets))
                if n_assets == 1:
                    axes = [axes]
                
                for asset_idx, (asset, result) in enumerate(asset_results.items()):
                    car = result['car']
                    days = result['days']
                    
                    axes[asset_idx].plot(days, car.values, marker='o', linewidth=2, 
                                  markersize=6, label='CAR')
                    axes[asset_idx].axhline(y=0, color='black', linestyle='--', linewidth=1)
                    axes[asset_idx].axvline(x=0, color='red', linestyle='--', linewidth=1, 
                                     label='Event Date')
                    
                    axes[asset_idx].set_xlabel('Days Relative to Event', fontsize=12)
                    axes[asset_idx].set_ylabel('Cumulative Abnormal Return (CAR)', fontsize=12)
                    axes[asset_idx].set_title(f'{asset} - {event_info.get("description", event_name)}', fontsize=14)
                    axes[asset_idx].legend()
                    axes[asset_idx].grid(True, alpha=0.3)
                    
                    # Add CAR final value
                    car_final = result['car_final']
                    t_stat = result['t_stat']
                    axes[asset_idx].text(0.02, 0.95, 
                                  f'CAR (final): {car_final:.4f}\nT-stat: {t_stat:.2f}',
                                  transform=axes[asset_idx].transAxes,
                                  verticalalignment='top',
                                  bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
                
                plt.suptitle(f'Event Study: {event_name}', fontsize=16, y=0.995)
                if use_tight_layout:
                    try:
                        plt.tight_layout()
                    except Exception as e:
                        print(f"  Warning: tight_layout failed for {event_name}: {e}", flush=True)
                
                # Lưu file với tên Event_Study_Event_X.png
                output_path = event_dir / f'Event_Study_Event_{idx}.png'
                plt.savefig(output_path, dpi=300, bbox_inches='tight')
                plt.close()
                
                if (idx % 10 == 0):
                    print(f"  Da tao {idx}/{len(results)} bieu do...", flush=True)
                    
            except Exception as e:
                print(f"  Loi khi tao bieu do cho {event_name}: {e}", flush=True)
                plt.close('all')
                continue
        
        print(f"  Hoan thanh tao {len(results)} bieu do", flush=True)
        
        # Aggregate plot - Average CAR across events
        try:
            self.plot_aggregate_car(results, str(event_dir))
        except Exception as e:
            print(f"  Loi khi tao aggregate CAR plot: {e}", flush=True)
        
        try:
            self.plot_average_aar(str(event_dir))
        except Exception as e:
            print(f"  Loi khi tao AAR/CAAR plot: {e}", flush=True)

    def compute_aggregate_statistics(self, results: dict) -> dict:
        """Compute AAR/CAAR and Patell stats across events"""
        window_len = self.event_window[1] - self.event_window[0] + 1
        days = np.arange(self.event_window[0], self.event_window[1] + 1)
        stats = {}

        for asset in self.assets:
            ar_list = []
            sar_list = []
            for event_data in results.values():
                res = event_data['results'].get(asset)
                if res is None:
                    continue
                ar_values = res['ar'].values
                sar_values = res['sar'].values if 'sar' in res else res['ar'].values * 0

                ar_pad = np.full(window_len, np.nan)
                sar_pad = np.full(window_len, np.nan)
                length = min(window_len, len(ar_values))
                ar_pad[:length] = ar_values[:length]
                sar_pad[:length] = sar_values[:length]

                ar_list.append(ar_pad)
                sar_list.append(sar_pad)

            if not ar_list:
                continue

            ar_array = np.array(ar_list)
            sar_array = np.array(sar_list)
            aar = np.nanmean(ar_array, axis=0)
            caar = np.nancumsum(aar)
            patell = np.nanmean(sar_array, axis=0) * np.sqrt(len(ar_list))
            caar_z = np.cumsum(np.nanmean(sar_array, axis=0)) * np.sqrt(len(ar_list))

            stats[asset] = {
                'AAR': aar,
                'CAAR': caar,
                'PatellZ': patell,
                'CAAR_Z': caar_z,
                'days': days,
                'num_events': len(ar_list)
            }

        return stats
    
    def plot_aggregate_car(self, results: dict, output_dir: str):
        """Plot average CAR across all events"""
        # Collect all CARs
        car_by_asset = {asset: [] for asset in self.assets}
        
        for event_name, event_data in results.items():
            asset_results = event_data['results']
            
            for asset, result in asset_results.items():
                if asset in car_by_asset:
                    car_by_asset[asset].append(result['car'].values)
        
        # Plot average CAR
        fig, axes = plt.subplots(len(car_by_asset), 1, figsize=(14, 4 * len(car_by_asset)))
        if len(car_by_asset) == 1:
            axes = [axes]
        
        for idx, (asset, car_list) in enumerate(car_by_asset.items()):
            if not car_list:
                continue
            
            # Align lengths (pad with NaN if needed)
            max_len = max(len(car) for car in car_list)
            car_aligned = []
            for car in car_list:
                if len(car) < max_len:
                    car_padded = np.pad(car, (0, max_len - len(car)), 
                                       constant_values=np.nan)
                    car_aligned.append(car_padded)
                else:
                    car_aligned.append(car)
            
            # Calculate average CAR
            car_array = np.array(car_aligned)
            avg_car = np.nanmean(car_array, axis=0)
            std_car = np.nanstd(car_array, axis=0)
            
            # Get days (use first event as reference)
            if car_list:
                days = np.arange(-10, len(avg_car) - 10)
                
                axes[idx].plot(days, avg_car, marker='o', linewidth=2, 
                              markersize=6, label='Average CAR')
                axes[idx].fill_between(days, avg_car - std_car, avg_car + std_car,
                                      alpha=0.3, label='±1 Std')
                axes[idx].axhline(y=0, color='black', linestyle='--', linewidth=1)
                axes[idx].axvline(x=0, color='red', linestyle='--', linewidth=1, 
                                 label='Event Date')
                
                axes[idx].set_xlabel('Days Relative to Event', fontsize=12)
                axes[idx].set_ylabel('Average CAR', fontsize=12)
                axes[idx].set_title(f'{asset} - Average CAR Across All Events', fontsize=14)
                axes[idx].legend()
                axes[idx].grid(True, alpha=0.3)
        
        plt.suptitle('Event Study: Average CAR Across All Geopolitical Events', 
                    fontsize=16, y=0.995)
        plt.tight_layout()
        plt.savefig(f'{output_dir}/Event_Study_Average_CAR.png', 
                   dpi=300, bbox_inches='tight')
        plt.close()

    def plot_average_aar(self, output_dir: str):
        """Plot average AAR and CAAR using aggregate stats"""
        if not self.aggregate_stats:
            return

        fig, axes = plt.subplots(len(self.aggregate_stats), 2, figsize=(16, 4 * len(self.aggregate_stats)))
        if len(self.aggregate_stats) == 1:
            axes = np.array([axes])

        for idx, (asset, stats) in enumerate(self.aggregate_stats.items()):
            days = stats['days']
            aar = stats['AAR']
            caar = stats['CAAR']

            axes[idx, 0].plot(days, aar, color='tab:blue', linewidth=2)
            axes[idx, 0].axhline(0, color='black', linestyle='--', linewidth=1)
            axes[idx, 0].axvline(0, color='red', linestyle='--', linewidth=1)
            axes[idx, 0].set_title(f'{asset} - Average Abnormal Return (AAR)')
            axes[idx, 0].set_xlabel('Days Relative to Event')
            axes[idx, 0].set_ylabel('AAR')
            axes[idx, 0].grid(True, alpha=0.3)

            axes[idx, 1].plot(days, caar, color='tab:orange', linewidth=2)
            axes[idx, 1].axhline(0, color='black', linestyle='--', linewidth=1)
            axes[idx, 1].axvline(0, color='red', linestyle='--', linewidth=1)
            axes[idx, 1].set_title(f'{asset} - Cumulative Average Abnormal Return (CAAR)')
            axes[idx, 1].set_xlabel('Days Relative to Event')
            axes[idx, 1].set_ylabel('CAAR')
            axes[idx, 1].grid(True, alpha=0.3)

        plt.suptitle('Event Study: Average AAR & CAAR', fontsize=16, y=0.99)
        plt.tight_layout()
        plt.savefig(f'{output_dir}/Event_Study_AAR_CAAR.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def generate_summary(self, results: dict, output_dir: str = 'results'):
        """Generate summary report"""
        # Tạo thư mục event_study
        event_dir = Path(output_dir) / 'event_study'
        event_dir.mkdir(parents=True, exist_ok=True)
        
        summary_path = event_dir / 'event_study_summary.txt'
        
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("EVENT STUDY ANALYSIS - SUMMARY\n")
            f.write("=" * 80 + "\n\n")
            f.write(f"Event window: {self.event_window[0]} to {self.event_window[1]} days\n")
            f.write(f"Estimation window: {self.estimation_window} days (gap {self.estimation_gap})\n")
            f.write(f"Expected return model: {self.model}\n\n")
            
            # Overall statistics
            all_car_final = {asset: [] for asset in self.assets}
            
            for event_name, event_data in results.items():
                f.write(f"\n{event_name}:\n")
                f.write(f"  Date: {event_data['event_info']['date']}\n")
                f.write(f"  Description: {event_data['event_info']['description']}\n\n")
                
                for asset, result in event_data['results'].items():
                    car_final = result['car_final']
                    t_stat = result['t_stat']
                    
                    all_car_final[asset].append(car_final)
                    
                    significance = ""
                    if abs(t_stat) > 2.58:
                        significance = "***"
                    elif abs(t_stat) > 1.96:
                        significance = "**"
                    elif abs(t_stat) > 1.65:
                        significance = "*"
                    
                    f.write(f"  {asset}:\n")
                    f.write(f"    CAR (final): {car_final:.6f} {significance}\n")
                    f.write(f"    T-statistic: {t_stat:.4f}\n")
                    
                    if abs(car_final) > 0.01:
                        direction = "tang" if car_final > 0 else "giam"
                        f.write(f"    -> Phan ung manh: {abs(car_final)*100:.2f}% {direction}\n")
                    elif abs(car_final) > 0.005:
                        direction = "tang nhe" if car_final > 0 else "giam nhe"
                        f.write(f"    -> Phan ung trung binh: {abs(car_final)*100:.2f}% {direction}\n")
                    else:
                        f.write(f"    -> Phan ung yeu hoac khong co phan ung\n")
                    f.write("\n")
            
            # Average CAR across events
            f.write("\n" + "=" * 80 + "\n")
            f.write("AVERAGE CAR ACROSS ALL EVENTS\n")
            f.write("=" * 80 + "\n\n")
            
            for asset, car_list in all_car_final.items():
                if car_list:
                    avg_car = np.mean(car_list)
                    std_car = np.std(car_list)
                    
                    f.write(f"{asset}:\n")
                    f.write(f"  Average CAR: {avg_car:.6f}\n")
                    f.write(f"  Std Deviation: {std_car:.6f}\n")
                    
                    if abs(avg_car) > 0.01:
                        f.write(f"  -> Phan ung manh trung binh: {abs(avg_car)*100:.2f}%\n")
                    elif abs(avg_car) > 0.005:
                        f.write(f"  -> Phan ung trung binh: {abs(avg_car)*100:.2f}%\n")
                    else:
                        f.write(f"  -> Phan ung yeu trung binh\n")
                    f.write("\n")
            
            # Conclusion
            f.write("\n" + "=" * 80 + "\n")
            f.write("KET LUAN\n")
            f.write("=" * 80 + "\n\n")
            
            strong_response = []
            weak_response = []
            no_response = []
            
            for asset, car_list in all_car_final.items():
                if car_list:
                    avg_car = np.mean([abs(c) for c in car_list])
                    if avg_car > 0.01:
                        strong_response.append(asset)
                    elif avg_car > 0.005:
                        weak_response.append(asset)
                    else:
                        no_response.append(asset)
            
            if strong_response:
                f.write(f"✓ PHAN UNG MANH: {', '.join(strong_response)}\n")
                f.write("  -> GPR co anh huong ro rang trong cac su kien lon\n\n")
            
            if weak_response:
                f.write(f"? PHAN UNG TRUNG BINH: {', '.join(weak_response)}\n")
                f.write("  -> GPR co anh huong nho trong cac su kien lon\n\n")
            
            if no_response:
                f.write(f"✗ KHONG CO PHAN UNG: {', '.join(no_response)}\n")
                f.write("  -> GPR khong co anh huong ro rang\n\n")

            if self.aggregate_stats:
                f.write("\n" + "=" * 80 + "\n")
                f.write("AAR/CAAR & PATELL TESTS\n")
                f.write("=" * 80 + "\n\n")
                for asset, stats in self.aggregate_stats.items():
                    final_caar = stats['CAAR'][-1]
                    final_z = stats['CAAR_Z'][-1]
                    signif = ""
                    if abs(final_z) > 2.58:
                        signif = "***"
                    elif abs(final_z) > 1.96:
                        signif = "**"
                    elif abs(final_z) > 1.65:
                        signif = "*"
                    f.write(f"{asset}:\n")
                    f.write(f"  CAAR (final): {final_caar:.6f}\n")
                    f.write(f"  Patell CAAR Z: {final_z:.3f} {signif}\n")
                    f.write(f"  Events analyzed: {stats['num_events']}\n\n")
            
            f.write("\nGhi chu:\n")
            f.write("- Event Study: Phan ung 5-15%% (ro rang)\n")
        
        print(f"\nSummary saved to {summary_path}")
    
    def analyze_asymmetry(self, results: dict, output_dir: str = 'results'):
        """
        Phân tích bất đối xứng: CAR dương vs CAR âm
        """
        asymmetry_dir = Path(output_dir) / 'asymmetry_analysis'
        asymmetry_dir.mkdir(parents=True, exist_ok=True)
        
        print("\n" + "=" * 80)
        print("PHAN TICH BAT DOI XUNG (CAR DUONG vs CAR AM)")
        print("=" * 80)
        
        # Collect CAR data
        car_data = {asset: [] for asset in self.assets}
        event_dates = []
        
        for event_name, event_data in results.items():
            event_date = event_data['event_info']['date']
            event_dates.append(event_date)
            
            for asset in self.assets:
                res = event_data['results'].get(asset)
                if res is not None:
                    car_final = res['car_final']
                    car_data[asset].append(car_final)
                else:
                    car_data[asset].append(np.nan)
        
        # Create DataFrame
        car_df = pd.DataFrame(car_data, index=event_dates)
        
        # Analyze asymmetry for each asset
        asymmetry_results = {}
        
        for asset in self.assets:
            car_values = car_df[asset].dropna()
            
            if len(car_values) == 0:
                continue
            
            positive_car = car_values[car_values > 0]
            negative_car = car_values[car_values < 0]
            zero_car = car_values[car_values == 0]
            
            asymmetry_results[asset] = {
                'total_events': len(car_values),
                'positive_count': len(positive_car),
                'positive_pct': 100 * len(positive_car) / len(car_values),
                'positive_mean': positive_car.mean() if len(positive_car) > 0 else 0,
                'positive_std': positive_car.std() if len(positive_car) > 0 else 0,
                'negative_count': len(negative_car),
                'negative_pct': 100 * len(negative_car) / len(car_values),
                'negative_mean': negative_car.mean() if len(negative_car) > 0 else 0,
                'negative_std': negative_car.std() if len(negative_car) > 0 else 0,
                'zero_count': len(zero_car),
                'skewness': car_values.skew(),
                'mean_car': car_values.mean(),
                'std_car': car_values.std()
            }
            
            print(f"\n{asset}:")
            print(f"  Total events: {len(car_values)}")
            print(f"  Positive CAR: {len(positive_car)} ({100*len(positive_car)/len(car_values):.1f}%)")
            print(f"    Mean: {positive_car.mean():.6f}, Std: {positive_car.std():.6f}")
            print(f"  Negative CAR: {len(negative_car)} ({100*len(negative_car)/len(car_values):.1f}%)")
            print(f"    Mean: {negative_car.mean():.6f}, Std: {negative_car.std():.6f}")
            print(f"  Skewness: {car_values.skew():.4f}")
            print(f"  Overall Mean CAR: {car_values.mean():.6f}")
        
        # Visualization
        fig, axes = plt.subplots(1, len(self.assets), figsize=(6*len(self.assets), 5))
        if len(self.assets) == 1:
            axes = [axes]
        
        for idx, asset in enumerate(self.assets):
            if asset not in asymmetry_results:
                continue
            
            car_values = car_df[asset].dropna()
            axes[idx].hist(car_values, bins=20, alpha=0.7, edgecolor='black', color='steelblue')
            axes[idx].axvline(x=0, color='red', linestyle='--', linewidth=2, label='Zero')
            axes[idx].axvline(x=car_values.mean(), color='green', linestyle='--', linewidth=2, label='Mean')
            axes[idx].set_title(f'{asset} - CAR Distribution\n(Skewness: {car_values.skew():.3f})')
            axes[idx].set_xlabel('CAR')
            axes[idx].set_ylabel('Frequency')
            axes[idx].legend()
            axes[idx].grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(asymmetry_dir / 'asymmetry_car_distribution.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # Save results to CSV
        asymmetry_df = pd.DataFrame(asymmetry_results).T
        asymmetry_df.to_csv(asymmetry_dir / 'asymmetry_results.csv', encoding='utf-8')
        
        print(f"\n✓ Saved asymmetry analysis to {asymmetry_dir}")
        return asymmetry_results
    
    def analyze_act_threat(self, results: dict, output_dir: str = 'results'):
        """
        Phân tích bất đối xứng: ACT events vs THREAT events
        """
        act_threat_dir = Path(output_dir) / 'act_threat_analysis'
        act_threat_dir.mkdir(parents=True, exist_ok=True)
        
        print("\n" + "=" * 80)
        print("PHAN TICH BAT DOI XUNG (ACT vs THREAT)")
        print("=" * 80)
        
        # Try to load classified events
        classified_path = Path('results/events_classified_act_threat.csv')
        if not classified_path.exists():
            print("⚠ Khong tim thay file events_classified_act_threat.csv")
            print("  Bo qua phan tich ACT vs THREAT")
            return None
        
        try:
            classified_df = pd.read_csv(classified_path, parse_dates=['date'])
            print(f"✓ Loaded {len(classified_df)} classified events")
        except Exception as e:
            print(f"⚠ Loi khi doc file classified: {e}")
            return None
        
        # Match events with results
        act_threat_data = []
        
        for event_name, event_data in results.items():
            event_date = event_data['event_info']['date']
            
            # Find matching classified event
            match = classified_df[classified_df['date'] == event_date]
            if len(match) == 0:
                # Try to find closest date
                date_diff = abs(classified_df['date'] - event_date)
                closest_idx = date_diff.idxmin()
                if date_diff[closest_idx].days <= 3:  # Within 3 days
                    match = classified_df.iloc[[closest_idx]]
                else:
                    continue
            
            event_type = match.iloc[0].get('Event_Type', 'UNKNOWN')
            gpr_act = match.iloc[0].get('GPR_ACT', np.nan)
            gpr_threat = match.iloc[0].get('GPR_THREAT', np.nan)
            
            row = {
                'event_name': event_name,
                'date': event_date,
                'event_type': event_type,
                'GPR_ACT': gpr_act,
                'GPR_THREAT': gpr_threat
            }
            
            # Add CAR for each asset
            for asset in self.assets:
                res = event_data['results'].get(asset)
                if res is not None:
                    row[f'{asset}_CAR'] = res['car_final']
                else:
                    row[f'{asset}_CAR'] = np.nan
            
            act_threat_data.append(row)
        
        if len(act_threat_data) == 0:
            print("⚠ Khong tim thay su kien nao khop voi classified events")
            return None
        
        act_threat_df = pd.DataFrame(act_threat_data)
        
        # Filter to ACT and THREAT only
        act_threat_df = act_threat_df[act_threat_df['event_type'].isin(['ACT', 'THREAT'])]
        
        if len(act_threat_df) == 0:
            print("⚠ Khong co su kien ACT hoac THREAT nao")
            return None
        
        print(f"\nPhan loai events:")
        print(act_threat_df['event_type'].value_counts())
        
        # Analyze by event type
        act_threat_results = {}
        
        for asset in self.assets:
            car_col = f'{asset}_CAR'
            if car_col not in act_threat_df.columns:
                continue
            
            act_cars = act_threat_df[act_threat_df['event_type'] == 'ACT'][car_col].dropna()
            threat_cars = act_threat_df[act_threat_df['event_type'] == 'THREAT'][car_col].dropna()
            
            if len(act_cars) == 0 or len(threat_cars) == 0:
                continue
            
            act_threat_results[asset] = {
                'ACT_count': len(act_cars),
                'ACT_mean': act_cars.mean(),
                'ACT_std': act_cars.std(),
                'THREAT_count': len(threat_cars),
                'THREAT_mean': threat_cars.mean(),
                'THREAT_std': threat_cars.std(),
                'difference': act_cars.mean() - threat_cars.mean()
            }
            
            print(f"\n{asset}:")
            print(f"  ACT events ({len(act_cars)}): Mean CAR = {act_cars.mean():.6f} (Std: {act_cars.std():.6f})")
            print(f"  THREAT events ({len(threat_cars)}): Mean CAR = {threat_cars.mean():.6f} (Std: {threat_cars.std():.6f})")
            print(f"  Difference (ACT - THREAT): {act_cars.mean() - threat_cars.mean():.6f}")
        
        # Visualization
        if act_threat_results:
            fig, axes = plt.subplots(1, len(act_threat_results), figsize=(6*len(act_threat_results), 5))
            if len(act_threat_results) == 1:
                axes = [axes]
            
            for idx, (asset, stats) in enumerate(act_threat_results.items()):
                act_cars = act_threat_df[act_threat_df['event_type'] == 'ACT'][f'{asset}_CAR'].dropna()
                threat_cars = act_threat_df[act_threat_df['event_type'] == 'THREAT'][f'{asset}_CAR'].dropna()
                
                axes[idx].boxplot([act_cars, threat_cars], labels=['ACT', 'THREAT'])
                axes[idx].axhline(y=0, color='red', linestyle='--', linewidth=1)
                axes[idx].set_title(f'{asset} - CAR by Event Type')
                axes[idx].set_ylabel('CAR')
                axes[idx].grid(True, alpha=0.3)
            
            plt.tight_layout()
            plt.savefig(act_threat_dir / 'act_threat_comparison.png', dpi=300, bbox_inches='tight')
            plt.close()
        
        # Save results
        act_threat_df.to_csv(act_threat_dir / 'act_threat_car_data.csv', index=False, encoding='utf-8')
        
        if act_threat_results:
            results_df = pd.DataFrame(act_threat_results).T
            results_df.to_csv(act_threat_dir / 'act_threat_results.csv', encoding='utf-8')
        
        print(f"\n✓ Saved ACT/THREAT analysis to {act_threat_dir}")
        return act_threat_results
    
    def analyze_reaction_phases(self, results: dict, output_dir: str = 'results'):
        """
        Phân tích rõ ràng các giai đoạn phản ứng giá:
        - Pre-event (T-10 đến T-1): Anticipatory effect
        - Event day (T0): Immediate reaction
        - Post-event (T+1 đến T+10): Post-event adjustment
        """
        phases_dir = Path(output_dir) / 'reaction_phases_analysis'
        phases_dir.mkdir(parents=True, exist_ok=True)
        
        print("\n" + "=" * 80)
        print("PHAN TICH CAC GIAI DOAN PHAN UNG GIA")
        print("=" * 80)
        
        # Collect AR data by day
        ar_by_day = {asset: {day: [] for day in range(-10, 11)} for asset in self.assets}
        
        for event_name, event_data in results.items():
            for asset in self.assets:
                res = event_data['results'].get(asset)
                if res is None:
                    continue
                
                ar_series = res['ar']
                days = res['days']
                
                for day, ar_value in zip(days, ar_series.values):
                    if day in ar_by_day[asset]:
                        ar_by_day[asset][day].append(ar_value)
        
        # Calculate statistics for each phase
        phase_results = {}
        
        for asset in self.assets:
            # Pre-event: T-10 to T-1
            pre_event_ars = []
            for day in range(-10, 0):
                pre_event_ars.extend(ar_by_day[asset][day])
            
            # Event day: T0
            event_day_ars = ar_by_day[asset][0]
            
            # Post-event: T+1 to T+10
            post_event_ars = []
            for day in range(1, 11):
                post_event_ars.extend(ar_by_day[asset][day])
            
            # Calculate statistics
            pre_event_array = np.array(pre_event_ars) if pre_event_ars else np.array([])
            event_day_array = np.array(event_day_ars) if event_day_ars else np.array([])
            post_event_array = np.array(post_event_ars) if post_event_ars else np.array([])
            
            # Statistical tests
            # 1. Test if each phase is significantly different from 0
            pre_event_tstat, pre_event_pvalue = (np.nan, np.nan), (np.nan, np.nan)
            event_day_tstat, event_day_pvalue = (np.nan, np.nan), (np.nan, np.nan)
            post_event_tstat, post_event_pvalue = (np.nan, np.nan), (np.nan, np.nan)
            
            if len(pre_event_array) > 1:
                pre_event_tstat, pre_event_pvalue = stats.ttest_1samp(pre_event_array, 0)
            if len(event_day_array) > 1:
                event_day_tstat, event_day_pvalue = stats.ttest_1samp(event_day_array, 0)
            if len(post_event_array) > 1:
                post_event_tstat, post_event_pvalue = stats.ttest_1samp(post_event_array, 0)
            
            # 2. Test if pre-event and post-event are significantly different
            pre_post_tstat, pre_post_pvalue = np.nan, np.nan
            pre_post_mannwhitney_u, pre_post_mannwhitney_p = np.nan, np.nan
            if len(pre_event_array) > 1 and len(post_event_array) > 1:
                # T-test (parametric)
                pre_post_tstat, pre_post_pvalue = stats.ttest_ind(pre_event_array, post_event_array)
                # Mann-Whitney U test (non-parametric)
                pre_post_mannwhitney_u, pre_post_mannwhitney_p = stats.mannwhitneyu(
                    pre_event_array, post_event_array, alternative='two-sided'
                )
            
            # 3. Test if event day is significantly different from pre-event
            pre_eventday_tstat, pre_eventday_pvalue = np.nan, np.nan
            if len(pre_event_array) > 1 and len(event_day_array) > 1:
                pre_eventday_tstat, pre_eventday_pvalue = stats.ttest_ind(pre_event_array, event_day_array)
            
            # 4. Test if event day is significantly different from post-event
            eventday_post_tstat, eventday_post_pvalue = np.nan, np.nan
            if len(event_day_array) > 1 and len(post_event_array) > 1:
                eventday_post_tstat, eventday_post_pvalue = stats.ttest_ind(event_day_array, post_event_array)
            
            phase_results[asset] = {
                'pre_event': {
                    'count': len(pre_event_ars),
                    'mean': np.mean(pre_event_ars) if pre_event_ars else np.nan,
                    'std': np.std(pre_event_ars) if pre_event_ars else np.nan,
                    'median': np.median(pre_event_ars) if pre_event_ars else np.nan,
                    'min': np.min(pre_event_ars) if pre_event_ars else np.nan,
                    'max': np.max(pre_event_ars) if pre_event_ars else np.nan,
                    't_stat': pre_event_tstat,
                    'p_value': pre_event_pvalue
                },
                'event_day': {
                    'count': len(event_day_ars),
                    'mean': np.mean(event_day_ars) if event_day_ars else np.nan,
                    'std': np.std(event_day_ars) if event_day_ars else np.nan,
                    'median': np.median(event_day_ars) if event_day_ars else np.nan,
                    'min': np.min(event_day_ars) if event_day_ars else np.nan,
                    'max': np.max(event_day_ars) if event_day_ars else np.nan,
                    't_stat': event_day_tstat,
                    'p_value': event_day_pvalue
                },
                'post_event': {
                    'count': len(post_event_ars),
                    'mean': np.mean(post_event_ars) if post_event_ars else np.nan,
                    'std': np.std(post_event_ars) if post_event_ars else np.nan,
                    'median': np.median(post_event_ars) if post_event_ars else np.nan,
                    'min': np.min(post_event_ars) if post_event_ars else np.nan,
                    'max': np.max(post_event_ars) if post_event_ars else np.nan,
                    't_stat': post_event_tstat,
                    'p_value': post_event_pvalue
                },
                'pre_vs_post': {
                    't_stat': pre_post_tstat,
                    'p_value': pre_post_pvalue,
                    'mannwhitney_u': pre_post_mannwhitney_u,
                    'mannwhitney_p': pre_post_mannwhitney_p
                },
                'pre_vs_eventday': {
                    't_stat': pre_eventday_tstat,
                    'p_value': pre_eventday_pvalue
                },
                'eventday_vs_post': {
                    't_stat': eventday_post_tstat,
                    'p_value': eventday_post_pvalue
                }
            }
            
            # Helper function to get significance stars
            def get_significance(p_value):
                if pd.isna(p_value):
                    return ""
                if p_value < 0.01:
                    return "***"
                elif p_value < 0.05:
                    return "**"
                elif p_value < 0.10:
                    return "*"
                else:
                    return ""
            
            # Print results
            print(f"\n{asset}:")
            print(f"  Pre-Event (T-10 to T-1):")
            print(f"    Mean AR: {phase_results[asset]['pre_event']['mean']*100:.4f}%")
            print(f"    Std: {phase_results[asset]['pre_event']['std']*100:.4f}%")
            print(f"    Median: {phase_results[asset]['pre_event']['median']*100:.4f}%")
            print(f"    Range: [{phase_results[asset]['pre_event']['min']*100:.2f}%, {phase_results[asset]['pre_event']['max']*100:.2f}%]")
            if not pd.isna(phase_results[asset]['pre_event']['t_stat']):
                sig = get_significance(phase_results[asset]['pre_event']['p_value'])
                print(f"    T-test vs 0: t={phase_results[asset]['pre_event']['t_stat']:.3f}, p={phase_results[asset]['pre_event']['p_value']:.4f} {sig}")
            
            print(f"  Event Day (T0):")
            print(f"    Mean AR: {phase_results[asset]['event_day']['mean']*100:.4f}%")
            print(f"    Std: {phase_results[asset]['event_day']['std']*100:.4f}%")
            print(f"    Median: {phase_results[asset]['event_day']['median']*100:.4f}%")
            print(f"    Range: [{phase_results[asset]['event_day']['min']*100:.2f}%, {phase_results[asset]['event_day']['max']*100:.2f}%]")
            if not pd.isna(phase_results[asset]['event_day']['t_stat']):
                sig = get_significance(phase_results[asset]['event_day']['p_value'])
                print(f"    T-test vs 0: t={phase_results[asset]['event_day']['t_stat']:.3f}, p={phase_results[asset]['event_day']['p_value']:.4f} {sig}")
            
            print(f"  Post-Event (T+1 to T+10):")
            print(f"    Mean AR: {phase_results[asset]['post_event']['mean']*100:.4f}%")
            print(f"    Std: {phase_results[asset]['post_event']['std']*100:.4f}%")
            print(f"    Median: {phase_results[asset]['post_event']['median']*100:.4f}%")
            print(f"    Range: [{phase_results[asset]['post_event']['min']*100:.2f}%, {phase_results[asset]['post_event']['max']*100:.2f}%]")
            if not pd.isna(phase_results[asset]['post_event']['t_stat']):
                sig = get_significance(phase_results[asset]['post_event']['p_value'])
                print(f"    T-test vs 0: t={phase_results[asset]['post_event']['t_stat']:.3f}, p={phase_results[asset]['post_event']['p_value']:.4f} {sig}")
            
            # Comparison tests
            print(f"\n  Statistical Comparisons:")
            if not pd.isna(phase_results[asset]['pre_vs_post']['t_stat']):
                sig = get_significance(phase_results[asset]['pre_vs_post']['p_value'])
                print(f"    Pre-Event vs Post-Event (T-test):")
                print(f"      t={phase_results[asset]['pre_vs_post']['t_stat']:.3f}, p={phase_results[asset]['pre_vs_post']['p_value']:.4f} {sig}")
            if not pd.isna(phase_results[asset]['pre_vs_post']['mannwhitney_p']):
                sig = get_significance(phase_results[asset]['pre_vs_post']['mannwhitney_p'])
                print(f"    Pre-Event vs Post-Event (Mann-Whitney U):")
                print(f"      U={phase_results[asset]['pre_vs_post']['mannwhitney_u']:.1f}, p={phase_results[asset]['pre_vs_post']['mannwhitney_p']:.4f} {sig}")
            
            if not pd.isna(phase_results[asset]['pre_vs_eventday']['t_stat']):
                sig = get_significance(phase_results[asset]['pre_vs_eventday']['p_value'])
                print(f"    Pre-Event vs Event Day (T-test):")
                print(f"      t={phase_results[asset]['pre_vs_eventday']['t_stat']:.3f}, p={phase_results[asset]['pre_vs_eventday']['p_value']:.4f} {sig}")
            
            if not pd.isna(phase_results[asset]['eventday_vs_post']['t_stat']):
                sig = get_significance(phase_results[asset]['eventday_vs_post']['p_value'])
                print(f"    Event Day vs Post-Event (T-test):")
                print(f"      t={phase_results[asset]['eventday_vs_post']['t_stat']:.3f}, p={phase_results[asset]['eventday_vs_post']['p_value']:.4f} {sig}")
        
        # Visualization
        fig, axes = plt.subplots(len(self.assets), 1, figsize=(14, 5*len(self.assets)))
        if len(self.assets) == 1:
            axes = [axes]
        
        for idx, asset in enumerate(self.assets):
            # Calculate AAR by day
            aar_by_day = []
            days_list = []
            for day in range(-10, 11):
                if ar_by_day[asset][day]:
                    aar_by_day.append(np.mean(ar_by_day[asset][day]) * 100)
                    days_list.append(day)
            
            axes[idx].plot(days_list, aar_by_day, marker='o', linewidth=2, markersize=6, label='AAR')
            
            # Highlight phases
            axes[idx].axvspan(-10, -0.5, alpha=0.1, color='blue', label='Pre-Event')
            axes[idx].axvspan(-0.5, 0.5, alpha=0.2, color='red', label='Event Day')
            axes[idx].axvspan(0.5, 10.5, alpha=0.1, color='green', label='Post-Event')
            
            axes[idx].axhline(y=0, color='black', linestyle='--', linewidth=1)
            axes[idx].axvline(x=0, color='red', linestyle='--', linewidth=2)
            
            axes[idx].set_xlabel('Day Relative to Event', fontsize=12)
            axes[idx].set_ylabel('Average Abnormal Return (%)', fontsize=12)
            axes[idx].set_title(f'{asset} - Reaction Phases Analysis', fontsize=14)
            axes[idx].legend()
            axes[idx].grid(True, alpha=0.3)
            axes[idx].set_xlim(-10.5, 10.5)
        
        plt.tight_layout()
        plt.savefig(phases_dir / 'reaction_phases.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # Save results to CSV
        phase_summary = []
        comparison_data = []
        
        for asset in self.assets:
            if asset not in phase_results:
                continue
            for phase in ['pre_event', 'event_day', 'post_event']:
                phase_summary.append({
                    'Asset': asset,
                    'Phase': phase,
                    'Mean_AR_pct': phase_results[asset][phase]['mean'] * 100,
                    'Std_AR_pct': phase_results[asset][phase]['std'] * 100,
                    'Median_AR_pct': phase_results[asset][phase]['median'] * 100,
                    'Min_AR_pct': phase_results[asset][phase]['min'] * 100,
                    'Max_AR_pct': phase_results[asset][phase]['max'] * 100,
                    'Count': phase_results[asset][phase]['count'],
                    'T_stat_vs_0': phase_results[asset][phase]['t_stat'],
                    'P_value_vs_0': phase_results[asset][phase]['p_value']
                })
            
            # Comparison statistics
            comparison_data.append({
                'Asset': asset,
                'Comparison': 'Pre-Event vs Post-Event',
                'T_stat': phase_results[asset]['pre_vs_post']['t_stat'],
                'P_value_Ttest': phase_results[asset]['pre_vs_post']['p_value'],
                'MannWhitney_U': phase_results[asset]['pre_vs_post']['mannwhitney_u'],
                'P_value_MannWhitney': phase_results[asset]['pre_vs_post']['mannwhitney_p']
            })
            comparison_data.append({
                'Asset': asset,
                'Comparison': 'Pre-Event vs Event Day',
                'T_stat': phase_results[asset]['pre_vs_eventday']['t_stat'],
                'P_value_Ttest': phase_results[asset]['pre_vs_eventday']['p_value'],
                'MannWhitney_U': np.nan,
                'P_value_MannWhitney': np.nan
            })
            comparison_data.append({
                'Asset': asset,
                'Comparison': 'Event Day vs Post-Event',
                'T_stat': phase_results[asset]['eventday_vs_post']['t_stat'],
                'P_value_Ttest': phase_results[asset]['eventday_vs_post']['p_value'],
                'MannWhitney_U': np.nan,
                'P_value_MannWhitney': np.nan
            })
        
        phase_df = pd.DataFrame(phase_summary)
        phase_df.to_csv(phases_dir / 'reaction_phases_summary.csv', index=False, encoding='utf-8')
        
        comparison_df = pd.DataFrame(comparison_data)
        comparison_df.to_csv(phases_dir / 'reaction_phases_statistical_tests.csv', index=False, encoding='utf-8')
        
        print(f"\n✓ Saved reaction phases analysis to {phases_dir}")
        return phase_results


def main():
    """Run Event Study Analysis"""
    print("=" * 80)
    print("EVENT STUDY ANALYSIS")
    print("=" * 80)
    print("\nSU DUNG TU DONG PHAT HIEN EVENTS TU GPR (khong dung manual)\n")
    print("Phuong phap:")
    print("1. Phat hien GPR spikes (percentile 95, GPR_diff > 74.45)")
    print("2. Phat hien high GPR periods (percentile 95, GPR > 213.66)")
    print("3. Tu dong identify cac su kien da biet\n")
    print("Phuong phap nay phan tich phan ung thuc te cua tai san")
    print("quanh cac su kien dia chinh tri lon.\n")
    
    # Load data (dùng cùng nguồn với detector để đồng nhất)
    preprocessor = DataPreprocessor()
    data_path = Path('data/raw/data.csv')
    if not data_path.exists():
        print("Error: data/raw/data.csv khong ton tai!")
        print("Vui long kiem tra lai duong dan file du lieu.")
        return
    data = preprocessor.load_data(str(data_path))
    
    # Initialize Event Study
    event_study = EventStudy(data, assets=['BTC', 'GOLD', 'OIL'])
    
    # Analyze all events
    print("Dang phan tich cac su kien...\n")
    results = event_study.analyze_all_events(use_auto_detection=True)
    
    # Plot results
    print("Dang tao bieu do...\n")
    event_study.plot_event_study(results, output_dir='results', use_tight_layout=False)
    
    # Generate summary
    print("Dang tao bao cao tong hop...\n")
    event_study.generate_summary(results, output_dir='results')
    
    # Analyze asymmetry (CAR positive vs negative)
    print("\nDang phan tich bat doi xung (CAR duong vs CAR am)...\n")
    asymmetry_results = event_study.analyze_asymmetry(results, output_dir='results')
    
    # Analyze ACT vs THREAT
    print("\nDang phan tich ACT vs THREAT...\n")
    act_threat_results = event_study.analyze_act_threat(results, output_dir='results')
    
    # Analyze reaction phases (pre-event, event day, post-event)
    print("\nDang phan tich cac giai doan phan ung gia...\n")
    phase_results = event_study.analyze_reaction_phases(results, output_dir='results')
    
    print("\n" + "=" * 80)
    print("HOAN THANH EVENT STUDY ANALYSIS")
    print("=" * 80)
    print("\nKiem tra thu muc results/ de xem:")
    print("- Event_Study_*.png: Bieu do cho tung su kien")
    print("- Event_Study_Average_CAR.png: Bieu do trung binh")
    print("- event_study_summary.txt: Bao cao tong hop")
    print("- asymmetry_analysis/: Phan tich bat doi xung CAR duong/am")
    print("- act_threat_analysis/: Phan tich ACT vs THREAT")
    print("- reaction_phases_analysis/: Phan tich cac giai doan phan ung gia")
    print("\n")


if __name__ == '__main__':
    main()

