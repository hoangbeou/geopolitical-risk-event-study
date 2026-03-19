"""
Multiple Windows Analysis - Compare CAR across different event windows
Short-term [-10,+10], Medium-term [-10,+30], Long-term [-10,+60]
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import sys
import io

# Fix encoding for Windows
if hasattr(sys.stdout, 'buffer') and not hasattr(sys.stdout, '_encoding_set'):
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stdout._encoding_set = True
    except (AttributeError, ValueError):
        pass

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.preprocessing import DataPreprocessor
from scripts.run_event_study import EventStudy

sns.set_style("whitegrid")
plt.rcParams['font.size'] = 10


class MultipleWindowsAnalyzer:
    """Analyze events with multiple event windows"""
    
    def __init__(self, data):
        self.data = data
        self.windows = [
            (-10, 10),   # Short-term (21 days)
            (-10, 30),   # Medium-term (41 days)
            (-10, 60)    # Long-term (71 days)
        ]
        self.output_dir = Path('results/multiple_windows')
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def run_analysis_for_all_windows(self):
        """Run Event Study for all windows"""
        print("="*100)
        print("MULTIPLE WINDOWS ANALYSIS")
        print("="*100)
        print()
        
        all_results = {}
        
        for window in self.windows:
            window_name = f"[{window[0]},{window[1]}]"
            print(f"Analyzing window {window_name}...")
            
            # Run Event Study with this window
            event_study = EventStudy(
                self.data,
                assets=['BTC', 'GOLD', 'OIL'],
                event_window=window,
                estimation_window=120,
                estimation_gap=5
            )
            
            # Analyze
            results = event_study.analyze_all_events(use_auto_detection=True)
            
            # Store
            all_results[window_name] = {
                'results': results,
                'aggregate_stats': event_study.aggregate_stats
            }
            
            print(f"  Completed: {len(results)} events analyzed\n")
        
        return all_results
    
    def compare_windows(self, all_results):
        """Compare CAR across different windows"""
        print("="*100)
        print("COMPARING CAR ACROSS WINDOWS")
        print("="*100)
        print()
        
        # Extract final CAR for each window
        comparison_data = []
        
        for window_name, data in all_results.items():
            results = data['results']
            
            for event_name, event_data in results.items():
                event_info = event_data['event_info']
                event_date = event_info['date']
                
                for asset in ['BTC', 'GOLD', 'OIL']:
                    if asset in event_data['results']:
                        car_final = event_data['results'][asset]['car_final']
                        
                        comparison_data.append({
                            'Event': event_name,
                            'Date': event_date,
                            'Asset': asset,
                            'Window': window_name,
                            'CAR': car_final
                        })
        
        comparison_df = pd.DataFrame(comparison_data)
        
        # Save
        comparison_df.to_csv(self.output_dir / 'window_comparison.csv', index=False)
        print(f"Saved: {self.output_dir / 'window_comparison.csv'}")
        
        # Calculate averages
        print("\nAverage CAR by Window:")
        print()
        
        for asset in ['BTC', 'GOLD', 'OIL']:
            print(f"{asset}:")
            asset_data = comparison_df[comparison_df['Asset'] == asset]
            
            for window in self.windows:
                window_name = f"[{window[0]},{window[1]}]"
                window_data = asset_data[asset_data['Window'] == window_name]
                
                if len(window_data) > 0:
                    mean_car = window_data['CAR'].mean()
                    median_car = window_data['CAR'].median()
                    print(f"  Window {window_name}: Mean {mean_car*100:+.2f}%, Median {median_car*100:+.2f}%")
            print()
        
        return comparison_df
    
    def find_peak_events(self, comparison_df):
        """Find events where longer windows have larger CAR (captures peak)"""
        print("="*100)
        print("EVENTS WITH PEAK OUTSIDE SHORT-TERM WINDOW")
        print("="*100)
        print()
        
        # Pivot to compare windows
        pivot = comparison_df.pivot_table(
            index=['Event', 'Date', 'Asset'],
            columns='Window',
            values='CAR'
        ).reset_index()
        
        # Find events where long-term > short-term (captures delayed peak)
        delayed_peaks = []
        
        for idx, row in pivot.iterrows():
            short = row.get('[-10,10]', np.nan)
            medium = row.get('[-10,30]', np.nan)
            long_term = row.get('[-10,60]', np.nan)
            
            # Check if peak is outside short window
            if pd.notna(short) and pd.notna(long_term):
                if abs(long_term) > abs(short) * 1.5:  # 50% larger
                    delayed_peaks.append({
                        'Event': row['Event'],
                        'Date': row['Date'],
                        'Asset': row['Asset'],
                        'Short_CAR': short,
                        'Long_CAR': long_term,
                        'Increase': (abs(long_term) - abs(short)) / abs(short) * 100
                    })
        
        if delayed_peaks:
            delayed_df = pd.DataFrame(delayed_peaks).sort_values('Increase', ascending=False)
            
            print("Top 10 events with delayed/extended peaks:")
            print()
            for idx, row in delayed_df.head(10).iterrows():
                print(f"{row['Event']} ({row['Date'].strftime('%Y-%m-%d')}) - {row['Asset']}:")
                print(f"  Short-term [-10,+10]: {row['Short_CAR']*100:+.2f}%")
                print(f"  Long-term [-10,+60]: {row['Long_CAR']*100:+.2f}%")
                print(f"  Increase: {row['Increase']:.0f}%")
                print()
        else:
            print("No events with significant delayed peaks found")
        
        return delayed_df if delayed_peaks else None
    
    def visualize_windows_comparison(self, comparison_df):
        """Visualize CAR across different windows"""
        print("Creating visualizations...")
        
        # Plot 1: Average CAR by window
        fig, axes = plt.subplots(1, 3, figsize=(18, 6))
        
        for idx, asset in enumerate(['BTC', 'GOLD', 'OIL']):
            asset_data = comparison_df[comparison_df['Asset'] == asset]
            
            # Group by window
            window_means = asset_data.groupby('Window')['CAR'].agg(['mean', 'std']).reset_index()
            window_means = window_means.sort_values('Window')
            
            x = range(len(window_means))
            means = window_means['mean'] * 100
            stds = window_means['std'] * 100
            
            axes[idx].bar(x, means, yerr=stds, capsize=5, alpha=0.7, 
                         color=['#3498db', '#e74c3c', '#2ecc71'],
                         edgecolor='black', linewidth=1.5)
            
            axes[idx].set_xticks(x)
            axes[idx].set_xticklabels(['Short\n[-10,+10]', 'Medium\n[-10,+30]', 'Long\n[-10,+60]'])
            axes[idx].set_ylabel('Average CAR (%)', fontsize=11, fontweight='bold')
            axes[idx].set_title(f'{asset} - CAR by Window Length', 
                               fontsize=12, fontweight='bold')
            axes[idx].axhline(y=0, color='black', linestyle='-', linewidth=1)
            axes[idx].grid(True, alpha=0.3, axis='y')
        
        plt.suptitle('Multiple Windows Analysis - Average CAR Comparison',
                    fontsize=14, fontweight='bold')
        plt.tight_layout()
        plt.savefig(self.output_dir / 'windows_comparison.png', 
                   dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"Saved: {self.output_dir / 'windows_comparison.png'}")
        
        # Plot 2: Distribution by window
        fig, axes = plt.subplots(3, 1, figsize=(14, 12))
        
        for idx, asset in enumerate(['BTC', 'GOLD', 'OIL']):
            asset_data = comparison_df[comparison_df['Asset'] == asset]
            
            # Box plot
            data_by_window = [
                asset_data[asset_data['Window'] == f'[{w[0]},{w[1]}]']['CAR'] * 100
                for w in self.windows
            ]
            
            bp = axes[idx].boxplot(data_by_window, 
                                  labels=['Short\n[-10,+10]', 'Medium\n[-10,+30]', 'Long\n[-10,+60]'],
                                  patch_artist=True)
            
            for patch, color in zip(bp['boxes'], ['lightblue', 'lightcoral', 'lightgreen']):
                patch.set_facecolor(color)
            
            axes[idx].set_ylabel('CAR (%)', fontsize=11, fontweight='bold')
            axes[idx].set_title(f'{asset} - CAR Distribution by Window',
                               fontsize=12, fontweight='bold')
            axes[idx].axhline(y=0, color='black', linestyle='-', linewidth=1)
            axes[idx].grid(True, alpha=0.3, axis='y')
        
        plt.suptitle('CAR Distribution Across Different Event Windows',
                    fontsize=14, fontweight='bold')
        plt.tight_layout()
        plt.savefig(self.output_dir / 'windows_distribution.png',
                   dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"Saved: {self.output_dir / 'windows_distribution.png'}")
    
    def analyze_major_events(self, comparison_df, all_results):
        """Analyze specific major events in detail"""
        print("="*100)
        print("DETAILED ANALYSIS: MAJOR EVENTS")
        print("="*100)
        print()
        
        # Find events with significant differences between windows
        pivot = comparison_df.pivot_table(
            index=['Event', 'Date', 'Asset'],
            columns='Window',
            values='CAR'
        ).reset_index()
        
        # Convert Date to string for easier handling
        pivot['Date_Str'] = pivot['Date'].dt.strftime('%Y-%m-%d')
        
        # Find Ukraine War (2022-02 or 2022-03)
        ukraine_events = pivot[
            (pivot['Date_Str'].str.startswith('2022-02')) | 
            (pivot['Date_Str'].str.startswith('2022-03'))
        ]
        
        if len(ukraine_events) > 0:
            print("UKRAINE WAR EVENTS (2022-02/03):")
            print()
            
            for asset in ['BTC', 'GOLD', 'OIL']:
                asset_events = ukraine_events[ukraine_events['Asset'] == asset]
                if len(asset_events) > 0:
                    print(f"{asset}:")
                    for idx, row in asset_events.iterrows():
                        short = row.get('[-10,10]', np.nan)
                        medium = row.get('[-10,30]', np.nan)
                        long_term = row.get('[-10,60]', np.nan)
                        
                        print(f"  Event: {row['Event']} ({row['Date_Str']})")
                        if pd.notna(short):
                            print(f"    Short-term [-10,+10]: {short*100:+.2f}%")
                        if pd.notna(medium):
                            print(f"    Medium-term [-10,+30]: {medium*100:+.2f}%")
                        if pd.notna(long_term):
                            print(f"    Long-term [-10,+60]: {long_term*100:+.2f}%")
                        
                        # Calculate change
                        if pd.notna(short) and pd.notna(long_term):
                            change = ((long_term - short) / abs(short) * 100) if abs(short) > 0.001 else 0
                            print(f"    Change (Long vs Short): {change:+.1f}%")
                        print()
        
        # Create summary table for top events
        summary_data = []
        for asset in ['BTC', 'GOLD', 'OIL']:
            asset_pivot = pivot[pivot['Asset'] == asset]
            
            # Calculate difference between long and short
            asset_pivot['Diff_Long_Short'] = (
                asset_pivot.get('[-10,60]', pd.Series([np.nan] * len(asset_pivot))) - 
                asset_pivot.get('[-10,10]', pd.Series([np.nan] * len(asset_pivot)))
            )
            
            # Sort by absolute difference
            top_events = asset_pivot.nlargest(5, 'Diff_Long_Short', keep='all')
            
            for idx, row in top_events.iterrows():
                summary_data.append({
                    'Asset': asset,
                    'Event': row['Event'],
                    'Date': row['Date_Str'],
                    'Short_CAR': row.get('[-10,10]', np.nan) * 100,
                    'Medium_CAR': row.get('[-10,30]', np.nan) * 100,
                    'Long_CAR': row.get('[-10,60]', np.nan) * 100,
                    'Diff_Long_Short': row['Diff_Long_Short'] * 100
                })
        
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_csv(self.output_dir / 'major_events_summary.csv', index=False)
        print(f"Saved: {self.output_dir / 'major_events_summary.csv'}")
        print()
        
        return summary_df
    
    def create_timeline_comparison(self, all_results):
        """Create timeline showing CAR evolution across windows for major events"""
        print("Creating timeline comparison for major events...")
        
        # Get Ukraine War events
        ukraine_results = {}
        for window_name, data in all_results.items():
            results = data['results']
            for event_name, event_data in results.items():
                event_date = event_data['event_info']['date']
                if event_date.year == 2022 and event_date.month in [2, 3]:
                    if event_name not in ukraine_results:
                        ukraine_results[event_name] = {}
                    ukraine_results[event_name][window_name] = event_data
        
        if not ukraine_results:
            print("No Ukraine War events found for timeline")
            return
        
        # Plot CAR timeline for each window
        fig, axes = plt.subplots(3, 1, figsize=(16, 12))
        
        for asset_idx, asset in enumerate(['BTC', 'GOLD', 'OIL']):
            ax = axes[asset_idx]
            
            for window_name, window_tuple in zip(
                ['[-10,10]', '[-10,30]', '[-10,60]'],
                self.windows
            ):
                for event_name, event_windows in ukraine_results.items():
                    if window_name in event_windows:
                        event_data = event_windows[window_name]
                        if asset in event_data['results']:
                            result = event_data['results'][asset]
                            car = result['car']
                            days = result['days']
                            
                            label = f"{window_name} - {event_name}"
                            ax.plot(days, car.values * 100, marker='o', 
                                   linewidth=2, markersize=4, label=label, alpha=0.7)
            
            ax.axhline(y=0, color='black', linestyle='-', linewidth=1)
            ax.axvline(x=0, color='red', linestyle='--', linewidth=1, label='Event Date')
            ax.set_xlabel('Days Relative to Event', fontsize=11, fontweight='bold')
            ax.set_ylabel('CAR (%)', fontsize=11, fontweight='bold')
            ax.set_title(f'{asset} - CAR Evolution Across Different Windows (Ukraine War)',
                        fontsize=12, fontweight='bold')
            ax.legend(fontsize=8, loc='best')
            ax.grid(True, alpha=0.3)
        
        plt.suptitle('Multiple Windows Analysis - Ukraine War Events',
                    fontsize=14, fontweight='bold')
        plt.tight_layout()
        plt.savefig(self.output_dir / 'ukraine_war_timeline.png',
                   dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"Saved: {self.output_dir / 'ukraine_war_timeline.png'}")


def main():
    """Main function"""
    print("\nLoading data...")
    preprocessor = DataPreprocessor()
    data = preprocessor.load_data('data/raw/data.csv')
    print(f"Loaded data: {len(data)} observations\n")
    
    # Initialize analyzer
    analyzer = MultipleWindowsAnalyzer(data)
    
    # Run analysis for all windows
    all_results = analyzer.run_analysis_for_all_windows()
    
    # Compare windows
    comparison_df = analyzer.compare_windows(all_results)
    
    # Find delayed peaks
    analyzer.find_peak_events(comparison_df)
    
    # Visualize
    analyzer.visualize_windows_comparison(comparison_df)
    
    # Analyze major events in detail
    analyzer.analyze_major_events(comparison_df, all_results)
    
    # Create timeline comparison
    analyzer.create_timeline_comparison(all_results)
    
    print("\n" + "="*100)
    print("MULTIPLE WINDOWS ANALYSIS COMPLETE!")
    print("="*100)
    print()
    print("Files created:")
    print("  - results/multiple_windows/window_comparison.csv")
    print("  - results/multiple_windows/windows_comparison.png")
    print("  - results/multiple_windows/windows_distribution.png")
    print("  - results/multiple_windows/major_events_summary.csv")
    print("  - results/multiple_windows/ukraine_war_timeline.png")
    print()
    print("Key insights:")
    print("  - Compare short vs long-term effects")
    print("  - Identify events with delayed peaks (peak outside short window)")
    print("  - Understand dynamics of major events like Ukraine War")
    print()


if __name__ == "__main__":
    main()
