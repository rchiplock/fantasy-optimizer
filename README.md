# 🏈 DFS Fantasy Football Optimizer


Build **optimal DraftKings or FanDuel lineups** in seconds using:


✔ **FantasyPros projections**  
✔ **Vegas odds (spreads & totals)** with dynamic control  
✔ **Smart lineup constraints** (stacking, uniqueness, exposure)  
✔ **Fully interactive web app – no install needed!**  


---


## ✅ Try It Now (No Installation!)
👉 **Launch the App:**  
[**fantasy-optimizer-pro.streamlit.app**](https://fantasy-optimizer-pro.streamlit.app)


Runs entirely in the cloud. No setup. No coding.  


---


## ✅ What You Need
✅ **1. Odds API Key**  
Free at [The Odds API](https://the-odds-api.com/).  
- Get your API key (free tier = 500 calls/month – plenty for personal use).  


✅ **2. Salary CSV from DraftKings or FanDuel**  
- DraftKings: Download from the contest page "Player List" link  
- FanDuel: Download from the contest lobby  
🖥️ 📱 **Follow Retrieving Salary Files instructions below**
- **No need to rename downloaded file**, but file must include the source in the name (e.g., dk, draftkings, fanduel, fd)  


---


## ✅ How to Use the App
1. **Open the app** → [fantasy-optimizer-pro.streamlit.app](https://fantasy-optimizer-pro.streamlit.app)  
2. **Upload your salary file** (DraftKings or FanDuel)  
3. **Enter your Odds API key** (from The Odds API)
- App can still run without and Odds API key but will not return any Vegas odds adjustments
5. Adjust **Vegas impact sliders** & options (uniqueness, stacking, etc.)  
6. Click **Run Optimizer** → Download your lineups! 🎉  

## ↔️ Player Matching
Player names **don't always match** between FantasyPros and DraftKings / Fanduel

- Example: CJ Stroud - C.J. Stroud

The app organizes unmatched players by **highest salary (most relevant)** and shows the top 50

Click the dropdown for any player you'd like to match and begin typing their name

Select the entry that matches the player you are trying to match up

Once you select the matching entry, that player is automatically added to the player pool and lineups are updated with that player available

If you don't want to match anyone, just scroll down to the bottom to retrieve your lineups 🏆


---


## ✅ Retrieving Salary Files - 🖥️ Desktop
- Login to your Draftkings or FanDuel account **on a browser** (cannot download player lists in the apps)

[🏆 DraftKings](https://www.draftkings.com/home/contestlistbysport?sport=NFL)

[🏆 FanDuel](https://www.fanduel.com/contests/nfl/5387)
- Select a **Classic** (Draftkings) or **Full Roster** (FanDuel) NFL contest
- Click on **Draft Team** (Draftkings) or **Enter new lineup** (FanDuel)
- Click the link to download the player list (salary file):
- Draftkings:
  <img width="2525" height="1521" alt="Draftkings Salary File Download" src="https://github.com/user-attachments/assets/4a326409-920b-4744-9631-443e2775d654" />
- FanDuel:
  <img width="3550" height="1555" alt="FanDuel Salary File Download" src="https://github.com/user-attachments/assets/8776ddbd-0447-4ab7-883d-c79b6d4c2982" />
- Save the file as a .CSV file with the source name included (iOS users can convert the file via the **Numbers** app)
-    **Draftkings example**: draftkings week 1 salary.csv (must have 'draftkings' or 'dk' in file name to detect correct salary constraints)
-    **FanDuel example**: fanduel week 1 salary.csv
- These are now ready to upload into the app.


---

## ✅ Retrieving Salary Files - 📱 Mobile


Follow these quick steps to download a file and make sure it's ready to upload as a **CSV** on your mobile device:


---


### ✅ For iPhone (Safari)


1. **Tap the retrieve salary file link** on the app.
<img width="207" height="448" alt="IMG_screenshot" src="https://github.com/user-attachments/assets/c3ec29ca-9e23-4308-8444-9879a67a8677" />


2. Select your **classic** or **full roster** contest
<img width="207" height="448" alt="IMG_9381" src="https://github.com/user-attachments/assets/eb56e07e-e24f-448f-a014-137d59a63de6" />
<img width="207" height="448" alt="IMG_9382" src="https://github.com/user-attachments/assets/15a191c7-27c7-4220-bd90-a150bb0dee56" />
<img width="207" height="448" alt="IMG_9372" src="https://github.com/user-attachments/assets/708bfa9f-f953-48aa-b747-ec5e9cd6ae34" />
<img width="207" height="448" alt="IMG_9373" src="https://github.com/user-attachments/assets/7276cfe8-e463-409b-8f6a-7f85b09a2c4d" />


3. **Export** the player list
   - **IMPORTANT: For Draftkings - You may need to turn your phone to landscape to see the Export to CSV option**
<img width="448" height="207" alt="IMG_9383" src="https://github.com/user-attachments/assets/8f347657-753d-4dc5-b239-e88fbe85b12b" />
<img width="207" height="448" alt="IMG_9374" src="https://github.com/user-attachments/assets/de166328-adc1-4931-bbd4-77f3f9ed9c98" />


4. **Save** the .CSV to your files
<img width="207" height="448" alt="IMG_9375" src="https://github.com/user-attachments/assets/64276690-dde8-454a-aeb6-0149fda4011d" />
<img width="448" height="207" alt="IMG_9385" src="https://github.com/user-attachments/assets/d42d0654-e872-4967-a663-af575c3c5268" />


5. **Upload** your file (it should appear in your recents)
<img width="207" height="448" alt="IMG_9388 - Copy" src="https://github.com/user-attachments/assets/1a9b5b93-9ff7-4c3d-934c-11f7ac782a4f" />
<img width="207" height="448" alt="IMG_9387" src="https://github.com/user-attachments/assets/dcfb2055-5ae1-4a36-959d-87bda0c83861" />


6. **Run** the optimizer
<img width="207" height="448" alt="IMG_9388" src="https://github.com/user-attachments/assets/bcc23ad1-a88c-4b4c-8a58-ed248fe79ea1" />
<img width="207" height="448" alt="IMG_9389" src="https://github.com/user-attachments/assets/6459cf26-4236-454f-b311-0bb8918fcf26" />


---


### ✅ For Android (Chrome)


1. **Tap the download link** on the website.  
2. The file will download to your **Downloads** folder.  
3. Open the **Files** (or **My Files**) app.  
4. Find your file:  
   - If the file name does **not** end with `.csv`, **rename it**:  
     - Tap the **3-dot menu** → **Rename** → Add `.csv` to the end (example: `data.csv`).
5. **Follow steps 5 and 6** in the iPhone instructions above


---


## ✅ Features at a Glance
✔ **DraftKings & FanDuel support**  
✔ **FantasyPros Projections** (built-in, always up-to-date)  
✔ Interactive optimizer settings:
- *QB-WR stack option*:
   - Classic fantasy football strategy
- *Scoring Optimization*:
   - Adjust point projections for low risk (Floor), high risk (Ceiling), or play it safe (Median)
- *Randomness for GPP variance*:
   - Add randomness for Guaranteed Prize Pool Contests
   - More randomness = more unique lineups 
- *Minimum projection filter*:
   - Ignore players below this point projection
     
✔ **Vegas-adjusted scoring** with user controls (Vegas lines tell us the expected game scripts):
   - **Big Favorites ➡️ Run the ball more ➡️ RB boost**
   - **Big Underdogs ➡️ Throw often ➡️ WR/TE boost**
   - **High Total Games ➡️ Shootouts ➡️ more upside for pass-catchers, less for DST**

- *Spread Trigger (points)*: 
   - When a team is favored (or a big underdog) by at least **this many points**, we start adjusting projections.
   - **Favored big?** Great spot for RBs (more rush attempts when leading)
   - **Big underdog?** Extra love for WRs/TEs (more passing when trailing - garbage time points!)  
- *Over/Under Trigger (points)*: 
   - If a game's **total points line** is **above this number**, we boost receiving options (more scoring expected)
   - **High total = Shootout alert!** WRs & TEs shine
   - **Low total = Defensive battle.** DST gets a little bump
- *Vegas Impact (%)*:
   - Decide how much the betting market moves the needle on player projections
   - **0% = Pure projections only.** ignore the line
   - **10% = Small edge from Vegas baked in**
   - **20% = Heavy lean on Vegas signals.** Trust the market like a sharp

 
  
- Multi-lineup builder  
✔ Fuzzy player name matching + manual corrections  
✔ Download optimized lineups as CSV  


---


## ✅ Notes
- No login, OAuth, or local install required  
- Runs live in your browser on Streamlit Cloud  
- Odds API key is **free** for casual use  


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

























