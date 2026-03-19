"""
Script để phân loại region từ Wiki_Content đã scrape được
"""
import pandas as pd
import re
from collections import Counter

# Định nghĩa các từ khóa cho từng region
REGION_KEYWORDS = {
    'Middle East': [
        'yemen', 'saudi arabia', 'iran', 'iraq', 'syria', 'israel', 'palestine', 
        'gaza', 'lebanon', 'jordan', 'kuwait', 'qatar', 'uae', 'bahrain', 
        'oman', 'houthi', 'hezbollah', 'israeli', 'palestinian', 'sanaa',
        'aden', 'baghdad', 'damascus', 'tel aviv', 'jerusalem', 'beirut',
        'middle east', 'gulf', 'persian gulf', 'red sea', 'sinai'
    ],
    'Europe': [
        'france', 'paris', 'brussels', 'belgium', 'germany', 'uk', 'london',
        'spain', 'italy', 'greece', 'poland', 'ukraine', 'russia', 'nato',
        'european', 'eu', 'europe', 'charleville', 'grenoble', 'toulouse',
        'bobigny', 'warsaw', 'rzeszów', 'lublin', 'kiev', 'kyiv', 'moscow'
    ],
    'Africa': [
        'nigeria', 'boko haram', 'borno', 'yobe', 'baga', 'burkina faso',
        'ouagadougou', 'somalia', 'mogadishu', 'al-shabab', 'africa', 'african',
        'niger', 'mali', 'chad', 'cameroon', 'libya', 'egypt', 'cairo'
    ],
    'Asia': [
        'china', 'india', 'pakistan', 'afghanistan', 'philippines', 'filipino',
        'abu sayyaf', 'nepal', 'kathmandu', 'asia', 'asian', 'south asia',
        'southeast asia', 'east asia', 'central asia', 'bangladesh', 'sri lanka',
        'myanmar', 'thailand', 'vietnam', 'indonesia', 'malaysia'
    ],
    'Americas': [
        'usa', 'united states', 'us', 'america', 'american', 'alabama', 'arizona',
        'arkansas', 'florida', 'georgia', 'texas', 'california', 'new york',
        'washington', 'canada', 'mexico', 'brazil', 'argentina', 'chile',
        'colombia', 'venezuela', 'north america', 'south america', 'latin america'
    ],
    'Russia/CIS': [
        'russia', 'russian', 'moscow', 'putin', 'kremlin', 'cis', 'belarus',
        'kazakhstan', 'uzbekistan', 'tajikistan', 'kyrgyzstan', 'armenia',
        'azerbaijan', 'georgia', 'moldova', 'ukraine', 'kiev', 'kyiv'
    ]
}

def classify_region_from_text(text):
    """
    Phân loại region từ text dựa trên keywords
    Trả về region chính và các region phụ (nếu có nhiều)
    """
    if pd.isna(text) or text == '':
        return 'UNKNOWN', []
    
    text_lower = text.lower()
    
    # Đếm số lần xuất hiện của mỗi region
    region_scores = {}
    for region, keywords in REGION_KEYWORDS.items():
        score = 0
        for keyword in keywords:
            # Tìm keyword trong text (word boundary để tránh match sai)
            pattern = r'\b' + re.escape(keyword.lower()) + r'\b'
            matches = len(re.findall(pattern, text_lower))
            score += matches
        
        if score > 0:
            region_scores[region] = score
    
    if not region_scores:
        return 'UNKNOWN', []
    
    # Sắp xếp theo score
    sorted_regions = sorted(region_scores.items(), key=lambda x: x[1], reverse=True)
    
    # Region chính là region có score cao nhất
    primary_region = sorted_regions[0][0]
    
    # Các region phụ là các region có score > 0 và khác primary
    secondary_regions = [r[0] for r in sorted_regions[1:] if r[1] > 0]
    
    # Nếu có nhiều region với score cao, có thể là MULTI_REGION
    if len(sorted_regions) > 1 and sorted_regions[1][1] >= sorted_regions[0][1] * 0.7:
        # Nếu region thứ 2 có score gần bằng region thứ 1
        return 'MULTI_REGION', [r[0] for r in sorted_regions[:3] if r[1] > 0]
    
    return primary_region, secondary_regions

def main():
    # Đọc file CSV
    input_file = 'ket_qua_wiki_final_clean.csv'
    output_file = 'ket_qua_wiki_with_regions.csv'
    
    print(f"Đang đọc file: {input_file}")
    df = pd.read_csv(input_file)
    
    print(f"Tổng số events: {len(df)}")
    print("\nĐang phân loại regions...")
    
    # Phân loại region cho mỗi event
    regions = []
    secondary_regions_list = []
    
    for idx, row in df.iterrows():
        wiki_content = row['Wiki_Content']
        primary, secondary = classify_region_from_text(wiki_content)
        regions.append(primary)
        secondary_regions_list.append(', '.join(secondary) if secondary else '')
        
        if (idx + 1) % 10 == 0:
            print(f"  Đã xử lý {idx + 1}/{len(df)} events")
    
    # Thêm cột Region vào dataframe
    df['Region'] = regions
    df['Secondary_Regions'] = secondary_regions_list
    
    # Thống kê phân bố
    print("\n" + "="*60)
    print("PHÂN BỐ REGIONS:")
    print("="*60)
    region_counts = Counter(regions)
    for region, count in region_counts.most_common():
        pct = count / len(df) * 100
        print(f"  {region:20s}: {count:3d} events ({pct:5.1f}%)")
    
    # Lưu kết quả
    df.to_csv(output_file, index=False)
    print(f"\n✓ Đã lưu kết quả vào: {output_file}")
    
    # Hiển thị một vài ví dụ
    print("\n" + "="*60)
    print("MỘT VÀI VÍ DỤ:")
    print("="*60)
    for idx in range(min(5, len(df))):
        row = df.iloc[idx]
        print(f"\nEvent {row['Event_Number']} ({row['Date']}):")
        print(f"  Region: {row['Region']}")
        if row['Secondary_Regions']:
            print(f"  Secondary: {row['Secondary_Regions']}")
        print(f"  Preview: {row['Wiki_Content'][:100]}...")

if __name__ == '__main__':
    main()

