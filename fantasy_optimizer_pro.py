import streamlit as st
import pandas as pd
import numpy as np
import requests
import re
from thefuzz import process
from pulp import LpProblem, LpMaximize, LpVariable, lpSum, PULP_CBC_CMD
from yahoo_data import get_weekly_raw_stats


# ------------------------------
# CONFIG
# ------------------------------
DEFAULT_API_KEY = "YOUR_API_KEY_HERE"
FUZZY_THRESHOLD = 85


DK_DEFAULTS = {'pass_yds':0.04,'pass_td':4,'pass_int':-1,'rush_yds':0.1,'rush_td':6,
               'rec':1,'rec_yds':0.1,'rec_td':6,'fum_lost':-1}
FD_DEFAULTS = {'pass_yds':0.04,'pass_td':4,'pass_int':-1,'rush_yds':0.1,'rush_td':6,
               'rec':0.5,'rec_yds':0.1,'rec_td':6,'fum_lost':-1}


TEAM_MAP = {
    'New England Patriots':'NE','Buffalo Bills':'BUF','Miami Dolphins':'MIA','New York Jets':'NYJ',
    'Baltimore Ravens':'BAL','Cincinnati Bengals':'CIN','Pittsburgh Steelers':'PIT','Cleveland Browns':'CLE',
    'Kansas City Chiefs':'KC','Los Angeles Chargers':'LAC','Las Vegas Raiders':'LV','Denver Broncos':'DEN',
    'Dallas Cowboys':'DAL','Philadelphia Eagles':'PHI','New York Giants':'NYG','Washington Commanders':'WAS',
    'San Francisco 49ers':'SF','Seattle Seahawks':'SEA','Los Angeles Rams':'LAR','Arizona Cardinals':'ARI',
    'Green Bay Packers':'GB','Minnesota Vikings':'MIN','Chicago Bears':'CHI','Detroit Lions':'DET',
    'Tampa Bay Buccaneers':'TB','New Orleans Saints':'NO','Atlanta Falcons':'ATL','Carolina Panthers':'CAR',
    'Jacksonville Jaguars':'JAX','Tennessee Titans':'TEN','Houston Texans':'HOU','Indianapolis Colts':'IND'
}


# ------------------------------
# Helper Functions
# ------------------------------
def normalize_name(name): 
    return re.sub(r'[^a-z]', '', str(name).lower())


def compute_projection(row, scoring):
    total=sum(row.get(cat,0)*pts for cat,pts in scoring.items() if pd.notna(row.get(cat)))
    if row.get('pass_yds',0)>=300: total+=3
    if row.get('rush_yds',0)>=100: total+=3
    if row.get('rec_yds',0)>=100: total+=3
    return total


def flatten_columns(df):
    if isinstance(df.columns, pd.MultiIndex):
        df.columns=['_'.join([str(c).strip().lower() for c in tup if c and 'unnamed' not in str(c).lower()]) for tup in df.columns]
    else:
        df.columns=[str(c).strip().lower() for c in df.columns]
    return df


def detect_fpts_column(df):
    cols=[c for c in df.columns if 'fpts' in c or 'fantasy' in c]
    return cols[0] if cols else df.columns[-1]


# ------------------------------
# FantasyPros fallback
# ------------------------------
def fetch_fantasypros_projections():
    positions=['qb','rb','wr','te']
    all_data=[]
    base_url="https://www.fantasypros.com/nfl/projections/"
    for pos in positions:
        try:
            df=pd.read_html(f"{base_url}{pos}.php")[0]
            df=flatten_columns(df)
            fpts_col=detect_fpts_column(df)
            df['projection']=pd.to_numeric(df[fpts_col],errors='coerce').fillna(0)
            df['pos']=pos.upper()
            if 'player' in df.columns: df.rename(columns={'player':'name'}, inplace=True)
            all_data.append(df)
        except Exception as e:
            st.warning(f"FP scrape failed for {pos}: {e}")
    skill=pd.concat(all_data,ignore_index=True) if all_data else pd.DataFrame()
    try:
        dst=pd.read_html(f"{base_url}dst.php")[0]
        dst=flatten_columns(dst)
        fpts_col=detect_fpts_column(dst)
        dst['projection']=pd.to_numeric(dst[fpts_col],errors='coerce').fillna(0)
        dst['pos']='DST'
        if 'player' in dst.columns: dst.rename(columns={'player':'name'}, inplace=True)
    except:
        dst=pd.DataFrame()
    combined=pd.concat([skill[['name','pos','projection']], dst[['name','pos','projection']]],ignore_index=True)
    combined['name']=combined['name'].fillna('Unknown')
    combined['name_norm']=combined['name'].apply(normalize_name)
    combined['team_abbr']=''
    combined.loc[combined['pos']=='DST','team_abbr']=combined.loc[combined['pos']=='DST','name'].map(TEAM_MAP)
    return combined


