# PPG_v2.py
# Refactored Procedural Planet Generator core (UI-safe)
import random

# =====================================================
#              DATA POOLS FOR GENERATION
# =====================================================

syllables = ["zor", "ath", "mar", "qu", "bel", "tri", "ul", "rax", "ven"]
climates = ["frozen", "tropical", "arid", "stormy", "toxic", "radioactive", "temperate", "oceanic", "volcanic"]
biomes = ["crystal forests", "lava plains", "fog swamps", "floating islands", "sapphire oceans"]
life_traits = ["bioluminescent", "telepathic", "amphibious", "metallic", "moss-covered"]

atmospheres = ["breathable", "acidic", "hallucinogenic", "toxic", "metallic"]
dangers = ["low", "moderate", "high", "extreme"]

civilizations = ["primitive tribes", "steam-tech cultures", "cybernetic hive minds",
                 "galactic merchants", "AI-run empires"]
tempers = ["friendly", "neutral", "suspicious", "hostile", "weirdly flirty"]

trade_goods = ["rare crystals", "alien spices", "molecular circuits", "void gems"]
events = [
    "A solar flare sweeps the orbit.",
    "You detect ancient ruins.",
    "A strange signal pierces your scanners.",
    "Time seems to run slightly backward here.",
    "Gravity bends light in odd ways."
]

# =====================================================
#                GAME API (UI-safe)
# =====================================================

def get_default_player():
    """Return a fresh player dict suitable for UIs to use and mutate."""
    return {
        "fuel": 100,
        "hull": 100,
        "credits": 50,
        "cargo": {},  # resource -> {"quantity": int, "value": int}
        "turns": 0
    }

def generate_planet():
    """Return a new planet dict (pure function)."""
    name = "".join(random.choice(syllables) for _ in range(random.randint(2, 4))).title()
    planet = {
        "name": name,
        "climate": random.choice(climates),
        "biome": random.choice(biomes),
        "life": random.choice(life_traits),
        "atmosphere": random.choice(atmospheres),
        "danger": random.choice(dangers),
        "civilization": random.choice(civilizations),
        "temperament": random.choice(tempers),
        "event": random.choice(events),
        "resource": random.choice(trade_goods),
        "value": random.randint(10, 50)  # sale value of goods
    }
    return planet

def add_to_cargo(player, name, qty, value):
    """Mutates player['cargo'] safely."""
    cargo = player.setdefault("cargo", {})
    if name not in cargo:
        cargo[name] = {"quantity": 0, "value": value}
    cargo[name]["quantity"] += qty

# --- Explore action ---
def explore(player, planet):
    """
    Mutates given player dict for exploration results.
    Returns a dict with keys: success (bool), messages (list), damage (int), found (dict or None), fuel_used (int)
    """
    messages = []
    danger_map = {"low":10,"moderate":20,"high":35,"extreme":50}
    risk = danger_map.get(planet.get("danger", "moderate"), 20)

    if random.randint(1,100) < risk:
        dmg = random.randint(5,25)
        player["hull"] = max(0, player.get("hull", 0) - dmg)
        messages.append(f"Encountered danger! Hull -{dmg}")
        found = None
        success = False
    else:
        gain = planet.get("value", 0)
        resource = planet.get("resource", "Unknown")
        add_to_cargo(player, resource, 1, planet.get("value", gain))
        messages.append(f"Found {resource} worth {gain} credits.")
        dmg = 0
        found = {"resource": resource, "value": gain}
        success = True

    fuel_used = random.randint(5,12)
    player["fuel"] = max(0, player.get("fuel", 0) - fuel_used)
    messages.append(f"Fuel used: -{fuel_used}")

    return {
        "success": success,
        "messages": messages,
        "damage": dmg,
        "found": found,
        "fuel_used": fuel_used
    }

# --- Scan action ---
def scan(player, planet):
    """
    Mutates player to deduct fuel and returns scan info.
    Returns dict: messages (list), fuel_used (int)
    """
    messages = [f"Scan detected: {planet.get('event')}"]
    fuel_used = random.randint(3,7)
    player["fuel"] = max(0, player.get("fuel", 0) - fuel_used)
    messages.append(f"Fuel used: -{fuel_used}")
    return {"messages": messages, "fuel_used": fuel_used}

# --- Trading helpers ---
def get_trade_prices(planet):
    """Return (buy_price, sell_price) for the planet's resource (stateless)."""
    base = planet.get("value", 10)
    buy_price = max(1, base - random.randint(1,10))
    sell_price = base + random.randint(1,15)
    return buy_price, sell_price

def buy(player, planet, qty=1):
    """Attempt to buy qty of the planet resource. Mutates player. Returns dict with result info."""
    buy_price, _ = get_trade_prices(planet)
    total = buy_price * qty
    if player.get("credits", 0) >= total:
        player["credits"] -= total
        add_to_cargo(player, planet.get("resource", "Unknown"), qty, buy_price)
        return {"success": True, "messages": [f"Bought {qty} x {planet.get('resource')} for {total} credits."], "credits_delta": -total}
    else:
        return {"success": False, "messages": ["Not enough credits."], "credits_delta": 0}

def sell(player, planet, qty=1):
    """Attempt to sell qty of the planet resource. Mutates player. Returns dict with result info."""
    _, sell_price = get_trade_prices(planet)
    resource = planet.get("resource", "Unknown")
    cargo = player.setdefault("cargo", {})
    if resource in cargo and cargo[resource].get("quantity", 0) >= qty:
        cargo[resource]["quantity"] -= qty
        if cargo[resource]["quantity"] <= 0:
            del cargo[resource]
        total = sell_price * qty
        player["credits"] = player.get("credits", 0) + total
        return {"success": True, "messages": [f"Sold {qty} x {resource} for {total} credits."], "credits_delta": total}
    else:
        return {"success": False, "messages": ["You don't have that resource."], "credits_delta": 0}

# Optional CLI helper for testing
def cli_main():
    player = get_default_player()
    print("Welcome to GALACTIC WANDERER (CLI)")
    while True:
        if player["fuel"] <= 0:
            print("You ran out of fuel. GAME OVER.")
            break
        if player["hull"] <= 0:
            print("Your hull collapsed. GAME OVER.")
            break

        planet = generate_planet()
        print(f"\nPlanet {planet['name']} — {planet['biome']} ({planet['climate']})")
        print(f"Resource: {planet['resource']} (value {planet['value']})")
        print("Actions: 1) Explore  2) Scan  3) Trade  4) Leave  5) Quit")
        action = input("> ").strip()
        if action == "1":
            res = explore(player, planet)
            for m in res["messages"]:
                print(m)
        elif action == "2":
            res = scan(player, planet)
            for m in res["messages"]:
                print(m)
        elif action == "3":
            b, s = get_trade_prices(planet)
            print(f"Buy {b} / Sell {s}")
            c = input("(B)uy/(S)ell/(L)eave: ").lower()
            if c == "b":
                q = int(input("Qty? ") or "1")
                r = buy(player, planet, q)
                for m in r["messages"]:
                    print(m)
            elif c == "s":
                q = int(input("Qty? ") or "1")
                r = sell(player, planet, q)
                for m in r["messages"]:
                    print(m)
        elif action == "4":
            cost = random.randint(2,6)
            player["fuel"] -= cost
            print(f"Left planet. Fuel -{cost}")
        elif action == "5":
            print("Bye.")
            break
        else:
            print("Invalid input.")
        player["turns"] = player.get("turns", 0) + 1

if __name__ == "__main__":
    cli_main()