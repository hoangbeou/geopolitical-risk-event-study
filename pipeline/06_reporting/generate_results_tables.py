"""
Script để tạo các bảng kết quả tự động cho khóa luận
"""

import pandas as pd
import numpy as np
from pathlib import Path
import json

def generate_summary_statistics(preprocessed_data, output_file='results/summary_statistics.tex'):
    """
    Tạo bảng thống kê mô tả
    """
    returns = preprocessed_data['returns']
    differenced = preprocessed_data['differenced']
    residuals = preprocessed_data['residuals']
    
    # Combine all series
    all_data = pd.concat([
        returns,
        differenced,
        residuals
    ], axis=1).dropna()
    
    # Calculate statistics
    stats = pd.DataFrame({
        'Mean': all_data.mean(),
        'Std': all_data.std(),
        'Min': all_data.min(),
        'Max': all_data.max(),
        'Skewness': all_data.skew(),
        'Kurtosis': all_data.kurtosis()
    })
    
    # Round to 4 decimal places
    stats = stats.round(4)
    
    # Save as CSV
    stats.to_csv('results/summary_statistics.csv')
    
    # Generate LaTeX table
    latex_table = stats.to_latex(
        float_format="%.4f",
        caption="Thống kê mô tả các biến",
        label="tab:summary_stats"
    )
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(latex_table)
    
    print(f"✓ Bảng thống kê mô tả đã được lưu: {output_file}")
    return stats


def generate_ces_table(dependence_results, output_file='results/ces_table.tex'):
    """
    Tạo bảng CES cho các scales
    """
    ces_data = {}
    
    for asset, results in dependence_results.items():
        ces_values = []
        scales = []
        for scale in sorted(results['ces'].keys()):
            ces = results['ces'][scale]
            if not np.isnan(ces):
                ces_values.append(ces)
                scales.append(scale)
        ces_data[asset] = dict(zip(scales, ces_values))
    
    # Create DataFrame
    max_scales = max(len(v) for v in ces_data.values())
    df_data = {}
    
    for asset, values in ces_data.items():
        df_data[asset] = [values.get(s, np.nan) for s in range(1, max_scales + 1)]
    
    df = pd.DataFrame(df_data, index=range(1, max_scales + 1))
    df.index.name = 'Scale'
    
    # Save as CSV
    df.to_csv('results/ces_table.csv')
    
    # Generate LaTeX
    latex_table = df.to_latex(
        float_format="%.4f",
        caption="Conditional Expected Shortfall (CES) qua các scales",
        label="tab:ces",
        na_rep="--"
    )
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(latex_table)
    
    print(f"✓ Bảng CES đã được lưu: {output_file}")
    return df


def generate_hedging_effectiveness_table(portfolio_results, output_file='results/he_table.tex'):
    """
    Tạo bảng Hedging Effectiveness
    """
    he_data = {
        'Strategy': ['MVP', 'MCP', 'MCoP'],
        'Hedging Effectiveness (%)': [
            portfolio_results.get('MVP_HE', np.nan),
            portfolio_results.get('MCP_HE', np.nan),
            portfolio_results.get('MCoP_HE', np.nan)
        ]
    }
    
    df = pd.DataFrame(he_data)
    
    # Save as CSV
    df.to_csv('results/he_table.csv')
    
    # Generate LaTeX
    latex_table = df.to_latex(
        index=False,
        float_format="%.2f",
        caption="Hiệu quả Phòng ngừa Rủi ro (Hedging Effectiveness)",
        label="tab:he"
    )
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(latex_table)
    
    print(f"✓ Bảng Hedging Effectiveness đã được lưu: {output_file}")
    return df


def generate_portfolio_weights_summary(portfolio_results, output_file='results/portfolio_weights_summary.tex'):
    """
    Tạo bảng tóm tắt trọng số danh mục
    """
    if 'weights' not in portfolio_results:
        print("⚠ Không có dữ liệu trọng số danh mục")
        return None
    
    weights = portfolio_results['weights']
    
    summary_data = []
    
    for strategy, weight_df in weights.items():
        avg_weights = weight_df.mean()
        std_weights = weight_df.std()
        
        for asset in weight_df.columns:
            summary_data.append({
                'Strategy': strategy,
                'Asset': asset,
                'Mean Weight': avg_weights[asset],
                'Std Weight': std_weights[asset],
                'Min Weight': weight_df[asset].min(),
                'Max Weight': weight_df[asset].max()
            })
    
    df = pd.DataFrame(summary_data)
    
    # Save as CSV
    df.to_csv('results/portfolio_weights_summary.csv')
    
    # Generate LaTeX
    latex_table = df.to_latex(
        index=False,
        float_format="%.4f",
        caption="Tóm tắt Trọng số Danh mục Tối ưu",
        label="tab:portfolio_weights"
    )
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(latex_table)
    
    print(f"✓ Bảng trọng số danh mục đã được lưu: {output_file}")
    return df


def generate_all_tables(results_dict):
    """
    Tạo tất cả các bảng kết quả
    """
    print("=" * 60)
    print("TẠO CÁC BẢNG KẾT QUẢ CHO KHÓA LUẬN")
    print("=" * 60)
    
    # Create tables directory
    Path('results/tables').mkdir(exist_ok=True)
    
    # 1. Summary statistics
    if 'preprocessed' in results_dict:
        generate_summary_statistics(
            results_dict['preprocessed'],
            'results/tables/summary_statistics.tex'
        )
    
    # 2. CES table
    if 'dependence' in results_dict:
        generate_ces_table(
            results_dict['dependence'],
            'results/tables/ces_table.tex'
        )
    
    # 3. Hedging Effectiveness
    if 'portfolio' in results_dict:
        generate_hedging_effectiveness_table(
            results_dict['portfolio'],
            'results/tables/he_table.tex'
        )
        
        generate_portfolio_weights_summary(
            results_dict['portfolio'],
            'results/tables/portfolio_weights_summary.tex'
        )
    
    print("\n" + "=" * 60)
    print("HOÀN TẤT TẠO BẢNG")
    print("=" * 60)
    print("\nCác bảng đã được lưu trong thư mục: results/tables/")
    print("  - summary_statistics.tex (và .csv)")
    print("  - ces_table.tex (và .csv)")
    print("  - he_table.tex (và .csv)")
    print("  - portfolio_weights_summary.tex (và .csv)")


if __name__ == '__main__':
    # Load results if available
    # This would need to be run after the main analysis
    print("Chạy script này sau khi đã chạy phân tích chính.")
    print("Hoặc import và sử dụng generate_all_tables() với results dictionary.")

