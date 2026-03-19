"""
Advanced GPR Impact Analysis
Phân tích nâng cao tác động của GPR đến giá tài sản
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

class AdvancedGPRAnalysis:
    def __init__(self, events_csv_path: str, output_dir: str = 'results/advanced_analysis'):
        """
        Initialize advanced analysis
        
        Parameters:
        -----------
        events_csv_path : str
            Path to CSV file with events and CAR data
        output_dir : str
            Output directory for results
        """
        self.events_df = pd.read_csv(events_csv_path)
        self.events_df['Date'] = pd.to_datetime(self.events_df['Date'])
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Assets
        self.assets = ['BTC', 'GOLD', 'OIL']
        
        print("=" * 80)
        print("ADVANCED GPR IMPACT ANALYSIS")
        print("=" * 80)
        print(f"Loaded {len(self.events_df)} events")
        print(f"Date range: {self.events_df['Date'].min()} to {self.events_df['Date'].max()}")
    
    def analysis_1_intensity_impact(self):
        """Phân tích 1: Tác động theo cường độ GPR"""
        print("\n" + "=" * 80)
        print("ANALYSIS 1: IMPACT BY GPR INTENSITY")
        print("=" * 80)
        
        df = self.events_df.dropna(subset=['CAR_BTC', 'CAR_GOLD', 'CAR_OIL'])
        
        # Chia thành 3 nhóm theo GPR_Value
        # Dùng qcut với duplicates='drop' để tránh lỗi khi quantile trùng nhau
        df['GPR_Intensity'] = pd.qcut(
            df['GPR_Value'],
            q=3,
            labels=['Low', 'Medium', 'High'],
            duplicates='drop'
        )
        
        results = {}
        for asset in self.assets:
            car_col = f'CAR_{asset}'
            results[asset] = df.groupby('GPR_Intensity')[car_col].agg(['mean', 'std', 'count'])
        
        # Print results
        print("\nAverage CAR by GPR Intensity:")
        for asset in self.assets:
            print(f"\n{asset}:")
            print(results[asset])
        
        # Correlation analysis
        print("\n" + "-" * 80)
        print("Correlation: GPR_Value vs CAR")
        print("-" * 80)
        for asset in self.assets:
            car_col = f'CAR_{asset}'
            corr = df[[car_col, 'GPR_Value']].corr().iloc[0, 1]
            print(f"{asset}: {corr:.4f}")
        
        # Visualization
        fig, axes = plt.subplots(1, 3, figsize=(18, 5))
        for idx, asset in enumerate(self.assets):
            car_col = f'CAR_{asset}'
            sns.boxplot(data=df, x='GPR_Intensity', y=car_col, ax=axes[idx])
            axes[idx].set_title(f'{asset} CAR by GPR Intensity')
            axes[idx].axhline(y=0, color='r', linestyle='--', alpha=0.5)
            axes[idx].set_ylabel('CAR')
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'analysis_1_intensity_impact.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # Scatter plots
        fig, axes = plt.subplots(1, 3, figsize=(18, 5))
        for idx, asset in enumerate(self.assets):
            car_col = f'CAR_{asset}'
            axes[idx].scatter(df['GPR_Value'], df[car_col], alpha=0.6)
            axes[idx].set_xlabel('GPR Value')
            axes[idx].set_ylabel(f'{asset} CAR')
            axes[idx].set_title(f'{asset}: GPR vs CAR')
            axes[idx].axhline(y=0, color='r', linestyle='--', alpha=0.5)
            axes[idx].axvline(x=df['GPR_Value'].median(), color='g', linestyle='--', alpha=0.5, label='Median')
            axes[idx].legend()
            
            # Add trend line
            z = np.polyfit(df['GPR_Value'].dropna(), df[car_col].dropna(), 1)
            p = np.poly1d(z)
            axes[idx].plot(df['GPR_Value'], p(df['GPR_Value']), "r--", alpha=0.5)
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'analysis_1_gpr_vs_car_scatter.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"\nSaved visualizations to {self.output_dir}")
        return results
    
    def analysis_2_method_impact(self):
        """Phân tích 2: Tác động theo loại event (Spike vs High Period)"""
        print("\n" + "=" * 80)
        print("ANALYSIS 2: IMPACT BY EVENT METHOD")
        print("=" * 80)
        
        df = self.events_df.dropna(subset=['CAR_BTC', 'CAR_GOLD', 'CAR_OIL'])
        
        results = {}
        for asset in self.assets:
            car_col = f'CAR_{asset}'
            stats_by_method = df.groupby('Detection_Method')[car_col].agg(['mean', 'std', 'count'])
            results[asset] = stats_by_method
            
            # T-test
            spike_car = df[df['Detection_Method'] == 'spike'][car_col].dropna()
            period_car = df[df['Detection_Method'] == 'high_period'][car_col].dropna()
            
            if len(spike_car) > 0 and len(period_car) > 0:
                t_stat, p_value = stats.ttest_ind(spike_car, period_car)
                print(f"\n{asset}:")
                print(stats_by_method)
                print(f"  T-test: t={t_stat:.4f}, p={p_value:.4f}")
                if p_value < 0.05:
                    print(f"  Significant difference (p < 0.05)")
        
        # Visualization
        fig, axes = plt.subplots(1, 3, figsize=(18, 5))
        for idx, asset in enumerate(self.assets):
            car_col = f'CAR_{asset}'
            sns.boxplot(data=df, x='Detection_Method', y=car_col, ax=axes[idx])
            axes[idx].set_title(f'{asset} CAR by Detection Method')
            axes[idx].axhline(y=0, color='r', linestyle='--', alpha=0.5)
            axes[idx].set_ylabel('CAR')
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'analysis_2_method_impact.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"\nSaved visualization to {self.output_dir}")
        return results
    
    def analysis_3_temporal_impact(self):
        """Phân tích 3: Tác động theo thời gian"""
        print("\n" + "=" * 80)
        print("ANALYSIS 3: TEMPORAL IMPACT")
        print("=" * 80)
        
        df = self.events_df.dropna(subset=['CAR_BTC', 'CAR_GOLD', 'CAR_OIL']).copy()
        
        # Define periods
        def assign_period(date):
            if date.year < 2018:
                return '2015-2017: Pre-crypto boom'
            elif date.year < 2020:
                return '2018-2019: Trade wars'
            elif date.year < 2022:
                return '2020-2021: COVID era'
            elif date.year < 2024:
                return '2022-2023: Ukraine war'
            else:
                return '2024-2025: Recent'
        
        df['Period'] = df['Date'].apply(assign_period)
        
        results = {}
        for asset in self.assets:
            car_col = f'CAR_{asset}'
            period_stats = df.groupby('Period')[car_col].agg(['mean', 'std', 'count'])
            results[asset] = period_stats
            print(f"\n{asset} CAR by Period:")
            print(period_stats)
        
        # Visualization
        fig, axes = plt.subplots(1, 3, figsize=(20, 6))
        for idx, asset in enumerate(self.assets):
            car_col = f'CAR_{asset}'
            period_order = ['2015-2017: Pre-crypto boom', '2018-2019: Trade wars', 
                           '2020-2021: COVID era', '2022-2023: Ukraine war', '2024-2025: Recent']
            sns.boxplot(data=df, x='Period', y=car_col, order=period_order, ax=axes[idx])
            axes[idx].set_title(f'{asset} CAR by Time Period')
            axes[idx].axhline(y=0, color='r', linestyle='--', alpha=0.5)
            axes[idx].set_ylabel('CAR')
            axes[idx].tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'analysis_3_temporal_impact.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # Time series plot
        fig, axes = plt.subplots(3, 1, figsize=(16, 12))
        for idx, asset in enumerate(self.assets):
            car_col = f'CAR_{asset}'
            axes[idx].scatter(df['Date'], df[car_col], alpha=0.6, s=50)
            axes[idx].axhline(y=0, color='r', linestyle='--', alpha=0.5)
            axes[idx].set_title(f'{asset} CAR Over Time')
            axes[idx].set_ylabel('CAR')
            axes[idx].grid(True, alpha=0.3)
            
            # Add moving average
            df_sorted = df.sort_values('Date')
            ma_window = 10
            if len(df_sorted) >= ma_window:
                ma = df_sorted[car_col].rolling(window=ma_window, min_periods=1).mean()
                axes[idx].plot(df_sorted['Date'], ma, 'r-', linewidth=2, label=f'{ma_window}-event MA')
                axes[idx].legend()
        
        axes[-1].set_xlabel('Date')
        plt.tight_layout()
        plt.savefig(self.output_dir / 'analysis_3_car_over_time.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"\nSaved visualizations to {self.output_dir}")
        return results
    
    def analysis_4_significance_magnitude(self):
        """Phân tích 4: Significance & Magnitude"""
        print("\n" + "=" * 80)
        print("ANALYSIS 4: SIGNIFICANCE & MAGNITUDE")
        print("=" * 80)
        
        df = self.events_df.dropna(subset=['CAR_BTC', 'CAR_GOLD', 'CAR_OIL']).copy()
        
        # Identify significant events (|T-stat| > 1.96 for 5% significance)
        for asset in self.assets:
            tstat_col = f'Tstat_{asset}'
            car_col = f'CAR_{asset}'
            
            df[f'{asset}_Significant'] = df[tstat_col].abs() > 1.96
            
            significant_count = df[f'{asset}_Significant'].sum()
            print(f"\n{asset}:")
            print(f"  Significant events (|T| > 1.96): {significant_count}/{len(df)} ({100*significant_count/len(df):.1f}%)")
            
            if significant_count > 0:
                sig_events = df[df[f'{asset}_Significant']]
                print(f"  Average CAR (significant): {sig_events[car_col].mean():.4f}")
                print(f"  Average CAR (non-significant): {df[~df[f'{asset}_Significant']][car_col].mean():.4f}")
        
        # Top 10 events by magnitude
        print("\n" + "-" * 80)
        print("TOP 10 EVENTS BY CAR MAGNITUDE (Absolute Value)")
        print("-" * 80)
        
        for asset in self.assets:
            car_col = f'CAR_{asset}'
            top_10 = df.assign(abs_car=df[car_col].abs()) \
                       .nlargest(10, 'abs_car') \
                       [['Event_Number', 'Date', 'Detection_Method', 'GPR_Value', car_col, f'Tstat_{asset}']]
            print(f"\n{asset} - Top 10 Largest |CAR|:")
            print(top_10.to_string(index=False))
        
        return df
    
    def analysis_5_asymmetry(self):
        """Phân tích 5: Asymmetry Analysis"""
        print("\n" + "=" * 80)
        print("ANALYSIS 5: ASYMMETRY ANALYSIS")
        print("=" * 80)
        
        df = self.events_df.dropna(subset=['CAR_BTC', 'CAR_GOLD', 'CAR_OIL'])
        
        results = {}
        for asset in self.assets:
            car_col = f'CAR_{asset}'
            
            positive_car = df[df[car_col] > 0][car_col]
            negative_car = df[df[car_col] < 0][car_col]
            
            results[asset] = {
                'positive_mean': positive_car.mean(),
                'positive_count': len(positive_car),
                'negative_mean': negative_car.mean(),
                'negative_count': len(negative_car),
                'skewness': df[car_col].skew()
            }
            
            print(f"\n{asset}:")
            print(f"  Positive CAR events: {len(positive_car)}/{len(df)} ({100*len(positive_car)/len(df):.1f}%)")
            print(f"    Average CAR: {positive_car.mean():.4f}")
            print(f"  Negative CAR events: {len(negative_car)}/{len(df)} ({100*len(negative_car)/len(df):.1f}%)")
            print(f"    Average CAR: {negative_car.mean():.4f}")
            print(f"  Skewness: {df[car_col].skew():.4f}")
        
        # Visualization
        fig, axes = plt.subplots(1, 3, figsize=(18, 5))
        for idx, asset in enumerate(self.assets):
            car_col = f'CAR_{asset}'
            axes[idx].hist(df[car_col], bins=20, alpha=0.7, edgecolor='black')
            axes[idx].axvline(x=0, color='r', linestyle='--', linewidth=2, label='Zero')
            axes[idx].axvline(x=df[car_col].mean(), color='g', linestyle='--', linewidth=2, label='Mean')
            axes[idx].set_title(f'{asset} CAR Distribution')
            axes[idx].set_xlabel('CAR')
            axes[idx].set_ylabel('Frequency')
            axes[idx].legend()
            axes[idx].grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'analysis_5_asymmetry.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"\nSaved visualization to {self.output_dir}")
        return results
    
    def analysis_6_consistency(self):
        """Phân tích 6: Consistency Analysis"""
        print("\n" + "=" * 80)
        print("ANALYSIS 6: CONSISTENCY ANALYSIS")
        print("=" * 80)
        
        df = self.events_df.dropna(subset=['CAR_BTC', 'CAR_GOLD', 'CAR_OIL'])
        
        # Correlation matrix
        car_cols = ['CAR_BTC', 'CAR_GOLD', 'CAR_OIL']
        corr_matrix = df[car_cols].corr()
        print("\nCorrelation Matrix:")
        print(corr_matrix)
        
        # Same direction analysis
        df['BTC_positive'] = df['CAR_BTC'] > 0
        df['GOLD_positive'] = df['CAR_GOLD'] > 0
        df['OIL_positive'] = df['CAR_OIL'] > 0
        
        # All same direction
        all_same = (df['BTC_positive'] == df['GOLD_positive']) & (df['GOLD_positive'] == df['OIL_positive'])
        print(f"\nEvents where all assets move in same direction: {all_same.sum()}/{len(df)} ({100*all_same.sum()/len(df):.1f}%)")
        
        # BTC vs GOLD
        btc_gold_same = df['BTC_positive'] == df['GOLD_positive']
        print(f"BTC-GOLD same direction: {btc_gold_same.sum()}/{len(df)} ({100*btc_gold_same.sum()/len(df):.1f}%)")
        
        # Visualization
        fig, ax = plt.subplots(figsize=(10, 8))
        sns.heatmap(corr_matrix, annot=True, fmt='.3f', cmap='coolwarm', center=0, 
                   square=True, linewidths=1, cbar_kws={"shrink": 0.8}, ax=ax)
        ax.set_title('CAR Correlation Matrix')
        plt.tight_layout()
        plt.savefig(self.output_dir / 'analysis_6_correlation_matrix.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"\nSaved visualization to {self.output_dir}")
        return corr_matrix
    
    def generate_summary_report(self):
        """Generate comprehensive summary report"""
        print("\n" + "=" * 80)
        print("GENERATING SUMMARY REPORT")
        print("=" * 80)
        
        df = self.events_df.dropna(subset=['CAR_BTC', 'CAR_GOLD', 'CAR_OIL'])
        
        report = []
        report.append("=" * 80)
        report.append("ADVANCED GPR IMPACT ANALYSIS - SUMMARY REPORT")
        report.append("=" * 80)
        report.append(f"\nTotal Events Analyzed: {len(df)}")
        report.append(f"Date Range: {df['Date'].min()} to {df['Date'].max()}")
        
        report.append("\n" + "-" * 80)
        report.append("KEY INSIGHTS")
        report.append("-" * 80)
        
        # Overall statistics
        report.append("\n1. OVERALL STATISTICS:")
        for asset in self.assets:
            car_col = f'CAR_{asset}'
            report.append(f"\n{asset}:")
            report.append(f"  Mean CAR: {df[car_col].mean():.4f} ({df[car_col].mean()*100:.2f}%)")
            report.append(f"  Std Dev: {df[car_col].std():.4f}")
            report.append(f"  Min: {df[car_col].min():.4f}")
            report.append(f"  Max: {df[car_col].max():.4f}")
        
        # Significant events
        report.append("\n2. SIGNIFICANT EVENTS (|T-stat| > 1.96):")
        for asset in self.assets:
            tstat_col = f'Tstat_{asset}'
            sig_count = (df[tstat_col].abs() > 1.96).sum()
            report.append(f"  {asset}: {sig_count}/{len(df)} ({100*sig_count/len(df):.1f}%)")
        
        # Method comparison
        report.append("\n3. SPIKE vs HIGH PERIOD:")
        for asset in self.assets:
            car_col = f'CAR_{asset}'
            spike_mean = df[df['Detection_Method'] == 'spike'][car_col].mean()
            period_mean = df[df['Detection_Method'] == 'high_period'][car_col].mean()
            report.append(f"  {asset}:")
            report.append(f"    Spike: {spike_mean:.4f}")
            report.append(f"    High Period: {period_mean:.4f}")
        
        # Save report
        report_text = "\n".join(report)
        report_path = self.output_dir / 'summary_report.txt'
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_text)
        
        print(report_text)
        print(f"\nReport saved to {report_path}")
        
        return report_text
    
    def run_all_analyses(self):
        """Run all analyses"""
        print("\n" + "=" * 80)
        print("RUNNING ALL ANALYSES")
        print("=" * 80)
        
        results = {}
        results['intensity'] = self.analysis_1_intensity_impact()
        results['method'] = self.analysis_2_method_impact()
        results['temporal'] = self.analysis_3_temporal_impact()
        results['significance'] = self.analysis_4_significance_magnitude()
        results['asymmetry'] = self.analysis_5_asymmetry()
        results['consistency'] = self.analysis_6_consistency()
        
        # Generate summary
        self.generate_summary_report()
        
        print("\n" + "=" * 80)
        print("ALL ANALYSES COMPLETED!")
        print("=" * 80)
        print(f"Results saved to: {self.output_dir}")
        
        return results


if __name__ == '__main__':
    # Run analysis
    analyzer = AdvancedGPRAnalysis(
        events_csv_path='results/event_study/detected_events_with_car.csv',
        output_dir='results/advanced_analysis'
    )
    
    results = analyzer.run_all_analyses()


Phân tích nâng cao tác động của GPR đến giá tài sản
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

class AdvancedGPRAnalysis:
    def __init__(self, events_csv_path: str, output_dir: str = 'results/advanced_analysis'):
        """
        Initialize advanced analysis
        
        Parameters:
        -----------
        events_csv_path : str
            Path to CSV file with events and CAR data
        output_dir : str
            Output directory for results
        """
        self.events_df = pd.read_csv(events_csv_path)
        self.events_df['Date'] = pd.to_datetime(self.events_df['Date'])
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Assets
        self.assets = ['BTC', 'GOLD', 'OIL']
        
        print("=" * 80)
        print("ADVANCED GPR IMPACT ANALYSIS")
        print("=" * 80)
        print(f"Loaded {len(self.events_df)} events")
        print(f"Date range: {self.events_df['Date'].min()} to {self.events_df['Date'].max()}")
    
    def analysis_1_intensity_impact(self):
        """Phân tích 1: Tác động theo cường độ GPR"""
        print("\n" + "=" * 80)
        print("ANALYSIS 1: IMPACT BY GPR INTENSITY")
        print("=" * 80)
        
        df = self.events_df.dropna(subset=['CAR_BTC', 'CAR_GOLD', 'CAR_OIL'])
        
        # Chia thành 3 nhóm theo GPR_Value
        # Dùng qcut với duplicates='drop' để tránh lỗi khi quantile trùng nhau
        df['GPR_Intensity'] = pd.qcut(
            df['GPR_Value'],
            q=3,
            labels=['Low', 'Medium', 'High'],
            duplicates='drop'
        )
        
        results = {}
        for asset in self.assets:
            car_col = f'CAR_{asset}'
            results[asset] = df.groupby('GPR_Intensity')[car_col].agg(['mean', 'std', 'count'])
        
        # Print results
        print("\nAverage CAR by GPR Intensity:")
        for asset in self.assets:
            print(f"\n{asset}:")
            print(results[asset])
        
        # Correlation analysis
        print("\n" + "-" * 80)
        print("Correlation: GPR_Value vs CAR")
        print("-" * 80)
        for asset in self.assets:
            car_col = f'CAR_{asset}'
            corr = df[[car_col, 'GPR_Value']].corr().iloc[0, 1]
            print(f"{asset}: {corr:.4f}")
        
        # Visualization
        fig, axes = plt.subplots(1, 3, figsize=(18, 5))
        for idx, asset in enumerate(self.assets):
            car_col = f'CAR_{asset}'
            sns.boxplot(data=df, x='GPR_Intensity', y=car_col, ax=axes[idx])
            axes[idx].set_title(f'{asset} CAR by GPR Intensity')
            axes[idx].axhline(y=0, color='r', linestyle='--', alpha=0.5)
            axes[idx].set_ylabel('CAR')
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'analysis_1_intensity_impact.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # Scatter plots
        fig, axes = plt.subplots(1, 3, figsize=(18, 5))
        for idx, asset in enumerate(self.assets):
            car_col = f'CAR_{asset}'
            axes[idx].scatter(df['GPR_Value'], df[car_col], alpha=0.6)
            axes[idx].set_xlabel('GPR Value')
            axes[idx].set_ylabel(f'{asset} CAR')
            axes[idx].set_title(f'{asset}: GPR vs CAR')
            axes[idx].axhline(y=0, color='r', linestyle='--', alpha=0.5)
            axes[idx].axvline(x=df['GPR_Value'].median(), color='g', linestyle='--', alpha=0.5, label='Median')
            axes[idx].legend()
            
            # Add trend line
            z = np.polyfit(df['GPR_Value'].dropna(), df[car_col].dropna(), 1)
            p = np.poly1d(z)
            axes[idx].plot(df['GPR_Value'], p(df['GPR_Value']), "r--", alpha=0.5)
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'analysis_1_gpr_vs_car_scatter.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"\nSaved visualizations to {self.output_dir}")
        return results
    
    def analysis_2_method_impact(self):
        """Phân tích 2: Tác động theo loại event (Spike vs High Period)"""
        print("\n" + "=" * 80)
        print("ANALYSIS 2: IMPACT BY EVENT METHOD")
        print("=" * 80)
        
        df = self.events_df.dropna(subset=['CAR_BTC', 'CAR_GOLD', 'CAR_OIL'])
        
        results = {}
        for asset in self.assets:
            car_col = f'CAR_{asset}'
            stats_by_method = df.groupby('Detection_Method')[car_col].agg(['mean', 'std', 'count'])
            results[asset] = stats_by_method
            
            # T-test
            spike_car = df[df['Detection_Method'] == 'spike'][car_col].dropna()
            period_car = df[df['Detection_Method'] == 'high_period'][car_col].dropna()
            
            if len(spike_car) > 0 and len(period_car) > 0:
                t_stat, p_value = stats.ttest_ind(spike_car, period_car)
                print(f"\n{asset}:")
                print(stats_by_method)
                print(f"  T-test: t={t_stat:.4f}, p={p_value:.4f}")
                if p_value < 0.05:
                    print(f"  Significant difference (p < 0.05)")
        
        # Visualization
        fig, axes = plt.subplots(1, 3, figsize=(18, 5))
        for idx, asset in enumerate(self.assets):
            car_col = f'CAR_{asset}'
            sns.boxplot(data=df, x='Detection_Method', y=car_col, ax=axes[idx])
            axes[idx].set_title(f'{asset} CAR by Detection Method')
            axes[idx].axhline(y=0, color='r', linestyle='--', alpha=0.5)
            axes[idx].set_ylabel('CAR')
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'analysis_2_method_impact.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"\nSaved visualization to {self.output_dir}")
        return results
    
    def analysis_3_temporal_impact(self):
        """Phân tích 3: Tác động theo thời gian"""
        print("\n" + "=" * 80)
        print("ANALYSIS 3: TEMPORAL IMPACT")
        print("=" * 80)
        
        df = self.events_df.dropna(subset=['CAR_BTC', 'CAR_GOLD', 'CAR_OIL']).copy()
        
        # Define periods
        def assign_period(date):
            if date.year < 2018:
                return '2015-2017: Pre-crypto boom'
            elif date.year < 2020:
                return '2018-2019: Trade wars'
            elif date.year < 2022:
                return '2020-2021: COVID era'
            elif date.year < 2024:
                return '2022-2023: Ukraine war'
            else:
                return '2024-2025: Recent'
        
        df['Period'] = df['Date'].apply(assign_period)
        
        results = {}
        for asset in self.assets:
            car_col = f'CAR_{asset}'
            period_stats = df.groupby('Period')[car_col].agg(['mean', 'std', 'count'])
            results[asset] = period_stats
            print(f"\n{asset} CAR by Period:")
            print(period_stats)
        
        # Visualization
        fig, axes = plt.subplots(1, 3, figsize=(20, 6))
        for idx, asset in enumerate(self.assets):
            car_col = f'CAR_{asset}'
            period_order = ['2015-2017: Pre-crypto boom', '2018-2019: Trade wars', 
                           '2020-2021: COVID era', '2022-2023: Ukraine war', '2024-2025: Recent']
            sns.boxplot(data=df, x='Period', y=car_col, order=period_order, ax=axes[idx])
            axes[idx].set_title(f'{asset} CAR by Time Period')
            axes[idx].axhline(y=0, color='r', linestyle='--', alpha=0.5)
            axes[idx].set_ylabel('CAR')
            axes[idx].tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'analysis_3_temporal_impact.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # Time series plot
        fig, axes = plt.subplots(3, 1, figsize=(16, 12))
        for idx, asset in enumerate(self.assets):
            car_col = f'CAR_{asset}'
            axes[idx].scatter(df['Date'], df[car_col], alpha=0.6, s=50)
            axes[idx].axhline(y=0, color='r', linestyle='--', alpha=0.5)
            axes[idx].set_title(f'{asset} CAR Over Time')
            axes[idx].set_ylabel('CAR')
            axes[idx].grid(True, alpha=0.3)
            
            # Add moving average
            df_sorted = df.sort_values('Date')
            ma_window = 10
            if len(df_sorted) >= ma_window:
                ma = df_sorted[car_col].rolling(window=ma_window, min_periods=1).mean()
                axes[idx].plot(df_sorted['Date'], ma, 'r-', linewidth=2, label=f'{ma_window}-event MA')
                axes[idx].legend()
        
        axes[-1].set_xlabel('Date')
        plt.tight_layout()
        plt.savefig(self.output_dir / 'analysis_3_car_over_time.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"\nSaved visualizations to {self.output_dir}")
        return results
    
    def analysis_4_significance_magnitude(self):
        """Phân tích 4: Significance & Magnitude"""
        print("\n" + "=" * 80)
        print("ANALYSIS 4: SIGNIFICANCE & MAGNITUDE")
        print("=" * 80)
        
        df = self.events_df.dropna(subset=['CAR_BTC', 'CAR_GOLD', 'CAR_OIL']).copy()
        
        # Identify significant events (|T-stat| > 1.96 for 5% significance)
        for asset in self.assets:
            tstat_col = f'Tstat_{asset}'
            car_col = f'CAR_{asset}'
            
            df[f'{asset}_Significant'] = df[tstat_col].abs() > 1.96
            
            significant_count = df[f'{asset}_Significant'].sum()
            print(f"\n{asset}:")
            print(f"  Significant events (|T| > 1.96): {significant_count}/{len(df)} ({100*significant_count/len(df):.1f}%)")
            
            if significant_count > 0:
                sig_events = df[df[f'{asset}_Significant']]
                print(f"  Average CAR (significant): {sig_events[car_col].mean():.4f}")
                print(f"  Average CAR (non-significant): {df[~df[f'{asset}_Significant']][car_col].mean():.4f}")
        
        # Top 10 events by magnitude
        print("\n" + "-" * 80)
        print("TOP 10 EVENTS BY CAR MAGNITUDE (Absolute Value)")
        print("-" * 80)
        
        for asset in self.assets:
            car_col = f'CAR_{asset}'
            top_10 = df.assign(abs_car=df[car_col].abs()) \
                       .nlargest(10, 'abs_car') \
                       [['Event_Number', 'Date', 'Detection_Method', 'GPR_Value', car_col, f'Tstat_{asset}']]
            print(f"\n{asset} - Top 10 Largest |CAR|:")
            print(top_10.to_string(index=False))
        
        return df
    
    def analysis_5_asymmetry(self):
        """Phân tích 5: Asymmetry Analysis"""
        print("\n" + "=" * 80)
        print("ANALYSIS 5: ASYMMETRY ANALYSIS")
        print("=" * 80)
        
        df = self.events_df.dropna(subset=['CAR_BTC', 'CAR_GOLD', 'CAR_OIL'])
        
        results = {}
        for asset in self.assets:
            car_col = f'CAR_{asset}'
            
            positive_car = df[df[car_col] > 0][car_col]
            negative_car = df[df[car_col] < 0][car_col]
            
            results[asset] = {
                'positive_mean': positive_car.mean(),
                'positive_count': len(positive_car),
                'negative_mean': negative_car.mean(),
                'negative_count': len(negative_car),
                'skewness': df[car_col].skew()
            }
            
            print(f"\n{asset}:")
            print(f"  Positive CAR events: {len(positive_car)}/{len(df)} ({100*len(positive_car)/len(df):.1f}%)")
            print(f"    Average CAR: {positive_car.mean():.4f}")
            print(f"  Negative CAR events: {len(negative_car)}/{len(df)} ({100*len(negative_car)/len(df):.1f}%)")
            print(f"    Average CAR: {negative_car.mean():.4f}")
            print(f"  Skewness: {df[car_col].skew():.4f}")
        
        # Visualization
        fig, axes = plt.subplots(1, 3, figsize=(18, 5))
        for idx, asset in enumerate(self.assets):
            car_col = f'CAR_{asset}'
            axes[idx].hist(df[car_col], bins=20, alpha=0.7, edgecolor='black')
            axes[idx].axvline(x=0, color='r', linestyle='--', linewidth=2, label='Zero')
            axes[idx].axvline(x=df[car_col].mean(), color='g', linestyle='--', linewidth=2, label='Mean')
            axes[idx].set_title(f'{asset} CAR Distribution')
            axes[idx].set_xlabel('CAR')
            axes[idx].set_ylabel('Frequency')
            axes[idx].legend()
            axes[idx].grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'analysis_5_asymmetry.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"\nSaved visualization to {self.output_dir}")
        return results
    
    def analysis_6_consistency(self):
        """Phân tích 6: Consistency Analysis"""
        print("\n" + "=" * 80)
        print("ANALYSIS 6: CONSISTENCY ANALYSIS")
        print("=" * 80)
        
        df = self.events_df.dropna(subset=['CAR_BTC', 'CAR_GOLD', 'CAR_OIL'])
        
        # Correlation matrix
        car_cols = ['CAR_BTC', 'CAR_GOLD', 'CAR_OIL']
        corr_matrix = df[car_cols].corr()
        print("\nCorrelation Matrix:")
        print(corr_matrix)
        
        # Same direction analysis
        df['BTC_positive'] = df['CAR_BTC'] > 0
        df['GOLD_positive'] = df['CAR_GOLD'] > 0
        df['OIL_positive'] = df['CAR_OIL'] > 0
        
        # All same direction
        all_same = (df['BTC_positive'] == df['GOLD_positive']) & (df['GOLD_positive'] == df['OIL_positive'])
        print(f"\nEvents where all assets move in same direction: {all_same.sum()}/{len(df)} ({100*all_same.sum()/len(df):.1f}%)")
        
        # BTC vs GOLD
        btc_gold_same = df['BTC_positive'] == df['GOLD_positive']
        print(f"BTC-GOLD same direction: {btc_gold_same.sum()}/{len(df)} ({100*btc_gold_same.sum()/len(df):.1f}%)")
        
        # Visualization
        fig, ax = plt.subplots(figsize=(10, 8))
        sns.heatmap(corr_matrix, annot=True, fmt='.3f', cmap='coolwarm', center=0, 
                   square=True, linewidths=1, cbar_kws={"shrink": 0.8}, ax=ax)
        ax.set_title('CAR Correlation Matrix')
        plt.tight_layout()
        plt.savefig(self.output_dir / 'analysis_6_correlation_matrix.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"\nSaved visualization to {self.output_dir}")
        return corr_matrix
    
    def generate_summary_report(self):
        """Generate comprehensive summary report"""
        print("\n" + "=" * 80)
        print("GENERATING SUMMARY REPORT")
        print("=" * 80)
        
        df = self.events_df.dropna(subset=['CAR_BTC', 'CAR_GOLD', 'CAR_OIL'])
        
        report = []
        report.append("=" * 80)
        report.append("ADVANCED GPR IMPACT ANALYSIS - SUMMARY REPORT")
        report.append("=" * 80)
        report.append(f"\nTotal Events Analyzed: {len(df)}")
        report.append(f"Date Range: {df['Date'].min()} to {df['Date'].max()}")
        
        report.append("\n" + "-" * 80)
        report.append("KEY INSIGHTS")
        report.append("-" * 80)
        
        # Overall statistics
        report.append("\n1. OVERALL STATISTICS:")
        for asset in self.assets:
            car_col = f'CAR_{asset}'
            report.append(f"\n{asset}:")
            report.append(f"  Mean CAR: {df[car_col].mean():.4f} ({df[car_col].mean()*100:.2f}%)")
            report.append(f"  Std Dev: {df[car_col].std():.4f}")
            report.append(f"  Min: {df[car_col].min():.4f}")
            report.append(f"  Max: {df[car_col].max():.4f}")
        
        # Significant events
        report.append("\n2. SIGNIFICANT EVENTS (|T-stat| > 1.96):")
        for asset in self.assets:
            tstat_col = f'Tstat_{asset}'
            sig_count = (df[tstat_col].abs() > 1.96).sum()
            report.append(f"  {asset}: {sig_count}/{len(df)} ({100*sig_count/len(df):.1f}%)")
        
        # Method comparison
        report.append("\n3. SPIKE vs HIGH PERIOD:")
        for asset in self.assets:
            car_col = f'CAR_{asset}'
            spike_mean = df[df['Detection_Method'] == 'spike'][car_col].mean()
            period_mean = df[df['Detection_Method'] == 'high_period'][car_col].mean()
            report.append(f"  {asset}:")
            report.append(f"    Spike: {spike_mean:.4f}")
            report.append(f"    High Period: {period_mean:.4f}")
        
        # Save report
        report_text = "\n".join(report)
        report_path = self.output_dir / 'summary_report.txt'
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_text)
        
        print(report_text)
        print(f"\nReport saved to {report_path}")
        
        return report_text
    
    def run_all_analyses(self):
        """Run all analyses"""
        print("\n" + "=" * 80)
        print("RUNNING ALL ANALYSES")
        print("=" * 80)
        
        results = {}
        results['intensity'] = self.analysis_1_intensity_impact()
        results['method'] = self.analysis_2_method_impact()
        results['temporal'] = self.analysis_3_temporal_impact()
        results['significance'] = self.analysis_4_significance_magnitude()
        results['asymmetry'] = self.analysis_5_asymmetry()
        results['consistency'] = self.analysis_6_consistency()
        
        # Generate summary
        self.generate_summary_report()
        
        print("\n" + "=" * 80)
        print("ALL ANALYSES COMPLETED!")
        print("=" * 80)
        print(f"Results saved to: {self.output_dir}")
        
        return results


if __name__ == '__main__':
    # Run analysis
    analyzer = AdvancedGPRAnalysis(
        events_csv_path='results/event_study/detected_events_with_car.csv',
        output_dir='results/advanced_analysis'
    )
    
    results = analyzer.run_all_analyses()

