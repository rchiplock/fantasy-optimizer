import streamlit as st
import pandas as pd
import requests
from thefuzz import process
import re
from pulp import LpProblem, LpMaximize, LpVariable, lpSum, PULP_CBC_CMD


# --------------------------------
# TEAM DATA
# --------------------------------
TEAM_CITY_MAP = {
    'BUF': 'Buffalo','MIA': 'Miami','NE': 'Foxborough','NYJ': 'East Rutherford',
    'BAL': 'Baltimore','CIN': 'Cincinnati','CLE': 'Cleveland','PIT': 'Pittsburgh',
    'HOU': 'Houston','IND': 'Indianapolis','JAX': 'Jacksonville','TEN': 'Nashville',
    'DEN': 'Denver','KC': 'Kansas City','LV': 'Las Vegas','LAC': 'Inglewood',
    'CHI': 'Chicago','DET': 'Detroit','GB': 'Green Bay','MIN': 'Minneapolis',
    'ATL': 'Atlanta','CAR': 'Charlotte','NO': 'New Orleans','TB': 'Tampa',
    'DAL': 'Arlington','NYG': 'East Rutherford','PHI': 'Philadelphia','WAS': 'Landover',
    'ARI': 'Glendale','LAR': 'Inglewood','SF': 'Santa Clara','SEA': 'Seattle'
}
INDOOR_STADIUMS = {'ATL','DAL','DET','HOU','IND','LAC','LAR','MIN','NO','ARI','LV'}


# --------------------------------
# FUNCTIONS
# --------------------------------
def fetch_dynastyprocess_projections():
    url = "https://raw.githubusercontent.com/dynastyprocess/data/master/files/fp_latest_weekly.csv"
    try:
        st.info("Fetching FantasyPros projections...")
        df = pd.read_csv(url)
        required=['player_name','pos','team','r2p_pts']
        if not all(c in df.columns for c in required):
            st.error("Projection file missing required columns.")
            return None
        df.rename(columns={'player_name':'full_name','team':'team_abbr','r2p_pts':'projection'}, inplace=True)
        df['full_name']=df['full_name'].str.lower().str.strip()
        df['pos']=df['pos'].str.upper()
        df['team_abbr']=df['team_abbr'].str.upper()
        return df[['full_name','pos','team_abbr','projection']]
    except Exception as e:
        st.error(f"Error fetching projections: {e}")
        return None


def fuzzy_match_names(salaries_df, projections_df, threshold=85):
    proj_names = projections_df['full_name'].tolist()
    name_map = {}
    for name in salaries_df['name']:
        match,score=process.extractOne(name,proj_names)
        name_map[name]=match if score>=threshold else None
    salaries_df['matched_name']=salaries_df['name'].map(name_map)
    return salaries_df.merge(projections_df,left_on='matched_name',right_on='full_name',how='left')


def scrape_odds():
    try:
        df=pd.read_html("https://www.fantasypros.com/nfl/odds/over-under.php")[0]
        df.columns=['Matchup','Spread','Total']
        df.dropna(subset=['Total'],inplace=True)
        df['Total']=df['Total'].astype(float)
        rows,homes=[],[]
        for _,row in df.iterrows():
            teams=re.split(r'@|vs',row['Matchup'])
            if len(teams)==2:
                t1,t2=teams[0].strip(),teams[1].strip()
                t1_abbr,t2_abbr=t1.split()[-1][:3].upper(),t2.split()[-1][:3].upper()
                spread=0
                if "PK" not in str(row['Spread']):
                    spread=float(row['Spread'].replace("½",".5").replace("+",""))
                fav=(row['Total']/2)+(spread/2)
                dog=(row['Total']/2)-(spread/2)
                home_team=t2_abbr if '@' in row['Matchup'] else t1_abbr
                rows.append({'team':t1_abbr,'implied_pts':fav})
                rows.append({'team':t2_abbr,'implied_pts':dog})
                homes.append({'team':t1_abbr,'home_team':home_team})
                homes.append({'team':t2_abbr,'home_team':home_team})
        return pd.DataFrame(rows),pd.DataFrame(homes)
    except:
        return pd.DataFrame(columns=['team','implied_pts']),pd.DataFrame(columns=['team','home_team'])


