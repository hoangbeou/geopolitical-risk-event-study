"""
Phân tích ACT vs THREAT events và tác động đến CAR
ACT = Actual geopolitical events (sự kiện thực tế)
THREAT = Threats/warnings (cảnh báo/đe dọa)
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Set style
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

class ACTThreatAnalyzer:
    def __init__(self, events_csv_path: str, data_csv_path: str, 
                 output_dir: str = 'results/act_threat_analysis'):
        """
        Initialize ACT/THREAT analysis
        
        Parameters:
        -----------
        events_csv_path : str
            Path to CSV file with events and CAR data
        data_csv_path : str
            Path to main data CSV with GPRD_ACT and GPRD_THREAT
        output_dir : str
            Output directory for results
        """
        self.events_df = pd.read_csv(events_csv_path)
        self.events_df['Date'] = pd.to_datetime(self.events_df['Date'])
        
        # Load main data to get ACT/THREAT values
        self.data_df = pd.read_csv(data_csv_path, index_col=0, parse_dates=True, dayfirst=True)
        
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Filter events with valid CAR
        self.df = self.events_df.dropna(subset=['CAR_BTC', 'CAR_GOLD', 'CAR_OIL']).copy()
        
        print("=" * 80)
        print("ACT vs THREAT ANALYSIS")
        print("=" * 80)
        print(f"Loaded {len(self.df)} events with valid CAR")
        print(f"Data range: {self.data_df.index.min()} to {self.data_df.index.max()}")
    
    def classify_act_threat(self, method='direct_comparison', threshold=1.0):
        """
        Phân loại events thành ACT, THREAT, hoặc BALANCED
        
        Parameters:
        -----------
        method : str
            'direct_comparison': So sánh trực tiếp ACT vs THREAT tại event date
            'percentile': So sánh percentile của ACT vs THREAT
            'spike': Detect spike riêng cho ACT và THREAT
        threshold : float
            Threshold để phân loại (1.0 = bằng nhau, 1.2 = chênh lệch 20%)
        """
        print("\n" + "=" * 80)
        print(f"CLASSIFYING EVENTS BY ACT/THREAT (Method: {method})")
        print("=" * 80)
        
        # Merge ACT/THREAT values từ main data
        act_threat_data = []
        for idx, row in self.df.iterrows():
            event_date = row['Date']
            # Find closest date in data
            closest_idx = self.data_df.index.get_indexer([event_date], method='nearest')[0]
            closest_date = self.data_df.index[closest_idx]
            
            act_value = self.data_df.loc[closest_date, 'GPRD_ACT'] if 'GPRD_ACT' in self.data_df.columns else np.nan
            threat_value = self.data_df.loc[closest_date, 'GPRD_THREAT'] if 'GPRD_THREAT' in self.data_df.columns else np.nan
            
            act_threat_data.append({
                'Event_Number': row['Event_Number'],
                'Date': event_date,
                'GPRD_ACT': act_value,
                'GPRD_THREAT': threat_value,
                'GPR_Value': row['GPR_Value']
            })
        
        act_threat_df = pd.DataFrame(act_threat_data)
        self.df = self.df.merge(act_threat_df[['Event_Number', 'GPRD_ACT', 'GPRD_THREAT']], 
                               on='Event_Number', how='left')
        
        # Classify based on method
        if method == 'direct_comparison':
            # Method 1: Direct comparison với threshold
            self.df['ACT_Threat_Ratio'] = self.df['GPRD_ACT'] / (self.df['GPRD_THREAT'] + 1e-6)  # Avoid division by zero
            
            # Classify
            self.df['ACT_Threat_Type'] = 'BALANCED'
            self.df.loc[self.df['ACT_Threat_Ratio'] > threshold, 'ACT_Threat_Type'] = 'ACT'
            self.df.loc[self.df['ACT_Threat_Ratio'] < 1/threshold, 'ACT_Threat_Type'] = 'THREAT'
            
        elif method == 'percentile':
            # Method 2: Compare percentiles
            act_pct = self.df['GPRD_ACT'].rank(pct=True)
            threat_pct = self.df['GPRD_THREAT'].rank(pct=True)
            
            self.df['ACT_Threat_Type'] = 'BALANCED'
            self.df.loc[act_pct > threat_pct + 0.1, 'ACT_Threat_Type'] = 'ACT'
            self.df.loc[threat_pct > act_pct + 0.1, 'ACT_Threat_Type'] = 'THREAT'
            
        elif method == 'spike':
            # Method 3: Detect spikes separately
            act_95th = np.percentile(self.df['GPRD_ACT'].dropna(), 95)
            threat_95th = np.percentile(self.df['GPRD_THREAT'].dropna(), 95)
            
            act_spike = self.df['GPRD_ACT'] > act_95th
            threat_spike = self.df['GPRD_THREAT'] > threat_95th
            
            self.df['ACT_Threat_Type'] = 'BALANCED'
            self.df.loc[act_spike & ~threat_spike, 'ACT_Threat_Type'] = 'ACT'
            self.df.loc[threat_spike & ~act_spike, 'ACT_Threat_Type'] = 'THREAT'
            self.df.loc[act_spike & threat_spike, 'ACT_Threat_Type'] = 'BOTH'
        
        # Print statistics
        print("\nClassification Statistics:")
        print(self.df['ACT_Threat_Type'].value_counts())
        print("\nPercentage:")
        print(self.df['ACT_Threat_Type'].value_counts(normalize=True) * 100)
        
        # Summary stats by type
        print("\nAverage ACT/THREAT values by type:")
        summary = self.df.groupby('ACT_Threat_Type').agg({
            'GPRD_ACT': ['mean', 'std'],
            'GPRD_THREAT': ['mean', 'std'],
            'GPR_Value': ['mean', 'std']
        })
        print(summary)
        
        return self.df
    
    def analyze_car_by_act_threat(self):
        """Phân tích CAR theo ACT/THREAT classification"""
        print("\n" + "=" * 80)
        print("CAR ANALYSIS BY ACT/THREAT TYPE")
        print("=" * 80)
        
        assets = ['BTC', 'GOLD', 'OIL']
        results = {}
        
        for asset in assets:
            car_col = f'CAR_{asset}'
            
            # Statistics by ACT/THREAT type
            stats_by_type = self.df.groupby('ACT_Threat_Type')[car_col].agg(['mean', 'std', 'count'])
            results[asset] = stats_by_type
            
            print(f"\n{asset} CAR by ACT/THREAT Type:")
            print(stats_by_type)
            
            # Statistical tests
            act_car = self.df[self.df['ACT_Threat_Type'] == 'ACT'][car_col].dropna()
            threat_car = self.df[self.df['ACT_Threat_Type'] == 'THREAT'][car_col].dropna()
            balanced_car = self.df[self.df['ACT_Threat_Type'] == 'BALANCED'][car_col].dropna()
            
            if len(act_car) > 0 and len(threat_car) > 0:
                t_stat, p_value = stats.ttest_ind(act_car, threat_car)
                print(f"\n  ACT vs THREAT T-test:")
                print(f"    t-statistic: {t_stat:.4f}")
                print(f"    p-value: {p_value:.4f}")
                if p_value < 0.05:
                    print(f"    -> Significant difference (p < 0.05)!")
                if p_value < 0.01:
                    print(f"    -> Highly significant (p < 0.01)!")
        
        return results
    
    def visualize_act_threat_impact(self):
        """Visualize ACT/THREAT impact"""
        print("\n" + "=" * 80)
        print("CREATING VISUALIZATIONS")
        print("=" * 80)
        
        assets = ['BTC', 'GOLD', 'OIL']
        
        # 1. Box plots: CAR by ACT/THREAT type
        fig, axes = plt.subplots(1, 3, figsize=(18, 5))
        for idx, asset in enumerate(assets):
            car_col = f'CAR_{asset}'
            sns.boxplot(data=self.df, x='ACT_Threat_Type', y=car_col, ax=axes[idx])
            axes[idx].axhline(y=0, color='r', linestyle='--', alpha=0.5)
            axes[idx].set_title(f'{asset} CAR by ACT/THREAT Type')
            axes[idx].set_ylabel('CAR')
            axes[idx].grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'car_by_act_threat_type.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # 2. Scatter: ACT vs THREAT values, colored by CAR
        fig, axes = plt.subplots(1, 3, figsize=(18, 5))
        for idx, asset in enumerate(assets):
            car_col = f'CAR_{asset}'
            scatter = axes[idx].scatter(self.df['GPRD_ACT'], self.df['GPRD_THREAT'], 
                                       c=self.df[car_col], cmap='RdYlGn', 
                                       alpha=0.6, s=50, vmin=-0.3, vmax=0.3)
            axes[idx].set_xlabel('GPRD_ACT')
            axes[idx].set_ylabel('GPRD_THREAT')
            axes[idx].set_title(f'{asset} CAR (Red=Negative, Green=Positive)')
            axes[idx].grid(True, alpha=0.3)
            
            # Add diagonal line (ACT = THREAT)
            max_val = max(self.df['GPRD_ACT'].max(), self.df['GPRD_THREAT'].max())
            axes[idx].plot([0, max_val], [0, max_val], 'k--', alpha=0.5, label='ACT=THREAT')
            axes[idx].legend()
            
            plt.colorbar(scatter, ax=axes[idx], label='CAR')
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'act_threat_scatter.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # 3. Bar chart: Average CAR by type
        fig, axes = plt.subplots(1, 3, figsize=(18, 5))
        for idx, asset in enumerate(assets):
            car_col = f'CAR_{asset}'
            avg_car = self.df.groupby('ACT_Threat_Type')[car_col].mean()
            std_car = self.df.groupby('ACT_Threat_Type')[car_col].std()
            
            bars = axes[idx].bar(avg_car.index, avg_car.values, yerr=std_car.values, 
                                capsize=5, alpha=0.7, edgecolor='black')
            axes[idx].axhline(y=0, color='r', linestyle='--', alpha=0.5)
            axes[idx].set_title(f'{asset} Average CAR by ACT/THREAT Type')
            axes[idx].set_ylabel('Average CAR')
            axes[idx].grid(True, alpha=0.3, axis='y')
            
            # Add value labels
            for bar in bars:
                height = bar.get_height()
                axes[idx].text(bar.get_x() + bar.get_width()/2., height,
                              f'{height:.4f}',
                              ha='center', va='bottom' if height > 0 else 'top')
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'average_car_by_type.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        print("Saved visualizations to", self.output_dir)
    
    def export_classified_events(self):
        """Export events với ACT/THREAT classification"""
        output_path = self.output_dir / 'events_with_act_threat_classification.csv'
        
        export_cols = [
            'Event_Number', 'Date', 'Detection_Method', 
            'GPR_Value', 'GPRD_ACT', 'GPRD_THREAT', 'ACT_Threat_Ratio', 'ACT_Threat_Type',
            'CAR_BTC', 'CAR_GOLD', 'CAR_OIL',
            'Tstat_BTC', 'Tstat_GOLD', 'Tstat_OIL'
        ]
        
        export_df = self.df[export_cols].copy()
        export_df['Date'] = export_df['Date'].dt.strftime('%Y-%m-%d')
        
        export_df.to_csv(output_path, index=False, encoding='utf-8-sig')
        print(f"\nExported classified events to: {output_path}")
        
        return export_df
    
    def generate_summary_report(self):
        """Generate summary report"""
        report = []
        report.append("=" * 80)
        report.append("ACT vs THREAT ANALYSIS - SUMMARY REPORT")
        report.append("=" * 80)
        report.append(f"\nTotal Events: {len(self.df)}")
        report.append(f"Date Range: {self.df['Date'].min()} to {self.df['Date'].max()}")
        
        report.append("\n" + "-" * 80)
        report.append("CLASSIFICATION DISTRIBUTION")
        report.append("-" * 80)
        type_counts = self.df['ACT_Threat_Type'].value_counts()
        for act_type, count in type_counts.items():
            pct = 100 * count / len(self.df)
            report.append(f"  {act_type}: {count} ({pct:.1f}%)")
        
        report.append("\n" + "-" * 80)
        report.append("AVERAGE CAR BY ACT/THREAT TYPE")
        report.append("-" * 80)
        for asset in ['BTC', 'GOLD', 'OIL']:
            car_col = f'CAR_{asset}'
            report.append(f"\n{asset}:")
            avg_by_type = self.df.groupby('ACT_Threat_Type')[car_col].mean()
            for act_type, avg_car in avg_by_type.items():
                report.append(f"  {act_type}: {avg_car:.4f} ({avg_car*100:.2f}%)")
        
        report.append("\n" + "-" * 80)
        report.append("STATISTICAL TESTS")
        report.append("-" * 80)
        for asset in ['BTC', 'GOLD', 'OIL']:
            car_col = f'CAR_{asset}'
            act_car = self.df[self.df['ACT_Threat_Type'] == 'ACT'][car_col].dropna()
            threat_car = self.df[self.df['ACT_Threat_Type'] == 'THREAT'][car_col].dropna()
            
            if len(act_car) > 0 and len(threat_car) > 0:
                t_stat, p_value = stats.ttest_ind(act_car, threat_car)
                report.append(f"\n{asset} - ACT vs THREAT:")
                report.append(f"  t-statistic: {t_stat:.4f}")
                report.append(f"  p-value: {p_value:.4f}")
                if p_value < 0.05:
                    report.append(f"  -> Significant difference!")
        
        # Save report
        report_text = "\n".join(report)
        report_path = self.output_dir / 'act_threat_analysis_report.txt'
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_text)
        
        print("\n" + report_text)
        print(f"\nReport saved to: {report_path}")
        
        return report_text
    
    def run_all_analyses(self, method='direct_comparison', threshold=1.0):
        """Run all ACT/THREAT analyses"""
        print("\n" + "=" * 80)
        print("RUNNING ALL ACT/THREAT ANALYSES")
        print("=" * 80)
        
        # Classify events
        self.classify_act_threat(method=method, threshold=threshold)
        
        # Analyze CAR
        self.analyze_car_by_act_threat()
        
        # Visualize
        self.visualize_act_threat_impact()
        
        # Export
        self.export_classified_events()
        
        # Generate report
        self.generate_summary_report()
        
        print("\n" + "=" * 80)
        print("ALL ACT/THREAT ANALYSES COMPLETED!")
        print("=" * 80)
        print(f"Results saved to: {self.output_dir}")


if __name__ == '__main__':
    analyzer = ACTThreatAnalyzer(
        events_csv_path='results/event_study/detected_events_with_car.csv',
        data_csv_path='data/data.csv',
        output_dir='results/act_threat_analysis'
    )
    print("\n" + "=" * 80)
    print("METHOD 1: Direct Comparison (threshold=1.0)")
    print("=" * 80)
    analyzer.run_all_analyses(method='direct_comparison', threshold=1.0)
    
    def export_classified_events(self):
        """Export events với ACT/THREAT classification"""
        output_path = self.output_dir / 'events_with_act_threat_classification.csv'
        
        export_cols = [
            'Event_Number', 'Date', 'Detection_Method', 
            'GPR_Value', 'GPRD_ACT', 'GPRD_THREAT', 'ACT_Threat_Ratio', 'ACT_Threat_Type',
            'CAR_BTC', 'CAR_GOLD', 'CAR_OIL',
            'Tstat_BTC', 'Tstat_GOLD', 'Tstat_OIL'
        ]
        
        export_df = self.df[export_cols].copy()
        export_df['Date'] = export_df['Date'].dt.strftime('%Y-%m-%d')
        
        export_df.to_csv(output_path, index=False, encoding='utf-8-sig')
        print(f"\nExported classified events to: {output_path}")
        
        return export_df
    
    def generate_summary_report(self):
        """Generate summary report"""
        report = []
        report.append("=" * 80)
        report.append("ACT vs THREAT ANALYSIS - SUMMARY REPORT")
        report.append("=" * 80)
        report.append(f"\nTotal Events: {len(self.df)}")
        report.append(f"Date Range: {self.df['Date'].min()} to {self.df['Date'].max()}")
        
        report.append("\n" + "-" * 80)
        report.append("CLASSIFICATION DISTRIBUTION")
        report.append("-" * 80)
        type_counts = self.df['ACT_Threat_Type'].value_counts()
        for act_type, count in type_counts.items():
            pct = 100 * count / len(self.df)
            report.append(f"  {act_type}: {count} ({pct:.1f}%)")
        
        report.append("\n" + "-" * 80)
        report.append("AVERAGE CAR BY ACT/THREAT TYPE")
        report.append("-" * 80)
        for asset in ['BTC', 'GOLD', 'OIL']:
            car_col = f'CAR_{asset}'
            report.append(f"\n{asset}:")
            avg_by_type = self.df.groupby('ACT_Threat_Type')[car_col].mean()
            for act_type, avg_car in avg_by_type.items():
                report.append(f"  {act_type}: {avg_car:.4f} ({avg_car*100:.2f}%)")
        
        report.append("\n" + "-" * 80)
        report.append("STATISTICAL TESTS")
        report.append("-" * 80)
        for asset in ['BTC', 'GOLD', 'OIL']:
            car_col = f'CAR_{asset}'
            act_car = self.df[self.df['ACT_Threat_Type'] == 'ACT'][car_col].dropna()
            threat_car = self.df[self.df['ACT_Threat_Type'] == 'THREAT'][car_col].dropna()
            
            if len(act_car) > 0 and len(threat_car) > 0:
                t_stat, p_value = stats.ttest_ind(act_car, threat_car)
                report.append(f"\n{asset} - ACT vs THREAT:")
                report.append(f"  t-statistic: {t_stat:.4f}")
                report.append(f"  p-value: {p_value:.4f}")
                if p_value < 0.05:
                    report.append(f"  -> Significant difference!")
        
        # Save report
        report_text = "\n".join(report)
        report_path = self.output_dir / 'act_threat_analysis_report.txt'
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_text)
        
        print("\n" + report_text)
        print(f"\nReport saved to: {report_path}")
        
        return report_text
    
    def run_all_analyses(self, method='direct_comparison', threshold=1.2):
        """Run all ACT/THREAT analyses"""
        print("\n" + "=" * 80)
        print("RUNNING ALL ACT/THREAT ANALYSES")
        print("=" * 80)
        
        # Classify events
        self.classify_act_threat(method=method, threshold=threshold)
        
        # Analyze CAR
        self.analyze_car_by_act_threat()
        
        # Visualize
        self.visualize_act_threat_impact()
        
        # Export
        self.export_classified_events()
        
        # Generate report
        self.generate_summary_report()
        
        print("\n" + "=" * 80)
        print("ALL ACT/THREAT ANALYSES COMPLETED!")
        print("=" * 80)
        print(f"Results saved to: {self.output_dir}")


if __name__ == '__main__':
    analyzer = ACTThreatAnalyzer(
        events_csv_path='results/event_study/detected_events_with_car.csv',
        data_csv_path='data/data.csv',
        output_dir='results/act_threat_analysis'
    )
    print("\n" + "=" * 80)
    print("METHOD 1: Direct Comparison (threshold=1.0)")
    print("=" * 80)
    analyzer.run_all_analyses(method='direct_comparison', threshold=1.0)

