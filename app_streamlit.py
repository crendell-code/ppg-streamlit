# app_streamlit.py — Galactic Wanderer Game
import streamlit as st
from io import BytesIO
from PIL import Image, ImageDraw, ImageFilter
from PPG_v2 import generate_planet, explore, scan, get_trade_prices, buy, sell
import os
import signal

# ===== COLOR PALETTE =====
CLIMATE_COLOR = {
    "arid": "#d79f6f", "temperate": "#6fbf6f", "tropical": "#2e8b57",
    "frozen": "#9fd3ff", "toxic": "#a3b13a", "volcanic": "#ff6b4d",
    "oceanic": "#4da6ff", "stormy": "#7f8fa6", "radioactive": "#8cff7a",
    "default": "#cccccc"
}

# ===== SESSION STATE INITIALIZATION =====
if "player" not in st.session_state:
    st.session_state.player = {"fuel": 100, "hull": 100, "credits": 50, "cargo": {}, "turns": 0}
if "planet" not in st.session_state:
    st.session_state.planet = generate_planet()
if "log" not in st.session_state:
    st.session_state.log = []
if "last_msg" not in st.session_state:
    st.session_state.last_msg = ""

# ===== UTILITY FUNCTIONS =====
def make_planet_image(climate, size=360):
    """Generate procedural planet image with climate-based colors."""
    color = CLIMATE_COLOR.get(climate.lower(), CLIMATE_COLOR["default"])
    bg = Image.new("RGB", (size, size), "#06121a")
    draw = ImageDraw.Draw(bg)
    
    cx, cy, radius = size // 2, size // 2, int(size * 0.4)
    
    # Radial gradient
    for r in range(radius, 0, -1):
        f = r / radius
        base = tuple(int(color.lstrip("#")[i:i+2], 16) for i in (0, 2, 4))
        shade = tuple(int(min(255, base[i] * (0.4 + 0.6 * f) + 255*(1-f)*0.05)) for i in range(3))
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=shade)
    
    # Highlight
    highlight = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    hd = ImageDraw.Draw(highlight)
    hd.ellipse([cx - 20, cy - 25, cx + 28, cy + 15], fill=(255, 255, 255, 200))
    highlight = highlight.filter(ImageFilter.GaussianBlur(6))
    bg.paste(highlight, (0, 0), highlight)
    
    # Ring
    ring = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    rd = ImageDraw.Draw(ring)
    rd.ellipse([cx - int(radius*1.1), cy - int(radius*0.2), cx + int(radius*1.1), cy + int(radius*0.05)], 
               outline=(200, 180, 120, 190), width=6)
    ring = ring.rotate(-22, center=(cx, cy))
    bg.paste(ring, (0, 0), ring)
    
    # Vignette
    vign = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    vd = ImageDraw.Draw(vign)
    vd.ellipse([0, 0, size, size], fill=(0, 0, 0, 20))
    bg = Image.alpha_composite(bg.convert("RGBA"), vign).convert("RGB")
    
    bio = BytesIO()
    bg.save(bio, format="PNG")
    bio.seek(0)
    return bio

def log(msg):
    """Add message to game log."""
    st.session_state.log.append(msg)
    st.session_state.last_msg = msg

# ===== PAGE CONFIG & STYLING =====
st.set_page_config(page_title="Galactic Wanderer", layout="wide", initial_sidebar_state="expanded")

# Hide Streamlit chrome
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    [data-testid="stToolbar"] {visibility: hidden;}
    [data-testid="stButton"][data-key="menu_toggle"] button {
        background-color: transparent !important;
        border: none !important;
        color: white !important;
        font-size: 28px !important;
        padding: 0 !important;
        height: 40px !important;
    }
    [data-testid="stButton"][data-key="menu_toggle"] button:hover {
        background-color: rgba(255,255,255,0.15) !important;
    }
    </style>
""", unsafe_allow_html=True)

# ===== FIXED MENU BUTTON & STYLING =====
st.markdown("""
    <style>
    /* Fixed menu button in top right */
    [data-testid="stButton"][data-key="menu_toggle"] button {
        position: fixed !important;
        top: 20px !important;
        right: 20px !important;
        z-index: 1000 !important;
        background-color: transparent !important;
        border: none !important;
        color: white !important;
        font-size: 28px !important;
        padding: 0 !important;
        height: 40px !important;
        width: 40px !important;
    }
    [data-testid="stButton"][data-key="menu_toggle"] button:hover {
        background-color: rgba(255,255,255,0.15) !important;
    }
    </style>
