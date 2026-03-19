"""
Download BTC, GOLD, OIL prices
Merge with GPR data from data_gpr_daily_recent.xls
"""

import pandas as pd
from pathlib import Path
from datetime import datetime
import yfinance as yf
import warnings
warnings.filterwarnings('ignore')

def download_btc_gold_oil(start_date='2015-01-01', end_date=None):
    """
    Download BTC, GOLD, OIL prices using yfinance
    
    Data sources:
    - BTC: BTC-USD (Bitcoin/USD from yfinance)
    - GOLD: GC=F (Gold Futures from yfinance)
    - OIL: CL=F (Crude Oil Futures from yfinance)
    
    Returns:
    --------
    pd.DataFrame with columns: BTC, GOLD, OIL
    """
    print("="*80)
    print("DOWNLOADING BTC, GOLD, OIL PRICES")
    print("="*80)
    
    if end_date is None:
        end_date = datetime.now().strftime('%Y-%m-%d')
    
    print(f"Date range: {start_date} to {end_date}")
    
    # Download data
    data_dict = {}
    
    # BTC - Bitcoin (BTC-USD)
    print("\n1. Downloading BTC (BTC-USD)...")
    try:
        btc = yf.download('BTC-USD', start=start_date, end=end_date, progress=False)
        if not btc.empty:
            # Handle MultiIndex columns - yfinance returns (Price, Ticker)
            if isinstance(btc.columns, pd.MultiIndex):
                # Get Close column from MultiIndex (level 0 is Price, level 1 is Ticker)
                close_col = btc.columns[btc.columns.get_level_values(0) == 'Close']
                if len(close_col) > 0:
                    data_dict['BTC'] = btc[close_col[0]]
                    print(f"   [OK] BTC: {len(btc)} days")
                else:
                    print(f"   [ERROR] BTC: No Close column in MultiIndex")
            elif 'Close' in btc.columns:
                data_dict['BTC'] = btc['Close']
                print(f"   [OK] BTC: {len(btc)} days")
            else:
                print(f"   [ERROR] BTC: No Close column. Columns: {btc.columns.tolist()}")
        else:
            print("   [ERROR] BTC: No data")
    except Exception as e:
        print(f"   [ERROR] BTC Error: {e}")
    
    # GOLD - Gold Futures (GC=F)
    print("\n2. Downloading GOLD (GC=F - Gold Futures)...")
    try:
        gold = yf.download('GC=F', start=start_date, end=end_date, progress=False)
        if not gold.empty:
            # Handle MultiIndex columns (Price, Ticker)
            if isinstance(gold.columns, pd.MultiIndex):
                close_col = gold.columns[gold.columns.get_level_values(0) == 'Close']
                if len(close_col) > 0:
                    data_dict['GOLD'] = gold[close_col[0]]
                    print(f"   [OK] GOLD: {len(gold)} days")
                else:
                    print(f"   [ERROR] GOLD: No Close column in MultiIndex")
            elif 'Close' in gold.columns:
                data_dict['GOLD'] = gold['Close']
                print(f"   [OK] GOLD: {len(gold)} days")
            else:
                print(f"   [ERROR] GOLD: No Close column. Columns: {gold.columns.tolist()}")
        else:
            print("   [ERROR] GOLD: No data")
    except Exception as e:
        print(f"   [ERROR] GOLD Error: {e}")
    
    # OIL - Crude Oil Futures (CL=F)
    print("\n3. Downloading OIL (CL=F - Crude Oil Futures)...")
    try:
        oil = yf.download('CL=F', start=start_date, end=end_date, progress=False)
        if not oil.empty:
            # Handle MultiIndex columns (Price, Ticker)
            if isinstance(oil.columns, pd.MultiIndex):
                close_col = oil.columns[oil.columns.get_level_values(0) == 'Close']
                if len(close_col) > 0:
                    data_dict['OIL'] = oil[close_col[0]]
                    print(f"   [OK] OIL: {len(oil)} days")
                else:
                    print(f"   [ERROR] OIL: No Close column in MultiIndex")
            elif 'Close' in oil.columns:
                data_dict['OIL'] = oil['Close']
                print(f"   [OK] OIL: {len(oil)} days")
            else:
                print(f"   [ERROR] OIL: No Close column. Columns: {oil.columns.tolist()}")
        else:
            print("   [ERROR] OIL: No data")
    except Exception as e:
        print(f"   [ERROR] OIL Error: {e}")
    
    # Combine into DataFrame
    if data_dict:
        # Align all series to common index
        df = None
        for key, series in data_dict.items():
            if series is not None:
                if isinstance(series, pd.Series) and len(series) > 0:
                    if df is None:
                        df = pd.DataFrame({key: series})
                    else:
                        df = df.join(pd.DataFrame({key: series}), how='outer')
        
        if df is not None and not df.empty:
            df.index.name = 'DATE'
            print(f"\n[OK] Combined data: {len(df)} days")
            print(f"  Date range: {df.index.min()} to {df.index.max()}")
            return df
        else:
            print("\n[ERROR] No valid data downloaded")
            return pd.DataFrame()
    else:
        print("\n[ERROR] No data downloaded")
        return pd.DataFrame()


