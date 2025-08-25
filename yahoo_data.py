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
    Provides debug info and fails gracefully if misconfigured.
    """
    st.write("🔍 DEBUG: Initializing Yahoo OAuth...")


    # ---------------------------
    # CASE 1: Local Environment
    # ---------------------------
    if os.path.exists("oauth2.json"):
        st.write("✅ Using local oauth2.json file for authentication.")
        oauth = OAuth2(None, None, from_file="oauth2.json")
        if not oauth.token_is_valid():
            st.warning("⚠️ Local token invalid. Attempting refresh...")
            oauth.refresh_access_token()
        return oauth


    # ---------------------------
    # CASE 2: Streamlit Cloud
    # ---------------------------
    if "oauth" not in st.secrets:
        st.error("❌ Missing [oauth] section in Streamlit Secrets. Add it in App → Settings → Secrets.")
        st.stop()


    creds = st.secrets["oauth"]
    required_keys = ["consumer_key", "consumer_secret", "access_token", "refresh_token"]
    missing = [k for k in required_keys if k not in creds]


    if missing:
        st.error(f"❌ Missing keys in [oauth]: {missing}. Fix your Streamlit secrets.")
        st.stop()


    st.write(f"✅ Found OAuth in secrets. Keys present: {list(creds.keys())}")


    try:
        oauth = OAuth2(
            creds["consumer_key"],
            creds["consumer_secret"],
            access_token=creds["access_token"],
            refresh_token=creds["refresh_token"]
        )


        if not oauth.token_is_valid():
            st.warning("⚠️ Token expired from secrets. Refreshing...")
            oauth.refresh_access_token()


        st.write("✅ Yahoo OAuth initialized successfully.")
        return oauth


    except Exception as e:
        st.error(f"❌ Failed to initialize Yahoo OAuth: {e}")
        st.stop()


# -------------------------------------------------------
# Strip XML namespaces for easier parsing
# -------------------------------------------------------
def strip_namespace(root):
    """Removes namespace from XML tags for easy access."""
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
        st.error(f"Error fetching game key: {resp.text}")
        return "461"  # fallback game key


    try:
        root = ET.fromstring(resp.text)
        root = strip_namespace(root)
        game_key_elem = root.find(".//game_key")
        return game_key_elem.text if game_key_elem is not None else "461"
    except Exception as e:
        st.warning(f"Exception parsing game key: {e}")
        return "461"


# -------------------------------------------------------
# Build full league key
# -------------------------------------------------------
def build_league_key(league_id):
    game_key = get_current_nfl_game_key()
    return f"{game_key}.l.{league_id}"


# -------------------------------------------------------
# Fetch weekly projections with pagination
# -------------------------------------------------------
def get_weekly_projections(league_key, week, page_size=25):
    """
    Fetch ALL Week-specific player projections for given league_key using pagination.
    Returns Pandas DataFrame with columns: [full_name, pos, team_abbr, projection]
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
            st.error(f"Error fetching projections at start={start}: {resp.text}")
            break


        root = ET.fromstring(resp.text)
        root = strip_namespace(root)
        players = root.findall(".//player")


        if not players:
            break  # No more player pages


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


        st.write(f"✅ Page starting at {start}: fetched {len(players)} players...")


        if len(players) < page_size:
            break  # Last page


        start += page_size
        time.sleep(0.05)  # minimize delay for speed (from 0.2 → 0.05)


    df = pd.DataFrame(all_players)


    if not df.empty:
        df = df.sort_values(by="projection", ascending=False)
        df = df.drop_duplicates(subset=["full_name"], keep="first").reset_index(drop=True)


    st.write(f"✅ Total unique players fetched: {len(df)}")
    return df