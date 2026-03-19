"""
Parse Event Study results from summary file and create comprehensive analysis
"""

import pandas as pd
import numpy as np
import re
from pathlib import Path


def parse_event_study_summary(summary_path):
    """
    Parse event_study_summary.txt to extract CAR for each event
    
    Returns:
    --------
    pd.DataFrame with columns: Event_ID, Date, BTC_CAR, GOLD_CAR, OIL_CAR, BTC_tstat, GOLD_tstat, OIL_tstat
    """
    with open(summary_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Split by events
    event_blocks = re.split(r'\n\nEvent_(\d+):', content)
    
    results = []
    
    for i in range(1, len(event_blocks), 2):
        event_num = int(event_blocks[i])
        event_text = event_blocks[i+1]
        
        # Extract date
        date_match = re.search(r'Date: (\d{4}-\d{2}-\d{2})', event_text)
        if not date_match:
            continue
        event_date = date_match.group(1)
        
        # Extract CAR and t-stat for each asset
        car_data = {'Event_ID': event_num, 'Date': event_date}
        
        for asset in ['BTC', 'GOLD', 'OIL']:
            # Find CAR
            car_pattern = rf'{asset}:.*?CAR \(final\): ([-\d.]+)'
            car_match = re.search(car_pattern, event_text, re.DOTALL)
            if car_match:
                car_data[f'{asset}_CAR'] = float(car_match.group(1))
            else:
                car_data[f'{asset}_CAR'] = np.nan
            
            # Find t-stat
            tstat_pattern = rf'{asset}:.*?T-statistic: ([-\d.]+)'
            tstat_match = re.search(tstat_pattern, event_text, re.DOTALL)
            if tstat_match:
                car_data[f'{asset}_tstat'] = float(tstat_match.group(1))
            else:
                car_data[f'{asset}_tstat'] = np.nan
        
        results.append(car_data)
    
    df = pd.DataFrame(results)
    df['Date'] = pd.to_datetime(df['Date'])
    return df


def merge_with_enriched_events(car_df, enriched_path):
    """
    Merge CAR data with enriched events (event names, locations)
    """
    enriched_df = pd.read_csv(enriched_path)
    enriched_df['date'] = pd.to_datetime(enriched_df['date'])
    
    # Merge on date
    merged = pd.merge(
        enriched_df,
        car_df,
        left_on='date',
        right_on='Date',
        how='left'
    )
    
    # Drop duplicate Date column if it exists
    if 'Date' in merged.columns and 'date' in merged.columns:
        merged = merged.drop(columns=['Date'])
    
    return merged


def main():
    """Parse and merge data"""
    print("="*80)
    print("PARSING EVENT STUDY RESULTS")
    print("="*80)
    print()
    
    # Parse CAR from summary
    summary_path = Path('results/event_study/event_study_summary.txt')
    print(f"Parsing {summary_path}...")
    car_df = parse_event_study_summary(summary_path)
    print(f"✓ Parsed {len(car_df)} events with CAR data\n")
    
    # Merge with enriched events
    enriched_path = Path('results/detected_events_enriched.csv')
    print(f"Merging with {enriched_path}...")
    merged_df = merge_with_enriched_events(car_df, enriched_path)
    print(f"✓ Merged data: {len(merged_df)} events\n")
    
    # Save merged data
    output_path = Path('results/events_complete.csv')
    merged_df.to_csv(output_path, index=False, encoding='utf-8-sig')
    print(f"✓ Saved complete data to {output_path}\n")
    
    # Print summary statistics
    print("="*80)
    print("SUMMARY STATISTICS")
    print("="*80)
    print()
    
    for asset in ['BTC', 'GOLD', 'OIL']:
        car_col = f'{asset}_CAR'
        print(f"{asset}:")
        print(f"  Count:  {merged_df[car_col].notna().sum()}")
        print(f"  Mean:   {merged_df[car_col].mean():.6f} ({merged_df[car_col].mean()*100:.2f}%)")
        print(f"  Median: {merged_df[car_col].median():.6f} ({merged_df[car_col].median()*100:.2f}%)")
        print(f"  Std:    {merged_df[car_col].std():.6f} ({merged_df[car_col].std()*100:.2f}%)")
        print(f"  Min:    {merged_df[car_col].min():.6f} ({merged_df[car_col].min()*100:.2f}%)")
        print(f"  Max:    {merged_df[car_col].max():.6f} ({merged_df[car_col].max()*100:.2f}%)")
        
        # Count positive/negative
        positive = (merged_df[car_col] > 0).sum()
        negative = (merged_df[car_col] < 0).sum()
        print(f"  Positive: {positive} events ({positive/merged_df[car_col].notna().sum()*100:.1f}%)")
        print(f"  Negative: {negative} events ({negative/merged_df[car_col].notna().sum()*100:.1f}%)")
        print()
    
    print("="*80)
    print("✅ COMPLETE!")
    print("="*80)
    print()
    print("Next step: Run analyze_event_insights.py with real CAR data")
    print()


if __name__ == "__main__":
    main()

