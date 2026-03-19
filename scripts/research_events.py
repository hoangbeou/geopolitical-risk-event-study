"""
Script để research events từ GPR spikes
Kết hợp: Wikipedia scraping + News API + Research template
"""

import pandas as pd
import numpy as np
from pathlib import Path
import json
import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

def get_wikipedia_events(date):
    """
    Lấy events từ Wikipedia bằng API (reliable hơn scraping)
    Returns: list of event descriptions
    """
    try:
        # Wikipedia API approach
        # Format: November_13,_2015
        date_str = date.strftime("%B_%d,_%Y")
        page_title = date_str.replace(' ', '_')
        
        # Use Wikipedia API để lấy page content
        api_url = "https://en.wikipedia.org/api/rest_v1/page/html/" + page_title
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(api_url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            events = []
            
            # Tìm section Events
            for h2 in soup.find_all('h2'):
                if 'Events' in h2.get_text():
                    # Tìm ul sau h2
                    ul = h2.find_next('ul')
                    if ul:
                        for li in ul.find_all('li', recursive=False):
                            text = li.get_text(separator=' ', strip=True)
                            # Remove references
                            import re
                            text = re.sub(r'\[\d+\]', '', text)
                            if text and len(text) > 15:
                                events.append(text)
                    break
            
            if events:
                return events[:10]
        
        # Fallback: Try direct page với better parsing
        page_url = f"https://en.wikipedia.org/wiki/{page_title}"
        response = requests.get(page_url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            events = []
            
            # Tìm Events section
            for span in soup.find_all('span', {'id': lambda x: x and 'Event' in x}):
                heading = span.find_parent(['h2', 'h3'])
                if heading:
                    for ul in heading.find_next_siblings('ul', limit=1):
                        for li in ul.find_all('li', recursive=False):
                            text = li.get_text(separator=' ', strip=True)
                            import re
                            text = re.sub(r'\[\d+\]', '', text)
                            if text and len(text) > 15:
                                events.append(text)
                    break
            
            return events[:10] if events else []
        
        return []
        
    except Exception as e:
        # Silently fail - return empty list
        return []

def get_newsapi_headlines(date, api_key=None):
    """
    Fetch headlines từ NewsAPI
    Requires API key (free tier: 100 requests/day)
    """
    if not api_key:
        return []
    
    try:
        # NewsAPI format: YYYY-MM-DD
        date_str = date.strftime("%Y-%m-%d")
        url = f"https://newsapi.org/v2/everything"
        
        params = {
            'q': 'geopolitical OR conflict OR war OR crisis OR tension',
            'from': date_str,
            'to': date_str,
            'sortBy': 'popularity',
            'language': 'en',
            'pageSize': 5,
            'apiKey': api_key
        }
        
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            headlines = [article['title'] for article in data.get('articles', [])]
            return headlines
        else:
            return []
            
    except Exception as e:
        print(f"  ⚠ Error fetching NewsAPI: {e}")
        return []

def generate_search_queries(date, gpr_level, act_level, threat_level):
    """Generate search queries để research"""
    date_str = date.strftime("%Y-%m-%d")
    date_str_readable = date.strftime("%B %d, %Y")
    
    queries = [
        f"{date_str_readable} news",
        f"geopolitical events {date_str}",
        f"major world events {date_str_readable}",
        f"international crisis {date_str_readable}"
    ]
    
    # Add specific queries based on ACT/THREAT
    if act_level > threat_level * 1.2:  # ACT significantly higher
        queries.extend([
            f"military action {date_str_readable}",
            f"conflict war {date_str_readable}"
        ])
    elif threat_level > act_level * 1.2:  # THREAT significantly higher
        queries.extend([
            f"diplomatic tension {date_str_readable}",
            f"threats sanctions {date_str_readable}"
        ])
    
    # Add high GPR queries
    if gpr_level > 150:
        queries.append(f"major geopolitical crisis {date_str_readable}")
    
    return queries[:6]  # Limit to 6 queries

def research_all_events():
    """Research tất cả events từ event_classification.csv"""
    print("=" * 80)
    print("RESEARCH EVENTS FROM GPR SPIKES")
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
    print("Starting research...\n")
    
    # Research results
    research_results = []
    
    # Check for NewsAPI key (optional)
    newsapi_key = None
    try:
        key_path = Path('newsapi_key.txt')
        if key_path.exists():
            newsapi_key = key_path.read_text().strip()
            print("✓ Found NewsAPI key")
        else:
            print("ℹ No NewsAPI key found (using Wikipedia only)")
    except:
        pass
    
    # Process each event
    for idx, event_row in events.iterrows():
        event_id = event_row['Event']
        event_date = pd.to_datetime(event_row['Date'])
        
        print(f"[{idx+1}/{len(events)}] Researching {event_id} ({event_date.date()})...")
        
        # Get GPR data for this date
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
        
        # Get Wikipedia events (with retry)
        wiki_events = []
        for attempt in range(2):  # Try twice
            wiki_events = get_wikipedia_events(event_date)
            if wiki_events:
                break
            time.sleep(0.5)
        
        # Get NewsAPI headlines (if available)
        news_headlines = []
        if newsapi_key:
            news_headlines = get_newsapi_headlines(event_date, newsapi_key)
            time.sleep(1)  # Rate limiting
        
        # Generate search queries
        search_queries = generate_search_queries(event_date, gpr_level, gpr_act, gpr_threat)
        
        # Store results
        research_results.append({
            'Event': event_id,
            'Date': event_date.strftime('%Y-%m-%d'),
            'GPR_Level': gpr_level,
            'GPRD_ACT': gpr_act,
            'GPRD_THREAT': gpr_threat,
            'N10D': n10d,
            'Wikipedia_Events': ' | '.join(wiki_events[:5]) if wiki_events else '',
            'News_Headlines': ' | '.join(news_headlines[:3]) if news_headlines else '',
            'Search_Queries': ' | '.join(search_queries),
            'Suggested_Event_Name': '',
            'Suggested_Region': '',
            'Suggested_Type': '',
            'Confidence': 'Low'  # To be filled manually
        })
        
        if wiki_events:
            print(f"  ✓ Found {len(wiki_events)} Wikipedia events")
        if news_headlines:
            print(f"  ✓ Found {len(news_headlines)} news headlines")
        print()
    
    # Save results
    output_dir = Path('results/event_study')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save as CSV for easy editing
    research_df = pd.DataFrame(research_results)
    csv_path = output_dir / 'events_research_template.csv'
    research_df.to_csv(csv_path, index=False, encoding='utf-8-sig')
    print(f"✓ Saved research template: {csv_path}")
    
    # Save as JSON for programmatic use
    json_path = output_dir / 'events_research_data.json'
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(research_results, f, indent=2, ensure_ascii=False, default=str)
    print(f"✓ Saved research data: {json_path}")
    
    # Generate summary
    print("\n" + "=" * 80)
    print("RESEARCH SUMMARY")
    print("=" * 80)
    print(f"Total events: {len(research_results)}")
    print(f"Events with Wikipedia data: {sum(1 for r in research_results if r['Wikipedia_Events'])}")
    print(f"Events with News data: {sum(1 for r in research_results if r['News_Headlines'])}")
    print("\nNext steps:")
    print("1. Open events_research_template.csv")
    print("2. Review Wikipedia_Events and News_Headlines columns")
    print("3. Fill in Suggested_Event_Name, Suggested_Region, Suggested_Type")
    print("4. Update Confidence level (High/Medium/Low)")
    print("5. Use Search_Queries for additional research if needed")

if __name__ == '__main__':
    research_all_events()

