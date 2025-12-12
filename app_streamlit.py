# app_streamlit.py — Galactic Wanderer Game (top-right floating menu, fixed scrolling)
import streamlit as st
import streamlit.components.v1 as components
from io import BytesIO
from PIL import Image, ImageDraw, ImageFilter
from PPG_v2 import generate_planet, explore, scan, get_trade_prices, buy, sell

# ===== COLOR PALETTE =====
CLIMATE_COLOR = {
    "arid": "#d79f6f", "temperate": "#6fbf6f", "tropical": "#2e8b57",
    "frozen": "#9fd3ff", "toxic": "#a3b13a", "volcanic": "#ff6b4d",
    "oceanic": "#4da6ff", "stormy": "#7f8fa6", "radioactive": "#8cff7a",
    "default": "#cccccc"
}

# ===== SESSION STATE INITIALIZATION =====
ss = st.session_state
if "player" not in ss:
    ss.player = {"fuel": 100, "hull": 100, "credits": 50, "cargo": {}, "turns": 0}
if "planet" not in ss:
    ss.planet = generate_planet()
if "log" not in ss:
    ss.log = []
if "last_msg" not in ss:
    ss.last_msg = ""
if "show_info" not in ss:
    ss.show_info = False
if "auto_next" not in ss:
    ss.auto_next = False
if "_prev_turns" not in ss:
    ss._prev_turns = ss.player["turns"]
if "quit" not in ss:
    ss.quit = False

# ===== UTILITY FUNCTIONS =====
def log(msg):
    ss.log.append(str(msg))
    ss.last_msg = str(msg)

def make_planet_image(climate, size=360):
    color = CLIMATE_COLOR.get((climate or "").lower(), CLIMATE_COLOR["default"])
    bg = Image.new("RGBA", (size, size), "#06121a")
    draw = ImageDraw.Draw(bg)
    cx, cy, radius = size // 2, size // 2, int(size * 0.4)

    base = tuple(int(color.lstrip("#")[i:i+2], 16) for i in (0, 2, 4))
    for r in range(radius, 0, -1):
        f = r / radius
        shade = tuple(int(min(255, base[i] * (0.4 + 0.6 * f) + 255*(1-f)*0.05)) for i in range(3))
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=shade)

    highlight = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    hd = ImageDraw.Draw(highlight)
    hd.ellipse([cx - 20, cy - 25, cx + 28, cy + 15], fill=(255, 255, 255, 200))
    highlight = highlight.filter(ImageFilter.GaussianBlur(6))
    bg = Image.alpha_composite(bg, highlight)

    ring = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    rd = ImageDraw.Draw(ring)
    rx = int(radius * 1.1)
    ry1 = int(radius * 0.2)
    ry2 = int(radius * 0.05)
    rd.ellipse([cx - rx, cy - ry1, cx + rx, cy + ry2], outline=(200, 180, 120, 190), width=6)
    ring = ring.rotate(-22, center=(cx, cy))
    bg = Image.alpha_composite(bg, ring)

    vign = Image.new("RGBA", (size, size), (0, 0, 0, 40))
    vd = ImageDraw.Draw(vign)
    vd.ellipse([0, 0, size, size], fill=(0, 0, 0, 40))
    bg = Image.alpha_composite(bg, vign)

    return bg.convert("RGB")

# ===== FLOATING MENU BUTTON WITH DROPDOWN =====
floating_html = """
<style>
#MainMenu, header, footer {visibility: hidden;}
#floating-menu-button {
    position: fixed; top: 20px; right: 20px;
    background: #0e1419; color: white; border: 2px solid #555;
    border-radius: 8px; padding: 8px 14px; font-size: 22px;
    cursor: pointer; z-index: 99999; box-shadow: 0 4px 12px rgba(0,0,0,0.5);
}
#floating-menu-button:hover { background: #1b232c; }
#floating-menu-panel {
    position: fixed; top: 65px; right: 20px;
    background: #0e1419; border: 1px solid #555; border-radius: 8px;
    padding: 10px 12px; width: 170px; z-index: 99998; display: none;
    box-shadow: 0 4px 12px rgba(0,0,0,0.5);
}
#floating-menu-panel button {
    width: 100%; margin-top: 6px; background: #1a222b; color: white;
    border: 1px solid #444; padding: 8px 10px; border-radius: 6px;
    cursor: pointer; font-size: 14px;
}
#floating-menu-panel button:hover { background: #25303a; }
#floating-menu-panel p { margin: 0 0 6px 0; color: white; text-align: center; font-weight: bold; }
</style>

<button id="floating-menu-button" title="Menu">☰</button>
<div id="floating-menu-panel" aria-hidden="true">
    <p>Menu</p>
    <button onclick="setMenuAction('info')">ℹ️ Info</button>
    <button onclick="setMenuAction('reset')">🔄 Reset</button>
    <button onclick="setMenuAction('quit')">❌ Quit</button>
</div>

<script>
(function(){
    const btn = document.getElementById("floating-menu-button");
    const panel = document.getElementById("floating-menu-panel");
    btn.addEventListener("click", (ev) => {
        ev.stopPropagation();
        panel.style.display = (panel.style.display === "block") ? "none" : "block";
    });
    window.setMenuAction = function(action) {
        const url = new URL(window.location.href);
        url.searchParams.set('menu_action', action);
        setTimeout(() => { window.location.href = url.toString(); }, 50);
    }
    document.addEventListener('click', (e) => {
        const target = e.target;
        if (!btn.contains(target) && !panel.contains(target)) {
            panel.style.display = 'none';
        }
    });
})();
</script>
"""