def load_gpr_data(file_path):
    """
    Load GPR data from Excel file
    
    Returns:
    --------
    pd.DataFrame with GPR data
    """
    print("\n" + "="*80)
    print("LOADING GPR DATA")
    print("="*80)
    
    try:
        # Try reading Excel file
        if file_path.suffix in ['.xls', '.xlsx']:
            df = pd.read_excel(file_path)
        elif file_path.suffix == '.csv':
            df = pd.read_csv(file_path)
        else:
            print(f"[ERROR] Unsupported file format: {file_path.suffix}")
            return pd.DataFrame()
        
        print(f"[OK] Loaded GPR data: {len(df)} rows")
        print(f"  Columns: {list(df.columns)}")
        
        # Try to find date column
        date_cols = [col for col in df.columns if 'date' in col.lower() or 'DATE' in col]
        if date_cols:
            date_col = date_cols[0]
            df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
            df = df.set_index(date_col)
            print(f"  Using '{date_col}' as date index")
        else:
            print("  [WARNING] No date column found, using first column as index")
            df = df.set_index(df.columns[0])
        
        return df
        
    except Exception as e:
        print(f"[ERROR] Error loading GPR data: {e}")
        return pd.DataFrame()


def merge_all_data(price_df, gpr_df):
    """
    Merge all data together
    
    Parameters:
    -----------
    price_df : pd.DataFrame
        BTC, GOLD, OIL prices
    gpr_df : pd.DataFrame
        GPR data
    
    Returns:
    --------
    pd.DataFrame
        Merged data
    """
    print("\n" + "="*80)
    print("MERGING ALL DATA")
    print("="*80)
    
    # Start with GPR data (if available)
    if not gpr_df.empty:
        merged = gpr_df.copy()
        print(f"Starting with GPR data: {len(merged)} rows")
    else:
        # Start with price data
        merged = price_df.copy()
        print(f"Starting with price data: {len(merged)} rows")
    
    # Merge prices
    if not price_df.empty:
        merged = merged.join(price_df, how='outer', rsuffix='_new')
        # If duplicate columns, keep new ones
        for col in price_df.columns:
            if f'{col}_new' in merged.columns:
                merged[col] = merged[f'{col}_new']
                merged = merged.drop(columns=[f'{col}_new'])
        print(f"After merging prices: {len(merged)} rows")
    
    # Sort by date
    merged = merged.sort_index()
    
    # Filter from 2015-01-01
    start_date = pd.Timestamp('2015-01-01')
    merged = merged[merged.index >= start_date]
    
    print(f"\n[OK] Final merged data: {len(merged)} rows")
    print(f"  Date range: {merged.index.min()} to {merged.index.max()}")
    print(f"  Columns: {list(merged.columns)}")
    
    return merged


def main():
    """Main function"""
    print("="*80)
    print("DOWNLOAD AND MERGE DATA FOR GEOPOLITICAL RISK ANALYSIS")
    print("="*80)
    
    # Find GPR file
    data_dir = Path('data')
    gpr_files = list(data_dir.glob('*gpr*.xls*')) + list(data_dir.glob('*gpr*.csv'))
    
    if not gpr_files:
        print(f"\n[WARNING] No GPR file found in {data_dir}")
        print("   Looking for files with 'gpr' in name...")
        gpr_file = None
    else:
        gpr_file = gpr_files[0]
        print(f"\n[OK] Found GPR file: {gpr_file}")
    
    # Download prices
    price_df = download_btc_gold_oil(start_date='2015-01-01')
    
    # Load GPR data
    if gpr_file:
        gpr_df = load_gpr_data(gpr_file)
    else:
        print("\n[WARNING] No GPR file found, will create new file with prices only")
        gpr_df = pd.DataFrame()
    
    # Merge all data
    merged_df = merge_all_data(price_df, gpr_df)
    
    # Save merged data
    output_path = data_dir / 'data.csv'
    merged_df.to_csv(output_path, date_format='%d/%m/%Y')
    print(f"\n[OK] Saved merged data to: {output_path}")
    
    # Also save as Excel if GPR was Excel
    if gpr_file and gpr_file.suffix in ['.xls', '.xlsx']:
        output_excel = data_dir / 'data_gpr_daily_recent.xlsx'
        merged_df.to_excel(output_excel, index=True)
        print(f"[OK] Saved merged data to: {output_excel}")
    
    print("\n" + "="*80)
    print("COMPLETE!")
    print("="*80)


if __name__ == '__main__':
    main()

