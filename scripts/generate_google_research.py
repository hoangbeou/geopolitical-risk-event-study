"""
Generate Google search links và scrape results (nếu được)
Query: "What happened on [Date] geopolitical news"
"""

import pandas as pd
from pathlib import Path
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import time
import urllib.parse

def create_google_search_link(query):
    """Tạo Google search link"""
    encoded_query = urllib.parse.quote_plus(query)
    return f"https://www.google.com/search?q={encoded_query}"

def scrape_google_results(query, max_results=5):
    """
    Thử scrape Google search results
    Warning: Google có thể block requests
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        url = create_google_search_link(query)
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            return []
        
        soup = BeautifulSoup(response.content, 'html.parser')
        results = []
        
        # Tìm search results (Google structure có thể thay đổi)
        for result in soup.find_all('div', class_='g', limit=max_results):
            title_elem = result.find('h3')
            snippet_elem = result.find('span', class_='aCOpRe') or result.find('div', class_='VwiC3b')
            
            if title_elem:
                title = title_elem.get_text(strip=True)
                snippet = snippet_elem.get_text(strip=True) if snippet_elem else ''
                results.append({'title': title, 'snippet': snippet[:200]})
        
        return results
        
    except Exception as e:
        # Silently fail - return empty
        return []

def generate_research_with_google():
    """Generate research template với Google search links và results"""
    print("=" * 80)
    print("GENERATE RESEARCH TEMPLATE WITH GOOGLE SEARCH")
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
    print("Generating Google search links...\n")
    
    # Ask user if they want to scrape (takes time)
    scrape_choice = input("Do you want to scrape Google results? (y/n, default=n): ").lower().strip()
    scrape_results = scrape_choice == 'y'
    
    if scrape_results:
        print("⚠ Warning: Scraping Google may be slow and may get blocked")
        print("   Will add delays between requests...\n")
    
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
        else:
            gpr_level = gpr_act = gpr_threat = 0
        
        # Format dates
        date_str = event_date.strftime("%Y-%m-%d")
        date_readable = event_date.strftime("%B %d, %Y")
        
        # Generate Google search queries
        queries = [
            f"What happened on {date_readable} geopolitical news",
            f"geopolitical events {date_readable}",
            f"major world news {date_readable}",
            f"international crisis {date_readable}"
        ]
        
        # Add specific queries based on ACT/THREAT
        if gpr_act > gpr_threat * 1.2:
            queries.append(f"military action conflict {date_readable}")
        elif gpr_threat > gpr_act * 1.2:
            queries.append(f"diplomatic tension {date_readable}")
        
        # Create Google links
        google_links = [create_google_search_link(q) for q in queries]
        
        # Scrape results if requested
        scraped_results = []
        if scrape_results:
            print(f"[{idx+1}/{len(events)}] Scraping {event_id} ({date_str})...", end=' ', flush=True)
            main_query = queries[0]  # Main query
            results = scrape_google_results(main_query, max_results=3)
            scraped_results = results
            if results:
                print(f"✓ Found {len(results)} results")
            else:
                print("✗ No results (may be blocked)")
            time.sleep(2)  # Be polite to Google
        else:
            print(f"[{idx+1}/{len(events)}] {event_id} ({date_str}) - Links generated")
        
        # Get CAR stats
        event_cars = car_df[car_df['Event'] == event_id]
        btc_car = event_cars[event_cars['Asset'] == 'BTC']['CAR_pct'].values[0] if len(event_cars[event_cars['Asset'] == 'BTC']) > 0 else 0
        gold_car = event_cars[event_cars['Asset'] == 'GOLD']['CAR_pct'].values[0] if len(event_cars[event_cars['Asset'] == 'GOLD']) > 0 else 0
        oil_car = event_cars[event_cars['Asset'] == 'OIL']['CAR_pct'].values[0] if len(event_cars[event_cars['Asset'] == 'OIL']) > 0 else 0
        
        # Format scraped results
        result_text = ""
        if scraped_results:
            result_text = " | ".join([f"{r['title']}: {r['snippet']}" for r in scraped_results])
        
        research_data.append({
            'Event': event_id,
            'Date': date_str,
            'Date_Readable': date_readable,
            'GPR_Level': f"{gpr_level:.1f}",
            'GPRD_ACT': f"{gpr_act:.1f}",
            'GPRD_THREAT': f"{gpr_threat:.1f}",
            'BTC_CAR_%': f"{btc_car:.2f}",
            'GOLD_CAR_%': f"{gold_car:.2f}",
            'OIL_CAR_%': f"{oil_car:.2f}",
            'Google_Link_1': google_links[0] if len(google_links) > 0 else '',
            'Google_Link_2': google_links[1] if len(google_links) > 1 else '',
            'Google_Link_3': google_links[2] if len(google_links) > 2 else '',
            'Google_Link_4': google_links[3] if len(google_links) > 3 else '',
            'Scraped_Results': result_text,
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
    
    csv_path = output_dir / 'events_google_research.csv'
    research_df.to_csv(csv_path, index=False, encoding='utf-8-sig')
    
    print("\n" + "=" * 80)
    print("RESEARCH TEMPLATE READY!")
    print("=" * 80)
    print(f"\n✓ Saved: {csv_path}")
    print(f"  Total events: {len(research_df)}")
    print()
    print("Cách sử dụng:")
    print("1. Mở file: results/event_study/events_google_research.csv")
    print("2. Click vào Google_Link_1 để search: 'What happened on [Date] geopolitical news'")
    print("3. Review Scraped_Results (nếu có)")
    print("4. Click các Google_Link khác để research thêm")
    print("5. Điền vào các cột Suggested_Event_Name, Suggested_Region, Suggested_Type")
    print()
    print("Note: Google scraping có thể không hoạt động (bị block).")
    print("      Nhưng bạn vẫn có thể click vào links để search manually.")

if __name__ == '__main__':
    generate_research_with_google()

