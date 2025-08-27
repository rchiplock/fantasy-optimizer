import os
import time
import xml.etree.ElementTree as ET
import pandas as pd
from yahoo_oauth import OAuth2
import streamlit as st


# ------------------------------
# OAuth Handling
# ------------------------------
def get_oauth():
    """
    Handles Yahoo OAuth authentication.
    Tries local oauth2.json first, then Streamlit secrets.
    """
    if os.path.exists("oauth2.json"):
        oauth = OAuth2(None, None, from_file="oauth2.json")
        if not oauth.token_is_valid():
            oauth.refresh_access_token()
        return oauth


    if "oauth" not in st.secrets:
        st.error("Missing [oauth] configuration in Streamlit secrets.")
        st.stop()


    creds = st.secrets["oauth"]
    for key in ["consumer_key","consumer_secret","access_token","refresh_token"]:
        if key not in creds:
            st.error(f"Missing key in secrets: {key}")
            st.stop()


    oauth = OAuth2(
        creds["consumer_key"], creds["consumer_secret"],
        access_token=creds["access_token"], refresh_token=creds["refresh_token"]
    )
    if not oauth.token_is_valid():
        oauth.refresh_access_token()
    return oauth


# ------------------------------
# Utility to strip XML namespaces
# ------------------------------
def strip_namespace(root):
    for elem in root.iter():
        if "}" in elem.tag:
            elem.tag = elem.tag.split("}", 1)[1]
    return root


# ------------------------------
# Get current NFL game key
# ------------------------------
def get_current_nfl_game_key(oauth):
    url = "https://fantasysports.yahooapis.com/fantasy/v2/game/nfl"
    resp = oauth.session.get(url)
    root = ET.fromstring(resp.text)
    root = strip_namespace(root)
    return root.find(".//game_key").text


def build_league_key(league_id):
    oauth = get_oauth()
    game_key = get_current_nfl_game_key(oauth)
    return f"{game_key}.l.{league_id}"


# ------------------------------
# Map Yahoo stat IDs to categories for DFS scoring
# ------------------------------
YAHOO_STAT_MAP = {
    '4':  'pass_yds',   # Passing yards
    '5':  'pass_td',    # Passing TD
    '6':  'pass_int',   # Pass Interception
    '15': 'rush_yds',   # Rushing yards
    '16': 'rush_td',    # Rushing TD
    '17': 'rec_yds',    # Receiving yards
    '18': 'rec_td',     # Receiving TD
    '19': 'fum_lost',   # Fumbles lost
    '53': 'rec'         # Receptions
}


# ------------------------------
# Fetch weekly raw projections (league context)
# ------------------------------
def get_weekly_raw_stats(league_id, week, page_size=25):
    """
    Fetches projected **raw stats** for all NFL players for a given week (league-based endpoint).
    Returns DataFrame with:
    [full_name, pos, team_abbr, pass_yds, pass_td, pass_int, rush_yds, rush_td, rec, rec_yds, rec_td, fum_lost]
    """
    oauth = get_oauth()
    league_key = build_league_key(league_id)


    all_rows = []
    start = 0


    while True:
        url = (f"https://fantasysports.yahooapis.com/fantasy/v2/"
               f"league/{league_key}/players;type=week;week={week};statType=projected;start={start};count={page_size}")
        resp = oauth.session.get(url)
        if resp.status_code != 200:
            st.error(f"Yahoo API error: {resp.text[:500]}")
            break


        try:
            root = ET.fromstring(resp.text)
        except ET.ParseError as e:
            st.error(f"XML Parse Error: {e}")
            break


        root = strip_namespace(root)
        players = root.findall(".//player")
        if not players:
            break


        for p in players:
            try:
                name_elem = p.find(".//name/full")
                pos_elem = p.find(".//display_position")
                team_elem = p.find(".//editorial_team_abbr")


                full_name = name_elem.text.lower() if name_elem is not None else ""
                pos = pos_elem.text.upper() if pos_elem is not None else ""
                team = team_elem.text.upper() if team_elem is not None else ""


                # Initialize stats dictionary with zeros
                stats_dict = {v:0.0 for v in YAHOO_STAT_MAP.values()}


                # Loop through projected stats
                for s in p.findall(".//stat"):
                    sid = s.findtext("stat_id")
                    val = s.findtext("value")
                    if sid in YAHOO_STAT_MAP and val is not None:
                        try:
                            stats_dict[YAHOO_STAT_MAP[sid]] = float(val)
                        except:
                            continue


                row = {'full_name': full_name, 'pos': pos, 'team_abbr': team}
                row.update(stats_dict)
                all_rows.append(row)


            except Exception:
                continue


        if len(players) < page_size:
            break
        start += page_size
        time.sleep(0.1)


    df = pd.DataFrame(all_rows)
    if not df.empty:
        df = df.drop_duplicates(subset=['full_name'])
    return df

