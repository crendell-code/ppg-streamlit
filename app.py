# app.py (Tkinter UI using PPG_v2 core)
import tkinter as tk
from tkinter import ttk, messagebox
import random
import pathlib
import importlib.util
import sys
import copy

# Import core functions
from PPG_v2 import generate_planet, explore, scan, get_trade_prices, buy, sell, get_default_player

DEFAULT_PLAYER = get_default_player()

CLIMATE_COLOR = {
    "arid": "#d79f6f",
    "temperate": "#6fbf6f",
    "tropical": "#2e8b57",
    "frozen": "#9fd3ff",
    "toxic": "#6b8e23",
    "volcanic": "#ff6b4d",
    "oceanic": "#4da6ff",
    "default": "#cccccc"
}

class GameApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Galactic Wanderer")
        self.resizable(False, False)

        self.player = copy.deepcopy(DEFAULT_PLAYER)
        self.planet = generate_planet()

        self._build_ui()
        self._refresh_ui()

    def _build_ui(self):
        top_frame = ttk.Frame(self, padding=8)
        top_frame.grid(row=0, column=0, sticky="nw")

        self.canvas = tk.Canvas(top_frame, width=180, height=180, bg="#fff")
        self.canvas.grid(row=0, column=0, rowspan=6, padx=(0,12))

        self.lbl_name = ttk.Label(top_frame, text="", font=None)
        self.lbl_name.grid(row=0, column=1, sticky="w")
        self.lbl_climate = ttk.Label(top_frame, text="")
        self.lbl_climate.grid(row=1, column=1, sticky="w")
        self.lbl_biome = ttk.Label(top_frame, text="")
        self.lbl_biome.grid(row=2, column=1, sticky="w")
        self.lbl_life = ttk.Label(top_frame, text="")
        self.lbl_life.grid(row=3, column=1, sticky="w")
        self.lbl_atmos = ttk.Label(top_frame, text="")
        self.lbl_atmos.grid(row=4, column=1, sticky="w")
        self.lbl_event = ttk.Label(top_frame, text="", foreground="#444")
        self.lbl_event.grid(row=5, column=1, sticky="w")

        mid_frame = ttk.Frame(self, padding=8)
        mid_frame.grid(row=1, column=0, sticky="w")

        stats_frame = ttk.LabelFrame(mid_frame, text="Ship Status", padding=8)
        stats_frame.grid(row=0, column=0, sticky="nw")
        self.lbl_fuel = ttk.Label(stats_frame, text="")
        self.lbl_fuel.grid(row=0, column=0, sticky="w")
        self.lbl_hull = ttk.Label(stats_frame, text="")
        self.lbl_hull.grid(row=1, column=0, sticky="w")
        self.lbl_credits = ttk.Label(stats_frame, text="")
        self.lbl_credits.grid(row=2, column=0, sticky="w")
        self.lbl_turns = ttk.Label(stats_frame, text="")
        self.lbl_turns.grid(row=3, column=0, sticky="w")
        self.lbl_cargo = ttk.Label(stats_frame, text="", wraplength=240, justify="left")
        self.lbl_cargo.grid(row=4, column=0, sticky="w", pady=(6,0))

        actions_frame = ttk.LabelFrame(mid_frame, text="Actions", padding=8)
        actions_frame.grid(row=0, column=1, padx=(12,0), sticky="n")
        ttk.Button(actions_frame, text="Generate New Planet", command=self.generate_new_planet).grid(row=0, column=0, sticky="ew", pady=2)
        ttk.Button(actions_frame, text="Land & Explore", command=self.land_explore).grid(row=1, column=0, sticky="ew", pady=2)
        ttk.Button(actions_frame, text="Scan from Orbit", command=self.scan_orbit).grid(row=2, column=0, sticky="ew", pady=2)
        ttk.Button(actions_frame, text="Trade", command=self.open_trade_window).grid(row=3, column=0, sticky="ew", pady=2)
        ttk.Button(actions_frame, text="Leave", command=self.leave_planet).grid(row=4, column=0, sticky="ew", pady=2)
        ttk.Button(actions_frame, text="Restart Game", command=self.restart_game).grid(row=5, column=0, sticky="ew", pady=6)

        log_frame = ttk.LabelFrame(self, text="Communications", padding=8)
        log_frame.grid(row=2, column=0, pady=(6,8), sticky="ew")
        self.txt_log = tk.Text(log_frame, width=60, height=8, wrap="word", state="disabled")
        self.txt_log.grid(row=0, column=0)

    def _refresh_ui(self):
        p = self.planet
        self.lbl_name.config(text=f"Planet: {p.get('name','Unknown')}")
        self.lbl_climate.config(text=f"Climate: {p.get('climate','?')}")
        self.lbl_biome.config(text=f"Biome: {p.get('biome','?')}")
        self.lbl_life.config(text=f"Life: {p.get('life','?')}")
        self.lbl_atmos.config(text=f"Atmosphere: {p.get('atmosphere','?')}")
        self.lbl_event.config(text=f"Event: {p.get('event','None')}")

        climate = p.get("climate", "default").lower()
        color = CLIMATE_COLOR.get(climate, CLIMATE_COLOR["default"])
        self.canvas.delete("all")
        self.canvas.create_oval(10, 10, 170, 170, fill=color, outline="#222", width=4)
        self.canvas.create_oval(28, 28, 58, 58, fill="#ffffff", outline="")

        self.lbl_fuel.config(text=f"Fuel: {self.player['fuel']}")
        self.lbl_hull.config(text=f"Hull: {self.player['hull']}")
        self.lbl_credits.config(text=f"Credits: {self.player['credits']}")
        self.lbl_turns.config(text=f"Turns: {self.player['turns']}")
        cargo = self.player.get("cargo", {})
        items = ", ".join(f"{k} x{v['quantity']}" for k, v in cargo.items()) if cargo else "Empty"
        self.lbl_cargo.config(text=f"Cargo: {items}")

    def _log(self, text):
        self.txt_log.config(state="normal")
        self.txt_log.insert("end", text + "\n")
        self.txt_log.see("end")
        self.txt_log.config(state="disabled")

    def generate_new_planet(self):
        self.planet = generate_planet()
        self._log(f"Generated new planet: {self.planet.get('name')}")
        self._refresh_ui()

    def land_explore(self):
        res = explore(self.player, self.planet)
        for m in res["messages"]:
            self._log(m)
        if res["damage"] > 0:
            messagebox.showwarning("Danger", res["messages"][0])
        else:
            messagebox.showinfo("Discovery", res["messages"][0])
        self.player["turns"] += 1
        self._check_game_over()
        self._refresh_ui()

    def scan_orbit(self):
        res = scan(self.player, self.planet)
        for m in res["messages"]:
            self._log(m)
        messagebox.showinfo("Scan", res["messages"][0])
        self.player["turns"] += 1
        self._check_game_over()
        self._refresh_ui()

    def open_trade_window(self):
        if self.planet.get("temperament","").lower() == "hostile":
            self._log("Locals hostile. Trade unavailable.")
            messagebox.showerror("Trade", "Locals hostile.")
            return

        buy_price, sell_price = get_trade_prices(self.planet)
        resource = self.planet.get("resource","Unknown")
        tw = tk.Toplevel(self)
        tw.title("Market")
        ttk.Label(tw, text=f"Planet trades: {resource}").grid(row=0, column=0, columnspan=2, pady=6, padx=8)
        ttk.Label(tw, text=f"Buy for: {buy_price} credits").grid(row=1, column=0, padx=8, sticky="w")
        ttk.Label(tw, text=f"Sell for: {sell_price} credits").grid(row=1, column=1, padx=8, sticky="w")

        def buy_one():
            r = buy(self.player, self.planet, qty=1)
            for m in r["messages"]:
                self._log(m)
            if r["success"]:
                messagebox.showinfo("Buy", r["messages"][0])
            else:
                messagebox.showerror("Buy", r["messages"][0])
            self._refresh_ui()

        def sell_one():
            r = sell(self.player, self.planet, qty=1)
            for m in r["messages"]:
                self._log(m)
            if r["success"]:
                messagebox.showinfo("Sell", r["messages"][0])
            else:
                messagebox.showerror("Sell", r["messages"][0])
            self._refresh_ui()

        ttk.Button(tw, text="Buy 1", command=buy_one).grid(row=2, column=0, padx=8, pady=8)
        ttk.Button(tw, text="Sell 1", command=sell_one).grid(row=2, column=1, padx=8, pady=8)

    def leave_planet(self):
        fuel_cost = random.randint(2, 6)
        self.player["fuel"] -= fuel_cost
        self._log(f"Left planet. Fuel -{fuel_cost}")
        self.generate_new_planet()
        self.player["turns"] += 1
        self._check_game_over()
        self._refresh_ui()

    def restart_game(self):
        if messagebox.askyesno("Restart", "Restart the game?"):
            self.player = copy.deepcopy(DEFAULT_PLAYER)
            self.planet = generate_planet()
            self.txt_log.config(state="normal"); self.txt_log.delete("1.0","end"); self.txt_log.config(state="disabled")
            self._log("Game restarted.")
            self._refresh_ui()

    def _check_game_over(self):
        if self.player["fuel"] <= 0:
            messagebox.showerror("Game Over", "You ran out of fuel. GAME OVER.")
            self._log("Game Over: out of fuel.")
            return True
        if self.player["hull"] <= 0:
            messagebox.showerror("Game Over", "Your hull collapsed. GAME OVER.")
            self._log("Game Over: hull collapsed.")
            return True
        return False

if __name__ == "__main__":
    app = GameApp()
    app.mainloop()