components.html(floating_html, height=220, scrolling=False)

# ===== HANDLE MENU ACTION =====
params = st.experimental_get_query_params()
action = params.get("menu_action", [None])[0]

if action:
    if action == "info":
        ss.show_info = not ss.show_info
        st.experimental_set_query_params()
        st.experimental_rerun()
    elif action == "reset":
        ss.player = {"fuel":100,"hull":100,"credits":50,"cargo":{},"turns":0}
        ss.planet = generate_planet()
        ss.log = []
        ss.last_msg = ""
        ss.auto_next = False
        ss._prev_turns = ss.player["turns"]
        log("Game reset. Fresh start!")
        st.experimental_set_query_params()
        st.experimental_rerun()
    elif action == "quit":
        ss.quit = True
        st.experimental_set_query_params()
        st.experimental_rerun()

# ===== HEADER =====
st.markdown("<h1 style='text-align:center;'>Galactic Wanderer</h1>", unsafe_allow_html=True)

# ===== SHOW INFO BOX =====
if ss.show_info:
    st.markdown("""
    **Galactic Wanderer** — Space exploration trading game.

    **Goal:** Explore planets, gather resources, build wealth.

    **Actions:**
    - Generate New Planet | Land & Explore | Scan from Orbit | Buy/Sell Resources

    **Tips:** Hostile planets won't trade • Buy low, sell high • Manage fuel & hull
    """)

# ===== QUIT FLAG =====
if ss.quit:
    st.warning("Game stopped. Refresh to play again.")
    st.stop()

# ===== MAIN GAME UI =====
col_left, col_mid, col_right = st.columns([1.1, 0.9, 1])

with col_left:
    planet = ss.planet or {}
    st.image(make_planet_image(planet.get("climate","default")), use_container_width=True)
    st.markdown(f"### {planet.get('name','Unknown')}")
    for key in ["climate","biome","life","atmosphere","danger","event","resource"]:
        if key == "resource":
            st.markdown(f"**{key.title()}:** {planet.get(key,'None')} — value {planet.get('value','N/A')}")
        else:
            st.markdown(f"**{key.title()}:** {planet.get(key,'Unknown')}")
    st.markdown(f"**Civilization:** {planet.get('civilization','None')} ({planet.get('temperament','Neutral')})")

with col_mid:
    st.subheader("Ship")
    p = ss.player
    st.metric("Credits", f"{int(p.get('credits',0))}")
    st.metric("Turns", f"{int(p.get('turns',0))}")
    st.text("Fuel")
    st.progress(int(max(0,min(100,int(p.get('fuel',0))))))
    st.text("Hull Integrity")
    st.progress(int(max(0,min(100,int(p.get('hull',0))))))
    st.markdown("**Cargo**")
    cargo = p.get("cargo",{}) or {}
    if cargo:
        rows=[]
        for k,v in cargo.items():
            qty = int(v.get("quantity",v.get("qty",0))) if isinstance(v,dict) else int(v)
            val = v.get("value","N/A") if isinstance(v,dict) else "N/A"
            rows.append({"Resource":k,"Qty":qty,"Value":val})
        st.table(rows)
    else:
        st.write("Empty")
    st.markdown("**Last action**")
    st.info(ss.last_msg or "No actions yet")

with col_right:
    st.subheader("Actions")
    if st.button("Generate New Planet", key="gen_planet"):
        ss.planet = generate_planet()
        log(f"Generated planet {ss.planet.get('name')}")
        st.experimental_rerun()

    if st.button("Land & Explore", key="explore_action"):
        res = explore(ss.player, ss.planet)
        for m in res.get("messages", []):
            log(m)
        ss.player["turns"] += 1
        st.experimental_rerun()

    if st.button("Scan from Orbit", key="scan_action"):
        res = scan(ss.player, ss.planet)
        for m in res.get("messages", []):
            log(m)
        ss.player["turns"] += 1
        st.experimental_rerun()

    st.markdown("---")
    st.subheader("Market")
    if ss.planet.get("temperament","").lower() == "hostile":
        st.write("Locals hostile — trade unavailable.")
    else:
        resource = ss.planet.get("resource","Unknown")
        buy_price, sell_price = get_trade_prices(ss.planet)
        st.write(f"Resource: **{resource}** | Buy: {buy_price} | Sell: {sell_price}")
        qty = st.slider("Quantity",1,10,1,key="trade_qty")
        col_b,col_s = st.columns(2)
        if col_b.button("Buy", key="buy_action"):
            r = buy(ss.player, ss.planet, qty=qty)
            for m in r.get("messages", []):
                log(m)
            st.experimental_rerun()
        if col_s.button("Sell", key="sell_action"):
            r = sell(ss.player, ss.planet, qty=qty)
            for m in r.get("messages", []):
                log(m)
            st.experimental_rerun()

    st.markdown("---")
    ss.auto_next = st.checkbox("Auto-generate new planet each turn", value=ss.auto_next, key="auto_next_check")

# ===== COMM LOG =====
st.markdown("---")
st.subheader("Communications Log")
log_col1, log_col2 = st.columns([3,1])
with log_col1:
    for entry in ss.log[-12:][::-1]:
        st.write(f"- {entry}")
with log_col2:
    if st.button("Clear Log", key="clear_log_unique"):
        ss.log = []
        ss.last_msg = ""

# ===== AUTO NEXT PLANET =====
if ss.auto_next:
    if ss.player.get("turns",0) > ss._prev_turns:
        ss.planet = generate_planet()
        log(f"Auto-generated planet {ss.planet.get('name')}")
    ss._prev_turns = ss.player.get("turns",0)