# ------------------------------
# Vegas odds
# ------------------------------
def fetch_vegas_odds(api_key):
    url=f"https://api.the-odds-api.com/v4/sports/americanfootball_nfl/odds/?regions=us&markets=spreads,totals&oddsFormat=american&apiKey={api_key}"
    try:
        r=requests.get(url);r.raise_for_status();games=r.json()
        rows=[]
        for g in games:
            ht,at=g['home_team'],g['away_team']
            spread,total=None,None
            for bm in g['bookmakers']:
                for m in bm['markets']:
                    if m['key']=='spreads':
                        for o in m['outcomes']:
                            if o['name']==ht: spread=o.get('point')
                    if m['key']=='totals' and m['outcomes']:
                        total=m['outcomes'][0].get('point')
            if spread is not None and total is not None:
                rows.append({'team':ht,'spread':spread,'total':total})
                rows.append({'team':at,'spread':-spread,'total':total})
        df=pd.DataFrame(rows)
        df['team_abbr']=df['team'].map(TEAM_MAP)
        df=df.groupby('team_abbr',as_index=False).agg({'spread':'mean','total':'mean'})
        return df
    except Exception as e:
        st.warning(f"Vegas API error: {e}")
        return pd.DataFrame(columns=['team_abbr','spread','total'])


# ------------------------------
# Dynamic multiplier (user sliders)
# ------------------------------
def calc_multiplier(row, spread_trigger, total_trigger, impact_pct):
    mult=1.0
    if pd.notna(row['spread']) and pd.notna(row['total']):
        s=row['spread']; t=row['total']; pos=row['pos']
        impact=impact_pct/100.0
        if s<=-spread_trigger and pos=='RB': mult+=impact
        if s>=spread_trigger and pos in['WR','TE']: mult+=impact
        if t>=total_trigger:
            if pos in['WR','TE']: mult+=impact
            if pos=='DST': mult-=impact/2
        if t<=total_trigger-5 and pos=='DST': mult+=impact/2
    return mult


# ------------------------------
# Streamlit UI
# ------------------------------
st.title("🏈 DFS Optimizer Pro")

league_id=st.sidebar.text_input("Yahoo League ID","1168764",help="Your Yahoo league number (from the URL). Needed for projections")
week=st.sidebar.number_input("Week",1,18,1,help="Which NFL week to optimize for")
num_lineups=st.sidebar.number_input("Number of Lineups",1,20,3,help="How many lineups should the optimizer build?")
api_key=st.sidebar.text_input("Odds API Key",value=DEFAULT_API_KEY,help="API key from The Odds API for game totals & spreads")
min_uniqueness=st.sidebar.slider("Min unique players per lineup",1,5,1,help="Force variety: Each lineup must differ by this many players")
stack_qb_wr=st.sidebar.checkbox("Enable QB-WR stack?",value=False,help="Keep it classic: Pair QB with at least one WR from the same team")
opt_mode=st.sidebar.radio("Optimize For:",["Median","Ceiling","Floor"],help="Median = safe. Ceiling = upside. Floor = low risk.")
rand_pct=st.sidebar.slider("Projection randomness % (GPP)",0,30,0,help="Add variance for GPP - more randomness = more unique lineups")
min_proj=st.sidebar.slider("Minimum Projection (FPTS)",0.0,30.0,1.0,help="Ignore players projected below this score")


# ✅ New Vegas sliders
spread_trigger=st.sidebar.slider("Spread trigger (pts)",1,10,3,help="Start adjusting the multipliers when point spread meets this value")
total_trigger=st.sidebar.slider("Over/Under trigger",30,60,45,help="Games above this OU boost WR/TE (and adjust DST)")
impact_pct=st.sidebar.slider("Vegas impact intensity (%)",0,20,5,help="How strong Vegas influence is on player projections")


salary_file=st.file_uploader("Upload Salary CSV (DK or FD)", type="csv")


# ✅ State control flag for persistent optimizer UI
if 'optimizer_started' not in st.session_state:
    st.session_state.optimizer_started = False


if salary_file and not st.session_state.optimizer_started:
    if st.sidebar.button("Run Optimizer"):
        st.session_state.optimizer_started = True


