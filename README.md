# 🏈 DFS Fantasy Football Optimizer


This app helps you **build optimal lineups for DraftKings or FanDuel** using:

✔ Yahoo Fantasy Projections with fallback to **FantasyPros** 

✔ Vegas odds (game totals & spreads with dynamic control)  

✔ Smart lineup constraints (**stacking, uniqueness**)

✔ Live user-controlled Vegas impact sliders  



---


## ✅ What You Need to Use This App


1. **Python 3.9 or newer**
   - Download from [python.org](https://www.python.org/downloads/)


2. **A Yahoo account** (for projections)
   - Create/login at [Yahoo Fantasy](https://sports.yahoo.com/fantasy/)
  

3. **An Odds API Key**
   - Sign up at [The Odds API](https://the-odds-api.com)
   - Free tier = 500 calls/month (Plenty for personal use)
  

4. **DraftKings or FanDuel salary CSV**


---


## ✅ How to Set Up and Run Locally (Step-by-Step)


---


### **Step 1: Get the App Files**
1. Go to [THIS GitHub Repo](https://github.com/rchiplock/fantasy-optimizer).
2. Click the green **“Code”** button → choose **Download ZIP**.
3. Extract the ZIP to a folder (example: `Desktop/fantasy-optimizer`).


---


### **Step 2: Open a Terminal (Command Prompt on Windows)**
- Navigate to the app folder:
```
cd Desktop/fantasy-optimizer
```


---


### **Step 3: Install Requirements**
Run:
```
pip install -r requirements.txt
```


---


### **Step 4: Set Up Yahoo Authentication**
1. The first time you run the app locally, it will create a file called `oauth2.json`.
2. To create this file:
   - Run the app (Step 6 below).
   - The app will show a Yahoo login link in your console.
   - **Click the link** → sign in → copy the code → paste it in the console.
3. Done! Your Yahoo credentials are now stored **locally** (safe on your computer).


---


### **Step 5: Get Your Odds API Key**
- From [The Odds API](https://the-odds-api.com), copy your **API key**.


---


### **Step 6: Run the App**
Run this command:
```
streamlit run fantasy_optimizer_pro.py
```
If that **doesn't work** (you see "'streamlit is not recognized"), use:
```
python -m streamlit run fantasy_optimizer_pro.py
```

✔ This will open the app in your browser at:
```
http://localhost:8501
```


---


### **Step 7: Use the App**
- Enter your Yahoo League ID (from your league URL, e.g., `1168764`).
- Enter your Odds API key.
- Upload your **salaries CSV** from DraftKings or FanDuel (See Below).
- Click **Run Optimizer** → Download your optimal lineups! 🎉


---


## ✅ Notes
- **Offseason?** Yahoo projections will show **0** (that’s normal).
- Your Yahoo tokens auto-refresh; no need to log in again unless they expire.
- All data stays **on your machine**; nothing is uploaded to a server.


---


## ✅ Retrieving Salary Files
- Login to your Draftkings or FanDuel account
- Select a **Classic** (Draftkings) or **Full Roster** (FanDuel) NFL contest
- Click on **Draft Team** (Draftkings) or **Enter new lineup** (FanDuel)
- Click the link to download the player list (salary file):
- Draftkings:
  <img width="2525" height="1521" alt="Draftkings Salary File Download" src="https://github.com/user-attachments/assets/4a326409-920b-4744-9631-443e2775d654" />
- FanDuel:
  <img width="3550" height="1555" alt="FanDuel Salary File Download" src="https://github.com/user-attachments/assets/8776ddbd-0447-4ab7-883d-c79b6d4c2982" />
- Save the file as a .CSV file with the source name included
-    **Draftkings example**: draftkings week 1 salary.csv (must have 'draftkings' or 'dk' in file name to detect correct salary constraints)
-    **FanDuel example**: fanduel week 1 salary.csv
- These are now ready to upload into the app.


---


## ✅ Troubleshooting
- ❌ **`st.secrets has no key oauth`**  
  → Ignore this error locally. It only applies to cloud deployment.
- ❌ **App hanging or slow**  
  → First run may take 15–30 seconds to fetch projections (Yahoo API).
- ❌ **No DST in player pool**  
  → Ensure you uploaded the correct salary file for NFL.


---


## ✅ Features at a Glance
✔ Supports DraftKings & FanDuel salary files 

✔ Yahoo or FantasyPros (fallback) Projections 

✔ Advanced Vegas logic for projected game flow (boost favorite RB / underdog pass catchers in blowouts, downgrade DST in shootouts) 
- **Spread Trigger (pts)**: When does game script start to matter? Set the point spread size (favorite vs underdog) where adjustments kick in. **Example**: At 7 pts, favored RBs gain an edge; underdog WR/TEs see more volume

- **Over/Under Trigger**: Games above this Over/Under threshold are considered shootouts and would boost WR/TE while slightly downgrading a DST. **Example**: At 47, WR/TE get a bump in high-scoring games; DST would get a small reduction

- **Vegas Impact Intensity (%)**: How much weight do Vegas odds add to player projections? 0% = ignore Vegas, 20% = strong game-script adjustments for spreads/totals

✔ Lineup constraints:  
- Min uniqueness  
- Optional QB-WR stacking  


---


✅ That’s it! No code editing, just follow these instructions:
- Download → Install → Login → Run → Optimize ✅


---


## 💸 Support This Project


This app is 100% free and open source, built for fun to help optimize your DFS lineups.  
If it helped you build better lineups (or even hit a big win 🏆), consider supporting the project!


👉 **[Buy Me a Coffee ☕](https://www.buymeacoffee.com/rchiplock)**  


Your support helps keep this project alive and updated. Thank you! 🙌  


---


### ✅ Official Links and Trust Notice
The **ONLY** official donation link for this project is the one above or linked from this GitHub repository.
If you find this app elsewhere with different donation links, please ignore them - they are **not official**.

Check the latest version and details here:
**[https://github.com/rchiplock/fantasy-optimizer](https://github.com/rchiplock/fantasy-optimizer)**


---







