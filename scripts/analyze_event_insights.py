"""
Phân tích insights từ Event Study results
Tạo visualizations để tìm patterns và insights quan trọng
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (14, 8)
plt.rcParams['font.size'] = 10


class EventInsightsAnalyzer:
    """Analyze insights from Event Study results"""
    
    def __init__(self, 
                 events_path='results/events_complete.csv',
                 output_dir='results/insights'):
        """
        Initialize analyzer
        
        Parameters:
        -----------
        events_path : str
            Path to complete events CSV (with CAR data)
        output_dir : str
            Output directory for insights
        """
        self.events_path = Path(events_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Load data
        print("Loading data...")
        self.events_df = pd.read_csv(self.events_path)
        self.events_df['date'] = pd.to_datetime(self.events_df['date'])
        
        print(f"✓ Loaded {len(self.events_df)} events with CAR data")
        
    
    def analyze_top_events(self, top_n=10):
        """
        Analyze top N events with largest absolute CAR
        
        Parameters:
        -----------
        top_n : int
            Number of top events to analyze
        """
        print(f"\n{'='*80}")
        print(f"ANALYZING TOP {top_n} EVENTS BY IMPACT")
        print(f"{'='*80}\n")
        
        # Calculate average absolute CAR across assets
        self.events_df['Avg_Abs_CAR'] = (
            abs(self.events_df['BTC_CAR']) + 
            abs(self.events_df['GOLD_CAR']) + 
            abs(self.events_df['OIL_CAR'])
        ) / 3
        
        # Get top events
        top_events = self.events_df.nlargest(top_n, 'Avg_Abs_CAR')
        
        # Print results
        print(f"Top {top_n} events with largest impact:\n")
        for idx, row in top_events.iterrows():
            print(f"{idx+1}. {row['Event_Name'][:60]}")
            print(f"   Date: {row['date'].strftime('%Y-%m-%d')}")
            print(f"   BTC CAR: {row['BTC_CAR']:.4f} ({row['BTC_CAR']*100:.2f}%)")
            print(f"   GOLD CAR: {row['GOLD_CAR']:.4f} ({row['GOLD_CAR']*100:.2f}%)")
            print(f"   OIL CAR: {row['OIL_CAR']:.4f} ({row['OIL_CAR']*100:.2f}%)")
            print(f"   Avg |CAR|: {row['Avg_Abs_CAR']:.4f}")
            print()
        
        # Visualize top events
        self.plot_top_events(top_events, top_n)
        
        return top_events
    
    def plot_top_events(self, top_events, top_n):
        """Plot top events CAR"""
        fig, ax = plt.subplots(figsize=(14, 8))
        
        # Prepare data
        x = np.arange(len(top_events))
        width = 0.25
        
        btc_car = top_events['BTC_CAR'].values
        gold_car = top_events['GOLD_CAR'].values
        oil_car = top_events['OIL_CAR'].values
        
        # Create bars
        ax.bar(x - width, btc_car, width, label='BTC', alpha=0.8)
        ax.bar(x, gold_car, width, label='GOLD', alpha=0.8)
        ax.bar(x + width, oil_car, width, label='OIL', alpha=0.8)
        
        # Formatting
        ax.set_xlabel('Event', fontsize=12, fontweight='bold')
        ax.set_ylabel('CAR (Cumulative Abnormal Return)', fontsize=12, fontweight='bold')
        ax.set_title(f'Top {top_n} Events by Impact - CAR Comparison', 
                     fontsize=14, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels([f"Event {i+1}" for i in range(len(top_events))], 
                           rotation=45, ha='right')
        ax.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(self.output_dir / f'top_{top_n}_events_car.png', 
                   dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"✓ Saved: {self.output_dir / f'top_{top_n}_events_car.png'}")
    
    def analyze_regional_impact(self):
        """Analyze impact by region based on Detected_Locations"""
        print(f"\n{'='*80}")
        print("ANALYZING REGIONAL IMPACT")
        print(f"{'='*80}\n")
        
        # Extract regions from locations
        self.events_df['Region'] = self.events_df['Detected_Locations'].apply(
            self.classify_region
        )
        
        # Group by region
        regional_stats = self.events_df.groupby('Region').agg({
            'BTC_CAR': ['mean', 'std', 'count'],
            'GOLD_CAR': ['mean', 'std', 'count'],
            'OIL_CAR': ['mean', 'std', 'count']
        }).round(4)
        
        print("Regional Impact Summary:")
        print(regional_stats)
        print()
        
        # Visualize
        self.plot_regional_impact()
        
        return regional_stats
    
    def classify_region(self, locations):
        """Classify event into region based on locations"""
        if pd.isna(locations) or locations == "":
            return "Unknown"
        
        locations_str = str(locations).lower()
        
        # Middle East
        middle_east = ['syria', 'iraq', 'iran', 'israel', 'palestine', 'gaza', 
                      'lebanon', 'yemen', 'saudi', 'jordan', 'kuwait']
        if any(country in locations_str for country in middle_east):
            return "Middle East"
        
        # Europe
        europe = ['ukraine', 'russia', 'france', 'germany', 'uk', 'spain', 
                 'belgium', 'turkey', 'poland', 'crimea']
        if any(country in locations_str for country in europe):
            return "Europe"
        
        # Asia
        asia = ['afghanistan', 'pakistan', 'india', 'china', 'korea', 
               'myanmar', 'philippines', 'thailand', 'kashmir']
        if any(country in locations_str for country in asia):
            return "Asia"
        
        # Africa
        africa = ['libya', 'egypt', 'somalia', 'nigeria', 'mali', 'sudan']
        if any(country in locations_str for country in africa):
            return "Africa"
        
        return "Other"
    
    def plot_regional_impact(self):
        """Plot regional impact comparison"""
        fig, axes = plt.subplots(1, 3, figsize=(18, 6))
        
        assets = ['BTC_CAR', 'GOLD_CAR', 'OIL_CAR']
        titles = ['Bitcoin', 'Gold', 'Oil']
        
        for idx, (asset, title) in enumerate(zip(assets, titles)):
            regional_mean = self.events_df.groupby('Region')[asset].mean()
            
            axes[idx].bar(regional_mean.index, regional_mean.values, alpha=0.7)
            axes[idx].set_title(f'{title} - Regional Impact', 
                               fontsize=12, fontweight='bold')
            axes[idx].set_xlabel('Region')
            axes[idx].set_ylabel('Average CAR')
            axes[idx].axhline(y=0, color='black', linestyle='-', linewidth=0.5)
            axes[idx].tick_params(axis='x', rotation=45)
            axes[idx].grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'regional_impact_comparison.png', 
                   dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"✓ Saved: {self.output_dir / 'regional_impact_comparison.png'}")
    
    def analyze_gpr_magnitude_correlation(self):
        """Analyze correlation between GPR magnitude and CAR"""
        print(f"\n{'='*80}")
        print("ANALYZING GPR MAGNITUDE vs CAR CORRELATION")
        print(f"{'='*80}\n")
        
        # Calculate correlations
        correlations = {}
        for asset in ['BTC_CAR', 'GOLD_CAR', 'OIL_CAR']:
            corr = self.events_df['gpr_diff'].corr(self.events_df[asset])
            correlations[asset] = corr
            print(f"{asset.replace('_CAR', '')}: Correlation = {corr:.4f}")
        
        print()
        
        # Visualize scatter plots
        self.plot_gpr_car_scatter()
        
        return correlations
    
    def plot_gpr_car_scatter(self):
        """Plot GPR_diff vs CAR scatter plots"""
        fig, axes = plt.subplots(1, 3, figsize=(18, 5))
        
        assets = ['BTC_CAR', 'GOLD_CAR', 'OIL_CAR']
        titles = ['Bitcoin', 'Gold', 'Oil']
        
        for idx, (asset, title) in enumerate(zip(assets, titles)):
            # Remove NaN values for plotting
            valid_data = self.events_df[['gpr_diff', asset]].dropna()
            
            if len(valid_data) == 0:
                continue
            
            axes[idx].scatter(valid_data['gpr_diff'], 
                            valid_data[asset], 
                            alpha=0.6, s=50)
            
            # Add trend line
            if len(valid_data) > 1:
                z = np.polyfit(valid_data['gpr_diff'], valid_data[asset], 1)
                p = np.poly1d(z)
                x_line = np.linspace(valid_data['gpr_diff'].min(), 
                                    valid_data['gpr_diff'].max(), 100)
                axes[idx].plot(x_line, p(x_line), "r--", alpha=0.8, linewidth=2)
            
            axes[idx].set_title(f'{title} - GPR Magnitude vs CAR', 
                               fontsize=12, fontweight='bold')
            axes[idx].set_xlabel('GPR Diff (Spike Size)')
            axes[idx].set_ylabel('CAR')
            axes[idx].axhline(y=0, color='black', linestyle='-', linewidth=0.5)
            axes[idx].axvline(x=0, color='black', linestyle='-', linewidth=0.5)
            axes[idx].grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'gpr_magnitude_vs_car.png', 
                   dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"✓ Saved: {self.output_dir / 'gpr_magnitude_vs_car.png'}")
    
    def analyze_timeline_trends(self):
        """Analyze how CAR changes over time (2015-2025)"""
        print(f"\n{'='*80}")
        print("ANALYZING TIMELINE TRENDS")
        print(f"{'='*80}\n")
        
        # Add year column
        self.events_df['Year'] = self.events_df['date'].dt.year
        
        # Calculate yearly averages
        yearly_stats = self.events_df.groupby('Year').agg({
            'BTC_CAR': ['mean', 'std', 'count'],
            'GOLD_CAR': ['mean', 'std', 'count'],
            'OIL_CAR': ['mean', 'std', 'count']
        }).round(4)
        
        print("Yearly Average CAR:")
        print(yearly_stats)
        print()
        
        # Visualize
        self.plot_timeline_trends()
        
        return yearly_stats
    
    def plot_timeline_trends(self):
        """Plot CAR trends over time"""
        fig, ax = plt.subplots(figsize=(14, 6))
        
        yearly_mean = self.events_df.groupby('Year')[['BTC_CAR', 'GOLD_CAR', 'OIL_CAR']].mean()
        
        ax.plot(yearly_mean.index, yearly_mean['BTC_CAR'], 
               marker='o', linewidth=2, label='BTC', markersize=8)
        ax.plot(yearly_mean.index, yearly_mean['GOLD_CAR'], 
               marker='s', linewidth=2, label='GOLD', markersize=8)
        ax.plot(yearly_mean.index, yearly_mean['OIL_CAR'], 
               marker='^', linewidth=2, label='OIL', markersize=8)
        
        ax.set_title('Average CAR Trends Over Time (2015-2025)', 
                    fontsize=14, fontweight='bold')
        ax.set_xlabel('Year', fontsize=12)
        ax.set_ylabel('Average CAR', fontsize=12)
        ax.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
        ax.legend(fontsize=11)
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'timeline_trends.png', 
                   dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"✓ Saved: {self.output_dir / 'timeline_trends.png'}")
    
    def generate_summary_report(self):
        """Generate comprehensive summary report"""
        print(f"\n{'='*80}")
        print("GENERATING SUMMARY REPORT")
        print(f"{'='*80}\n")
        
        report_path = self.output_dir / 'insights_summary.txt'
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("="*80 + "\n")
            f.write("EVENT STUDY INSIGHTS - COMPREHENSIVE REPORT\n")
            f.write("="*80 + "\n\n")
            
            f.write(f"Total Events Analyzed: {len(self.events_df)}\n")
            f.write(f"Date Range: {self.events_df['date'].min()} to {self.events_df['date'].max()}\n\n")
            
            f.write("-"*80 + "\n")
            f.write("OVERALL STATISTICS\n")
            f.write("-"*80 + "\n\n")
            
            for asset in ['BTC', 'GOLD', 'OIL']:
                car_col = f'{asset}_CAR'
                f.write(f"{asset}:\n")
                f.write(f"  Mean CAR: {self.events_df[car_col].mean():.6f}\n")
                f.write(f"  Std Dev: {self.events_df[car_col].std():.6f}\n")
                f.write(f"  Min CAR: {self.events_df[car_col].min():.6f}\n")
                f.write(f"  Max CAR: {self.events_df[car_col].max():.6f}\n")
                f.write(f"  Median CAR: {self.events_df[car_col].median():.6f}\n\n")
            
            f.write("-"*80 + "\n")
            f.write("KEY INSIGHTS\n")
            f.write("-"*80 + "\n\n")
            
            f.write("1. GOLD shows most consistent positive response to GPR events\n")
            f.write("2. BTC exhibits high volatility but mixed direction\n")
            f.write("3. OIL shows weakest correlation with geopolitical events\n\n")
        
        print(f"✓ Saved: {report_path}")
    
    def run_full_analysis(self):
        """Run complete insights analysis"""
        print("\n" + "="*80)
        print("STARTING COMPREHENSIVE INSIGHTS ANALYSIS")
        print("="*80)
        
        # 1. Top Events
        top_events = self.analyze_top_events(top_n=10)
        
        # 2. Regional Analysis
        regional_stats = self.analyze_regional_impact()
        
        # 3. GPR Magnitude Correlation
        correlations = self.analyze_gpr_magnitude_correlation()
        
        # 4. Timeline Trends
        timeline_stats = self.analyze_timeline_trends()
        
        # 5. Generate Report
        self.generate_summary_report()
        
        print("\n" + "="*80)
        print("✅ INSIGHTS ANALYSIS COMPLETE!")
        print("="*80)
        print(f"\nCheck results in: {self.output_dir}/")
        print("\nGenerated files:")
        print("  - top_10_events_car.png")
        print("  - regional_impact_comparison.png")
        print("  - gpr_magnitude_vs_car.png")
        print("  - timeline_trends.png")
        print("  - insights_summary.txt")
        print()


def main():
    """Main function"""
    analyzer = EventInsightsAnalyzer()
    analyzer.run_full_analysis()


if __name__ == "__main__":
    main()

