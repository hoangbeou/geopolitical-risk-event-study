"""
Enrich detected events with Wikipedia current-events content and extracted locations.

Usage:
    python -u scripts/enrich_events_with_locations.py \
        --input results/event_study/detected_events_with_car.csv \
        --output results/event_study/detected_events_with_locations.csv \
        --date-col Date

Notes:
- Tries to use spaCy en_core_web_sm to extract GPE entities; if not available, falls back
  to a simple regex-based heuristic (less accurate).
- Scrapes the Wikipedia Current Events portal for each date:
    https://en.wikipedia.org/wiki/Portal:Current_events/{YEAR}_{Month}_{DAY}
"""

import argparse
import random
import re
import time
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup

# Optional: spaCy for better location extraction
try:
    import spacy

    try:
        nlp = spacy.load("en_core_web_sm")
        SPACY_AVAILABLE = True
    except Exception:
        SPACY_AVAILABLE = False
        nlp = None
except ImportError:
    SPACY_AVAILABLE = False
    nlp = None

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    )
}

# List of countries and major regions for location filtering
KNOWN_LOCATIONS = {
    # Countries
    'Afghanistan', 'Albania', 'Algeria', 'Argentina', 'Armenia', 'Australia', 'Austria', 'Azerbaijan',
    'Bahrain', 'Bangladesh', 'Belarus', 'Belgium', 'Bolivia', 'Bosnia', 'Brazil', 'Bulgaria',
    'Cambodia', 'Cameroon', 'Canada', 'Chad', 'Chile', 'China', 'Colombia', 'Congo', 'Croatia', 'Cuba', 'Cyprus',
    'Denmark', 'Ecuador', 'Egypt', 'Estonia', 'Ethiopia', 'Finland', 'France',
    'Georgia', 'Germany', 'Ghana', 'Greece', 'Guatemala', 'Haiti', 'Honduras', 'Hungary',
    'Iceland', 'India', 'Indonesia', 'Iran', 'Iraq', 'Ireland', 'Israel', 'Italy',
    'Japan', 'Jordan', 'Kazakhstan', 'Kenya', 'Korea', 'Kosovo', 'Kuwait', 'Kyrgyzstan',
    'Latvia', 'Lebanon', 'Libya', 'Lithuania', 'Luxembourg',
    'Macedonia', 'Malaysia', 'Mali', 'Malta', 'Mexico', 'Moldova', 'Mongolia', 'Montenegro', 'Morocco', 'Myanmar',
    'Nepal', 'Netherlands', 'Nigeria', 'Norway',
    'Pakistan', 'Palestine', 'Panama', 'Peru', 'Philippines', 'Poland', 'Portugal',
    'Qatar', 'Romania', 'Russia', 'Rwanda',
    'Saudi Arabia', 'Senegal', 'Serbia', 'Singapore', 'Slovakia', 'Slovenia', 'Somalia', 'Spain', 'Sudan', 'Sweden', 'Switzerland', 'Syria',
    'Taiwan', 'Tajikistan', 'Tanzania', 'Thailand', 'Tunisia', 'Turkey', 'Turkmenistan',
    'Uganda', 'Ukraine', 'United Arab Emirates', 'United Kingdom', 'United States', 'Uruguay', 'Uzbekistan',
    'Venezuela', 'Vietnam', 'Yemen', 'Zimbabwe',
    # Major cities often mentioned
    'Baghdad', 'Kabul', 'Damascus', 'Tehran', 'Jerusalem', 'Gaza', 'Aleppo', 'Mosul', 'Tripoli', 'Benghazi',
    'Kyiv', 'Kiev', 'Donetsk', 'Crimea', 'Donbas', 'Mariupol',
    # Regions
    'Middle East', 'Eastern Europe', 'Western Europe', 'Central Asia', 'Southeast Asia', 'South Asia',
    'North Africa', 'Sub-Saharan Africa', 'Latin America', 'Caribbean',
    'Balkans', 'Caucasus', 'Persian Gulf', 'Arabian Peninsula',
    # Conflict zones
    'Kashmir', 'Nagorno-Karabakh', 'Chechnya', 'Dagestan', 'Sinai', 'Golan Heights',
    'West Bank', 'Gaza Strip', 'Kurdistan', 'Xinjiang', 'Tibet'
}


