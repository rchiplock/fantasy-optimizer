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
    """Handles Yahoo OAuth authentication and refresh."""
    st.write("🔍 Initializing Yahoo OAuth...")


    # CASE 1: Local OAuth file
    if os.path.exists("oauth2.json"):
        st.write("✅ Using local oauth2.json for auth...")
        oauth = OAuth2(None, None, from_file="oauth2.json")
        if not oauth.token_is_valid():
            st.warning("⚠️ Local token invalid. Refreshing...")
            oauth.refresh_access_token()
        return oauth


    # CASE 2: Streamlit Secrets
    if "oauth" not in st.secrets:
        st.error("❌ Missing [oauth] section in secrets. Add it in Settings → Secrets.")
        st.stop()


    creds = st.secrets["oauth"]
    required_keys = ["consumer_key", "consumer_secret", "access_token", "refresh_token"]
    missing = [k for k in required_keys if k not in creds]
    if missing:
        st.error(f"❌ Missing keys in [oauth]: {missing}. Fix your secrets.")
        st.stop()


    oauth = OAuth2(
        creds["consumer_key"], creds["consumer_secret"],
        access_token=creds["access_token"], refresh_token=creds["refresh_token"]
    )
    if not oauth.token_is_valid():
        st.warning("⚠️ Token expired. Refreshing...")
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
        st.error(f"Error fetching game key: {resp.text}")
        return "461"  # fallback
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
# DEBUG: Fetch weekly projections
# -------------------------------------------------------
def get_weekly_projections(week, page_size=25):
    """
    DEBUG VERSION:
    - Fetch projected Fan Pts from game-level endpoint
    - PRINT raw API response snippet
    - DISPLAY first player XML in Streamlit
    - STOP after debug so you can verify if stat id="900" exists
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


        print(f"\nDEBUG: Request URL: {url}")
        resp = oauth.session.get(url)
        print("DEBUG: Status Code:", resp.status_code)


        if resp.status_code != 200:
            st.error(f"Yahoo API error: {resp.text[:500]}")
            return pd.DataFrame()


        # 🔍 Print first 3000 chars of raw XML to console
        print("\n------ RAW XML RESPONSE START ------\n")
        print(resp.text[:3000])
        print("\n------ RAW XML RESPONSE END ------\n")


        try:
            root = ET.fromstring(resp.text)
        except ET.ParseError as e:
            st.error(f"XML Parse Error: {e}")
            print("Full Response:\n", resp.text)
            return pd.DataFrame()


        root = strip_namespace(root)
        players = root.findall(".//player")


        print(f"DEBUG: Found {len(players)} players on this page (start={start})")


        # ✅ Show first player's raw XML in Streamlit for inspection
        if players:
            first_player_xml = ET.tostring(players[0], encoding="unicode")
            st.subheader("🔍 Raw XML of First Player (Inspect for <stat id='900'>)")
            st.code(first_player_xml, language="xml")
            st.warning("Scroll above for raw XML snippet in console too.")
            st.stop()  # STOP APP so you can inspect before continuing


        # If you want to continue parsing after removing st.stop(), below code works:
        for p in players:
            name_elem = p.find(".//name/full")
            pos_elem = p.find(".//display_position")
            team_elem = p.find(".//editorial_team_abbr")


            # Look for Yahoo Fan Pts stat (id=900)
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


        # pagination
        if len(players) < page_size:
            break
        start += page_size
        time.sleep(0.1)


    df = pd.DataFrame(all_players)
    if not df.empty:
        df = df.sort_values(by="projection", ascending=False).drop_duplicates(subset=["full_name"]).reset_index(drop=True)


    print(f"✅ Total players parsed: {len(df)}")
    return df

