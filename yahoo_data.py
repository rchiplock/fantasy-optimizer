from yahoo_oauth import OAuth2
import xml.etree.ElementTree as ET
import pandas as pd
import time
import os
import streamlit as st


# -------------------------------------------------------
# Authenticate with Yahoo OAuth (Local + Streamlit Cloud)
# -------------------------------------------------------
def get_oauth():
    """
    Returns an authorized Yahoo OAuth session.
    Supports:
    - Local mode: reads oauth2.json from current directory
    - Cloud mode: reads credentials from Streamlit secrets
    """
    if os.path.exists("oauth2.json"):
        # Local development
        oauth = OAuth2(None, None, from_file="oauth2.json")
    else:
        # Cloud or no file: use Streamlit secrets
        creds = st.secrets["oauth"]
        oauth = OAuth2(
            creds["consumer_key"],
            creds["consumer_secret"],
            access_token=creds["access_token"],
            refresh_token=creds["refresh_token"]
        )


    if not oauth.token_is_valid():
        oauth.refresh_access_token()
    return oauth


# -------------------------------------------------------
# Remove XML namespace for easier parsing
# -------------------------------------------------------
def strip_namespace(root):
    for elem in root.iter():
        if "}" in elem.tag:
            elem.tag = elem.tag.split("}", 1)[1]
    return root


# -------------------------------------------------------
# Get current NFL game key dynamically
# -------------------------------------------------------
def get_current_nfl_game_key():
    oauth = get_oauth()
    url = "https://fantasysports.yahooapis.com/fantasy/v2/game/nfl"
    resp = oauth.session.get(url)


    if resp.status_code != 200:
        st.error(f"Error getting game key: {resp.text}")
        return "461"  # fallback


    try:
        root = ET.fromstring(resp.text)
        root = strip_namespace(root)
        game_key_elem = root.find(".//game_key")
        return game_key_elem.text if game_key_elem is not None else "461"
    except Exception:
        return "461"


# -------------------------------------------------------
# Build full league key from League ID
# -------------------------------------------------------
def build_league_key(league_id):
    game_key = get_current_nfl_game_key()
    return f"{game_key}.l.{league_id}"


# -------------------------------------------------------
# Get Weekly Projections (with Pagination)
# -------------------------------------------------------
def get_weekly_projections(league_key, week, page_size=25):
    """
    Fetch ALL Week-specific player projections for a given league_key using pagination.
    """
    oauth = get_oauth()
    all_players = []
    start = 0


    while True:
        url = (
            f"https://fantasysports.yahooapis.com/fantasy/v2/league/{league_key}"
            f"/players;status=A;type=week;week={week};start={start};count={page_size};out=stats"
        )


        resp = oauth.session.get(url)
        if resp.status_code != 200:
            print(f"Error fetching projections at start={start}: {resp.text}")
            break


        root = ET.fromstring(resp.text)
        root = strip_namespace(root)
        players = root.findall(".//player")


        if not players:
            break  # No more players


        for p in players:
            try:
                name_elem = p.find(".//name/full")
                pos_elem = p.find(".//display_position")
                team_elem = p.find(".//editorial_team_abbr")
                points_elem = p.find(".//player_points/total")
                if name_elem is not None:
                    all_players.append({
                        "full_name": name_elem.text.lower(),
                        "pos": pos_elem.text.upper() if pos_elem is not None else "",
                        "team_abbr": team_elem.text.upper() if team_elem is not None else "",
                        "projection": float(points_elem.text) if points_elem is not None else 0.0
                    })
            except Exception:
                continue


        # Debug
        print(f"✅ Page starting at {start}: {len(players)} players fetched")
        if len(players) < page_size:
            break


        start += page_size
        time.sleep(0.2)


    # Deduplicate by name
    df = pd.DataFrame(all_players)
    if not df.empty:
        df = df.sort_values(by='projection', ascending=False)
        df = df.drop_duplicates(subset=['full_name'], keep='first').reset_index(drop=True)


    print(f"✅ Total unique players after pagination: {len(df)}")
    return df