def parse_args():
    parser = argparse.ArgumentParser(description="Enrich events with wiki content and locations")
    parser.add_argument("--input", type=str, default="results/detected_events.csv")
    parser.add_argument("--output", type=str, default="results/detected_events_enriched.csv")
    parser.add_argument("--date-col", type=str, default="date")
    parser.add_argument("--sleep-min", type=float, default=0.5)
    parser.add_argument("--sleep-max", type=float, default=1.5)
    return parser.parse_args()


def parse_flexible_date(date_str: str):
    date_str = str(date_str).strip()
    formats = ["%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", "%Y/%m/%d"]
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return None


def get_wiki_content(url: str) -> tuple:
    """
    Fetch 'Armed conflicts and attacks' section.
    Returns: (content, has_armed_conflicts_section)
    """
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        if resp.status_code == 404:
            return "Link không tồn tại", False
        if resp.status_code != 200:
            return f"Lỗi HTTP: {resp.status_code}", False
        soup = BeautifulSoup(resp.content, "html.parser")

        target_text_node = soup.find(string="Armed conflicts and attacks")
        if not target_text_node:
            return "Không có mục Armed conflicts", False

        main_ul = target_text_node.parent.find_next("ul")
        if not main_ul:
            return "Có tiêu đề nhưng không có nội dung", False

        result_text = ""
        for li in main_ul.find_all("li", recursive=False):
            parent_text_parts = []
            for child in li.contents:
                if getattr(child, "name", None) not in ["ul", "dl"]:
                    text = child.get_text(separator=" ", strip=True) if hasattr(child, "get_text") else str(child).strip()
                    if text:
                        parent_text_parts.append(text)
            full_parent_text = " ".join(parent_text_parts)
            result_text += f"• {full_parent_text}\n"

            sub_ul = li.find("ul")
            if sub_ul:
                for sub_li in sub_ul.find_all("li"):
                    child_text = sub_li.get_text(separator=" ", strip=True)
                    result_text += f"   - {child_text}\n"
            result_text += "\n"

        return result_text.strip(), True
    except Exception as e:
        return f"Lỗi cào: {e}", False


def get_wiki_content_flexible(date_obj: datetime, max_days_back: int = 7) -> tuple:
    """
    Try to get wiki content from date_obj, then -1, -2, ... -max_days_back days until Armed conflicts found.
    Returns: (content, actual_date_used, has_armed_conflicts)
    """
    from datetime import timedelta
    
    # Try dates in order: 0, -1, -2, ..., -max_days_back
    for offset in range(0, -max_days_back - 1, -1):
        try_date = date_obj + timedelta(days=offset)
        url_suffix = f"{try_date.year}_{try_date.strftime('%B')}_{try_date.day}"
        url = f"https://en.wikipedia.org/wiki/Portal:Current_events/{url_suffix}"
        
        content, has_armed = get_wiki_content(url)
        
        # If found Armed conflicts section, return immediately
        if has_armed:
            return content, try_date, True
    
    # If no Armed conflicts found in any date, return last attempt
    return content, try_date, False


def extract_locations_spacy(text: str):
    if not SPACY_AVAILABLE or nlp is None:
        return None
    doc = nlp(text)
    locs = [ent.text for ent in doc.ents if ent.label_ == "GPE"]
    return ", ".join(sorted(set(locs)))