def fetch_weather(api_key,teams):
    data={}
    for t in teams:
        indoor=(t in INDOOR_STADIUMS)
        if indoor:
            data[t]={'temp':70,'wind':0,'prec':0,'indoor':True}
        else:
            if api_key:
                try:
                    city=TEAM_CITY_MAP.get(t)
                    url=f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=imperial"
                    w=requests.get(url).json()
                    temp=w.get('main',{}).get('temp',70)
                    wind=w.get('wind',{}).get('speed',0)
                    rain=w.get('rain',{}).get('1h',0)
                    snow=w.get('snow',{}).get('1h',0)
                    data[t]={'temp':temp,'wind':wind,'prec':rain+snow,'indoor':False}
                except:
                    data[t]={'temp':70,'wind':0,'prec':0,'indoor':False}
            else:
                data[t]={'temp':70,'wind':0,'prec':0,'indoor':False}
    return data


def weather_mult(temp,wind,prec,indoor):
    f=1.0
    if indoor:return f
    if wind>20:f-=0.10
    if temp<32:f-=0.05
    if prec>0:f-=0.05
    return max(f,0.8)


# --------------------------------
# UI
# --------------------------------
st.title("🏈 DFS Optimizer – DraftKings & FanDuel")


salary_file = st.file_uploader("Upload Salary CSV (DraftKings or FanDuel)", type="csv")
platform = st.selectbox("Platform", ["DraftKings", "FanDuel"])
api_key = st.text_input("Weather API Key (Optional)", type="password")
num_lineups = st.number_input("Number of Lineups", 1, 20, 5)
max_exposure = st.slider("Max Player Exposure %", 10, 100, 50)
min_uniqueness = st.slider("Min unique players difference per lineup", 1, 5, 1)
stack_qb_wr = st.checkbox("Require QB + WR stack?", value=False)  # Stack option