# ------------------------------
# Main logic
# ------------------------------
if st.session_state.optimizer_started and salary_file:
    filename=salary_file.name.lower()
    platform='DraftKings' if 'draftkings' in filename or 'dk' in filename else 'FanDuel'
    salary_cap=50000 if platform=='DraftKings' else 60000
    st.write(f"✅ Platform: {platform} | Cap: {salary_cap}")


    salaries=pd.read_csv(salary_file)
    salaries.columns=[c.strip().lower() for c in salaries.columns]
    if 'position' in salaries.columns: salaries.rename(columns={'position':'pos'},inplace=True)
    if 'teamabbrev' in salaries.columns: salaries.rename(columns={'teamabbrev':'team_abbr'},inplace=True)
    if 'team' in salaries.columns and 'team_abbr' not in salaries.columns: salaries.rename(columns={'team':'team_abbr'},inplace=True)
    if 'name' not in salaries.columns:
        if {'first name','last name'}.issubset(salaries.columns):
            salaries['name']=(salaries['first name'].fillna('')+' '+salaries['last name'].fillna('')).str.strip()
        elif 'nickname' in salaries.columns: salaries['name']=salaries['nickname']
        else: st.error("No 'name' column in salary file."); st.stop()
    salaries['pos']=salaries['pos'].str.upper().replace({'D/ST':'DST','D':'DST'})
    salaries['team_abbr']=salaries['team_abbr'].astype(str).str.upper()
    salaries['name_norm']=salaries['name'].apply(normalize_name)


    st.info("Fetching Yahoo projections…")
    yahoo_df=get_weekly_raw_stats(league_id,week)
    yahoo_df['name_norm']=yahoo_df['full_name'].apply(normalize_name)
    scoring=DK_DEFAULTS if platform=='DraftKings' else FD_DEFAULTS
    yahoo_df['projection']=yahoo_df.apply(lambda r:compute_projection(r,scoring),axis=1)


    using="Yahoo"
    if yahoo_df.empty or yahoo_df['projection'].sum()==0:
        st.warning("Yahoo projections empty → Using FantasyPros fallback.")
        yahoo_df=fetch_fantasypros_projections()
        using="FantasyPros"
    st.success(f"Using projections: {using}")


    salaries['matched_name'] = None
    names = list(yahoo_df['name_norm'])
    unmatched_rows = []


    for idx, row in salaries.iterrows():
        match, score = process.extractOne(row['name_norm'], names)
        if match and score >= FUZZY_THRESHOLD:
            candidate = yahoo_df[yahoo_df['name_norm'] == match].iloc[0]
            if str(candidate['pos']).upper() == str(row['pos']).upper():
                salaries.at[idx, 'matched_name'] = match
            else:
                same_pos = yahoo_df[yahoo_df['pos'].str.upper() == str(row['pos']).upper()]
                if not same_pos.empty:
                    alt_match, alt_score = process.extractOne(row['name_norm'], list(same_pos['name_norm']))
                    if alt_match and alt_score >= FUZZY_THRESHOLD:
                        salaries.at[idx, 'matched_name'] = alt_match
                    else:
                        unmatched_rows.append(row)
                else:
                    unmatched_rows.append(row)
        else:
            unmatched_rows.append(row)


    merged = salaries.merge(yahoo_df, left_on='matched_name', right_on='name_norm', how='left')


    # ✅ Interactive Mapping with Session Persistence
    if 'corrected_matches' not in st.session_state:
        st.session_state.corrected_matches = {}


    if unmatched_rows:
        st.warning(f"{len(unmatched_rows)} players could not be matched. Showing top 50 by salary. Please map those you'd like to include in projections below:")
        unmatched_df = pd.DataFrame(unmatched_rows)
        # Sort by salary and keep only top 25
        unmatched_df['salary'] = pd.to_numeric(unmatched_df.get('salary',0),errors='coerce').fillna(0)
        unmatched_df = unmatched_df.sort_values(by='salary', ascending=False).head(50)
        display_col = 'full_name' if 'full_name' in yahoo_df.columns else 'name'


        for i, r in unmatched_df.iterrows():
            candidates = yahoo_df[yahoo_df['pos'].str.upper() == str(r['pos']).upper()][display_col].dropna().tolist()
            current_value = st.session_state.corrected_matches.get(r['name_norm'], "-- No Match --")
            selected = st.selectbox(
                f"Match for {r['name']}",
                ["-- No Match --"] + candidates,
                index=(["-- No Match --"] + candidates).index(current_value) if current_value in candidates else 0,
                key=f"map_{i}"
            )
            if selected != "-- No Match --":
                st.session_state.corrected_matches[r['name_norm']] = normalize_name(selected)


    if st.session_state.corrected_matches:
        st.success(f"{len(st.session_state.corrected_matches)} manual matches selected. Applying...")
        for idx, row in salaries.iterrows():
            if row['name_norm'] in st.session_state.corrected_matches:
                salaries.at[idx, 'matched_name'] = st.session_state.corrected_matches[row['name_norm']]


        merged = salaries.merge(yahoo_df, left_on='matched_name', right_on='name_norm', how='left')


    # ------------------- Continue -------------------
    merged['pos'] = merged['pos_x'].combine_first(merged.get('pos_y'))
    merged['salary'] = pd.to_numeric(merged['salary'], errors='coerce')
    merged = merged.dropna(subset=['projection', 'salary'])
    if 'name_x' in merged.columns: merged.rename(columns={'name_x': 'name'}, inplace=True)
    if 'name_y' in merged.columns: merged.drop(columns=['name_y'], inplace=True)


    merged['team_abbr'] = merged.get('team_abbr_x', '').str.upper()
    final = merged[merged['projection'] >= min_proj].copy()
    vegas = fetch_vegas_odds(api_key)
    final = final.merge(vegas, on='team_abbr', how='left')


    final['multiplier'] = final.apply(lambda r: calc_multiplier(r, spread_trigger, total_trigger, impact_pct), axis=1)
    final['final_score'] = final['projection'] * final['multiplier']
    if opt_mode == "Ceiling": final['final_score'] *= 1.1
    elif opt_mode == "Floor": final['final_score'] *= 0.9
    if rand_pct > 0: final['final_score'] *= np.random.normal(1, rand_pct/100, len(final))


    st.subheader("Top 20 Players")
    st.dataframe(final[['name','pos','salary','projection','multiplier']].sort_values('projection',ascending=False).head(20))


    if 'DST' not in final['pos'].values: st.error("No DST found."); st.stop()


    prev_sets=[]; lineups=[]; pool=final.index
    def build(prev):
        prob=LpProblem("DFS",LpMaximize)
        vars_={i:LpVariable(f"p_{i}",cat='Binary') for i in pool}
        prob+=lpSum(vars_[i]*final.loc[i,'final_score'] for i in pool)
        prob+=lpSum(vars_[i]*final.loc[i,'salary'] for i in pool)<=salary_cap
        prob+=lpSum(vars_[i] for i in pool if final.loc[i,'pos']=="QB")==1
        prob+=lpSum(vars_[i] for i in pool if final.loc[i,'pos']=="DST")==1
        prob+=lpSum(vars_[i] for i in pool if final.loc[i,'pos']=="RB")>=2
        prob+=lpSum(vars_[i] for i in pool if final.loc[i,'pos']=="WR")>=3
        prob+=lpSum(vars_[i] for i in pool if final.loc[i,'pos']=="TE")>=1
        prob+=lpSum(vars_[i] for i in pool)==9
        if stack_qb_wr:
            qb_ids=[i for i in pool if final.loc[i,'pos']=="QB"]
            wr_ids=[i for i in pool if final.loc[i,'pos']=="WR"]
            for qb in qb_ids:
                t=final.loc[qb,'team_abbr']
                twr=[wr for wr in wr_ids if final.loc[wr,'team_abbr']==t]
                if twr: prob+=lpSum(vars_[w] for w in twr)>=vars_[qb]
        for ps in prev: prob+=lpSum(vars_[i] for i in ps)<=len(ps)-min_uniqueness
        prob.solve(PULP_CBC_CMD(msg=0))
        if prob.status!=1: return pd.DataFrame()
        sel=[i for i in pool if vars_[i].value()==1]
        return final.loc[sel,['name','pos','salary','projection','multiplier','final_score']]


    for _ in range(num_lineups):
        lu=build(prev_sets)
        if lu.empty: break
        prev_sets.append(set(lu.index))
        lineups.append(lu)


    if lineups:
        for i,lu in enumerate(lineups):
            st.subheader(f"Lineup #{i+1}")
            st.table(lu)
            st.write(f"Salary: {lu['salary'].sum()} | Proj: {lu['projection'].sum():.2f} | Adjusted Total: {lu['final_score'].sum():.2f}")
        out=pd.concat(lineups,keys=[f"Lineup_{i+1}"for i in range(len(lineups))])
        st.download_button("⬇ Download CSV",out.to_csv(index=False),"optimized_lineups.csv")
    else:
        st.error("No valid lineups created.")


st.write("---")
st.markdown("Enjoying the App? [Visit GitHub](https://github.com/rchiplock/fantasy-optimizer) for the latest updates or to contribute!")

