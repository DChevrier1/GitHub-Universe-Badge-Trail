"""Portable wagon simulation shared by the browser and MicroPython badge.

This is an original implementation of the mechanics described by MECC's 1985
manual, with a fictional coast-to-Universe itinerary and original writing/art.
No sound, clock, network, filesystem, or desktop-only modules are used here.
"""

try:
    from .companion import BadgeEffects
except (ImportError, ValueError):
    try:
        from ..pipboy.companion import BadgeEffects
    except (ImportError, ValueError):
        from companion import BadgeEffects

try:
    from .data import OCCUPATIONS, MONTHS, MONTH_DAYS, PACES, RATIONS, PRODUCTS, DEFAULT_NAMES, KEYS, ROUTE, TOTAL_MILES, HELP
    from .render import render_game
except (ImportError, ValueError):
    from data import OCCUPATIONS, MONTHS, MONTH_DAYS, PACES, RATIONS, PRODUCTS, DEFAULT_NAMES, KEYS, ROUTE, TOTAL_MILES, HELP
    from render import render_game

SCREENS = ("title", "help", "occupation", "names", "keyboard", "month", "store", "travel", "menu", "supplies", "map", "pace", "rations", "rest", "trade", "river", "landmark", "event", "hunt", "hunt_result", "final_route", "raft", "arrival", "gameover", "restart")


