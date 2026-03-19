"""
Generate research template với search queries và direct links
Cách đơn giản và hiệu quả nhất để research events
"""

import pandas as pd
from pathlib import Path
from datetime import datetime

def generate_research_template():
    """Generate research template với search queries và links"""
    print("=" * 80)
    print("GENERATE RESEARCH TEMPLATE FOR EVENTS")
    print("=" * 80)
    print()
    
    # Load data
    car_path = Path('results/event_study/event_classification.csv')
    car_df = pd.read_csv(car_path)
    car_df['Date'] = pd.to_datetime(car_df['Date'])
    
    # Load GPR data
    data_path = Path('data/data_optimized.csv')
    df_gpr = pd.read_csv(data_path)
    if 'DAY' in df_gpr.columns:
        try:
            df_gpr['DATE'] = pd.to_datetime(df_gpr['DAY'].astype(int).astype(str), format='%Y%m%d', errors='coerce')
        except:
            df_gpr['DATE'] = pd.to_datetime(df_gpr['DAY'], format='%d/%m/%Y', errors='coerce')
    df_gpr = df_gpr.dropna(subset=['DATE'])
    df_gpr['DATE'] = pd.to_datetime(df_gpr['DATE'])
    
    # Get unique events
    events = car_df.groupby('Event').first().reset_index()
    events = events.sort_values('Date')
    
    print(f"Found {len(events)} unique events")
    print("Generating research template...\n")
    
    # Generate research data
    research_data = []
    
    for idx, event_row in events.iterrows():
        event_id = event_row['Event']
        event_date = pd.to_datetime(event_row['Date'])
        
        # Get GPR data
        date_diffs = (df_gpr['DATE'] - event_date).abs()
        closest_idx = date_diffs.idxmin()
        closest_date = df_gpr.loc[closest_idx, 'DATE']
        
        if abs((closest_date - event_date).days) <= 7:
            gpr_level = float(df_gpr.loc[closest_idx, 'GPRD']) if 'GPRD' in df_gpr.columns else 0
            gpr_act = float(df_gpr.loc[closest_idx, 'GPRD_ACT']) if 'GPRD_ACT' in df_gpr.columns else 0
            gpr_threat = float(df_gpr.loc[closest_idx, 'GPRD_THREAT']) if 'GPRD_THREAT' in df_gpr.columns else 0
            n10d = float(df_gpr.loc[closest_idx, 'N10D']) if 'N10D' in df_gpr.columns else 0
        else:
            gpr_level = gpr_act = gpr_threat = n10d = 0
        
        # Format dates
        date_str = event_date.strftime("%Y-%m-%d")
        date_readable = event_date.strftime("%B %d, %Y")
        date_wiki = event_date.strftime("%B_%d,_%Y")
        
        # Generate search queries
        queries = [
            f"{date_readable} news",
            f"geopolitical events {date_readable}",
            f"world events {date_readable}",
            f"major news {date_str}"
        ]
        
        if gpr_act > gpr_threat * 1.2:
            queries.append(f"military action {date_readable}")
            queries.append(f"conflict war {date_readable}")
        elif gpr_threat > gpr_act * 1.2:
            queries.append(f"diplomatic tension {date_readable}")
            queries.append(f"threats sanctions {date_readable}")
        
        if gpr_level > 150:
            queries.append(f"geopolitical crisis {date_readable}")
        
        # Generate links
        wiki_link = f"https://en.wikipedia.org/wiki/{date_wiki}"
        google_search_base = "https://www.google.com/search?q="
        google_queries = [google_search_base + q.replace(' ', '+') for q in queries[:3]]
        
        # Get CAR stats
        event_cars = car_df[car_df['Event'] == event_id]
        btc_car = event_cars[event_cars['Asset'] == 'BTC']['CAR_pct'].values[0] if len(event_cars[event_cars['Asset'] == 'BTC']) > 0 else 0
        gold_car = event_cars[event_cars['Asset'] == 'GOLD']['CAR_pct'].values[0] if len(event_cars[event_cars['Asset'] == 'GOLD']) > 0 else 0
        oil_car = event_cars[event_cars['Asset'] == 'OIL']['CAR_pct'].values[0] if len(event_cars[event_cars['Asset'] == 'OIL']) > 0 else 0
        
        research_data.append({
            'Event': event_id,
            'Date': date_str,
            'Date_Readable': date_readable,
            'GPR_Level': f"{gpr_level:.1f}",
            'GPRD_ACT': f"{gpr_act:.1f}",
            'GPRD_THREAT': f"{gpr_threat:.1f}",
            'N10D': f"{n10d:.0f}",
            'BTC_CAR_%': f"{btc_car:.2f}",
            'GOLD_CAR_%': f"{gold_car:.2f}",
            'OIL_CAR_%': f"{oil_car:.2f}",
            'Wikipedia_Link': wiki_link,
            'Search_Query_1': queries[0] if len(queries) > 0 else '',
            'Search_Query_2': queries[1] if len(queries) > 1 else '',
            'Search_Query_3': queries[2] if len(queries) > 2 else '',
            'Search_Query_4': queries[3] if len(queries) > 3 else '',
            'Google_Link_1': google_queries[0] if len(google_queries) > 0 else '',
            'Google_Link_2': google_queries[1] if len(google_queries) > 1 else '',
            'Google_Link_3': google_queries[2] if len(google_queries) > 2 else '',
            'Suggested_Event_Name': '',
            'Suggested_Region': '',
            'Suggested_Type': '',
            'Confidence': 'Low',
            'Notes': ''
        })
    
    # Save as CSV
    research_df = pd.DataFrame(research_data)
    output_dir = Path('results/event_study')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    csv_path = output_dir / 'events_research_template.csv'
    research_df.to_csv(csv_path, index=False, encoding='utf-8-sig')
    print(f"✓ Saved: {csv_path}")
    print(f"  Total events: {len(research_df)}")
    print()
    print("=" * 80)
    print("RESEARCH TEMPLATE READY!")
    print("=" * 80)
    print()
    print("Cách sử dụng:")
    print("1. Mở file: results/event_study/events_research_template.csv")
    print("2. Click vào Wikipedia_Link để xem events của ngày đó")
    print("3. Click vào Google_Link để search tin tức")
    print("4. Điền vào các cột:")
    print("   - Suggested_Event_Name: Tên sự kiện")
    print("   - Suggested_Region: Europe/Middle East/Asia/Americas/Global")
    print("   - Suggested_Type: War/Political/Economic/Terrorist/Other")
    print("   - Confidence: High/Medium/Low")
    print("   - Notes: Ghi chú thêm")
    print()
    print("Tips:")
    print("- Events có GPR_Level > 150 thường là events lớn")
    print("- ACT > THREAT: có thể là military action")
    print("- THREAT > ACT: có thể là diplomatic tension")
    print("- N10D cao: nhiều tin tức về sự kiện đó")

if __name__ == '__main__':
    generate_research_template()

