import pandas as pd

events = pd.read_csv('ket_qua_wiki_with_regions.csv')
events['Date'] = pd.to_datetime(events['Date'])

car = pd.read_csv('results/event_study/detected_events_with_car.csv')
car['Date'] = pd.to_datetime(car['Date'])

merged = pd.merge(events[['Date', 'Region']], car[['Date', 'CAR_BTC', 'CAR_GOLD', 'CAR_OIL']], on='Date')
df = merged[~merged['Region'].isin(['UNKNOWN', 'MULTI_REGION'])].copy()

results = []
for region in sorted(df['Region'].unique()):
    r_data = df[df['Region'] == region]
    if len(r_data) < 2:
        continue
    btc = r_data['CAR_BTC'].dropna()
    gold = r_data['CAR_GOLD'].dropna()
    oil = r_data['CAR_OIL'].dropna()
    if len(btc) > 0 and len(gold) > 0 and len(oil) > 0:
        results.append({
            'Region': region,
            'N': len(r_data),
            'BTC': btc.mean() * 100,
            'GOLD': gold.mean() * 100,
            'OIL': oil.mean() * 100
        })

results_df = pd.DataFrame(results).sort_values('N', ascending=False)

print("\n| Region | N Events | BTC CAR | GOLD CAR | OIL CAR |")
print("|--------|----------|---------|----------|---------|")
for _, r in results_df.iterrows():
    print(f"| {r['Region']} | {int(r['N'])} | {r['BTC']:.2f}% | {r['GOLD']:.2f}% | {r['OIL']:.2f}% |")

