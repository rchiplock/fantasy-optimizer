import streamlit as st
import pandas as pd
import requests
import re
from thefuzz import process
from pulp import LpProblem, LpMaximize, LpVariable, lpSum, PULP_CBC_CMD
from yahoo_data import build_league_key, get_weekly_projections


# ------------------------------
# CONFIG
# ------------------------------
DEFAULT_API_KEY = "YOUR_API_KEY_HERE"


def normalize_name(name):
    return re.sub(r'[^a-z]', '', str(name).lower())


# Fetch Vegas Odds
def fetch_vegas_odds(api_key):
    url = f"https://api.the-odds-api.com/v4/sports/americanfootball_nfl/odds/?regions=us&markets=spreads,totals&oddsFormat=american&apiKey={api_key}"
    try:
        resp = requests.get(url)
        resp.raise_for_status()
        games = resp.json()
        rows = []
        for game in games:
            ht, at = game['home_team'], game['away_team']
            spread, total = None, None
            for bm in game['bookmakers']:
                for m in bm['markets']:
                    if m['key'] == 'spreads':
                        for o in m['outcomes']:
                            if o['name'] == ht:
                                spread = o.get('point')
                    if m['key'] == 'totals' and m['outcomes']:
                        total = m['outcomes'][0].get('point')
            if spread is not None and total is not None:
                rows.append({'team': ht, 'opponent': at, 'spread': spread, 'total': total})
                rows.append({'team': at, 'opponent': ht, 'spread': -spread, 'total': total})


        df = pd.DataFrame(rows)
        team_map = {
            'New England Patriots': 'NE','Buffalo Bills': 'BUF','Miami Dolphins': 'MIA','New York Jets': 'NYJ',
            'Baltimore Ravens': 'BAL','Cincinnati Bengals': 'CIN','Pittsburgh Steelers': 'PIT','Cleveland Browns': 'CLE',
            'Kansas City Chiefs': 'KC','Los Angeles Chargers': 'LAC','Las Vegas Raiders': 'LV','Denver Broncos': 'DEN',
            'Dallas Cowboys': 'DAL','Philadelphia Eagles': 'PHI','New York Giants': 'NYG','Washington Commanders': 'WAS',
            'San Francisco 49ers': 'SF','Seattle Seahawks': 'SEA','Los Angeles Rams': 'LAR','Arizona Cardinals': 'ARI',
            'Green Bay Packers': 'GB','Minnesota Vikings': 'MIN','Chicago Bears': 'CHI','Detroit Lions': 'DET',
            'Tampa Bay Buccaneers': 'TB','New Orleans Saints': 'NO','Atlanta Falcons': 'ATL','Carolina Panthers': 'CAR',
            'Jacksonville Jaguars': 'JAX','Tennessee Titans': 'TEN','Houston Texans': 'HOU','Indianapolis Colts': 'IND'
        }
        df['team_abbr'] = df['team'].map(team_map)
        df['favorite'] = df['spread'] < 0
        return df[['team_abbr','spread','total','favorite']]
    except Exception as e:
        st.warning(f"Could not fetch odds: {e}")
        return pd.DataFrame(columns=['team_abbr','spread','total','favorite'])


# Advanced Multiplier Logic: Spread + O/U
def calc_multiplier(row):
    mult = 1.0
    if pd.notna(row['spread']) and pd.notna(row['total']):
        spread = row['spread']
        total = row['total']
        pos = row['pos']


        # Big favorite RB boost, larger if low total
        if spread <= -10 and pos == 'RB':
            mult += 0.08
        elif spread <= -7 and pos == 'RB':
            mult += 0.05


        # Big underdog WR/TE boost
        if spread >= 10 and pos in ['WR','TE']:
            mult += 0.07
        elif spread >= 7 and pos in ['WR','TE']:
            mult += 0.05


        # High total shootout adjustments
        if total >= 50:
            if pos in ['WR','TE']:
                mult += 0.03
            if pos == 'DST':
                mult -= 0.07  # DST downgrade for shootout


        # Low total adjustments
        if total <= 42 and pos == 'DST':
            mult += 0.06
    return mult


# ------------------------------
# APP UI
# ------------------------------
st.title("🏈 DFS Optimizer")


