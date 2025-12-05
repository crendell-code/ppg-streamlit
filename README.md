Galactic Wanderer (Streamlit) — Deploy Guide
-------------------------------------------

Files:
- `app_streamlit.py` : Streamlit web app entry (use this for hosting)
- `PPG_v2.py` : Core procedural generator (unchanged)
- `requirements.txt` : Dependencies for Streamlit Cloud

Deploy to Streamlit Community Cloud (no installs for players)
1. Create a GitHub repo with this project (push the folder).
   Example:
     git init
     git add .
     git commit -m "Add Streamlit app"
     gh repo create <your-repo-name> --public --source=. --push

2. Go to https://share.streamlit.io and sign in (free).
3. Click "New app", connect your GitHub repo, set the main file to `app_streamlit.py`, and click "Deploy".
4. The app will build and be available at a URL you can share. Your friends just open the link — no installs required.

Local testing (optional)
- If you want to test locally (requires installing Streamlit):
  python3 -m pip install --upgrade pip
  python3 -m pip install -r requirements.txt
  streamlit run app_streamlit.py

