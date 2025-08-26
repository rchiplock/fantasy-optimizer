import os
import time
import xml.etree.ElementTree as ET
import pandas as pd
import streamlit as st
from yahoo_oauth import OAuth2


# -------------------------------------------------------
# Yahoo OAuth Handling: Local OR Streamlit Secrets
# -------------------------------------------------------
def get_oauth():
    """
    Handles Yahoo OAuth authentication.
    - Local mode: uses oauth2.json file.
    - Streamlit Cloud: uses Streamlit secrets.
    """
    if os.path.exists("oauth2.json"):
        oauth = OAuth2(None, None, from_file="oauth2.json")
        if not oauth.token_is_valid():
            oauth.refresh_access_token()
        return oauth


    # For Streamlit deployments
    if "oauth" not in st.secrets:
        st.error("Missing [oauth] configuration in Streamlit secrets.")
        st.stop()


    creds = st.secrets["oauth"]
    required_keys = ["consumer_key", "consumer_secret", "access_token", "refresh_token"]
    missing = [k for k in required_keys if k not in creds]
    if missing:
        st.error(f"Missing keys in [oauth] secrets: {missing}")
        st.stop()


    oauth = OAuth2(
        creds["consumer_key"], creds["consumer_secret"],
        access_token=creds["access_token"], refresh_token=creds["refresh_token"]
    )
    if not oauth.token_is_valid():
        oauth.refresh_access_token()
    return oauth


# -------------------------------------------------------
# Utility to strip XML namespaces
# -------------------------------------------------------
def strip_namespace(root):
    for elem in root.iter():
        if "}" in elem.tag:
            elem.tag = elem.tag.split("}", 1)[1]
    return root


# -------------------------------------------------------
# Get NFL game key dynamically
# -------------------------------------------------------
def get_current_nfl_game_key():
    oauth = get_oauth()
    url = "https://fantasysports.yahooapis.com/fantasy/v2/game/nfl"
    resp = oauth.session.get(url)
    if resp.status_code != 200:
        return "461"  # fallback game key
    try:
        root = ET.fromstring(resp.text)
        root = strip_namespace(root)
        return root.find(".//game_key").text
    except:
        return "461"


def build_league_key(league_id):
    game_key = get_current_nfl_game_key()
    return f"{game_key}.l.{league_id}"


# -------------------------------------------------------
# Fetch Yahoo projections using game-level endpoint
# Will automatically work when Yahoo publishes stat id=900
# -------------------------------------------------------
def get_weekly_projections(week, page_size=25):
    """
    Fetches projected Fan Points (stat id=900) for all NFL players
    from the Yahoo Fantasy API game-level endpoint.


    Parameters:
        week (int): Week number for projections
        page_size (int): Players per page (default: 25)


    Returns:
        DataFrame with columns: [full_name, pos, team_abbr, projection]
    """
    oauth = get_oauth()
    all_players = []
    start = 0


    while True:
        url = (
            f"https://fantasysports.yahooapis.com/fantasy/v2/game/nfl"
            f"/players;status=A;type=week;week={week};statType=projected;"
            f"start={start};count={page_size};out=stats"
        )


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


                # Projected Fantasy Points (Fan Pts) is stat id=900
                projection = 0.0
                stat_elem = p.find('.//stat[@id="900"]')
                if stat_elem is not None and stat_elem.text:
                    projection = float(stat_elem.text)


                all_players.append({
                    "full_name": name_elem.text.lower() if name_elem is not None else "",
                    "pos": pos_elem.text.upper() if pos_elem is not None else "",
                    "team_abbr": team_elem.text.upper() if team_elem is not None else "",
                    "projection": projection
                })
            except Exception:
                continue


        # Pagination
        if len(players) < page_size:
            break
        start += page_size
        time.sleep(0.1)


    df = pd.DataFrame(all_players)
    if not df.empty:
        df = df.sort_values(by="projection", ascending=False)
        df = df.drop_duplicates(subset=["full_name"], keep="first").reset_index(drop=True)


    return df