# Sidebar controls
league_id = st.sidebar.text_input("Yahoo League ID", value="1168764")
week = st.sidebar.number_input("Week", 1, 18, 1)
api_key = st.sidebar.text_input("Odds API Key", value=DEFAULT_API_KEY)
threshold = st.sidebar.slider("Fuzzy Match Threshold", 50, 95, 80)
salary_file = st.file_uploader("Upload Salary CSV (DK or FD)", type="csv")
mapping_file = st.file_uploader("Optional: Upload Name Mapping CSV", type="csv")
num_lineups = st.sidebar.number_input("Number of Lineups", 1, 20, 3)
max_exposure = st.sidebar.slider("Max Player Ownership %", 10, 100, 50)
min_uniqueness = st.sidebar.slider("Minimum unique players per lineup", 1, 5, 1)
stack_qb_wr = st.sidebar.checkbox("Enable QB-WR stack?", value=False)
relax_constraints = st.sidebar.checkbox("Relax position constraints if pool is small?", value=True)


if salary_file and st.sidebar.button("Run Optimizer"):
    # Load Salary CSV
    salaries = pd.read_csv(salary_file)
    salaries.columns = [c.strip().lower() for c in salaries.columns]


    # Handle DK vs FD name constructs
    if 'name' not in salaries.columns:
        if 'first name' in salaries.columns and 'last name' in salaries.columns:
            salaries['name'] = (salaries['first name'].fillna('') + ' ' + salaries['last name'].fillna('')).str.strip()
        elif 'nickname' in salaries.columns:
            salaries['name'] = salaries['nickname']
        else:
            st.error("No recognizable player name field.")
            st.stop()


    # Position normalization (DST handling)
    if 'position' in salaries.columns: salaries.rename(columns={'position':'pos'}, inplace=True)
    if 'teamabbrev' in salaries.columns: salaries.rename(columns={'teamabbrev':'team_abbr'}, inplace=True)
    if 'team' in salaries.columns and 'team_abbr' not in salaries.columns:
        salaries.rename(columns={'team':'team_abbr'}, inplace=True)


    salaries['pos'] = salaries['pos'].str.upper().replace({'D/ST':'DST','D':'DST'})
    defense_mask = salaries['pos'] == 'DST'
    salaries.loc[defense_mask, 'name'] = salaries.loc[defense_mask, 'name'].str.replace(r'\s*DST$', '', regex=True)


    salaries['name_norm'] = salaries['name'].apply(normalize_name)
    salaries['team_abbr'] = salaries['team_abbr'].astype(str).str.upper()
    salaries = salaries.drop_duplicates(subset=['name_norm'], keep='first')


    # Determine platform salary cap
    salary_cap = 50000 if 'draftkings' in salary_file.name.lower() or 'dk' in salary_file.name.lower() else 60000
    st.write(f"✅ Loaded {len(salaries)} salary rows. Salary Cap = {salary_cap}")


    # Fetch Yahoo projections
    league_key = build_league_key(league_id)
    with st.spinner("Fetching Yahoo projections..."):
        projections = get_weekly_projections(league_key, week)
    projections['name_norm'] = projections['full_name'].apply(normalize_name)
    projections = projections.drop_duplicates(subset=['name_norm'], keep='first')
    st.write(f"✅ Yahoo Projections fetched: {len(projections)} players")


    # Apply optional mapping
    if mapping_file:
        mapping = pd.read_csv(mapping_file)
        map_dict = dict(zip(mapping['dfs_name'], mapping['yahoo_name']))
        salaries['matched_name'] = salaries['name_norm'].map(map_dict)
    else:
        salaries['matched_name'] = None


    # Fuzzy match (DST lower threshold)
    proj_names = projections['name_norm'].tolist()
    for idx, nm in salaries.loc[salaries['matched_name'].isna(), 'name_norm'].items():
        player_pos = salaries.loc[idx, 'pos']
        fuzzy_threshold = 50 if player_pos == 'DST' else threshold
        match, score = process.extractOne(nm, proj_names)
        if score >= fuzzy_threshold:
            salaries.at[idx, 'matched_name'] = match


    # Merge Salaries + Yahoo
    merged = salaries.merge(projections, left_on='matched_name', right_on='name_norm', how='left')
    merged['pos'] = merged.get('pos_x', merged.get('pos_y', ''))
    merged['team_abbr'] = merged.get('team_abbr_x', merged.get('team_abbr_y', ''))
    merged['pos'] = merged['pos'].replace({'D/ST':'DST','D':'DST'})
    merged = merged.drop_duplicates(subset=['name_norm_x'], keep='first')


    # Drop unmatched
    merged = merged.dropna(subset=['projection'])
    if len(merged) < 150:
        st.error("Too few matched players. Adjust threshold or upload mapping file.")
        st.stop()


    # Add Vegas odds
    vegas = fetch_vegas_odds(api_key)
    final = merged.merge(vegas, on='team_abbr', how='left')


    # Apply advanced multiplier
    final['multiplier'] = final.apply(calc_multiplier, axis=1)
    final['final_score'] = final['projection'] * final['multiplier']
    final = final.drop_duplicates(subset=['name'], keep='first')


    # Debug info
    st.subheader("📊 Player Pool Summary")
    st.write("Position Counts:", final['pos'].value_counts().to_dict())
    st.write(f"Salary Range: {final['salary'].min()} - {final['salary'].max()}")


    if 'DST' not in final['pos'].values:
        st.error("❌ No DST found. Cannot build lineups.")
        st.stop()


    # --- OPTIMIZER ---
    usage_count = {i:0 for i in final.index}
    previous_lineups = []


    def generate_lineup(exclude, previous_lineups):
        prob = LpProblem("DFS", LpMaximize)
        pool = [i for i in final.index if i not in exclude]
        if len(pool) < 9: return pd.DataFrame()
        vars_ = {i:LpVariable(f'p_{i}',cat='Binary') for i in pool}
        prob += lpSum(vars_[i]*final.loc[i,'final_score'] for i in pool)
        prob += lpSum(vars_[i]*final.loc[i,'salary'] for i in pool) <= salary_cap
        prob += lpSum(vars_[i] for i in pool if final.loc[i,'pos']=="QB") == 1
        prob += lpSum(vars_[i] for i in pool if final.loc[i,'pos']=="DST") == 1
        if relax_constraints:
            prob += lpSum(vars_[i] for i in pool if final.loc[i,'pos']=="RB") >= 2
            prob += lpSum(vars_[i] for i in pool if final.loc[i,'pos']=="WR") >= 2
            prob += lpSum(vars_[i] for i in pool if final.loc[i,'pos']=="TE") >= 1
        else:
            prob += lpSum(vars_[i] for i in pool if final.loc[i,'pos']=="RB") >= 2
            prob += lpSum(vars_[i] for i in pool if final.loc[i,'pos']=="WR") >= 3
            prob += lpSum(vars_[i] for i in pool if final.loc[i,'pos']=="TE") >= 1
        prob += lpSum(vars_[i] for i in pool) == 9
        if stack_qb_wr:
            qb_ids=[i for i in pool if final.loc[i,'pos']=="QB"]
            wr_ids=[i for i in pool if final.loc[i,'pos']=="WR"]
            for qb in qb_ids:
                team=final.loc[qb,'team_abbr']
                team_wrs=[wr for wr in wr_ids if final.loc[wr,'team_abbr']==team]
                if team_wrs:
                    prob += lpSum(vars_[wr] for wr in team_wrs) >= vars_[qb]
        for prev in previous_lineups:
            prob += lpSum(vars_[i] for i in prev if i in vars_) <= len(prev)-min_uniqueness
        prob.solve(PULP_CBC_CMD(msg=0))
        if prob.status != 1: return pd.DataFrame()
        sel=[i for i in pool if vars_[i].value()==1]
        return final.loc[sel]


    lineups=[]
    for _ in range(num_lineups):
        exclude={i for i,c in usage_count.items() if c >= (max_exposure/100)*num_lineups}
        lu=generate_lineup(exclude,previous_lineups)
        if lu.empty: break
        previous_lineups.append(set(lu.index))
        for idx in lu.index: usage_count[idx]+=1
        lineups.append(lu)


    if lineups:
        for i,lu in enumerate(lineups):
            st.subheader(f"Lineup #{i+1}")
            st.table(lu[['name','pos','salary','projection','final_score']])
            st.write(f"Salary: {lu['salary'].sum()} | Proj: {lu['projection'].sum():.2f}")
        out=pd.concat(lineups,keys=[f"Lineup_{i+1}" for i in range(len(lineups))])
        st.download_button("⬇ Download Lineups", out.to_csv(index=False), "optimized_lineups.csv")
    else:

        st.error("No valid lineups generated even after relaxing constraints.")

st.write("---")
st.markdown(
    """
    Enjoying the App?
    Visit the [official GitHub repo](https://github.com/rchiplock/fantasy-optimizer) for updates and ways to support!
    """
)
