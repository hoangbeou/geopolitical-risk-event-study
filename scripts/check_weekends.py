"""Kiểm tra xem file optimized có còn ngày cuối tuần không"""
import pandas as pd

df = pd.read_csv('data/data_optimized.csv', index_col=0)
df.index = pd.to_datetime(df.index, format='%d/%m/%Y')

weekday_nums = df.index.weekday
print('Weekday distribution:')
print('Mon (0):', (weekday_nums == 0).sum())
print('Tue (1):', (weekday_nums == 1).sum())
print('Wed (2):', (weekday_nums == 2).sum())
print('Thu (3):', (weekday_nums == 3).sum())
print('Fri (4):', (weekday_nums == 4).sum())
print('Sat (5):', (weekday_nums == 5).sum())
print('Sun (6):', (weekday_nums == 6).sum())

print('\nChecking for weekends:')
weekend_dates = df.index[weekday_nums.isin([5, 6])]
if len(weekend_dates) > 0:
    print(f'FOUND {len(weekend_dates)} WEEKENDS:')
    for date in weekend_dates[:20]:
        print(f'  {date.strftime("%Y-%m-%d")} ({date.strftime("%A")})')
else:
    print('✓ No weekends found - All good!')