def extract_locations_regex(text: str):
    """Fallback: Extract locations using known countries/regions list."""
    if pd.isna(text) or text == "":
        return ""
    
    text_str = str(text)
    found_locations = []
    
    # Check for known locations in text
    for location in KNOWN_LOCATIONS:
        # Use word boundary to avoid partial matches
        pattern = r'\b' + re.escape(location) + r'\b'
        if re.search(pattern, text_str, re.IGNORECASE):
            found_locations.append(location)
    
    # Remove duplicates and sort
    unique_locations = sorted(set(found_locations))
    return ", ".join(unique_locations)


def extract_event_name(text: str) -> str:
    """Extract event name/summary from wiki content (first meaningful sentence)."""
    if pd.isna(text) or text == "":
        return ""
    
    # Remove error messages
    if any(x in text for x in ["Link không tồn tại", "Lỗi HTTP", "Không có mục", "Lỗi cào"]):
        return ""
    
    # Get first bullet point (main event)
    lines = text.split('\n')
    for line in lines:
        line = line.strip()
        if line.startswith('•'):
            # Remove bullet and clean
            event_text = line.replace('•', '').strip()
            # Take first sentence (up to period or max 150 chars)
            if '.' in event_text:
                first_sentence = event_text.split('.')[0] + '.'
            else:
                first_sentence = event_text[:150] + '...' if len(event_text) > 150 else event_text
            return first_sentence
    
    # Fallback: take first 150 chars
    clean_text = text.replace('•', '').replace('-', '').strip()
    return clean_text[:150] + '...' if len(clean_text) > 150 else clean_text


def main():
    args = parse_args()
    input_path = Path(args.input)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Đang đọc file '{input_path}'...")
    df = pd.read_csv(input_path, dtype=str)
    if args.date_col not in df.columns:
        raise SystemExit(f"Không tìm thấy cột '{args.date_col}'")

    results_content = []
    results_locations = []
    results_event_names = []
    results_actual_dates = []
    results_has_armed = []

    total = len(df)
    for idx, row in df.iterrows():
        raw_date = row[args.date_col]
        date_obj = parse_flexible_date(raw_date)
        if not date_obj:
            print(f"❌ Dòng {idx+1}: Ngày '{raw_date}' lỗi.")
            results_content.append("Lỗi ngày tháng")
            results_locations.append("")
            results_event_names.append("")
            results_actual_dates.append("")
            results_has_armed.append(False)
            continue

        print(f"[{idx+1}/{total}] {date_obj.strftime('%d/%m/%Y')} -> Trying flexible dates...")

        # Try flexible date scraping (0, -1, -2 days)
        content, actual_date, has_armed = get_wiki_content_flexible(date_obj)
        
        if has_armed:
            days_back = (date_obj - actual_date).days
            if days_back > 0:
                print(f"  ✓ Found Armed conflicts at {actual_date.strftime('%d/%m/%Y')} (-{days_back} days)")
            else:
                print(f"  ✓ Found Armed conflicts at {actual_date.strftime('%d/%m/%Y')}")
        else:
            print(f"  ⚠ No Armed conflicts found (tried 0 to -7 days)")
        
        results_content.append(content)
        results_actual_dates.append(actual_date.strftime('%Y-%m-%d'))
        results_has_armed.append(has_armed)

        # Extract event name
        event_name = extract_event_name(content)
        results_event_names.append(event_name)

        # Extract locations
        if isinstance(content, str) and content.startswith("Lỗi cào"):
            locations = ""
        else:
            locations = extract_locations_spacy(content)
            if locations is None:
                locations = extract_locations_regex(content)
        results_locations.append(locations)

        time.sleep(random.uniform(args.sleep_min, args.sleep_max))

    df["Event_Name"] = results_event_names
    df["Wiki_Content"] = results_content
    df["Detected_Locations"] = results_locations
    df["Wiki_Scraped_Date"] = results_actual_dates
    df["Has_Armed_Conflicts"] = results_has_armed
    df.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"\n✅ XONG! File: {output_path}")
    if not SPACY_AVAILABLE:
        print("Lưu ý: spaCy không khả dụng, dùng regex fallback (độ chính xác thấp hơn).")


if __name__ == "__main__":
    main()

