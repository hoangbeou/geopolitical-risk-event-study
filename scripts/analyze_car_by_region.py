"""
Phân tích CAR theo Region từ dữ liệu Wikipedia đã phân loại
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import os

# Set style
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

class RegionCARAnalyzer:
    def __init__(self, events_csv, car_csv, output_dir='results/region_analysis'):
        self.events_csv = events_csv
        self.car_csv = car_csv
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
    def load_data(self):
        """Load và merge dữ liệu"""
        print("Đang load dữ liệu...")
        
        # Load events với region
        self.events_df = pd.read_csv(self.events_csv)
        self.events_df['Date'] = pd.to_datetime(self.events_df['Date'])
        
        # Load CAR data
        self.car_df = pd.read_csv(self.car_csv)
        self.car_df['Date'] = pd.to_datetime(self.car_df['Date'])
        
        # Merge trên Date
        self.merged_df = pd.merge(
            self.events_df[['Event_Number', 'Date', 'Region', 'Secondary_Regions', 
                           'GPR_Value', 'Detection_Method']],
            self.car_df[['Date', 'CAR_BTC', 'CAR_GOLD', 'CAR_OIL', 
                        'Tstat_BTC', 'Tstat_GOLD', 'Tstat_OIL']],
            on='Date',
            how='inner'
        )
        
        print(f"  Đã merge {len(self.merged_df)} events với CAR data")
        return self.merged_df
    
    def analyze_by_region(self):
        """Phân tích CAR theo region"""
        print("\n" + "="*60)
        print("PHÂN TÍCH CAR THEO REGION")
        print("="*60)
        
        # Loại bỏ UNKNOWN và MULTI_REGION để phân tích rõ ràng hơn
        df_clean = self.merged_df[
            (~self.merged_df['Region'].isin(['UNKNOWN', 'MULTI_REGION']))
        ].copy()
        
        print(f"\nSố events sau khi loại bỏ UNKNOWN và MULTI_REGION: {len(df_clean)}")
        
        # Tính average CAR theo region
        assets = ['BTC', 'GOLD', 'OIL']
        results = []
        
        for region in df_clean['Region'].unique():
            region_data = df_clean[df_clean['Region'] == region]
            n_events = len(region_data)
            
            if n_events < 2:
                continue
            
            row = {'Region': region, 'N_Events': n_events}
            
            for asset in assets:
                car_col = f'CAR_{asset}'
                car_values = region_data[car_col].dropna()
                
                if len(car_values) > 0:
                    row[f'{asset}_Mean'] = car_values.mean()
                    row[f'{asset}_Median'] = car_values.median()
                    row[f'{asset}_Std'] = car_values.std()
                    row[f'{asset}_Min'] = car_values.min()
                    row[f'{asset}_Max'] = car_values.max()
                else:
                    row[f'{asset}_Mean'] = np.nan
            
            results.append(row)
        
        results_df = pd.DataFrame(results)
        results_df = results_df.sort_values('N_Events', ascending=False)
        
        print("\nBảng 1: Average CAR (%) theo Region")
        print("-" * 80)
        print(results_df.to_string(index=False))
        
        return results_df, df_clean
    
    def statistical_tests(self, df_clean):
        """Kiểm định thống kê giữa các regions"""
        print("\n" + "="*60)
        print("KIỂM ĐỊNH THỐNG KÊ")
        print("="*60)
        
        assets = ['BTC', 'GOLD', 'OIL']
        regions = df_clean['Region'].unique()
        
        # ANOVA test để kiểm tra sự khác biệt giữa các regions
        print("\nANOVA Test (kiểm tra sự khác biệt giữa các regions):")
        print("-" * 60)
        
        for asset in assets:
            car_col = f'CAR_{asset}'
            groups = [df_clean[df_clean['Region'] == r][car_col].dropna() 
                     for r in regions if len(df_clean[df_clean['Region'] == r][car_col].dropna()) >= 2]
            
            if len(groups) >= 2:
                f_stat, p_value = stats.f_oneway(*groups)
                print(f"\n{asset}:")
                print(f"  F-statistic: {f_stat:.4f}")
                print(f"  P-value: {p_value:.4f}")
                if p_value < 0.05:
                    print(f"  → Có sự khác biệt có ý nghĩa thống kê (p < 0.05)")
                else:
                    print(f"  → Không có sự khác biệt có ý nghĩa thống kê")
        
        # Pairwise t-tests cho các regions chính
        print("\n" + "-" * 60)
        print("Pairwise T-tests (so sánh từng cặp regions):")
        print("-" * 60)
        
        main_regions = ['Middle East', 'Russia/CIS', 'Africa', 'Asia']
        main_regions = [r for r in main_regions if r in regions]
        
        for asset in assets:
            car_col = f'CAR_{asset}'
            print(f"\n{asset}:")
            
            for i, r1 in enumerate(main_regions):
                for r2 in main_regions[i+1:]:
                    data1 = df_clean[df_clean['Region'] == r1][car_col].dropna()
                    data2 = df_clean[df_clean['Region'] == r2][car_col].dropna()
                    
                    if len(data1) >= 2 and len(data2) >= 2:
                        t_stat, p_value = stats.ttest_ind(data1, data2)
                        mean1 = data1.mean()
                        mean2 = data2.mean()
                        print(f"  {r1} vs {r2}:")
                        print(f"    Mean: {mean1:.2f}% vs {mean2:.2f}%")
                        print(f"    T-stat: {t_stat:.4f}, P-value: {p_value:.4f}")
                        if p_value < 0.05:
                            print(f"    → Significant difference!")
    
    def visualize(self, df_clean, results_df):
        """Tạo visualizations"""
        print("\n" + "="*60)
        print("TẠO VISUALIZATIONS")
        print("="*60)
        
        assets = ['BTC', 'GOLD', 'OIL']
        
        # 1. Box plot CAR theo region
        fig, axes = plt.subplots(1, 3, figsize=(18, 6))
        
        for idx, asset in enumerate(assets):
            car_col = f'CAR_{asset}'
            df_plot = df_clean[['Region', car_col]].dropna()
            
            # Sắp xếp theo số lượng events
            region_counts = df_plot['Region'].value_counts()
            region_order = region_counts.index.tolist()
            
            sns.boxplot(data=df_plot, x='Region', y=car_col, ax=axes[idx], order=region_order)
            axes[idx].set_title(f'{asset} CAR by Region', fontsize=14, fontweight='bold')
            axes[idx].set_xlabel('Region', fontsize=12)
            axes[idx].set_ylabel('CAR (%)', fontsize=12)
            axes[idx].tick_params(axis='x', rotation=45)
            axes[idx].axhline(y=0, color='r', linestyle='--', alpha=0.5)
            axes[idx].grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/car_by_region_boxplot.png', dpi=300, bbox_inches='tight')
        print(f"  ✓ Đã lưu: {self.output_dir}/car_by_region_boxplot.png")
        plt.close()
        
        # 2. Bar chart average CAR theo region
        fig, axes = plt.subplots(1, 3, figsize=(18, 6))
        
        for idx, asset in enumerate(assets):
            mean_col = f'{asset}_Mean'
            if mean_col in results_df.columns:
                data_plot = results_df[['Region', mean_col]].dropna()
                data_plot = data_plot.sort_values(mean_col, ascending=False)
                
                bars = axes[idx].bar(data_plot['Region'], data_plot[mean_col], 
                                     color=sns.color_palette("husl", len(data_plot)))
                axes[idx].set_title(f'{asset} Average CAR by Region', fontsize=14, fontweight='bold')
                axes[idx].set_xlabel('Region', fontsize=12)
                axes[idx].set_ylabel('Average CAR (%)', fontsize=12)
                axes[idx].tick_params(axis='x', rotation=45)
                axes[idx].axhline(y=0, color='r', linestyle='--', alpha=0.5)
                axes[idx].grid(True, alpha=0.3, axis='y')
                
                # Thêm giá trị trên bars
                for bar in bars:
                    height = bar.get_height()
                    axes[idx].text(bar.get_x() + bar.get_width()/2., height,
                                  f'{height:.2f}%',
                                  ha='center', va='bottom' if height > 0 else 'top',
                                  fontsize=9)
        
        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/car_by_region_barchart.png', dpi=300, bbox_inches='tight')
        print(f"  ✓ Đã lưu: {self.output_dir}/car_by_region_barchart.png")
        plt.close()
        
        # 3. Heatmap correlation giữa regions
        fig, axes = plt.subplots(1, 3, figsize=(18, 6))
        
        for idx, asset in enumerate(assets):
            car_col = f'CAR_{asset}'
            
            # Tạo pivot table: Region x Event (CAR values)
            pivot_data = df_clean.pivot_table(
                values=car_col,
                index='Region',
                columns='Event_Number',
                aggfunc='first'
            )
            
            # Tính correlation giữa các regions
            corr_matrix = pivot_data.T.corr()
            
            sns.heatmap(corr_matrix, annot=True, fmt='.2f', cmap='coolwarm', 
                       center=0, vmin=-1, vmax=1, ax=axes[idx],
                       square=True, linewidths=0.5)
            axes[idx].set_title(f'{asset} CAR Correlation between Regions', 
                               fontsize=14, fontweight='bold')
        
        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/region_correlation_heatmap.png', dpi=300, bbox_inches='tight')
        print(f"  ✓ Đã lưu: {self.output_dir}/region_correlation_heatmap.png")
        plt.close()
    
    def export_results(self, results_df, df_clean):
        """Export kết quả"""
        # Export summary
        results_df.to_csv(f'{self.output_dir}/car_by_region_summary.csv', index=False)
        print(f"\n  ✓ Đã lưu: {self.output_dir}/car_by_region_summary.csv")
        
        # Export full data với region
        df_export = df_clean[['Event_Number', 'Date', 'Region', 'Secondary_Regions',
                             'GPR_Value', 'Detection_Method',
                             'CAR_BTC', 'CAR_GOLD', 'CAR_OIL',
                             'Tstat_BTC', 'Tstat_GOLD', 'Tstat_OIL']]
        df_export.to_csv(f'{self.output_dir}/events_with_region_and_car.csv', index=False)
        print(f"  ✓ Đã lưu: {self.output_dir}/events_with_region_and_car.csv")
        
        # Tạo report
        self.create_report(results_df, df_clean)
    
    def create_report(self, results_df, df_clean):
        """Tạo báo cáo text"""
        report_path = f'{self.output_dir}/region_analysis_report.txt'
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("="*80 + "\n")
            f.write("PHÂN TÍCH CAR THEO REGION - BÁO CÁO TỔNG HỢP\n")
            f.write("="*80 + "\n\n")
            
            f.write(f"Tổng số events phân tích: {len(df_clean)}\n")
            f.write(f"Thời gian: {df_clean['Date'].min().strftime('%Y-%m-%d')} đến "
                   f"{df_clean['Date'].max().strftime('%Y-%m-%d')}\n\n")
            
            f.write("-"*80 + "\n")
            f.write("PHÂN BỐ EVENTS THEO REGION\n")
            f.write("-"*80 + "\n")
            region_counts = df_clean['Region'].value_counts()
            for region, count in region_counts.items():
                pct = count / len(df_clean) * 100
                f.write(f"  {region:20s}: {count:3d} events ({pct:5.1f}%)\n")
            
            f.write("\n" + "-"*80 + "\n")
            f.write("AVERAGE CAR (%) THEO REGION\n")
            f.write("-"*80 + "\n")
            f.write(results_df.to_string(index=False))
            
            f.write("\n\n" + "-"*80 + "\n")
            f.write("KẾT LUẬN CHÍNH\n")
            f.write("-"*80 + "\n")
            
            # Tìm region có CAR cao nhất/thấp nhất cho mỗi asset
            assets = ['BTC', 'GOLD', 'OIL']
            for asset in assets:
                mean_col = f'{asset}_Mean'
                if mean_col in results_df.columns:
                    max_region = results_df.loc[results_df[mean_col].idxmax(), 'Region']
                    max_car = results_df[mean_col].max()
                    min_region = results_df.loc[results_df[mean_col].idxmin(), 'Region']
                    min_car = results_df[mean_col].min()
                    
                    f.write(f"\n{asset}:\n")
                    f.write(f"  Region có CAR cao nhất: {max_region} ({max_car:.2f}%)\n")
                    f.write(f"  Region có CAR thấp nhất: {min_region} ({min_car:.2f}%)\n")
        
        print(f"  ✓ Đã lưu: {report_path}")

def main():
    events_csv = 'ket_qua_wiki_with_regions.csv'
    car_csv = 'results/event_study/detected_events_with_car.csv'
    
    analyzer = RegionCARAnalyzer(events_csv, car_csv)
    
    # Load data
    merged_df = analyzer.load_data()
    
    # Analyze
    results_df, df_clean = analyzer.analyze_by_region()
    
    # Statistical tests
    analyzer.statistical_tests(df_clean)
    
    # Visualize
    analyzer.visualize(df_clean, results_df)
    
    # Export
    analyzer.export_results(results_df, df_clean)
    
    print("\n" + "="*60)
    print("HOÀN THÀNH!")
    print("="*60)

if __name__ == '__main__':
    main()

