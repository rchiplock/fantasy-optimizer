# 🏈 Fantasy Optimizer


This app helps you **build optimal lineups for DraftKings or FanDuel** using:
✔ Yahoo Fantasy Projections  
✔ Vegas odds (game totals & spreads)  
✔ Smart lineup constraints (**stacking, exposure limits, uniqueness**)  


---


## ✅ What You Need to Use This App


1. **Python 3.9 or newer**
   - Download from [python.org](https://www.python.org/downloads/)


2. **A Yahoo account**
   - Create/login at [Yahoo Fantasy](https://sports.yahoo.com/fantasy/)


3. **An Odds API Key**
   - Sign up at [The Odds API](https://the-odds-api.com)
   - Free tier = 500 calls/month (Plenty for personal use)


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
streamlit run fantasy_optimizer_pro_v2.py
```


✔ This will open the app in your browser at:
```
http://localhost:8501
```


---


### **Step 7: Use the App**
- Enter your Yahoo League ID (from your league URL, e.g., `1168764`).
- Enter your Odds API key.
- Upload your **salaries CSV** from DraftKings or FanDuel.
- Click **Run Optimizer** → Download your optimal lineups! 🎉


---


## ✅ Notes
- **Offseason?** Yahoo projections will show **0** (that’s normal).
- Your Yahoo tokens auto-refresh; no need to log in again unless they expire.
- All data stays **on your machine**; nothing is uploaded to a server.


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
✔ Yahoo Fantasy integration  
✔ Advanced Vegas logic (boost RB in blowouts, downgrade DST in shootouts)  
✔ Lineup constraints:
- Max exposure  
- Min uniqueness  
- Optional QB-WR stacking  


---


---


✅ That’s it! No code editing, just follow these instructions:
- Download → Install → Login → Run → Optimize ✅



