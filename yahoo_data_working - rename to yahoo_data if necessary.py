from yahoo_oauth import OAuth2
import xml.etree.ElementTree as ET
import pandas as pd
import time


# -------------------------------------------------------
# Authenticate with Yahoo OAuth
# -------------------------------------------------------
def get_oauth():
    """
    Returns an authorized Yahoo OAuth session.
    Refreshes token if needed.
    Requires 'oauth2.json' file with consumer_key, consumer_secret, and tokens.
    """
    oauth = OAuth2(None, None, from_file="oauth2.json")
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
        print(f"Error getting game key: {resp.text}")
        return "461"  # fallback key for current season (2025 NFL)


    try:
        root = ET.fromstring(resp.text)
        root = strip_namespace(root)
        game_key_elem = root.find(".//game_key")
        return game_key_elem.text if game_key_elem is not None else "461"
    except Exception:
        return "461"


# -------------------------------------------------------
# Build full league key from league ID
# -------------------------------------------------------
def build_league_key(league_id):
    game_key = get_current_nfl_game_key()
    return f"{game_key}.l.{league_id}"


# -------------------------------------------------------
# Get all user leagues (for league selection)
# -------------------------------------------------------
def get_user_leagues():
    oauth = get_oauth()
    url = "https://fantasysports.yahooapis.com/fantasy/v2/users;use_login=1/games;out=leagues"
    resp = oauth.session.get(url)


    if resp.status_code != 200:
        raise Exception(f"Error getting leagues: {resp.text}")


    root = ET.fromstring(resp.text)
    root = strip_namespace(root)


    leagues = []
    for league in root.findall(".//league"):
        league_key = league.find("league_key").text
        league_name = league.find("name").text
        leagues.append({"league_key": league_key, "league_name": league_name})
    return leagues


# -------------------------------------------------------
# Get weekly projections with proper pagination
# -------------------------------------------------------
def get_weekly_projections(league_key, week, page_size=25):
    """
    Fetch ALL Week-specific player projections for a given Yahoo league using pagination.
    Yahoo returns 25 players per page for league player lists.
    
    Returns:
        DataFrame with columns: full_name, pos, team_abbr, projection
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
            break  # no more players, stop loop


        for p in players:
            try:
                name_elem = p.find(".//name/full")
                pos_elem = p.find(".//display_position")
                team_elem = p.find(".//editorial_team_abbr")
                points_elem = p.find(".//player_points/total")


                if name_elem is not None:
                    all_players.append({
                        "full_name": name_elem.text.lower(),  # for easier matching
                        "pos": pos_elem.text.upper() if pos_elem is not None else "",
                        "team_abbr": team_elem.text.upper() if team_elem is not None else "",
                        "projection": float(points_elem.text) if points_elem is not None else 0.0
                    })
            except Exception:
                continue


        print(f"✅ Page starting at {start}: {len(players)} players fetched")
        if len(players) < page_size:
            break  # Reached last page


        start += page_size
        time.sleep(0.2)  # rate limit safety


    # Create DataFrame and deduplicate
    df = pd.DataFrame(all_players)
    if not df.empty:
        df = df.sort_values(by='projection', ascending=False)
        df = df.drop_duplicates(subset=['full_name'], keep='first').reset_index(drop=True)


    print(f"✅ Total unique players after pagination: {len(df)}")
    return df

