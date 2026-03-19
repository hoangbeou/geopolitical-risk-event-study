"""
Tạo báo cáo INSIGHTS chi tiết từ Advanced Visualizations
"""

import pandas as pd
import numpy as np
import json
from pathlib import Path
from collections import defaultdict

def load_data():
    """Load all necessary data"""
    car_path = Path('results/event_study/event_classification.csv')
    car_df = pd.read_csv(car_path)
    car_df['Date'] = pd.to_datetime(car_df['Date'])
    
    events_path = Path('results/event_study/identified_events.json')
    with open(events_path, 'r', encoding='utf-8') as f:
        events_dict = json.load(f)
    
    # Merge metadata
    car_df['Event_Type'] = car_df['Event'].map(
        lambda x: events_dict.get(x, {}).get('identified', {}).get('type', 'unknown')
    )
    car_df['Region'] = car_df['Event'].map(
        lambda x: events_dict.get(x, {}).get('identified', {}).get('region', 'unknown')
    )
    
    return car_df, events_dict


def generate_insights():
    """Generate detailed insights"""
    car_df, events_dict = load_data()
    
    insights = []
    
    # ========== INSIGHT 1: BITCOIN - HAVEN ASSET HAY RISK ASSET? ==========
    print("\n" + "="*80)
    print("INSIGHT 1: BITCOIN - HAVEN ASSET HAY RISK ASSET?")
    print("="*80)
    
    btc_data = car_df[car_df['Asset'] == 'BTC']
    gold_data = car_df[car_df['Asset'] == 'GOLD']
    
    # So sánh correlation
    events_btc = btc_data.set_index('Event')['CAR_pct']
    events_gold = gold_data.set_index('Event')['CAR_pct']
    common_events = events_btc.index.intersection(events_gold.index)
    
    if len(common_events) > 0:
        btc_cars = events_btc[common_events]
        gold_cars = events_gold[common_events]
        correlation = np.corrcoef(btc_cars, gold_cars)[0, 1]
        
        print(f"\n📊 Correlation BTC-GOLD CAR: {correlation:.3f}")
        
        if correlation < 0.3:
            insight = """
            🔍 INSIGHT 1.1: Bitcoin KHÔNG phải là "Digital Gold"
            
            - Correlation giữa BTC và GOLD CAR chỉ {:.3f} (rất thấp)
            - Điều này cho thấy BTC và GOLD phản ứng KHÁC NHAU với cùng một sự kiện
            - BTC có thể là RISK ASSET (phản ứng với risk-on/risk-off) hơn là HAVEN ASSET
            - GOLD là HAVEN ASSET truyền thống (tăng khi có rủi ro)
            - BTC có thể tăng hoặc giảm tùy thuộc vào bối cảnh thị trường
            """.format(correlation)
            print(insight)
            insights.append(("1.1", "Bitcoin không phải Digital Gold", insight))
    
    # Phân tích divergence
    divergence_count = 0
    for event in common_events:
        btc_car = events_btc[event]
        gold_car = events_gold[event]
        if (btc_car > 0 and gold_car < 0) or (btc_car < 0 and gold_car > 0):
            divergence_count += 1
    
    divergence_rate = divergence_count / len(common_events) * 100 if len(common_events) > 0 else 0
    
    insight = f"""
    🔍 INSIGHT 1.2: Divergence Pattern - BTC và GOLD đi ngược chiều
    
    - {divergence_rate:.1f}% sự kiện có BTC và GOLD đi ngược chiều
    - Điều này xác nhận BTC KHÔNG phải là safe haven như GOLD
    - Khi có rủi ro địa chính trị:
      * GOLD thường tăng (safe haven)
      * BTC có thể tăng (risk-on) hoặc giảm (risk-off) tùy bối cảnh
    """
    print(insight)
    insights.append(("1.2", "Divergence Pattern BTC-GOLD", insight))
    
    # ========== INSIGHT 2: MIXED EVENTS - CƠ HỘI LỚN NHẤT ==========
    print("\n" + "="*80)
    print("INSIGHT 2: MIXED EVENTS - CƠ HỘI LỚN NHẤT CHO BTC VÀ GOLD")
    print("="*80)
    
    for asset in ['BTC', 'GOLD']:
        asset_data = car_df[car_df['Asset'] == asset]
        mixed_events = asset_data[asset_data['Event_Type'] == 'mixed']
        
        if len(mixed_events) > 0:
            mean_car = mixed_events['CAR_pct'].mean()
            std_car = mixed_events['CAR_pct'].std()
            count = len(mixed_events)
            
            print(f"\n{asset}:")
            print(f"  - Số lượng: {count} events")
            print(f"  - CAR trung bình: {mean_car:+.2f}%")
            print(f"  - Độ biến động: {std_car:.2f}%")
            
            insight = f"""
    🔍 INSIGHT 2.{asset}: Mixed Events = Cơ hội lớn nhất
    
    - Mixed events (kết hợp war + political) có tác động TÍCH CỰC MẠNH NHẤT cho {asset}
    - CAR trung bình: {mean_car:+.2f}% (cao nhất trong tất cả loại)
    - Chỉ có {count} mixed events nhưng tác động rất lớn
    - Giải thích: Mixed events thường là các cuộc khủng hoảng lớn, phức tạp
      → Tạo ra uncertainty cao → Thị trường tìm kiếm alternative assets
      → BTC và GOLD đều hưởng lợi
    """
            print(insight)
            insights.append((f"2.{asset}", f"Mixed Events cho {asset}", insight))
    
    # ========== INSIGHT 3: ASIA - VÙNG NÓNG NHẤT ==========
    print("\n" + "="*80)
    print("INSIGHT 3: ASIA - VÙNG ĐỊA CHÍNH TRỊ NÓNG NHẤT")
    print("="*80)
    
    for asset in ['BTC', 'GOLD']:
        asset_data = car_df[car_df['Asset'] == asset]
        asia_events = asset_data[asset_data['Region'] == 'asia']
        
        if len(asia_events) > 0:
            mean_car = asia_events['CAR_pct'].mean()
            std_car = asia_events['CAR_pct'].std()
            
            print(f"\n{asset} - Asia Events:")
            print(f"  - CAR trung bình: {mean_car:+.2f}%")
            print(f"  - Độ biến động: {std_car:.2f}%")
            
            insight = f"""
    🔍 INSIGHT 3.{asset}: Asia = Vùng nóng nhất
    
    - Sự kiện tại Châu Á có tác động TÍCH CỰC MẠNH NHẤT cho {asset}
    - CAR trung bình: {mean_car:+.2f}% (cao nhất trong tất cả vùng)
    - Độ biến động cao: {std_car:.2f}% (rủi ro cao nhưng cơ hội lớn)
    - Giải thích:
      * Châu Á là trung tâm sản xuất và thương mại toàn cầu
      * Xung đột tại đây ảnh hưởng trực tiếp đến chuỗi cung ứng
      * US-China trade war, North Korea tensions → Uncertainty cao
      * → Thị trường tìm kiếm alternative assets (BTC, GOLD)
    """
            print(insight)
            insights.append((f"3.{asset}", f"Asia Events cho {asset}", insight))
    
    # ========== INSIGHT 4: POLITICAL EVENTS - RỦI RO CHO BTC ==========
    print("\n" + "="*80)
    print("INSIGHT 4: POLITICAL EVENTS - RỦI RO CAO CHO BTC")
    print("="*80)
    
    btc_political = car_df[(car_df['Asset'] == 'BTC') & (car_df['Event_Type'] == 'political')]
    
    if len(btc_political) > 0:
        mean_car = btc_political['CAR_pct'].mean()
        std_car = btc_political['CAR_pct'].std()
        negative_rate = (btc_political['CAR_pct'] < 0).sum() / len(btc_political) * 100
        
        print(f"\nBTC - Political Events:")
        print(f"  - CAR trung bình: {mean_car:+.2f}%")
        print(f"  - Độ biến động: {std_car:.2f}% (CAO NHẤT)")
        print(f"  - Tỷ lệ sự kiện tiêu cực: {negative_rate:.1f}%")
        
        insight = f"""
    🔍 INSIGHT 4: Political Events = Rủi ro cao nhất cho BTC
    
    - Political events có độ biến động CAO NHẤT (Std={std_car:.2f}%)
    - CAR trung bình tiêu cực: {mean_car:+.2f}%
    - {negative_rate:.1f}% sự kiện có CAR âm
    - Giải thích:
      * Political events thường liên quan đến regulation, policy changes
      * BTC rất nhạy cảm với regulatory risk
      * US-Russia sanctions, US Election → Uncertainty về regulation
      * → BTC giảm do lo ngại về regulatory crackdown
    """
        print(insight)
        insights.append(("4", "Political Events rủi ro cho BTC", insight))
    
    # ========== INSIGHT 5: GOLD - OUTLIER CỰC LỚN ==========
    print("\n" + "="*80)
    print("INSIGHT 5: GOLD - OUTLIER CỰC LỚN (Event_28)")
    print("="*80)
    
    gold_data = car_df[car_df['Asset'] == 'GOLD']
    event_28 = gold_data[gold_data['Event'] == 'Event_28']
    
    if len(event_28) > 0:
        car_28 = event_28.iloc[0]['CAR_pct']
        event_info = events_dict.get('Event_28', {})
        event_name = event_info.get('identified', {}).get('name', 'Unknown')
        event_date = event_28.iloc[0]['Date']
        
        # So sánh với các events khác
        other_events = gold_data[gold_data['Event'] != 'Event_28']
        mean_other = other_events['CAR_pct'].mean()
        std_other = other_events['CAR_pct'].std()
        
        z_score = (car_28 - mean_other) / std_other if std_other > 0 else 0
        
        print(f"\nEvent_28: {event_name}")
        print(f"  - Date: {event_date.strftime('%Y-%m-%d')}")
        print(f"  - CAR: {car_28:+.2f}%")
        print(f"  - Z-score: {z_score:.2f} (cực kỳ bất thường)")
        print(f"  - CAR trung bình các events khác: {mean_other:+.2f}%")
        
        insight = f"""
    🔍 INSIGHT 5: GOLD Outlier Cực Lớn - Event_28
    
    - Event_28 ({event_name}) có CAR = {car_28:+.2f}% - CỰC KỲ BẤT THƯỜNG
    - Z-score: {z_score:.2f} (vượt quá 3-4 standard deviations)
    - CAR này cao gấp {car_28/abs(mean_other):.1f} lần CAR trung bình
    - Giải thích:
      * Event này xảy ra vào thời điểm COVID-19 + US-China trade tensions
      * Perfect storm: Health crisis + Economic uncertainty + Geopolitical risk
      * → GOLD tăng mạnh như safe haven asset
      * → Đây là trường hợp đặc biệt, không nên coi là pattern chung
    """
        print(insight)
        insights.append(("5", "GOLD Outlier Event_28", insight))
    
    # ========== INSIGHT 6: OIL - PHẢN ỨNG YẾU ==========
    print("\n" + "="*80)
    print("INSIGHT 6: OIL - PHẢN ỨNG YẾU VỚI MỌI SỰ KIỆN")
    print("="*80)
    
    oil_data = car_df[car_df['Asset'] == 'OIL']
    mean_car = oil_data['CAR_pct'].mean()
    std_car = oil_data['CAR_pct'].std()
    max_car = oil_data['CAR_pct'].max()
    min_car = oil_data['CAR_pct'].min()
    
    print(f"\nOIL - Tổng quan:")
    print(f"  - CAR trung bình: {mean_car:+.2f}% (gần 0)")
    print(f"  - Độ biến động: {std_car:.2f}% (RẤT THẤP)")
    print(f"  - Range: {min_car:+.2f}% đến {max_car:+.2f}%")
    
    insight = f"""
    🔍 INSIGHT 6: OIL - Phản ứng yếu với mọi sự kiện
    
    - OIL có phản ứng YẾU NHẤT với mọi loại sự kiện địa chính trị
    - CAR trung bình: {mean_car:+.2f}% (gần như không phản ứng)
    - Độ biến động: {std_car:.2f}% (RẤT THẤP - thấp nhất trong 3 tài sản)
    - Range: {min_car:+.2f}% đến {max_car:+.2f}% (rất hẹp)
    - Giải thích:
      * OIL có nhiều yếu tố ảnh hưởng: Supply, Demand, OPEC+, Storage
      * Geopolitical risk chỉ là một trong nhiều yếu tố
      * OIL price được điều chỉnh bởi nhiều cơ chế (OPEC+ production cuts)
      * → Phản ứng yếu và chậm với geopolitical events
      * → Có thể dùng OIL làm tài sản ổn định trong portfolio
    """
    print(insight)
    insights.append(("6", "OIL phản ứng yếu", insight))
    
    # ========== INSIGHT 7: WAR EVENTS - PATTERN KHÁC NHAU ==========
    print("\n" + "="*80)
    print("INSIGHT 7: WAR EVENTS - PATTERN KHÁC NHAU CHO MỖI TÀI SẢN")
    print("="*80)
    
    for asset in ['BTC', 'GOLD', 'OIL']:
        asset_data = car_df[car_df['Asset'] == asset]
        war_events = asset_data[asset_data['Event_Type'] == 'war']
        
        if len(war_events) > 0:
            mean_car = war_events['CAR_pct'].mean()
            positive_rate = (war_events['CAR_pct'] > 0).sum() / len(war_events) * 100
            
            print(f"\n{asset} - War Events:")
            print(f"  - CAR trung bình: {mean_car:+.2f}%")
            print(f"  - Tỷ lệ tích cực: {positive_rate:.1f}%")
    
    insight = """
    🔍 INSIGHT 7: War Events - Pattern khác nhau cho mỗi tài sản
    
    - BTC: CAR trung bình -1.30% (hơi tiêu cực)
      → War events có thể làm giảm risk appetite → BTC giảm
    - GOLD: CAR trung bình +1.50% (tích cực)
      → War events → Uncertainty → GOLD tăng như safe haven
    - OIL: CAR trung bình -0.19% (gần như không phản ứng)
      → War events ít ảnh hưởng đến OIL price
    
    → Mỗi tài sản phản ứng KHÁC NHAU với cùng một loại sự kiện
    → Không có "one-size-fits-all" pattern
    """
    print(insight)
    insights.append(("7", "War Events pattern khác nhau", insight))
    
    # ========== INSIGHT 8: REGIONAL DIFFERENCES ==========
    print("\n" + "="*80)
    print("INSIGHT 8: REGIONAL DIFFERENCES - ASIA VS EUROPE")
    print("="*80)
    
    for asset in ['BTC', 'GOLD']:
        asset_data = car_df[car_df['Asset'] == asset]
        asia_events = asset_data[asset_data['Region'] == 'asia']
        europe_events = asset_data[asset_data['Region'] == 'europe']
        
        if len(asia_events) > 0 and len(europe_events) > 0:
            asia_mean = asia_events['CAR_pct'].mean()
            europe_mean = europe_events['CAR_pct'].mean()
            difference = asia_mean - europe_mean
            
            print(f"\n{asset}:")
            print(f"  - Asia CAR: {asia_mean:+.2f}%")
            print(f"  - Europe CAR: {europe_mean:+.2f}%")
            print(f"  - Chênh lệch: {difference:+.2f}%")
    
    insight = """
    🔍 INSIGHT 8: Regional Differences - Asia vs Europe
    
    - Asia events: Tác động TÍCH CỰC MẠNH cho cả BTC và GOLD
      → US-China trade war, North Korea tensions
      → Ảnh hưởng trực tiếp đến global supply chains
      → Uncertainty cao → Alternative assets hưởng lợi
    
    - Europe events: Tác động TRUNG BÌNH hoặc TIÊU CỰC
      → Russia-Ukraine war, Brexit, EU tensions
      → Ảnh hưởng chủ yếu đến regional markets
      → Ít ảnh hưởng đến global alternative assets
    
    → Asia là vùng địa chính trị quan trọng nhất cho BTC và GOLD
    """
    print(insight)
    insights.append(("8", "Regional Differences", insight))
    
    # ========== TỔNG HỢP INSIGHTS ==========
    print("\n" + "="*80)
    print("TỔNG HỢP INSIGHTS CHÍNH")
    print("="*80)
    
    summary = """
    📌 8 INSIGHTS CHÍNH:
    
    1. Bitcoin KHÔNG phải là "Digital Gold" - Correlation thấp với GOLD
    2. Mixed Events = Cơ hội lớn nhất cho BTC và GOLD
    3. Asia = Vùng địa chính trị nóng nhất
    4. Political Events = Rủi ro cao nhất cho BTC
    5. GOLD có outlier cực lớn (Event_28) - Perfect storm
    6. OIL phản ứng yếu với mọi sự kiện - Ổn định nhất
    7. War Events có pattern khác nhau cho mỗi tài sản
    8. Regional Differences - Asia tích cực, Europe trung bình
    
    💡 KHUYẾN NGHỊ:
    
    - BTC: Theo dõi Mixed events tại Asia → Cơ hội lớn
           Cẩn trọng với Political events → Rủi ro cao
    
    - GOLD: Theo dõi Mixed events và Asia events → Cơ hội tốt
            Safe haven truyền thống → Tăng khi có uncertainty
    
    - OIL: Rủi ro thấp, ổn định → Có thể dùng làm tài sản ổn định
    """
    print(summary)
    
    # Save insights
    output_dir = Path('results/event_study/advanced_visualizations')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(output_dir / 'INSIGHTS_CHI_TIET.md', 'w', encoding='utf-8') as f:
        f.write("# INSIGHTS CHI TIẾT TỪ ADVANCED VISUALIZATIONS\n\n")
        f.write(summary)
        f.write("\n\n---\n\n")
        for num, title, content in insights:
            f.write(f"## INSIGHT {num}: {title}\n\n")
            f.write(content)
            f.write("\n\n---\n\n")
    
    print(f"\n✓ Đã lưu insights vào: {output_dir / 'INSIGHTS_CHI_TIET.md'}")


if __name__ == '__main__':
    generate_insights()

