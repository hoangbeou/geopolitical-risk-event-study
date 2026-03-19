"""
Phân tích phân loại events theo hướng phản ứng của các assets
Xác định khi nào BTC, GOLD, OIL cùng hướng vs ngược hướng
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Set style
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

class EventDirectionAnalyzer:
    def __init__(self, events_csv_path: str, output_dir: str = 'results/direction_analysis'):
        """
        Initialize direction analysis
        
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
        
        # Filter events with valid CAR for all assets
        self.df = self.events_df.dropna(subset=['CAR_BTC', 'CAR_GOLD', 'CAR_OIL']).copy()
        
        print("=" * 80)
        print("EVENT DIRECTION ANALYSIS")
        print("=" * 80)
        print(f"Loaded {len(self.df)} events with valid CAR for all assets")
    
    def classify_event_directions(self):
        """Phân loại events theo hướng phản ứng"""
        print("\n" + "=" * 80)
        print("CLASSIFYING EVENTS BY DIRECTION")
        print("=" * 80)
        
        # Xác định hướng (positive/negative) cho từng asset
        self.df['BTC_direction'] = (self.df['CAR_BTC'] > 0).map({True: 'Positive', False: 'Negative'})
        self.df['GOLD_direction'] = (self.df['CAR_GOLD'] > 0).map({True: 'Positive', False: 'Negative'})
        self.df['OIL_direction'] = (self.df['CAR_OIL'] > 0).map({True: 'Positive', False: 'Negative'})
        
        # 1. All cùng hướng (cả 3 cùng positive hoặc cùng negative)
        self.df['All_Same'] = (
            (self.df['BTC_direction'] == self.df['GOLD_direction']) & 
            (self.df['GOLD_direction'] == self.df['OIL_direction'])
        )
        
        # 2. All Positive (cả 3 cùng tăng)
        self.df['All_Positive'] = (
            (self.df['CAR_BTC'] > 0) & 
            (self.df['CAR_GOLD'] > 0) & 
            (self.df['CAR_OIL'] > 0)
        )
        
        # 3. All Negative (cả 3 cùng giảm)
        self.df['All_Negative'] = (
            (self.df['CAR_BTC'] < 0) & 
            (self.df['CAR_GOLD'] < 0) & 
            (self.df['CAR_OIL'] < 0)
        )
        
        # 4. Mixed (không cùng hướng)
        self.df['Mixed'] = ~self.df['All_Same']
        
        # 5. BTC-GOLD cùng hướng (có thể khác OIL)
        self.df['BTC_GOLD_Same'] = (self.df['BTC_direction'] == self.df['GOLD_direction'])
        
        # 6. BTC-OIL cùng hướng
        self.df['BTC_OIL_Same'] = (self.df['BTC_direction'] == self.df['OIL_direction'])
        
        # 7. GOLD-OIL cùng hướng
        self.df['GOLD_OIL_Same'] = (self.df['GOLD_direction'] == self.df['OIL_direction'])
        
        # 8. Tạo category tổng hợp
        def get_direction_category(row):
            if row['All_Positive']:
                return 'All_Positive'
            elif row['All_Negative']:
                return 'All_Negative'
            elif row['BTC_GOLD_Same'] and not row['BTC_OIL_Same']:
                return 'BTC_GOLD_Same_OIL_Diff'
            elif row['BTC_OIL_Same'] and not row['BTC_GOLD_Same']:
                return 'BTC_OIL_Same_GOLD_Diff'
            elif row['GOLD_OIL_Same'] and not row['BTC_GOLD_Same']:
                return 'GOLD_OIL_Same_BTC_Diff'
            else:
                return 'Fully_Mixed'
        
        self.df['Direction_Category'] = self.df.apply(get_direction_category, axis=1)
        
        # Print statistics
        print("\nDirection Statistics:")
        print(f"  All Same Direction: {self.df['All_Same'].sum()}/{len(self.df)} ({100*self.df['All_Same'].sum()/len(self.df):.1f}%)")
        print(f"    - All Positive: {self.df['All_Positive'].sum()}")
        print(f"    - All Negative: {self.df['All_Negative'].sum()}")
        print(f"  Mixed Direction: {self.df['Mixed'].sum()}/{len(self.df)} ({100*self.df['Mixed'].sum()/len(self.df):.1f}%)")
        print(f"\nPair-wise Same Direction:")
        print(f"  BTC-GOLD Same: {self.df['BTC_GOLD_Same'].sum()}/{len(self.df)} ({100*self.df['BTC_GOLD_Same'].sum()/len(self.df):.1f}%)")
        print(f"  BTC-OIL Same: {self.df['BTC_OIL_Same'].sum()}/{len(self.df)} ({100*self.df['BTC_OIL_Same'].sum()/len(self.df):.1f}%)")
        print(f"  GOLD-OIL Same: {self.df['GOLD_OIL_Same'].sum()}/{len(self.df)} ({100*self.df['GOLD_OIL_Same'].sum()/len(self.df):.1f}%)")
        
        print("\nDirection Categories:")
        print(self.df['Direction_Category'].value_counts().sort_index())
        
        return self.df
    
    def analyze_by_direction_category(self):
        """Phân tích đặc điểm của từng category"""
        print("\n" + "=" * 80)
        print("ANALYSIS BY DIRECTION CATEGORY")
        print("=" * 80)
        
        # Statistics by category
        stats_by_category = self.df.groupby('Direction_Category').agg({
            'GPR_Value': ['mean', 'std', 'count'],
            'GPR_Diff': ['mean', 'std'],
            'CAR_BTC': ['mean', 'std'],
            'CAR_GOLD': ['mean', 'std'],
            'CAR_OIL': ['mean', 'std'],
            'Detection_Method': lambda x: x.value_counts().to_dict()
        })
        
        print("\nStatistics by Direction Category:")
        print(stats_by_category)
        
        # Method distribution
        print("\nDetection Method by Category:")
        method_by_cat = pd.crosstab(self.df['Direction_Category'], self.df['Detection_Method'], normalize='index') * 100
        print(method_by_cat)
        
        # Period analysis
        def assign_period(date):
            if date.year < 2018:
                return '2015-2017'
            elif date.year < 2020:
                return '2018-2019'
            elif date.year < 2022:
                return '2020-2021'
            elif date.year < 2024:
                return '2022-2023'
            else:
                return '2024-2025'
        
        self.df['Period'] = self.df['Date'].apply(assign_period)
        
        print("\nPeriod Distribution by Category:")
        period_by_cat = pd.crosstab(self.df['Direction_Category'], self.df['Period'], normalize='index') * 100
        print(period_by_cat)
        
        return stats_by_category
    
    def visualize_directions(self):
        """Visualize direction patterns"""
        print("\n" + "=" * 80)
        print("CREATING VISUALIZATIONS")
        print("=" * 80)
        
        # 1. Direction category distribution
        fig, ax = plt.subplots(figsize=(12, 6))
        category_counts = self.df['Direction_Category'].value_counts().sort_index()
        colors = plt.cm.Set3(np.linspace(0, 1, len(category_counts)))
        bars = ax.bar(range(len(category_counts)), category_counts.values, color=colors)
        ax.set_xticks(range(len(category_counts)))
        ax.set_xticklabels(category_counts.index, rotation=45, ha='right')
        ax.set_ylabel('Number of Events')
        ax.set_title('Event Distribution by Direction Category')
        ax.grid(True, alpha=0.3, axis='y')
        
        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{int(height)}',
                   ha='center', va='bottom')
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'direction_category_distribution.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # 2. Scatter plot: CAR_BTC vs CAR_GOLD, colored by direction
        fig, axes = plt.subplots(1, 2, figsize=(16, 6))
        
        # Left: All events colored by direction category
        scatter = axes[0].scatter(self.df['CAR_BTC'], self.df['CAR_GOLD'], 
                                 c=pd.Categorical(self.df['Direction_Category']).codes,
                                 cmap='tab10', alpha=0.6, s=50)
        axes[0].axhline(y=0, color='black', linestyle='--', alpha=0.5)
        axes[0].axvline(x=0, color='black', linestyle='--', alpha=0.5)
        axes[0].set_xlabel('BTC CAR')
        axes[0].set_ylabel('GOLD CAR')
        axes[0].set_title('BTC vs GOLD CAR (colored by direction category)')
        axes[0].grid(True, alpha=0.3)
        
        # Right: All events colored by All_Same vs Mixed
        colors_map = self.df['All_Same'].map({True: 'green', False: 'red'})
        axes[1].scatter(self.df['CAR_BTC'], self.df['CAR_GOLD'], 
                       c=colors_map, alpha=0.6, s=50)
        axes[1].axhline(y=0, color='black', linestyle='--', alpha=0.5)
        axes[1].axvline(x=0, color='black', linestyle='--', alpha=0.5)
        axes[1].set_xlabel('BTC CAR')
        axes[1].set_ylabel('GOLD CAR')
        axes[1].set_title('BTC vs GOLD CAR (Green=Same, Red=Mixed)')
        axes[1].grid(True, alpha=0.3)
        
        # Add legend
        from matplotlib.patches import Patch
        legend_elements = [
            Patch(facecolor='green', label='Same Direction'),
            Patch(facecolor='red', label='Mixed Direction')
        ]
        axes[1].legend(handles=legend_elements)
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'btc_gold_scatter_by_direction.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # 3. 3D scatter plot (if possible) or 3 separate 2D plots
        fig, axes = plt.subplots(1, 3, figsize=(18, 5))
        
        # BTC vs GOLD
        colors_map = self.df['All_Same'].map({True: 'green', False: 'red'})
        axes[0].scatter(self.df['CAR_BTC'], self.df['CAR_GOLD'], c=colors_map, alpha=0.6, s=50)
        axes[0].axhline(y=0, color='black', linestyle='--', alpha=0.5)
        axes[0].axvline(x=0, color='black', linestyle='--', alpha=0.5)
        axes[0].set_xlabel('BTC CAR')
        axes[0].set_ylabel('GOLD CAR')
        axes[0].set_title('BTC vs GOLD')
        axes[0].grid(True, alpha=0.3)
        
        # BTC vs OIL
        axes[1].scatter(self.df['CAR_BTC'], self.df['CAR_OIL'], c=colors_map, alpha=0.6, s=50)
        axes[1].axhline(y=0, color='black', linestyle='--', alpha=0.5)
        axes[1].axvline(x=0, color='black', linestyle='--', alpha=0.5)
        axes[1].set_xlabel('BTC CAR')
        axes[1].set_ylabel('OIL CAR')
        axes[1].set_title('BTC vs OIL')
        axes[1].grid(True, alpha=0.3)
        
        # GOLD vs OIL
        axes[2].scatter(self.df['CAR_GOLD'], self.df['CAR_OIL'], c=colors_map, alpha=0.6, s=50)
        axes[2].axhline(y=0, color='black', linestyle='--', alpha=0.5)
        axes[2].axvline(x=0, color='black', linestyle='--', alpha=0.5)
        axes[2].set_xlabel('GOLD CAR')
        axes[2].set_ylabel('OIL CAR')
        axes[2].set_title('GOLD vs OIL')
        axes[2].grid(True, alpha=0.3)
        
        plt.suptitle('CAR Relationships (Green=Same Direction, Red=Mixed)', fontsize=14)
        plt.tight_layout()
        plt.savefig(self.output_dir / 'all_pairs_scatter.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # 4. Heatmap: Direction category vs Period
        pivot_table = pd.crosstab(self.df['Direction_Category'], self.df['Period'])
        fig, ax = plt.subplots(figsize=(12, 6))
        sns.heatmap(pivot_table, annot=True, fmt='d', cmap='YlOrRd', ax=ax)
        ax.set_title('Direction Category Distribution by Period')
        ax.set_ylabel('Direction Category')
        ax.set_xlabel('Period')
        plt.tight_layout()
        plt.savefig(self.output_dir / 'direction_period_heatmap.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        print("Saved visualizations to", self.output_dir)
    
    def export_direction_classified_events(self):
        """Export events với direction classification"""
        output_path = self.output_dir / 'events_with_direction_classification.csv'
        
        # Select relevant columns
        export_cols = [
            'Event_Number', 'Date', 'Detection_Method', 'GPR_Value', 'GPR_Diff',
            'CAR_BTC', 'CAR_GOLD', 'CAR_OIL',
            'Tstat_BTC', 'Tstat_GOLD', 'Tstat_OIL',
            'BTC_direction', 'GOLD_direction', 'OIL_direction',
            'All_Same', 'All_Positive', 'All_Negative', 'Mixed',
            'BTC_GOLD_Same', 'BTC_OIL_Same', 'GOLD_OIL_Same',
            'Direction_Category', 'Period'
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
        report.append("EVENT DIRECTION ANALYSIS - SUMMARY REPORT")
        report.append("=" * 80)
        report.append(f"\nTotal Events: {len(self.df)}")
        report.append(f"Date Range: {self.df['Date'].min()} to {self.df['Date'].max()}")
        
        report.append("\n" + "-" * 80)
        report.append("KEY FINDINGS")
        report.append("-" * 80)
        
        # Same vs Mixed
        same_count = self.df['All_Same'].sum()
        mixed_count = self.df['Mixed'].sum()
        report.append(f"\n1. DIRECTION CONSISTENCY:")
        report.append(f"   All Same Direction: {same_count}/{len(self.df)} ({100*same_count/len(self.df):.1f}%)")
        report.append(f"   Mixed Direction: {mixed_count}/{len(self.df)} ({100*mixed_count/len(self.df):.1f}%)")
        
        # All Positive vs All Negative
        pos_count = self.df['All_Positive'].sum()
        neg_count = self.df['All_Negative'].sum()
        report.append(f"\n2. UNIFORM REACTIONS:")
        report.append(f"   All Positive: {pos_count} events")
        report.append(f"   All Negative: {neg_count} events")
        
        # Pair-wise
        report.append(f"\n3. PAIR-WISE CONSISTENCY:")
        report.append(f"   BTC-GOLD Same: {self.df['BTC_GOLD_Same'].sum()}/{len(self.df)} ({100*self.df['BTC_GOLD_Same'].sum()/len(self.df):.1f}%)")
        report.append(f"   BTC-OIL Same: {self.df['BTC_OIL_Same'].sum()}/{len(self.df)} ({100*self.df['BTC_OIL_Same'].sum()/len(self.df):.1f}%)")
        report.append(f"   GOLD-OIL Same: {self.df['GOLD_OIL_Same'].sum()}/{len(self.df)} ({100*self.df['GOLD_OIL_Same'].sum()/len(self.df):.1f}%)")
        
        # Category breakdown
        report.append(f"\n4. DIRECTION CATEGORIES:")
        for cat, count in self.df['Direction_Category'].value_counts().items():
            pct = 100 * count / len(self.df)
            report.append(f"   {cat}: {count} ({pct:.1f}%)")
        
        # Average CAR by category
        report.append(f"\n5. AVERAGE CAR BY CATEGORY:")
        car_by_cat = self.df.groupby('Direction_Category')[['CAR_BTC', 'CAR_GOLD', 'CAR_OIL']].mean()
        report.append(car_by_cat.to_string())
        
        # Save report
        report_text = "\n".join(report)
        report_path = self.output_dir / 'direction_analysis_report.txt'
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_text)
        
        print("\n" + report_text)
        print(f"\nReport saved to: {report_path}")
        
        return report_text
    
    def run_all_analyses(self):
        """Run all direction analyses"""
        print("\n" + "=" * 80)
        print("RUNNING ALL DIRECTION ANALYSES")
        print("=" * 80)
        
        # Classify events
        self.classify_event_directions()
        
        # Analyze by category
        self.analyze_by_direction_category()
        
        # Visualize
        self.visualize_directions()
        
        # Export
        self.export_direction_classified_events()
        
        # Generate report
        self.generate_summary_report()
        
        print("\n" + "=" * 80)
        print("ALL DIRECTION ANALYSES COMPLETED!")
        print("=" * 80)
        print(f"Results saved to: {self.output_dir}")


if __name__ == '__main__':
    analyzer = EventDirectionAnalyzer(
        events_csv_path='results/event_study/detected_events_with_car.csv',
        output_dir='results/direction_analysis'
    )
    
    analyzer.run_all_analyses()
    
    def visualize_directions(self):
        """Visualize direction patterns"""
        print("\n" + "=" * 80)
        print("CREATING VISUALIZATIONS")
        print("=" * 80)
        
        # 1. Direction category distribution
        fig, ax = plt.subplots(figsize=(12, 6))
        category_counts = self.df['Direction_Category'].value_counts().sort_index()
        colors = plt.cm.Set3(np.linspace(0, 1, len(category_counts)))
        bars = ax.bar(range(len(category_counts)), category_counts.values, color=colors)
        ax.set_xticks(range(len(category_counts)))
        ax.set_xticklabels(category_counts.index, rotation=45, ha='right')
        ax.set_ylabel('Number of Events')
        ax.set_title('Event Distribution by Direction Category')
        ax.grid(True, alpha=0.3, axis='y')
        
        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{int(height)}',
                   ha='center', va='bottom')
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'direction_category_distribution.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # 2. Scatter plot: CAR_BTC vs CAR_GOLD, colored by direction
        fig, axes = plt.subplots(1, 2, figsize=(16, 6))
        
        # Left: All events colored by direction category
        scatter = axes[0].scatter(self.df['CAR_BTC'], self.df['CAR_GOLD'], 
                                 c=pd.Categorical(self.df['Direction_Category']).codes,
                                 cmap='tab10', alpha=0.6, s=50)
        axes[0].axhline(y=0, color='black', linestyle='--', alpha=0.5)
        axes[0].axvline(x=0, color='black', linestyle='--', alpha=0.5)
        axes[0].set_xlabel('BTC CAR')
        axes[0].set_ylabel('GOLD CAR')
        axes[0].set_title('BTC vs GOLD CAR (colored by direction category)')
        axes[0].grid(True, alpha=0.3)
        
        # Right: All events colored by All_Same vs Mixed
        colors_map = self.df['All_Same'].map({True: 'green', False: 'red'})
        axes[1].scatter(self.df['CAR_BTC'], self.df['CAR_GOLD'], 
                       c=colors_map, alpha=0.6, s=50)
        axes[1].axhline(y=0, color='black', linestyle='--', alpha=0.5)
        axes[1].axvline(x=0, color='black', linestyle='--', alpha=0.5)
        axes[1].set_xlabel('BTC CAR')
        axes[1].set_ylabel('GOLD CAR')
        axes[1].set_title('BTC vs GOLD CAR (Green=Same, Red=Mixed)')
        axes[1].grid(True, alpha=0.3)
        
        # Add legend
        from matplotlib.patches import Patch
        legend_elements = [
            Patch(facecolor='green', label='Same Direction'),
            Patch(facecolor='red', label='Mixed Direction')
        ]
        axes[1].legend(handles=legend_elements)
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'btc_gold_scatter_by_direction.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # 3. 3D scatter plot (if possible) or 3 separate 2D plots
        fig, axes = plt.subplots(1, 3, figsize=(18, 5))
        
        # BTC vs GOLD
        colors_map = self.df['All_Same'].map({True: 'green', False: 'red'})
        axes[0].scatter(self.df['CAR_BTC'], self.df['CAR_GOLD'], c=colors_map, alpha=0.6, s=50)
        axes[0].axhline(y=0, color='black', linestyle='--', alpha=0.5)
        axes[0].axvline(x=0, color='black', linestyle='--', alpha=0.5)
        axes[0].set_xlabel('BTC CAR')
        axes[0].set_ylabel('GOLD CAR')
        axes[0].set_title('BTC vs GOLD')
        axes[0].grid(True, alpha=0.3)
        
        # BTC vs OIL
        axes[1].scatter(self.df['CAR_BTC'], self.df['CAR_OIL'], c=colors_map, alpha=0.6, s=50)
        axes[1].axhline(y=0, color='black', linestyle='--', alpha=0.5)
        axes[1].axvline(x=0, color='black', linestyle='--', alpha=0.5)
        axes[1].set_xlabel('BTC CAR')
        axes[1].set_ylabel('OIL CAR')
        axes[1].set_title('BTC vs OIL')
        axes[1].grid(True, alpha=0.3)
        
        # GOLD vs OIL
        axes[2].scatter(self.df['CAR_GOLD'], self.df['CAR_OIL'], c=colors_map, alpha=0.6, s=50)
        axes[2].axhline(y=0, color='black', linestyle='--', alpha=0.5)
        axes[2].axvline(x=0, color='black', linestyle='--', alpha=0.5)
        axes[2].set_xlabel('GOLD CAR')
        axes[2].set_ylabel('OIL CAR')
        axes[2].set_title('GOLD vs OIL')
        axes[2].grid(True, alpha=0.3)
        
        plt.suptitle('CAR Relationships (Green=Same Direction, Red=Mixed)', fontsize=14)
        plt.tight_layout()
        plt.savefig(self.output_dir / 'all_pairs_scatter.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # 4. Heatmap: Direction category vs Period
        pivot_table = pd.crosstab(self.df['Direction_Category'], self.df['Period'])
        fig, ax = plt.subplots(figsize=(12, 6))
        sns.heatmap(pivot_table, annot=True, fmt='d', cmap='YlOrRd', ax=ax)
        ax.set_title('Direction Category Distribution by Period')
        ax.set_ylabel('Direction Category')
        ax.set_xlabel('Period')
        plt.tight_layout()
        plt.savefig(self.output_dir / 'direction_period_heatmap.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        print("Saved visualizations to", self.output_dir)
    
    def export_direction_classified_events(self):
        """Export events với direction classification"""
        output_path = self.output_dir / 'events_with_direction_classification.csv'
        
        # Select relevant columns
        export_cols = [
            'Event_Number', 'Date', 'Detection_Method', 'GPR_Value', 'GPR_Diff',
            'CAR_BTC', 'CAR_GOLD', 'CAR_OIL',
            'Tstat_BTC', 'Tstat_GOLD', 'Tstat_OIL',
            'BTC_direction', 'GOLD_direction', 'OIL_direction',
            'All_Same', 'All_Positive', 'All_Negative', 'Mixed',
            'BTC_GOLD_Same', 'BTC_OIL_Same', 'GOLD_OIL_Same',
            'Direction_Category', 'Period'
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
        report.append("EVENT DIRECTION ANALYSIS - SUMMARY REPORT")
        report.append("=" * 80)
        report.append(f"\nTotal Events: {len(self.df)}")
        report.append(f"Date Range: {self.df['Date'].min()} to {self.df['Date'].max()}")
        
        report.append("\n" + "-" * 80)
        report.append("KEY FINDINGS")
        report.append("-" * 80)
        
        # Same vs Mixed
        same_count = self.df['All_Same'].sum()
        mixed_count = self.df['Mixed'].sum()
        report.append(f"\n1. DIRECTION CONSISTENCY:")
        report.append(f"   All Same Direction: {same_count}/{len(self.df)} ({100*same_count/len(self.df):.1f}%)")
        report.append(f"   Mixed Direction: {mixed_count}/{len(self.df)} ({100*mixed_count/len(self.df):.1f}%)")
        
        # All Positive vs All Negative
        pos_count = self.df['All_Positive'].sum()
        neg_count = self.df['All_Negative'].sum()
        report.append(f"\n2. UNIFORM REACTIONS:")
        report.append(f"   All Positive: {pos_count} events")
        report.append(f"   All Negative: {neg_count} events")
        
        # Pair-wise
        report.append(f"\n3. PAIR-WISE CONSISTENCY:")
        report.append(f"   BTC-GOLD Same: {self.df['BTC_GOLD_Same'].sum()}/{len(self.df)} ({100*self.df['BTC_GOLD_Same'].sum()/len(self.df):.1f}%)")
        report.append(f"   BTC-OIL Same: {self.df['BTC_OIL_Same'].sum()}/{len(self.df)} ({100*self.df['BTC_OIL_Same'].sum()/len(self.df):.1f}%)")
        report.append(f"   GOLD-OIL Same: {self.df['GOLD_OIL_Same'].sum()}/{len(self.df)} ({100*self.df['GOLD_OIL_Same'].sum()/len(self.df):.1f}%)")
        
        # Category breakdown
        report.append(f"\n4. DIRECTION CATEGORIES:")
        for cat, count in self.df['Direction_Category'].value_counts().items():
            pct = 100 * count / len(self.df)
            report.append(f"   {cat}: {count} ({pct:.1f}%)")
        
        # Average CAR by category
        report.append(f"\n5. AVERAGE CAR BY CATEGORY:")
        car_by_cat = self.df.groupby('Direction_Category')[['CAR_BTC', 'CAR_GOLD', 'CAR_OIL']].mean()
        report.append(car_by_cat.to_string())
        
        # Save report
        report_text = "\n".join(report)
        report_path = self.output_dir / 'direction_analysis_report.txt'
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_text)
        
        print("\n" + report_text)
        print(f"\nReport saved to: {report_path}")
        
        return report_text
    
    def run_all_analyses(self):
        """Run all direction analyses"""
        print("\n" + "=" * 80)
        print("RUNNING ALL DIRECTION ANALYSES")
        print("=" * 80)
        
        # Classify events
        self.classify_event_directions()
        
        # Analyze by category
        self.analyze_by_direction_category()
        
        # Visualize
        self.visualize_directions()
        
        # Export
        self.export_direction_classified_events()
        
        # Generate report
        self.generate_summary_report()
        
        print("\n" + "=" * 80)
        print("ALL DIRECTION ANALYSES COMPLETED!")
        print("=" * 80)
        print(f"Results saved to: {self.output_dir}")


if __name__ == '__main__':
    analyzer = EventDirectionAnalyzer(
        events_csv_path='results/event_study/detected_events_with_car.csv',
        output_dir='results/direction_analysis'
    )
    
    analyzer.run_all_analyses()