""", unsafe_allow_html=True)

# ===== HEADER =====
st.markdown("<h1 style='text-align:center;'>Galactic Wanderer</h1>", unsafe_allow_html=True)

# ===== MENU BUTTON (FIXED POSITION) =====
if st.button("☰", key="menu_toggle"):
    st.session_state.menu_open = not st.session_state.get("menu_open", False)

# ===== MENU DROPDOWN =====
if st.session_state.get("menu_open", False):
    # Create a fixed position menu box with options
    menu_html = """
    <div style="position:fixed;top:70px;right:20px;background:#0e1419;border:1px solid #555;border-radius:8px;padding:15px;z-index:999;width:150px;box-shadow:0 4px 12px rgba(0,0,0,0.5);">
        <p style="margin:0 0 10px 0;color:white;text-align:center;font-weight:bold;">Menu</p>
    </div>
    """
    st.markdown(menu_html, unsafe_allow_html=True)
    
    # Create menu options in a narrow column on the left
    menu_col, _ = st.columns([0.8, 5])
    with menu_col:
        if st.button("ℹ️ Info", key="menu_info", use_container_width=True):
            st.session_state.show_info = not st.session_state.get("show_info", False)
            st.session_state.menu_open = False
            st.rerun()
        if st.button("🔄 Reset", key="menu_reset", use_container_width=True):
            st.session_state.player = {"fuel": 100, "hull": 100, "credits": 50, "cargo": {}, "turns": 0}
            st.session_state.planet = generate_planet()
            st.session_state.log = []
            st.session_state.last_msg = ""
            st.session_state.auto_next = False
            st.session_state.menu_open = False
            log("Game reset. Fresh start!")
            st.rerun()
        if st.button("❌ Quit", key="menu_quit", use_container_width=True):
            st.session_state.menu_open = False
            os.kill(os.getpid(), signal.SIGTERM)

# ===== HANDLE MENU ACTIONS =====
query_params = st.query_params
if query_params.get("menu_action") == ["reset"]:
    st.session_state.player = {"fuel": 100, "hull": 100, "credits": 50, "cargo": {}, "turns": 0}
    st.session_state.planet = generate_planet()
    st.session_state.log = []
    st.session_state.last_msg = ""
    st.session_state.auto_next = False
    st.session_state.menu_open = False
    log("Game reset. Fresh start!")
    st.query_params.clear()
    st.rerun()

if query_params.get("menu_action") == ["quit"]:
    st.query_params.clear()
    st.session_state.menu_open = False
    os.kill(os.getpid(), signal.SIGTERM)

if query_params.get("menu_action") == ["info"]:
    st.session_state.show_info = not st.session_state.get("show_info", False)
    st.session_state.menu_open = False
    st.query_params.clear()
    st.rerun()
# ===== MENU DROPDOWN =====
if st.session_state.get("menu_open", False):
    st.markdown("""
    <style>
    .menu-button {
        display: inline-block;
        width: 100%;
        padding: 10px 12px;
        margin-bottom: 8px;
        background-color: #262730;
        color: white;
        border: 1px solid #555;
        border-radius: 4px;
        cursor: pointer;
        font-weight: bold;
        text-align: center;
        transition: all 0.2s;
    }
    .menu-button:hover {
        background-color: #3a3f47;
        border-color: #888;
    }
    </style>
    """, unsafe_allow_html=True)
    
    menu_col1, menu_col2, menu_col3 = st.columns([1, 1, 1])
    with menu_col1:
        if st.button("🔄 Reset", key="menu_reset"):
            st.session_state.player = {"fuel": 100, "hull": 100, "credits": 50, "cargo": {}, "turns": 0}
            st.session_state.planet = generate_planet()
            st.session_state.log = []
            st.session_state.last_msg = ""
            st.session_state.auto_next = False
            st.session_state.menu_open = False
            log("Game reset. Fresh start!")
            st.rerun()
    with menu_col2:
        if st.button("ℹ️ Info", key="menu_info"):
            st.session_state.show_info = not st.session_state.get("show_info", False)
            st.session_state.menu_open = False
            st.rerun()
    with menu_col3:
        if st.button("❌ Quit", key="menu_quit"):
            st.session_state.menu_open = False
            os.kill(os.getpid(), signal.SIGTERM)
if st.session_state.get("show_info", False):
    st.markdown("""
    **Galactic Wanderer** — Space exploration trading game.
    
    **Goal:** Explore planets, gather resources, build wealth.
    
    **Actions:**
    - Generate New Planet | Land & Explore | Scan from Orbit | Buy/Sell Resources
    
    **Tips:** Hostile planets won't trade • Buy low, sell high • Manage fuel & hull
    """)

# ===== MAIN GAME LAYOUT =====
col_left, col_mid, col_right = st.columns([1.1, 0.9, 1])

with col_left:
    planet = st.session_state.planet
    st.image(make_planet_image(planet.get("climate", "default")), use_container_width=True)
    st.markdown(f"### {planet.get('name', 'Unknown')}")
    for key in ["climate", "biome", "life", "atmosphere", "danger", "event", "resource"]:
        if key == "resource":
            st.markdown(f"**{key.title()}:** {planet.get(key)} — value {planet.get('value')}")
        else:
            st.markdown(f"**{key.title()}:** {planet.get(key)}")
    st.markdown(f"**Civilization:** {planet.get('civilization')} ({planet.get('temperament')})")

with col_mid:
    st.subheader("Ship")
    p = st.session_state.player
    st.metric("Credits", f"{p['credits']}")
    st.metric("Turns", f"{p['turns']}")
    st.text("Fuel")
    st.progress(int(max(0, min(100, p["fuel"]))))
    st.text("Hull Integrity")
    st.progress(int(max(0, min(100, p["hull"]))))
    
    st.markdown("**Cargo**")
    cargo = p.get("cargo", {})
    if cargo:
        st.table([{"Resource": k, "Qty": v["quantity"], "Value": v["value"]} for k, v in cargo.items()])
    else:
        st.write("Empty")
    
    st.markdown("**Last action**")
    st.info(st.session_state.last_msg or "No actions yet")

with col_right:
    st.subheader("Actions")
    if st.button("Generate New Planet", key="gen_planet"):
        st.session_state.planet = generate_planet()
        log(f"Generated planet {st.session_state.planet.get('name')}")
        st.rerun()
    if st.button("Land & Explore", key="explore"):
        res = explore(st.session_state.player, st.session_state.planet)
        for m in res["messages"]:
            log(m)
        st.session_state.player["turns"] += 1
        st.rerun()
    if st.button("Scan from Orbit", key="scan"):
        res = scan(st.session_state.player, st.session_state.planet)
        for m in res["messages"]:
            log(m)
        st.session_state.player["turns"] += 1
        st.rerun()
    
    st.markdown("---")
    st.subheader("Market")
    if st.session_state.planet.get("temperament", "").lower() == "hostile":
        st.write("Locals hostile — trade unavailable.")
    else:
        resource = st.session_state.planet.get("resource", "Unknown")
        buy_price, sell_price = get_trade_prices(st.session_state.planet)
        st.write(f"Resource: **{resource}** | Buy: {buy_price} | Sell: {sell_price}")
        qty = st.slider("Quantity", 1, 10, 1)
        col_b, col_s = st.columns(2)
        if col_b.button("Buy", key="buy"):
            r = buy(st.session_state.player, st.session_state.planet, qty=qty)
            for m in r["messages"]:
                log(m)
            st.rerun()
        if col_s.button("Sell", key="sell"):
            r = sell(st.session_state.player, st.session_state.planet, qty=qty)
            for m in r["messages"]:
                log(m)
            st.rerun()
    
    st.markdown("---")
    st.checkbox("Auto-generate new planet each turn", value=False, key="auto_next")

# ===== COMMUNICATIONS LOG =====
st.markdown("---")
st.subheader("Communications Log")
log_col1, log_col2 = st.columns([3, 1])
with log_col1:
    for entry in st.session_state.log[-12:][::-1]:
        st.write(f"- {entry}")
with log_col2:
    if st.button("Clear Log", key="clear_log"):
        st.session_state.log = []
        st.session_state.last_msg = ""

# ===== AUTO-GENERATE NEXT PLANET =====
if st.session_state.get("auto_next", False):
    prev_turns = st.session_state.get("_prev_turns", st.session_state.player["turns"])
    if st.session_state.player["turns"] > prev_turns:
        st.session_state.planet = generate_planet()
        log(f"Auto-generated planet {st.session_state.planet.get('name')}")
    st.session_state._prev_turns = st.session_state.player["turns"]