if salary_file:
    salary_cap = 50000 if platform == "DraftKings" else 60000
    salaries = pd.read_csv(salary_file)
    salaries.columns = [c.strip().lower() for c in salaries.columns]


    # Parse file by platform
    if platform == "DraftKings":
        if all(c in salaries.columns for c in ['position', 'name', 'salary', 'teamabbrev']):
            salaries.rename(columns={'position': 'pos', 'teamabbrev': 'team_abbr'}, inplace=True)
        else:
            st.error("DraftKings file missing required columns.")
            st.stop()
    elif platform == "FanDuel":
        if 'first name' in salaries.columns and 'last name' in salaries.columns:
            salaries['name'] = (salaries['first name'].fillna('') + ' ' + salaries['last name'].fillna('')).str.strip()
        elif 'nickname' in salaries.columns:
            salaries['name'] = salaries['nickname']
        else:
            st.error("FanDuel file missing name info.")
            st.stop()
        if not all(c in salaries.columns for c in ['position', 'salary', 'team']):
            st.error("FanDuel file missing required columns.")
            st.stop()
        salaries.rename(columns={'position': 'pos', 'team': 'team_abbr'}, inplace=True)


    salaries = salaries[['name', 'pos', 'salary', 'team_abbr']]
    salaries['name'] = salaries['name'].astype(str).str.lower()


    # ✅ Clean salaries
    salaries['salary'] = salaries['salary'].astype(str).str.replace(r'[^0-9]', '', regex=True).str.strip()
    salaries = salaries[salaries['salary'] != '']
    salaries['salary'] = salaries['salary'].astype(int)


    # ✅ Normalize positions (VERY IMPORTANT for FanDuel: convert D -> DST)
    salaries['pos'] = salaries['pos'].str.upper().replace({'D': 'DST'})


    st.write("Salary Stats After Cleaning:", salaries['salary'].describe())


    # Fetch projections
    projections = fetch_dynastyprocess_projections()
    if projections is None: st.stop()


    dfs = fuzzy_match_names(salaries, projections).dropna(subset=['projection'])


    # Normalize merged columns
    if 'pos_x' in dfs.columns: dfs.rename(columns={'pos_x': 'pos'}, inplace=True)
    if 'pos_y' in dfs.columns: dfs.drop(columns=['pos_y'], inplace=True)
    if 'team_abbr_x' in dfs.columns or 'team_abbr_y' in dfs.columns:
        dfs['team_abbr'] = dfs.get('team_abbr_x', dfs.get('team_abbr_y'))
        dfs.drop(columns=['team_abbr_x', 'team_abbr_y'], inplace=True, errors='ignore')


    # Normalize positions post merge
    dfs['pos'] = dfs['pos'].str.upper().replace({'D': 'DST'})


    # Vegas & weather adjustments
    vegas, homes = scrape_odds()
    avg = vegas['implied_pts'].mean() if not vegas.empty else 0
    dfs = dfs.merge(vegas.rename(columns={'team': 'team_abbr'}), on='team_abbr', how='left')
    dfs = dfs.merge(homes.rename(columns={'team': 'team_abbr'}), on='team_abbr', how='left')


    home_teams = dfs['home_team'].dropna().unique()
    wdata = fetch_weather(api_key, home_teams)
    dfs['temp'] = dfs['home_team'].map(lambda t: wdata.get(t, {}).get('temp', 70))
    dfs['wind'] = dfs['home_team'].map(lambda t: wdata.get(t, {}).get('wind', 0))
    dfs['prec'] = dfs['home_team'].map(lambda t: wdata.get(t, {}).get('prec', 0))
    dfs['indoor'] = dfs['home_team'].map(lambda t: wdata.get(t, {}).get('indoor', True))


    dfs['weather_mult'] = dfs.apply(lambda r: weather_mult(r['temp'], r['wind'], r['prec'], r['indoor']), axis=1)
    dfs['vegas_mult'] = dfs['implied_pts'].apply(lambda x: 1 + ((x - avg) / 100) if pd.notna(x) else 1)
    dfs['final_score'] = dfs['projection'] * dfs['weather_mult'] * dfs['vegas_mult']


    st.download_button("⬇ Download Adjusted Player Pool", dfs.to_csv(index=False), "adjusted_player_pool.csv")


    # OPTIMIZER
    usage_count = {i: 0 for i in dfs.index}
    previous_lineups = []


    def generate_lineup(exclude, previous_lineups):
        prob = LpProblem("DFS", LpMaximize)
        pool = [i for i in dfs.index if i not in exclude]
        vars_ = {i: LpVariable(f'p_{i}', cat='Binary') for i in pool}


        # Objective
        prob += lpSum(vars_[i] * dfs.loc[i, 'final_score'] for i in pool)


        # Salary cap
        prob += lpSum(vars_[i] * dfs.loc[i, 'salary'] for i in pool) <= salary_cap


        # Roster constraints with FLEX
        prob += lpSum(vars_[i] for i in pool if dfs.loc[i, 'pos'] == "QB") == 1
        prob += lpSum(vars_[i] for i in pool if dfs.loc[i, 'pos'] == "DST") == 1
        prob += lpSum(vars_[i] for i in pool if dfs.loc[i, 'pos'] == "RB") >= 2
        prob += lpSum(vars_[i] for i in pool if dfs.loc[i, 'pos'] == "WR") >= 3
        prob += lpSum(vars_[i] for i in pool if dfs.loc[i, 'pos'] == "TE") >= 1
        prob += lpSum(vars_[i] for i in pool) == 9  # total players


        # QB-WR stack
        if stack_qb_wr:
            qb_ids = [i for i in pool if dfs.loc[i, 'pos'] == "QB"]
            wr_ids = [i for i in pool if dfs.loc[i, 'pos'] == "WR"]
            for qb in qb_ids:
                team = dfs.loc[qb, 'team_abbr']
                team_wr = [wr for wr in wr_ids if dfs.loc[wr, 'team_abbr'] == team]
                if team_wr:
                    prob += lpSum(vars_[wr] for wr in team_wr) >= vars_[qb]


        # Uniqueness
        for prev in previous_lineups:
            prob += lpSum(vars_[i] for i in prev if i in vars_) <= len(prev) - min_uniqueness


        prob.solve(PULP_CBC_CMD(msg=0))
        if prob.status != 1:
            st.warning("""No feasible solution. Check that:
                - Player pool has DST and all required positions
                - Salary cap ($60K FD/$50K DK) allows 9 players
                - QB/WR stack is possible
            """)
            return pd.DataFrame()


        sel = [i for i in pool if vars_[i].value() == 1]
        return dfs.loc[sel]


    # Generate lineups
    lineups = []
    for _ in range(num_lineups):
        exclude = {i for i, c in usage_count.items() if c >= (max_exposure / 100) * num_lineups}
        lu = generate_lineup(exclude, previous_lineups)
        if lu.empty: break


        total_salary = lu['salary'].sum()
        if total_salary > salary_cap:
            st.warning(f"Lineup exceeded cap ({total_salary} > {salary_cap}), skipping...")
            continue


        previous_lineups.append(set(lu.index))
        for idx in lu.index: usage_count[idx] += 1
        lineups.append(lu)


    for i, lu in enumerate(lineups):
        st.subheader(f"Lineup #{i + 1}")
        st.table(lu[['name', 'pos', 'salary', 'projection', 'final_score']])
        st.write(f"Salary Used: {lu['salary'].sum()} | Projection: {lu['projection'].sum():.2f}")


    if lineups:
        out = pd.concat(lineups, keys=[f"Lineup_{i + 1}" for i in range(len(lineups))])
        st.download_button("⬇ Download Optimized Lineups", out.to_csv(index=False), "optimized_lineups.csv")