def _copy(value):
    if isinstance(value, dict):
        return {key: _copy(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_copy(item) for item in value]
    return value


def _num(value, default=0, low=0, high=1000000):
    try:
        value = float(value)
        return default if value != value or value < low or value > high else value
    except (ValueError, TypeError, OverflowError):
        return default


def _name(value, default="TRAVELER"):
    value = "".join(c for c in str(value)[:24].upper() if "A" <= c <= "Z" or "0" <= c <= "9" or c in " -.").strip()
    return value[:12] or default


def _text(value, limit=180):
    return "".join(c if 32 <= ord(c) < 127 else " " for c in str(value)[:limit])


class UniverseTrail:
    def __init__(self, state=None, config=None):
        self.phase = 0.0
        self.config = config if isinstance(config, dict) else {}
        self.state = self._fresh(int(_num(self.config.get("seed"), 19851013, 1, 2147483646)))
        if isinstance(state, dict):
            self._restore(state)
        self.effects = BadgeEffects(self.config, state.get("effects") if isinstance(state, dict) else None)
        self.telemetry = {}

    def _fresh(self, seed):
        return {
            "version": 1, "screen": "title", "selected": 0, "rng": seed,
            "started": False, "finished": False, "won": False,
            "occupation": 0, "month": 3, "day": 1, "year": 2026, "elapsed": 0,
            "miles": 0, "landmark": 0, "last_stop": 0, "crossed": [],
            "money": 2500, "supplies": {p["id"]: 0 for p in PRODUCTS},
            "party": [{"name": name, "alive": True, "health": 100, "illness": "", "sick_days": 0} for name in DEFAULT_NAMES],
            "pace": 0, "rations": 0, "weather": "COOL", "ox_health": 100,
            "message": [], "event_title": "TRAIL JOURNAL", "return_screen": "menu",
            "resume_screen": "title", "help_page": 0, "name_index": 0, "key_index": 0, "name_draft": "",
            "store_qty": 1, "store_initial": True, "store_return": "landmark", "notice": "",
            "rest_days": 3, "trade": None, "river": {}, "hunt": {}, "raft": {},
            "travel_clock": 0, "broken": "", "stalled": 0, "log": [], "score": 0,
        }

    def _restore(self, saved):
        s = self.state
        for key, low, high in (("rng", 1, 2147483646), ("occupation", 0, 2), ("month", 1, 12), ("day", 1, 31), ("year", 2026, 2027), ("elapsed", 0, 730), ("miles", 0, TOTAL_MILES), ("landmark", 0, len(ROUTE)-1), ("last_stop", 0, len(ROUTE)-1), ("selected", 0, 40), ("pace", 0, 2), ("rations", 0, 2), ("help_page", 0, len(HELP)-1), ("name_index", 0, 4), ("key_index", 0, len(KEYS)-1), ("store_qty", 1, 20), ("rest_days", 1, 9), ("stalled", 0, 30), ("score", 0, 1000000)):
            s[key] = int(_num(saved.get(key), s[key], low, high))
        s["day"] = min(s["day"], MONTH_DAYS[s["month"]-1])
        for key, high in (("money", 50000), ("ox_health", 100), ("travel_clock", 2)):
            s[key] = _num(saved.get(key), s[key], 0, high)
        for key in ("started", "finished", "won", "store_initial"):
            s[key] = saved.get(key) is True
        for key in ("screen", "return_screen", "resume_screen", "store_return"):
            if saved.get(key) in SCREENS:
                s[key] = saved[key]
        for key in ("notice", "event_title", "name_draft", "weather"):
            s[key] = _text(saved.get(key, s[key]), 180 if key == "notice" else 32)
        s["name_draft"] = _name(s["name_draft"], "")
        s["broken"] = saved.get("broken", "") if saved.get("broken") in ("wheels", "axles", "tongues") else ""
        supplies = saved.get("supplies")
        if isinstance(supplies, dict):
            for key in s["supplies"]:
                s["supplies"][key] = int(_num(supplies.get(key), 0, 0, 20000 if key == "food" else 999))
        party = saved.get("party")
        if isinstance(party, list):
            for index, person in enumerate(party[:5]):
                if isinstance(person, dict):
                    s["party"][index] = {"name": _name(person.get("name"), DEFAULT_NAMES[index]), "alive": person.get("alive") is not False, "health": _num(person.get("health"), 100, 0, 100), "illness": _text(person.get("illness", ""), 24), "sick_days": int(_num(person.get("sick_days"), 0, 0, 30))}
        for key, limit in (("message", 8), ("log", 16)):
            if isinstance(saved.get(key), list):
                s[key] = [_text(v) for v in saved[key][-limit:]]
        crossed = saved.get("crossed")
        if isinstance(crossed, list):
            s["crossed"] = [int(n) for n in crossed[:20] if isinstance(n, (int, float)) and n == n and 0 <= n < len(ROUTE)]
        trade = saved.get("trade")
        if isinstance(trade, dict):
            give, receive = trade.get("give"), trade.get("receive")
            if give in ("money", "labor", "food", "bullets", "clothes") and receive in s["supplies"]:
                cost = int(_num(trade.get("cost"), 0, 1, 35))
                amount = int(_num(trade.get("amount"), 0, 1, 50))
                available = 2 if give == "labor" else s["money"] if give == "money" else s["supplies"][give]
                if cost and amount and cost <= available:
                    s["trade"] = {"give": give, "cost": cost, "receive": receive, "amount": amount}
        river = saved.get("river")
        if isinstance(river, dict) and river:
            s["river"] = {"width": int(_num(river.get("width"), 300, 50, 3000)), "depth": _num(river.get("depth"), 3, 0.5, 15), "ferry": int(_num(river.get("ferry"), 0, 0, 100)), "wait": int(_num(river.get("wait"), 1, 1, 6))}
        # Minigames are bounded and resumable; unknown structures are discarded.
        hunt = saved.get("hunt")
        if isinstance(hunt, dict) and hunt:
            s["hunt"] = {"x": _num(hunt.get("x"), 160, 20, 300), "y": _num(hunt.get("y"), 175, 50, 180), "dx": _num(hunt.get("dx"), 0, -1, 1), "dy": _num(hunt.get("dy"), -1, -1, 1), "time": _num(hunt.get("time"), 45, 0, 45), "meat": int(_num(hunt.get("meat"), 0, 0, 20000)), "kills": int(_num(hunt.get("kills"), 0, 0, 999)), "animals": [], "shot": {}}
            for animal in hunt.get("animals", [])[:6] if isinstance(hunt.get("animals"), list) else []:
                if isinstance(animal, dict):
                    s["hunt"]["animals"].append({"x": _num(animal.get("x"), 160, 0, 320), "y": _num(animal.get("y"), 110, 55, 175), "kind": animal.get("kind") if animal.get("kind") in ("bison", "deer", "rabbit") else "deer", "alive": animal.get("alive") is not False, "vx": _num(animal.get("vx"), 8, -60, 60), "respawn": _num(animal.get("respawn"), 0, 0, 10)})
        raft = saved.get("raft")
        if isinstance(raft, dict) and raft:
            s["raft"] = {"x": _num(raft.get("x"), 160, 40, 280), "y": 170, "progress": _num(raft.get("progress"), 0, 0, 100), "lives": int(_num(raft.get("lives"), 3, 0, 3)), "cooldown": _num(raft.get("cooldown"), 0, 0, 2), "obstacles": []}
            for item in raft.get("obstacles", [])[:6] if isinstance(raft.get("obstacles"), list) else []:
                if isinstance(item, dict):
                    s["raft"]["obstacles"].append({"x": _num(item.get("x"), 100, 40, 280), "y": _num(item.get("y"), 60, 15, 210), "kind": "rock"})
        if s["screen"] == "hunt" and not s["hunt"]:
            s["screen"] = "menu"
        if s["screen"] == "raft" and not s["raft"]:
            s["screen"] = "final_route"
        if not s["trade"]:
            for key in ("screen", "resume_screen", "return_screen"):
                if s[key] == "trade":
                    s[key] = "menu"
        if s["screen"] == "river" and not s["river"]:
            self._river_conditions()
        if s["finished"]:
            s["screen"] = "arrival" if s["won"] else "gameover"
        self._clamp_selection()

    def _rand(self, upper=100):
        self.state["rng"] = (self.state["rng"] * 48271) % 2147483647
        return self.state["rng"] % max(1, int(upper))

    def _show(self, screen, selected=0):
        self.state["screen"] = screen
        self.state["selected"] = selected
        self.state["notice"] = ""

    def _record(self, message):
        self.state["log"].append(message)
        self.state["log"] = self.state["log"][-16:]

    def _event(self, title, messages, return_screen="menu"):
        if self.state["finished"]:
            return
        self.state["event_title"] = title
        self.state["message"] = [messages] if isinstance(messages, str) else messages
        self.state["return_screen"] = return_screen
        self._record(title + ": " + " ".join(self.state["message"]))
        self._show("event")

    def _alive(self):
        return [person for person in self.state["party"] if person["alive"]]

    def _health_number(self):
        alive = self._alive()
        return sum(p["health"] for p in alive) / len(alive) if alive else 0

    def _health(self):
        value = self._health_number()
        return "GOOD" if value >= 75 else "FAIR" if value >= 50 else "POOR" if value >= 25 else "VERY POOR"

    def _date(self):
        s = self.state
        return MONTHS[s["month"]-1][:3] + " " + str(s["day"]) + ", " + str(s["year"])

    def _at_stop(self):
        return self.state["miles"] == ROUTE[self.state["landmark"]]["miles"]

    def _options(self):
        s, page = self.state, self.state["screen"]
        options = []
        if page == "title":
            if s["started"] and not s["finished"]:
                options.append(("resume", "RESUME EXPEDITION"))
            options += [("new", "TRAVEL TO UNIVERSE"), ("help", "READ THE TRAIL GUIDE"), ("effects:open", "LIGHTS / REMINDERS")]
        elif page == "occupation":
            options = [(o["id"], o["label"] + "  $" + str(o["cash"]) + "  " + str(o["multiplier"]) + "X") for o in OCCUPATIONS]
        elif page == "names":
            options = [("name:"+str(i), str(i+1)+". "+p["name"]) for i, p in enumerate(s["party"])] + [("done", "PARTY IS READY")]
        elif page == "keyboard":
            options = [("key:"+key, key) for key in KEYS]
        elif page == "month":
            options = [("month:"+str(m), MONTHS[m-1]) for m in range(3, 8)]
        elif page == "store":
            for p in PRODUCTS:
                amount = p["step"] * s["store_qty"]
                options.append(("buy:"+p["id"], p["label"] + " +" + str(amount) + " $" + self._cost_text(self._price(p, amount))))
            options += [("done", "LEAVE THE STORE")]
            if s["store_initial"]:
                options.append(("new", "START OVER"))
        elif page == "travel":
            options = [("camp", "STOP AND MAKE CAMP")]
        elif page == "menu":
            options = [("continue", "CONTINUE ON THE TRAIL"), ("supplies", "CHECK SUPPLIES / PARTY"), ("map", "LOOK AT THE MAP"), ("pace", "CHANGE PACE"), ("rations", "CHANGE FOOD RATIONS"), ("rest", "STOP TO REST"), ("hunt", "HUNT FOR FOOD"), ("trade", "TRY TO TRADE")]
            if self._at_stop() and ROUTE[s["landmark"]].get("store"):
                options.append(("store", "VISIT THE STORE"))
            options += [("journal", "READ TRAIL JOURNAL"), ("title", "TRAIL TITLE SCREEN"), ("effects:open", "LIGHTS / REMINDERS")]
        elif page in ("event", "hunt_result", "supplies", "map"):
            options = [("continue", "CONTINUE")]
        elif page == "help":
            options = [("next", "NEXT PAGE" if s["help_page"] < len(HELP)-1 else "BACK TO TITLE")]
        elif page == "pace":
            options = [("pace:"+str(i), label+(" *" if s["pace"] == i else "")) for i, label in enumerate(PACES)]
        elif page == "rations":
            options = [("rations:"+str(i), label+(" *" if s["rations"] == i else "")) for i, label in enumerate(RATIONS)]
        elif page == "rest":
            options = [("days", "REST FOR "+str(s["rest_days"])+" DAYS"), ("cancel", "RETURN TO CAMP")]
        elif page == "trade":
            options = [("accept", "ACCEPT THE OFFER"), ("decline", "DECLINE THE OFFER")]
        elif page == "landmark":
            options = [("continue", "CONTINUE JOURNEY"), ("talk", "TALK TO A TRAVELER"), ("camp", "MAKE CAMP")]
            if ROUTE[s["landmark"]].get("store"):
                options.append(("store", "VISIT THE STORE"))
        elif page == "river":
            options = [("ford", "FORD THE RIVER"), ("float", "CAULK AND FLOAT"), ("wait", "WAIT ONE DAY")]
            if s["river"].get("ferry"):
                options.append(("ferry", "TAKE FERRY $"+str(s["river"]["ferry"])))
            options += [("talk", "ASK ABOUT THE CROSSING"), ("camp", "RETURN TO CAMP")]
        elif page == "final_route":
            options = [("raft", "RAFT TO SAN FRANCISCO"), ("toll", "TAKE THE TOLL ROAD ($20)"), ("camp", "RETURN TO CAMP")]
        elif page in ("arrival", "gameover"):
            options = [("new", "START A NEW EXPEDITION"), ("title", "BACK TO TITLE")]
        elif page == "restart":
            options = [("cancel", "KEEP CURRENT EXPEDITION"), ("confirm", "START AGAIN")]
        return [{"id": key, "label": label} for key, label in options]

    def _clamp_selection(self):
        options = self._options()
        self.state["selected"] %= max(1, len(options))

    @staticmethod
    def _cost_text(amount):
        return str(int(amount)) if int(amount) == amount else str(round(amount, 2))

    def _price(self, product, amount):
        factor = 1 if self.state["store_initial"] else 1 + self.state["miles"] / TOTAL_MILES
        return round(product["price"] * amount * factor, 2)

    def update(self, actions=None, dt=0.0, telemetry=None, return_snapshot=False):
        dt = _num(dt, 0, 0, 2)
        self.phase = (self.phase + dt) % 3600
        self.telemetry.update(telemetry or {})
        self.effects.tick(dt, self.telemetry)
        paused = bool(self.effects.active or self.effects.settings)
        if isinstance(actions, str):
            actions = [actions]
        for action in (actions or [])[:32]:
            if isinstance(action, str):
                if not self.effects.handle(action):
                    self._action(action[:100])
        paused = paused or bool(self.effects.active or self.effects.settings)
        if paused:
            return self.snapshot() if return_snapshot else None
        if self.state["screen"] == "travel":
            self.state["travel_clock"] += dt
            if self.state["travel_clock"] >= 1.25:
                self.state["travel_clock"] -= 1.25
                self._travel_day()
        elif self.state["screen"] == "hunt":
            self._hunt_tick(dt)
        elif self.state["screen"] == "raft":
            self._raft_tick(dt)
        return self.snapshot() if return_snapshot else None

    def _action(self, action):
        s, page = self.state, self.state["screen"]
        if action == "effects:open":
            self.effects.open_settings()
            return
        if action.startswith("name:"):
            parts = action.split(":", 2)
            if len(parts) == 3 and parts[1].isdigit() and 0 <= int(parts[1]) < 5 and not s["started"]:
                s["party"][int(parts[1])]["name"] = _name(parts[2], DEFAULT_NAMES[int(parts[1])])
            return
        if action in ("home", "title"):
            if page not in ("title", "help"):
                s["resume_screen"] = page
            self._show("title")
            return
        if action in ("back", "menu", "cancel"):
            self._back()
            return
        if page == "hunt":
            if action in ("left", "right", "up", "down"):
                h = s["hunt"]
                h["dx"], h["dy"] = {"left": (-1, 0), "right": (1, 0), "up": (0, -1), "down": (0, 1)}[action]
                h["x"] = max(22, min(298, h["x"]+h["dx"]*8))
                h["y"] = max(58, min(178, h["y"]+h["dy"]*8))
            elif action in ("select", "fire"):
                self._fire()
            return
        if page == "raft":
            if action in ("left", "right"):
                s["raft"]["x"] = max(40, min(280, s["raft"]["x"]+(-18 if action == "left" else 18)))
            return
        options = self._options()
        if action.startswith("choice:"):
            try:
                index = int(action.split(":", 1)[1])
            except ValueError:
                return
            if 0 <= index < len(options):
                s["selected"] = index
                self._choose(options[index]["id"])
        elif action.startswith("option:"):
            key = action.split(":", 1)[1]
            if any(o["id"] == key for o in options):
                self._choose(key)
        elif action in ("up", "down"):
            s["selected"] = (s["selected"] + (-1 if action == "up" else 1)) % max(1, len(options))
        elif action in ("left", "right"):
            delta = -1 if action == "left" else 1
            if page == "store":
                s["store_qty"] = max(1, min(20, s["store_qty"]+delta))
            elif page == "rest":
                s["rest_days"] = max(1, min(9, s["rest_days"]+delta))
            elif page == "help":
                s["help_page"] = max(0, min(len(HELP)-1, s["help_page"]+delta))
            else:
                s["selected"] = (s["selected"]+delta) % max(1, len(options))
        elif action == "select" and options:
            self._choose(options[s["selected"] % len(options)]["id"])

    def _back(self):
        s, page = self.state, self.state["screen"]
        if page == "hunt":
            self._finish_hunt()
        elif page == "raft":
            self._show("final_route")
        elif page == "travel":
            self._show("menu")
        elif page == "keyboard":
            self._show("names", s["name_index"])
        elif page == "names":
            self._show("occupation", s["occupation"])
        elif page == "month":
            self._show("names", 5)
        elif page == "store":
            self._leave_store()
        elif page in ("event", "hunt_result"):
            self._show(s["return_screen"])
        elif page == "menu":
            self._continue()
        elif page in ("occupation", "help", "arrival", "gameover", "restart"):
            self._show("title")
        elif page != "title":
            self._show("menu")

    def _choose(self, key):
        if key == "effects:open":
            self.effects.open_settings()
            return
        s, page = self.state, self.state["screen"]
        if page == "title":
            if key == "resume":
                self._show(s["resume_screen"] if s["resume_screen"] not in ("title", "help") else "menu")
            elif key == "help":
                s["help_page"] = 0
                self._show("help")
            elif s["started"] and not s["finished"]:
                self._show("restart")
            else:
                self._new()
        elif page == "restart":
            self._new() if key == "confirm" else self._show("title")
        elif page == "occupation":
            s["occupation"] = [o["id"] for o in OCCUPATIONS].index(key)
            s["money"] = OCCUPATIONS[s["occupation"]]["cash"]
            self._show("names")
        elif page == "names":
            if key == "done":
                self._show("month")
            else:
                s["name_index"] = int(key.split(":")[1])
                s["name_draft"] = s["party"][s["name_index"]]["name"]
                self._show("keyboard")
        elif page == "keyboard":
            char = key.split(":")[1]
            if char == "DONE":
                s["party"][s["name_index"]]["name"] = _name(s["name_draft"], DEFAULT_NAMES[s["name_index"]])
                self._show("names", s["name_index"])
            elif char == "DEL":
                s["name_draft"] = s["name_draft"][:-1]
            elif char == "CLEAR":
                s["name_draft"] = ""
            elif len(s["name_draft"]) < 12:
                s["name_draft"] += " " if char == "SPACE" else char
        elif page == "month":
            s["month"], s["day"] = int(key.split(":")[1]), 1
            s["store_initial"] = True
            self._show("store")
        elif page == "store":
            if key == "done":
                self._leave_store()
            elif key == "new":
                self._new()
            else:
                self._buy(key.split(":")[1])
        elif page in ("arrival", "gameover"):
            self._new() if key == "new" else self._show("title")
        elif page == "help":
            if s["help_page"] == len(HELP)-1:
                self._show("title")
            else:
                s["help_page"] += 1
        elif page in ("event", "hunt_result"):
            self._show(s["return_screen"])
        elif page in ("supplies", "map"):
            self._show("menu")
        elif page == "pace":
            s["pace"] = int(key.split(":")[1])
            self._show("menu")
        elif page == "rations":
            s["rations"] = int(key.split(":")[1])
            self._show("menu")
        elif page == "rest":
            self._rest(s["rest_days"]) if key == "days" else self._show("menu")
        elif page == "trade":
            self._accept_trade() if key == "accept" else self._show("menu")
        elif page == "river":
            if key == "camp":
                self._show("menu")
            elif key == "talk":
                self._event("RIVER ADVICE", ROUTE[s["landmark"]]["talk"], "river")
            else:
                self._cross(key)
        elif page == "final_route":
            if key == "camp":
                self._show("menu")
            elif key == "raft":
                self._start_raft()
            elif s["money"] >= 20:
                s["money"] -= 20
                for _ in range(3):
                    if not self._day(resting=False):
                        return
                self._win()
            else:
                s["notice"] = "The toll is $20. Trade supplies or take the raft."
        elif page == "travel":
            self._show("menu")
        elif page in ("landmark", "menu"):
            if key == "continue":
                self._continue()
            elif key == "talk":
                self._event("TRAIL TALK", ROUTE[s["landmark"]]["talk"], "landmark")
            elif key == "camp":
                self._show("menu")
            elif key == "store":
                s["store_initial"], s["store_return"], s["store_qty"] = False, page, 1
                self._show("store")
            elif key == "hunt":
                self._start_hunt()
            elif key == "trade":
                self._offer_trade()
            elif key == "journal":
                self._event("RECENT TRAIL JOURNAL", s["log"][-3:] or ["Your journal begins in Cape Cod."], "menu")
            elif key == "title":
                s["resume_screen"] = "menu"
                self._show("title")
            else:
                self._show(key)

    def _new(self):
        seed = self._rand(2147483646)+1
        self.state = self._fresh(seed)
        self._show("occupation")

    def _buy(self, item):
        s = self.state
        product = next(p for p in PRODUCTS if p["id"] == item)
        amount = product["step"] * s["store_qty"]
        cost = self._price(product, amount)
        if s["money"] < cost:
            s["notice"] = "Not enough money. Reduce quantity with LEFT."
        elif s["supplies"][item]+amount > (20000 if item == "food" else 999):
            s["notice"] = "The wagon cannot carry any more of this item."
        else:
            s["money"] = round(s["money"]-cost, 2)
            s["supplies"][item] += amount
            s["notice"] = "Bought "+str(amount)+" "+product["label"]+". On hand: "+str(s["supplies"][item])+"."
            if s["broken"] == item:
                s["supplies"][item] -= 1
                s["broken"] = ""
                s["notice"] += " Wagon repaired."

    def _leave_store(self):
        s = self.state
        if s["store_initial"]:
            if s["supplies"]["oxen"] < 2:
                s["notice"] = "Buy at least two oxen to pull the wagon."
                return
            if s["supplies"]["food"] < 50:
                s["notice"] = "Buy at least 50 lb of food before departure."
                return
            s["started"] = True
            s["store_initial"] = False
            self._record("Departed Cape Cod on "+self._date()+".")
            self._event("LEAVING CAPE COD", ["The wagon crew rolls west toward GitHub Universe.", "Your first stop is Providence, 80 miles away.", "SELECT during travel opens camp."], "travel")
        else:
            self._show(s["store_return"])

    def _continue(self):
        s = self.state
        stop = ROUTE[s["landmark"]]
        if self._at_stop() and stop.get("river") and s["landmark"] not in s["crossed"]:
            if not s["river"]:
                self._river_conditions()
            self._show("river")
        elif self._at_stop() and stop.get("final"):
            self._show("final_route")
        elif s["broken"]:
            self._event("WAGON NEEDS REPAIR", "You need a spare "+s["broken"][:-1]+". Try trading or visit a store at this stop.")
        elif s["supplies"]["oxen"] <= 0:
            self._event("NO OXEN LEFT", "Your wagon cannot move. Try to trade for an ox or buy one at a store.")
        else:
            self._show("travel")

    def _next_date(self):
        s = self.state
        s["day"] += 1
        s["elapsed"] += 1
        if s["day"] > MONTH_DAYS[s["month"]-1]:
            s["day"] = 1
            s["month"] += 1
            if s["month"] > 12:
                s["month"] = 1
                s["year"] += 1

    def _weather(self):
        s = self.state
        mountains = ROUTE[s["landmark"]]["scene"] == "mountain"
        cold = s["month"] in (1, 2, 11, 12) or (mountains and s["month"] in (3, 10))
        roll = self._rand()
        if cold:
            return "BLIZZARD" if roll < 12 else "SNOW" if roll < 42 else "COLD"
        if roll < 8:
            return "HEAVY RAIN"
        if roll < 20:
            return "RAIN"
        if s["month"] in (6, 7, 8):
            return "HOT" if roll < 55 else "WARM"
        return "COOL" if roll < 65 else "WARM"

    def _day(self, resting=False):
        s = self.state
        if s["finished"]:
            return False
        self._next_date()
        s["weather"] = self._weather()
        alive = self._alive()
        demand = len(alive)*(3-s["rations"])
        fraction = min(1, s["supplies"]["food"]/max(1, demand))
        s["supplies"]["food"] = max(0, s["supplies"]["food"]-demand)
        cold = s["weather"] in ("COLD", "SNOW", "BLIZZARD")
        exposure = max(0, len(alive)-s["supplies"]["clothes"])*0.65 if cold else 0
        delta = (3.2 if resting else (0.4, -0.5, -1.35)[s["pace"]])-(0, 0.55, 1.35)[s["rations"]]-exposure
        delta -= (1-fraction)*6
        deaths = []
        for p in alive:
            change = delta
            if p["illness"]:
                p["sick_days"] += 1
                change -= 1.4 if resting else 2.6
                if p["sick_days"] >= 4 and self._rand() < (45 if resting else 18):
                    self._record(p["name"]+" recovered from "+p["illness"]+".")
                    p["illness"], p["sick_days"] = "", 0
            p["health"] = max(0, min(100, p["health"]+change))
            if p["health"] <= 0:
                p["alive"] = False
                deaths.append(p["name"])
        for name in deaths:
            self._record(name+" died on "+self._date()+".")
        ox_change = 4 if resting else -(0.15, 0.65, 1.35)[s["pace"]]
        ox_change -= 0.8 if s["weather"] == "HOT" else 0
        s["ox_health"] = max(0, min(100, s["ox_health"] + ox_change))
        if s["ox_health"] == 0 and s["supplies"]["oxen"]:
            s["supplies"]["oxen"] -= 1
            s["ox_health"] = 35
            self._record("An exhausted ox died.")
        if not self._alive():
            self._lose("Your last traveler has died. The wagon will go no farther.")
            return False
        if s["elapsed"] >= 365:
            self._lose("A full year has passed. The expedition has run out of time.")
            return False
        if s["weather"] == "BLIZZARD" and s["month"] in (11, 12, 1, 2) and ROUTE[s["landmark"]]["scene"] == "mountain" and self._rand() < 15:
            self._lose("Winter has closed the mountain pass. Your expedition is stranded.")
            return False
        if deaths:
            self._event("A GRAVE BESIDE THE TRAIL", [", ".join(deaths)+" died.", "The remaining travelers must carry on."], "menu")
        return True

    def _travel_day(self):
        s = self.state
        if not self._day():
            return
        if s["screen"] != "travel":
            return
        if s["supplies"]["oxen"] <= 0 or s["broken"]:
            self._show("menu")
            return
        miles = (23, 29, 35)[s["pace"]]+self._rand(9)-4
        miles *= min(1.15, 0.6+s["supplies"]["oxen"]*0.075)
        if s["weather"] in ("HEAVY RAIN", "SNOW", "BLIZZARD"):
            miles *= 0.6
        if ROUTE[s["landmark"]]["scene"] == "mountain":
            miles *= 0.8
        if s["ox_health"] < 30:
            miles *= 0.7
        next_stop = min(len(ROUTE)-1, s["landmark"]+1)
        s["miles"] = min(ROUTE[next_stop]["miles"], s["miles"]+max(4, int(miles)))
        if s["miles"] >= ROUTE[next_stop]["miles"]:
            s["landmark"], s["last_stop"], s["river"] = next_stop, next_stop, {}
            self._record("Reached "+ROUTE[next_stop]["name"]+" on "+self._date()+".")
            if next_stop == len(ROUTE)-1:
                self._win()
            else:
                self._show("landmark")
            return
        self._random_event()

    def _random_event(self):
        s = self.state
        if self._rand() >= 14:
            return
        kind = self._rand(10)
        if kind <= 2:
            alive = self._alive()
            person = alive[self._rand(len(alive))]
            if person["illness"]:
                return
            illness = ("dysentery", "cholera", "a fever", "a broken arm", "exhaustion")[self._rand(5)]
            person["illness"], person["sick_days"] = illness, 0
            person["health"] = max(1, person["health"]-8)
            self._event("ILLNESS IN THE PARTY", person["name"]+" has "+illness+". Rest and adequate food improve the chance of recovery.")
        elif kind == 3:
            part = ("wheels", "axles", "tongues")[self._rand(3)]
            if s["occupation"] == 1 and self._rand() < 60:
                text = "A wagon "+part[:-1]+" broke. Your carpenter repaired it without using a spare."
            elif s["supplies"][part]:
                s["supplies"][part] -= 1
                text = "A wagon "+part[:-1]+" broke. You replaced it with a spare."
            else:
                s["broken"] = part
                text = "A wagon "+part[:-1]+" broke. You have no spare. Trade for a replacement before continuing."
            self._event("WAGON BREAKDOWN", text)
        elif kind == 4 and s["supplies"]["oxen"] > 0:
            s["supplies"]["oxen"] -= 1
            self._event("OX LOST", "An ox wandered away during the night. You now have "+str(s["supplies"]["oxen"])+" oxen.")
        elif kind == 5:
            lost = min(s["supplies"]["food"], 20+self._rand(50))
            s["supplies"]["food"] -= lost
            self._event("SPOILED PROVISIONS", str(lost)+" lb of food spoiled in a leaking sack.")
        elif kind == 6:
            found = 20+self._rand(40)
            s["supplies"]["food"] = min(20000, s["supplies"]["food"]+found)
            self._event("WILD FRUIT", "The party gathered "+str(found)+" lb of edible fruit beside the trail.", "travel")
        elif kind == 7:
            if not self._day(resting=True):
                return
            self._event("TRAIL DELAY", "A washed-out stretch of trail cost one day. The team rested while scouting a way around.")
        elif kind == 8:
            lost = min(s["money"], 5+self._rand(30))
            s["money"] = round(s["money"]-lost, 2)
            self._event("MISSING COIN PURSE", "$"+self._cost_text(lost)+" disappeared from the wagon overnight.")
        else:
            s["ox_health"] = max(0, s["ox_health"]-12)
            self._event("POOR GRAZING", "The oxen found little grass. A few days of rest will help the team recover.")

    def _rest(self, days):
        completed = 0
        for _ in range(days):
            if not self._day(resting=True):
                return
            completed += 1
        self._event("RESTED IN CAMP", [str(completed)+" days passed. Health is "+self._health()+".", "Food remaining: "+str(self.state["supplies"]["food"])+" lb."], "menu")

    def _offer_trade(self):
        s = self.state
        if not self._day(resting=True):
            return
        need = s["broken"] or ("oxen" if s["supplies"]["oxen"] < 2 else "food" if s["supplies"]["food"] < 100 else "bullets" if s["supplies"]["bullets"] < 10 else PRODUCTS[self._rand(len(PRODUCTS))]["id"])
        amount = 50 if need == "food" else 20 if need == "bullets" else 1
        choices = [("money", 15 if need == "oxen" else 8), ("food", 35), ("bullets", 20), ("clothes", 1)]
        choices = [(key, count) for key, count in choices if key != need and (s["money"] if key == "money" else s["supplies"][key]) >= count]
        if not choices:
            # A labor exchange prevents a broken wagon and empty purse softlock.
            s["trade"] = {"give": "labor", "cost": 2, "receive": need, "amount": amount}
        else:
            give, cost = choices[self._rand(len(choices))]
            s["trade"] = {"give": give, "cost": cost, "receive": need, "amount": amount}
        self._show("trade")

    def _accept_trade(self):
        s, trade = self.state, self.state["trade"]
        if not trade:
            self._show("menu")
            return
        if trade["give"] == "labor":
            for _ in range(trade["cost"]):
                if not self._day(resting=False):
                    return
        elif trade["give"] == "money":
            s["money"] = round(s["money"]-trade["cost"], 2)
        else:
            s["supplies"][trade["give"]] -= trade["cost"]
        item = trade["receive"]
        s["supplies"][item] = min(20000 if item == "food" else 999, s["supplies"][item]+trade["amount"])
        if s["broken"] == item:
            s["broken"] = ""
            s["supplies"][item] -= 1
            message = "The replacement part is fitted. Your wagon can move again."
        else:
            message = "Received "+str(trade["amount"])+" "+item+"."
        s["trade"] = None
        self._event("TRADE COMPLETE", message)

    def _river_conditions(self):
        stop = ROUTE[self.state["landmark"]]
        rain = self.state["weather"] in ("RAIN", "HEAVY RAIN")
        self.state["river"] = {"width": stop.get("width", 300)+self._rand(101)-50, "depth": round(max(0.8, stop.get("depth", 3)+(self._rand(19)-9)/10+(1.2 if rain else 0)), 1), "ferry": stop.get("ferry", 0), "wait": 1+self._rand(3)}

    def _cross(self, method):
        s, river = self.state, self.state["river"]
        if method == "wait":
            if not self._day(resting=True):
                return
            river["depth"] = round(max(0.8, min(12, river["depth"]+(self._rand(17)-9)/10)), 1)
            river["wait"] = max(1, river["wait"]-1)
            self._event("WAITED AT THE RIVER", "The river is now "+str(river["depth"])+" feet deep.", "river")
            return
        if method == "ferry":
            if not river.get("ferry"):
                return
            if s["money"] < river["ferry"]:
                s["notice"] = "Not enough money for the ferry."
                return
            s["money"] -= river["ferry"]
            days = river["wait"]
            risk = 0
        else:
            days = 1
            risk = min(95, max(5, int((river["depth"]-1.5)*22))) if method == "ford" else 12+int(river["width"]/150)
            if s["weather"] == "HEAVY RAIN":
                risk += 15
        for _ in range(days):
            if not self._day(resting=method == "ferry"):
                return
        messages = []
        if self._rand() < risk:
            lost_food = min(s["supplies"]["food"], 30+self._rand(100))
            s["supplies"]["food"] -= lost_food
            lost_bullets = min(s["supplies"]["bullets"], 10+self._rand(31))
            s["supplies"]["bullets"] -= lost_bullets
            messages.append("The wagon capsized! Lost "+str(lost_food)+" lb of food and "+str(lost_bullets)+" bullets.")
            if s["supplies"]["oxen"] and self._rand() < 40:
                s["supplies"]["oxen"] -= 1
                messages.append("An ox was swept away.")
            if self._rand() < 22:
                alive = self._alive()
                person = alive[self._rand(len(alive))]
                person["alive"], person["health"] = False, 0
                messages.append(person["name"]+" drowned.")
            for p in self._alive():
                p["health"] = max(1, p["health"]-8)
            if not self._alive():
                self._lose("No one survived the river crossing.")
                return
        else:
            messages.append("The wagon and everyone aboard reached the far bank safely.")
        s["crossed"].append(s["landmark"])
        self._event("RIVER CROSSED", messages, "travel")

    def _animal(self):
        scene = ROUTE[self.state["landmark"]]["scene"]
        kind = "bison" if scene == "plains" and self._rand() < 40 else "deer" if self._rand() < 60 else "rabbit"
        return {"x": 30+self._rand(260), "y": 64+self._rand(100), "kind": kind, "alive": True, "vx": (1 if self._rand(2) else -1)*(7 if kind == "bison" else 15 if kind == "deer" else 25), "respawn": 0}

    def _start_hunt(self):
        s = self.state
        if s["supplies"]["bullets"] <= 0:
            self._event("NO AMMUNITION", "You need bullets to hunt. Try trading or visit a store.")
            return
        if not self._day(resting=False):
            return
        s["hunt"] = {"x": 160, "y": 175, "dx": 0, "dy": -1, "time": 45, "meat": 0, "kills": 0, "animals": [self._animal() for _ in range(5)], "shot": {}}
        self._show("hunt")

    def _fire(self):
        s, h = self.state, self.state["hunt"]
        if s["supplies"]["bullets"] <= 0:
            self._finish_hunt()
            return
        s["supplies"]["bullets"] -= 1
        h["shot"] = {"x": h["x"], "y": h["y"], "dx": h["dx"], "dy": h["dy"], "ttl": 0.25}
        targets = []
        for animal in h["animals"]:
            if not animal["alive"]:
                continue
            dx, dy = animal["x"]-h["x"], animal["y"]-h["y"]
            along = dx*h["dx"]+dy*h["dy"]
            across = abs(dx*h["dy"]-dy*h["dx"])
            if along > 0 and across <= (14 if animal["kind"] == "bison" else 10 if animal["kind"] == "deer" else 7):
                targets.append((along, animal))
        if targets:
            targets.sort(key=lambda item: item[0])
            animal = targets[0][1]
            animal["alive"], animal["respawn"] = False, 3
            h["meat"] += {"bison": 500, "deer": 80, "rabbit": 8}[animal["kind"]]
            h["kills"] += 1

    def _hunt_tick(self, dt):
        h = self.state["hunt"]
        h["time"] = max(0, h["time"]-dt)
        if h["shot"]:
            h["shot"]["ttl"] -= dt
            if h["shot"]["ttl"] <= 0:
                h["shot"] = {}
        for i, animal in enumerate(h["animals"]):
            if animal["alive"]:
                animal["x"] += animal["vx"]*dt
                if animal["x"] < 20 or animal["x"] > 300:
                    animal["x"] = max(20, min(300, animal["x"]))
                    animal["vx"] = -animal["vx"]
            else:
                animal["respawn"] -= dt
                if animal["respawn"] <= 0:
                    h["animals"][i] = self._animal()
        if h["time"] <= 0:
            self._finish_hunt()

    def _finish_hunt(self):
        s, h = self.state, self.state["hunt"]
        brought = min(100, h.get("meat", 0))
        s["supplies"]["food"] = min(20000, s["supplies"]["food"]+brought)
        s["message"] = ["You hunted "+str(h.get("meat", 0))+" lb of meat.", "You carried "+str(brought)+" lb back to the wagon.", "The party can carry only 100 lb per hunt."]
        s["return_screen"] = "menu"
        self._record("Hunting brought back "+str(brought)+" lb of food.")
        self._show("hunt_result")

    def _start_raft(self):
        self.state["raft"] = {"x": 160, "y": 170, "progress": 0, "lives": 3, "cooldown": 0, "obstacles": [{"x": 48+self._rand(225), "y": 25+i*32, "kind": "rock"} for i in range(5)]}
        self._show("raft")

    def _raft_tick(self, dt):
        s, raft = self.state, self.state["raft"]
        raft["progress"] = min(100, raft["progress"]+dt*2.8)
        raft["cooldown"] = max(0, raft["cooldown"]-dt)
        for obstacle in raft["obstacles"]:
            obstacle["y"] += dt*36
            if obstacle["y"] > 207:
                obstacle["x"], obstacle["y"] = 48+self._rand(225), 25
            if abs(obstacle["y"]-170) < 13 and abs(obstacle["x"]-raft["x"]) < 22 and raft["cooldown"] <= 0:
                raft["lives"] -= 1
                raft["cooldown"] = 1.5
                s["supplies"]["food"] = max(0, s["supplies"]["food"]-25)
                if raft["lives"] <= 0:
                    self._lose("The raft struck too many rocks and broke apart in the bay.")
                    return
        if raft["progress"] >= 100:
            if self._day(resting=False):
                self._win()

    def _score(self):
        s = self.state
        points = {"GOOD": 500, "FAIR": 400, "POOR": 300, "VERY POOR": 200}[self._health()]*len(self._alive())
        supplies = s["supplies"]
        resources = 50+supplies["oxen"]*4+(supplies["wheels"]+supplies["axles"]+supplies["tongues"])*2+supplies["clothes"]*2+supplies["bullets"]//50+supplies["food"]//25+int(s["money"]//5)
        return (points+resources)*OCCUPATIONS[s["occupation"]]["multiplier"]

    def _win(self):
        s = self.state
        s["miles"], s["landmark"] = TOTAL_MILES, len(ROUTE)-1
        s["finished"], s["won"], s["score"] = True, True, self._score()
        s["message"] = ["You reached Fort Mason in San Francisco!", str(len(self._alive()))+" travelers arrived after "+str(s["elapsed"])+" days.", "Coast to GitHub Universe: "+str(TOTAL_MILES)+" miles.", "Final score: "+str(s["score"])+" ("+str(OCCUPATIONS[s["occupation"]]["multiplier"])+"X occupation bonus)."]
        self._show("arrival")

    def _lose(self, reason):
        self.state["finished"], self.state["won"] = True, False
        self.state["message"] = [reason, "The trail ends "+str(TOTAL_MILES-self.state["miles"])+" miles from GitHub Universe.", "Every expedition teaches something for the next journey."]
        self._show("gameover")

    def serialize(self):
        result = _copy(self.state)
        result["effects"] = _copy(self.effects.state)
        return result

    def snapshot(self, include_content=False):
        s, page = self.state, self.state["screen"]
        stop = ROUTE[s["landmark"]]
        next_stop = ROUTE[min(len(ROUTE)-1, s["landmark"]+1)]
        title = {
            "title": "THE UNIVERSE TRAIL", "occupation": "WHO WILL LEAD THE PARTY?", "names": "NAME YOUR TRAVELERS", "keyboard": "NAME A TRAVELER", "month": "WHEN WILL YOU DEPART?", "store": "TRAIL OUTFITTER", "travel": "ON THE UNIVERSE TRAIL", "menu": "SIZE UP THE SITUATION", "supplies": "YOUR SUPPLIES AND PARTY", "map": "CAPE COD TO UNIVERSE", "pace": "CHANGE YOUR PACE", "rations": "CHANGE FOOD RATIONS", "rest": "REST ALONG THE TRAIL", "trade": "A TRAVELER OFFERS A TRADE", "river": stop["name"], "landmark": stop["name"], "event": s["event_title"], "hunt": "HUNTING", "hunt_result": "BACK FROM THE HUNT", "final_route": "THE FINAL PASSAGE", "raft": "RAFTING TO SAN FRANCISCO", "arrival": "WELCOME TO GITHUB UNIVERSE", "gameover": "THE EXPEDITION HAS ENDED", "help": "TRAIL GUIDE "+str(s["help_page"]+1)+" / "+str(len(HELP)), "restart": "REPLACE THIS EXPEDITION?",
        }.get(page, "THE UNIVERSE TRAIL")
        text = []
        hint = "UP/DOWN CHOOSE  SELECT CONFIRMS"
        if page == "title":
            text = ["CAPE COD, MA  ->  SAN FRANCISCO", "A silent, 1985-style wagon adventure", "COAST TO GITHUB UNIVERSE"]
        elif page == "occupation":
            text = ["A banker starts with the most money.", "Carpenters earn double points; farmers triple."]
        elif page == "names":
            text = ["Select a name to edit it with the buttons.", "Your expedition has five travelers."]
        elif page == "keyboard":
            text = ["TRAVELER "+str(s["name_index"]+1)+": "+s["name_draft"]+"_", "Choose letters, then DONE. Maximum 12."]
        elif page == "month":
            text = ["Early spring brings cold; late departures", "risk snow before the Sierra crossing."]
        elif page == "store":
            text = ["CASH $"+self._cost_text(s["money"])+"   BUY QUANTITY x"+str(s["store_qty"]), "LEFT / RIGHT adjusts purchase size."]
            if s["selected"] < len(PRODUCTS):
                p = PRODUCTS[s["selected"]]
                text.append("ON HAND: "+str(s["supplies"][p["id"]])+" "+p["unit"])
            hint = "UP/DOWN ITEM  LEFT/RIGHT QTY  SELECT BUY"
        elif page in ("travel", "menu"):
            text = [self._date()+"   "+s["weather"], "HEALTH "+self._health()+"   FOOD "+str(s["supplies"]["food"])+" LB", PACES[s["pace"]]+" PACE / "+RATIONS[s["rations"]]+" RATIONS"]
            if page == "travel":
                hint = "SELECT TO STOP AND MAKE CAMP"
        elif page == "supplies":
            text = ["CASH $"+self._cost_text(s["money"])+" / OXEN "+str(s["supplies"]["oxen"]), "FOOD "+str(s["supplies"]["food"])+" LB / CLOTHING "+str(s["supplies"]["clothes"]), "BULLETS "+str(s["supplies"]["bullets"]), "SPARES WHEEL/AXLE/TONGUE: "+"/".join(str(s["supplies"][key]) for key in ("wheels", "axles", "tongues"))]
            for person in s["party"]:
                text.append(person["name"]+": "+("DECEASED" if not person["alive"] else person["illness"].upper() if person["illness"] else "WELL"))
            if s["broken"]:
                text.append("BROKEN WAGON "+s["broken"][:-1].upper())
        elif page == "pace":
            text = ["Steady: roughly 23 miles each day.", "Strenuous: 29 miles. Grueling: 35 miles.", "Faster travel strains people and oxen."]
        elif page == "rations":
            text = ["Food per traveler per day:", "Filling 3 lb / Meager 2 lb / Bare bones 1 lb", "Short rations make recovery harder."]
        elif page == "rest":
            text = ["LEFT / RIGHT: choose 1 to 9 days.", "Rest restores health but consumes food."]
        elif page == "trade" and s["trade"]:
            t = s["trade"]
            text = ["Receive "+str(t["amount"])+" "+t["receive"]+".", "Give "+str(t["cost"])+(" days of work." if t["give"] == "labor" else " "+t["give"]+"."), "Searching for a trader used one day."]
        elif page == "river":
            r = s["river"]
            text = ["WIDTH "+str(r.get("width", 0))+" FEET / DEPTH "+str(r.get("depth", 0))+" FEET", "WEATHER "+s["weather"]+" / CASH $"+self._cost_text(s["money"]), "FERRY WAIT "+str(r.get("wait", 0))+" DAYS" if r.get("ferry") else "NO FERRY AT THIS CROSSING"]
        elif page == "landmark":
            text = [self._date()+" / "+str(s["miles"])+" MILES TRAVELED", "You have reached "+stop["name"]+"."]
        elif page in ("event", "hunt_result", "arrival", "gameover"):
            text = list(s["message"])
        elif page == "help":
            text = [HELP[s["help_page"]]]
            hint = "LEFT/RIGHT PAGE  SELECT NEXT  HOLD BACK"
        elif page == "final_route":
            text = ["San Francisco lies beyond the delta.", "Pay $20 for a three-day toll road,", "or steer a raft through the bay."]
        elif page == "hunt":
            hint = "ARROWS MOVE/AIM  SELECT FIRE  HOLD FINISH"
        elif page == "raft":
            hint = "LEFT / RIGHT STEER  AVOID THE ROCKS"
        elif page == "restart":
            text = ["Starting again replaces the saved journey.", "Your current party has traveled "+str(s["miles"])+" miles."]
        if s["notice"]:
            text.append(s["notice"])
        result = {"app": "universe_trail", "theme": "trail", "font_mode": "pixel", "pixel_glow": False, "screen": page, "title": title, "hint": hint, "options": self._options(), "selected_index": s["selected"], "text": text, "date": self._date(), "location": stop["name"], "next_landmark": next_stop["name"], "next_distance": max(0, next_stop["miles"]-s["miles"]), "miles": s["miles"], "total_miles": TOTAL_MILES, "elapsed": s["elapsed"], "weather": s["weather"], "health": self._health(), "health_value": self._health_number(), "food": s["supplies"]["food"], "money": s["money"], "supplies": _copy(s["supplies"]), "party": _copy(s["party"]), "pace": PACES[s["pace"]], "rations": RATIONS[s["rations"]], "occupation": OCCUPATIONS[s["occupation"]]["label"], "multiplier": OCCUPATIONS[s["occupation"]]["multiplier"], "month": MONTHS[s["month"]-1], "scene": stop["scene"], "route": _copy(ROUTE), "landmark_index": s["landmark"], "river": _copy(s["river"]), "hunt": _copy(s["hunt"]), "raft": _copy(s["raft"]), "score": s["score"], "won": s["won"], "finished": s["finished"], "started": s["started"], "name_draft": s["name_draft"], "name_index": s["name_index"], "keyboard_keys": list(KEYS), "store_qty": s["store_qty"], "notice": s["notice"], "phase": self.phase, "regions": []}
        if include_content:
            result["log"] = list(s["log"])
            result["reference"] = "MECC, The Oregon Trail instruction booklet, July 1985. Original code, artwork, route and dialogue."
        result.update(self.effects.metadata())
        if self.effects.active or self.effects.settings:
            result["options"] = result["effects_options"]
            result["selected_index"] = self.effects.selected if self.effects.settings and not self.effects.active else 0
            result["title"] = "SESSION REMINDER" if self.effects.active else "LIGHTS / REMINDERS"
            result["hint"] = "SELECT: DISMISS / DOWN: SNOOZE / RIGHT: OFF" if self.effects.active else "UP/DOWN: CHOOSE / SELECT: CHANGE"
        return result

    def render(self):
        page = self.state["screen"]
        event = self.state["event_title"] if page == "event" else ""
        scene = ("camp" if page in ("menu", "rest") or event == "RESTED IN CAMP" else
                 "river" if page in ("river", "raft") or event in ("RIVER CROSSED", "WAITED AT THE RIVER") else "")
        self.effects.lights(scene)
        if self.effects.active or self.effects.settings:
            return [["clear"], ["text", "UNIVERSE TRAIL", 82, 17, 2, 4],
                    ["line", 12, 40, 308, 40, 2]] + self.effects.overlay()
        return render_game(self) + self.effects.overlay()
