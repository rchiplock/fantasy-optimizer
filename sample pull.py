# 2. Fetch week 1 projections
df = yahoo_data.get_weekly_projections(league_key, week=1)
print(df.head())
