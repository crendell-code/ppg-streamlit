# app_streamlit.py — improved visual UI
import streamlit as st
import random
from io import BytesIO
from PIL import Image, ImageDraw, ImageFilter
from PPG_v2 import generate_planet, explore, scan, get_trade_prices, buy, sell

# Visual palette
CLIMATE_COLOR = {
    "arid": "#d79f6f",
    "temperate": "#6fbf6f",
    "tropical": "#2e8b57",
    "frozen": "#9fd3ff",
    "toxic": "#a3b13a",
    "volcanic": "#ff6b4d",
    "oceanic": "#4da6ff",
    "stormy": "#7f8fa6",
    "radioactive": "#8cff7a",
    "default": "#cccccc"
}

# --- Session state initialization ---
if "player" not in st.session_state:
    st.session_state.player = {"fuel":100, "hull":100, "credits":50, "cargo":{}, "turns":0}
if "planet" not in st.session_state:
    st.session_state.planet = generate_planet()
if "log" not in st.session_state:
    st.session_state.log = []
if "last_msg" not in st.session_state:
    st.session_state.last_msg = ""

# --- Helpers ---
def safe_rerun():
    try:
        if hasattr(st, "experimental_rerun"):
            st.experimental_rerun()
    except Exception:
        pass

def make_planet_image(climate, size=360):
    """Create a simple shaded planet image with an optional ring."""
    color = CLIMATE_COLOR.get(climate.lower(), CLIMATE_COLOR["default"])
    bg = Image.new("RGB", (size, size), "#06121a")
    draw = ImageDraw.Draw(bg)

    # radial gradient for planet
    cx, cy = size // 2, size // 2
    radius = int(size * 0.4)
    for r in range(radius, 0, -1):
        f = r / radius
        # brighter at center
        # mix white with base color based on f**2
        base = tuple(int(color.lstrip("#")[i:i+2], 16) for i in (0,2,4))
        shade = tuple(int(min(255, base[i] * (0.4 + 0.6 * f) + 255*(1-f)*0.05)) for i in range(3))
        bbox = [cx - r, cy - r, cx + r, cy + r]
        draw.ellipse(bbox, fill=shade)

    # slightly blurred highlight
    highlight = Image.new("RGBA", (size, size), (0,0,0,0))
    hd = ImageDraw.Draw(highlight)
    hx = cx - int(radius * 0.4)
    hy = cy - int(radius * 0.5)
    hd.ellipse((hx-20, hy-10, hx+28, hy+40), fill=(255,255,255,200))
    highlight = highlight.filter(ImageFilter.GaussianBlur(6))
    bg.paste(highlight, (0,0), highlight)

    # ring
    ring = Image.new("RGBA", (size, size), (0,0,0,0))
    rd = ImageDraw.Draw(ring)
    rx0 = cx - int(radius*1.1)
    ry0 = cy - int(radius*0.2)
    rx1 = cx + int(radius*1.1)
    ry1 = cy + int(radius*0.05)
    rd.ellipse((rx0, ry0, rx1, ry1), outline=(200,180,120,190), width=6)
    ring = ring.rotate(-22, resample=Image.BICUBIC, center=(cx,cy))
    bg.paste(ring, (0,0), ring)

    # vignette
    vign = Image.new("RGBA", (size, size), (0,0,0,0))
    vd = ImageDraw.Draw(vign)
    vd.ellipse((0,0,size,size), fill=(0,0,0,20))
    bg = Image.alpha_composite(bg.convert("RGBA"), vign).convert("RGB")
    bio = BytesIO()
    bg.save(bio, format="PNG")
    bio.seek(0)
    return bio

def log(msg):
    st.session_state.log.append(msg)
    st.session_state.last_msg = msg

# --- UI layout ---
st.set_page_config(page_title="Galactic Wanderer", layout="wide")
st.markdown("<h1 style='text-align:center;'>Galactic Wanderer</h1>", unsafe_allow_html=True)
col_left, col_mid, col_right = st.columns([1.1, 0.9, 1])

# Left: big planet visual + attributes
with col_left:
    planet = st.session_state.planet
    st.image(make_planet_image(planet.get("climate","default")), use_container_width=True)
    st.markdown(f"### {planet.get('name','Unknown')}")
    st.markdown(f"**Climate:** {planet.get('climate')}")
    st.markdown(f"**Biome:** {planet.get('biome')}")
    st.markdown(f"**Life:** {planet.get('life')}")
    st.markdown(f"**Atmosphere:** {planet.get('atmosphere')}")
    st.markdown(f"**Danger:** {planet.get('danger')}")
    st.markdown(f"**Civilization:** {planet.get('civilization')} ({planet.get('temperament')})")
    st.markdown(f"**Event:** {planet.get('event')}")
    st.markdown(f"**Resource:** {planet.get('resource')} — value {planet.get('value')}")

# Middle: stats + cargo
with col_mid:
    st.subheader("Ship")
    p = st.session_state.player
    # Metrics
    st.metric("Credits", f"{p['credits']}")
    st.metric("Turns", f"{p['turns']}")
    # Progress bars
    st.text("Fuel")
    st.progress(int(max(0, min(100, p["fuel"]))))
    st.text("Hull Integrity")
    st.progress(int(max(0, min(100, p["hull"]))))
    st.markdown("**Cargo**")
    cargo = p.get("cargo", {})
    if cargo:
        cargo_rows = [{"Resource": k, "Qty": v["quantity"], "Value": v["value"]} for k,v in cargo.items()]
        st.table(cargo_rows)
    else:
        st.write("Empty")

    st.markdown("**Last action**")
    st.info(st.session_state.last_msg or "No actions yet")

# Right: actions & trade
with col_right:
    st.subheader("Actions")
    if st.button("Generate New Planet"):
        st.session_state.planet = generate_planet()
        log(f"Generated planet {st.session_state.planet.get('name')}")
        safe_rerun()

    if st.button("Land & Explore"):
        res = explore(st.session_state.player, st.session_state.planet)
        for m in res["messages"]:
            log(m)
        if res["damage"] > 0:
            st.warning(res["messages"][0])
        else:
            st.success(res["messages"][0])
        st.session_state.player["turns"] += 1
        safe_rerun()

    if st.button("Scan from Orbit"):
        res = scan(st.session_state.player, st.session_state.planet)
        for m in res["messages"]:
            log(m)
        st.info(res["messages"][0])
        st.session_state.player["turns"] += 1
        safe_rerun()

    st.markdown("---")
    st.subheader("Market")
    if st.session_state.planet.get("temperament","").lower() == "hostile":
        st.write("Market: Locals hostile — trade unavailable.")
    else:
        resource = st.session_state.planet.get("resource","Unknown")
        buy_price, sell_price = get_trade_prices(st.session_state.planet)
        st.write(f"Resource: **{resource}**")
        st.write(f"Buy price: **{buy_price}**   Sell price: **{sell_price}**")
        qty = st.slider("Quantity", min_value=1, max_value=10, value=1)
        col_b, col_s = st.columns(2)
        if col_b.button("Buy"):
            r = buy(st.session_state.player, st.session_state.planet, qty=qty)
            for m in r["messages"]:
                log(m)
            if r["success"]:
                st.success(r["messages"][0])
            else:
                st.error(r["messages"][0])
            safe_rerun()
        if col_s.button("Sell"):
            r = sell(st.session_state.player, st.session_state.planet, qty=qty)
            for m in r["messages"]:
                log(m)
            if r["success"]:
                st.success(r["messages"][0])
            else:
                st.error(r["messages"][0])
            safe_rerun()

    st.markdown("---")
    st.subheader("Quick Options")
    if st.checkbox("Auto-generate new planet each turn", value=False):
        st.session_state.auto_next = True
    else:
        st.session_state.auto_next = False

# Bottom: communications log
st.markdown("---")
st.subheader("Communications Log")
log_col1, log_col2 = st.columns([3,1])
with log_col1:
    logs = st.session_state.log[-12:]
    for entry in logs[::-1]:
        st.write(f"- {entry}")
with log_col2:
    if st.button("Clear Log"):
        st.session_state.log = []
        st.session_state.last_msg = ""
        safe_rerun()

# auto-generate next planet if enabled and last action changed turns
if st.session_state.get("auto_next", False):
    # if turns increased since last render, generate new planet
    # store previous turns value
    prev_turns = st.session_state.get("_prev_turns", st.session_state.player["turns"])
    if st.session_state.player["turns"] > prev_turns:
        st.session_state.planet = generate_planet()
        log(f"Auto-generated planet {st.session_state.planet.get('name')}")
    st.session_state._prev_turns = st.session_state.player["turns"]