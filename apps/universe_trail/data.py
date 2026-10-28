"""Original route and writing for a silent, 1985-style wagon expedition.

Distances describe the game's fictional wagon itinerary, not driving directions.
The historic mechanics reference is MECC's July 1985 instruction booklet.
"""

OCCUPATIONS = (
    {"id": "banker", "label": "BANKER", "cash": 2500, "multiplier": 1},
    {"id": "carpenter", "label": "CARPENTER", "cash": 1000, "multiplier": 2},
    {"id": "farmer", "label": "FARMER", "cash": 400, "multiplier": 3},
)
MONTHS = ("JANUARY", "FEBRUARY", "MARCH", "APRIL", "MAY", "JUNE", "JULY", "AUGUST", "SEPTEMBER", "OCTOBER", "NOVEMBER", "DECEMBER")
MONTH_DAYS = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
PACES = ("STEADY", "STRENUOUS", "GRUELING")
RATIONS = ("FILLING", "MEAGER", "BARE BONES")
PRODUCTS = (
    {"id": "oxen", "label": "OXEN", "unit": "OX", "step": 2, "price": 20},
    {"id": "food", "label": "FOOD", "unit": "LB", "step": 50, "price": 0.2},
    {"id": "clothes", "label": "CLOTHING", "unit": "SET", "step": 1, "price": 10},
    {"id": "bullets", "label": "AMMUNITION", "unit": "ROUND", "step": 20, "price": 0.1},
    {"id": "wheels", "label": "SPARE WHEELS", "unit": "PART", "step": 1, "price": 10},
    {"id": "axles", "label": "SPARE AXLES", "unit": "PART", "step": 1, "price": 10},
    {"id": "tongues", "label": "SPARE TONGUES", "unit": "PART", "step": 1, "price": 10},
)
DEFAULT_NAMES = ("CAPTAIN", "ADA", "GRACE", "ALAN", "MARGARET")
KEYS = tuple("ABCDEFGHIJKLMNOPQRSTUVWXYZ") + ("SPACE", "DEL", "CLEAR", "DONE")
ROUTE = (
    {"name": "CAPE COD", "miles": 0, "scene": "coast", "store": True, "map": [292, 61], "talk": "The wagon is packed. Five travelers, one wagon, and a continent between Cape Cod and Universe. Buy oxen, food, clothing, ammunition, and repair parts before leaving."},
    {"name": "PROVIDENCE", "miles": 80, "scene": "city", "store": True, "map": [282, 69], "talk": "An early start buys time in the mountains. A late start means more grass for the oxen here, but snow on the western passes."},
    {"name": "HUDSON RIVER", "miles": 240, "scene": "river", "river": True, "width": 630, "depth": 5, "ferry": 8, "map": [266, 75], "talk": "River depth matters more than width. A shallow ford can turn dangerous after heavy rain. A ferry protects the wagon, if you can afford the fare."},
    {"name": "ERIE CANAL", "miles": 490, "scene": "river", "store": True, "map": [243, 66], "talk": "Teams leaving the canal country keep extra wagon parts. A carpenter can sometimes repair a broken part without using a spare."},
    {"name": "CLEVELAND", "miles": 690, "scene": "city", "store": True, "map": [222, 84], "talk": "Five travelers eat fifteen pounds each day on filling rations. Check the distance ahead before buying supplies. Prices climb as the trail gets longer."},
    {"name": "CHICAGO", "miles": 1030, "scene": "city", "store": True, "map": [191, 81], "talk": "Hard travel wears out travelers and oxen. Resting can restore health, but every day in camp still uses food."},
    {"name": "MISSISSIPPI RIVER", "miles": 1220, "scene": "river", "river": True, "width": 1100, "depth": 7, "ferry": 12, "map": [168, 84], "talk": "A wide river is no place to hurry. Caulk the wagon to float it, or pay the ferry. Waiting changes the conditions, but the weather makes no promises."},
    {"name": "COUNCIL BLUFFS", "miles": 1510, "scene": "plains", "store": True, "map": [142, 82], "talk": "The plains have abundant game. Aim with the arrows and fire with SELECT. A wagon party can bring back only one hundred pounds from each hunt."},
    {"name": "PLATTE RIVER", "miles": 1660, "scene": "river", "river": True, "width": 460, "depth": 3, "ferry": 6, "map": [126, 87], "talk": "The Platte is often shallow, but its bottom is treacherous. Even a promising ford carries some risk. Keep dry clothing for the far bank."},
    {"name": "CHIMNEY ROCK", "miles": 1920, "scene": "plains", "map": [109, 82], "talk": "That narrow stone tower means the mountains are getting closer. Winter arrives earlier at high elevations than it does on the coast."},
    {"name": "FORT LARAMIE", "miles": 2040, "scene": "plains", "store": True, "map": [97, 79], "talk": "Stock up before the high country. Warm clothing, sound oxen, and healthy travelers will matter more than a fast pace."},
    {"name": "SOUTH PASS", "miles": 2300, "scene": "mountain", "map": [83, 81], "talk": "The Continental Divide lies under your wheels. Snow can close this country early. Let tired oxen recover before the next climb."},
    {"name": "GREAT SALT LAKE", "miles": 2490, "scene": "mountain", "store": True, "map": [69, 95], "talk": "The desert ahead offers little water or grass. A rested team and filling rations give you the best chance of crossing safely."},
    {"name": "HUMBOLDT RIVER", "miles": 2790, "scene": "river", "river": True, "width": 180, "depth": 2.5, "ferry": 0, "map": [50, 100], "talk": "There is no ferry here. Judge the depth and decide whether to ford, float, or wait. A few days of patience can save many supplies."},
    {"name": "SIERRA NEVADA", "miles": 2970, "scene": "mountain", "map": [34, 114], "talk": "These are the last high mountains. Cold and short rations make illness harder to survive. Rest while you still have food."},
    {"name": "SACRAMENTO DELTA", "miles": 3120, "scene": "river", "store": True, "final": True, "map": [23, 126], "talk": "The bay is within reach. Take the wagon by toll road or build a raft for the final passage. The channel has rocks and drifting logs."},
    {"name": "GITHUB UNIVERSE", "miles": 3210, "scene": "city", "map": [18, 137], "talk": "Fort Mason, San Francisco. The long journey from the Cape Cod is complete. The next chapter begins at Universe."},
)
TOTAL_MILES = ROUTE[-1]["miles"]
HELP = (
    "Lead five travelers from Cape Cod, Massachusetts to GitHub Universe in San Francisco.",
    "Choose an occupation, name your party, select a spring or summer departure, and buy supplies. Banker: $2500 / 1x score. Carpenter: $1000 / 2x. Farmer: $400 / 3x.",
    "Travel advances one day at a time. SELECT opens camp. Change pace or rations, rest, hunt, trade, check supplies, or study the route.",
    "Filling rations use 3 lb per person per day, meager 2 lb, and bare bones 1 lb. Harder paces cover more miles but damage health.",
    "At rivers, choose a ford, float, ferry when available, or wait. Deep water and storms increase the danger.",
    "Hunting: arrows move and aim; SELECT fires. Hold SELECT or use BACK to finish. You can carry at most 100 lb back to camp. Hunting takes one day.",
    "The final passage offers a paid road or a raft. On the raft use LEFT / RIGHT to steer around rocks. Reach the bay with your wagon afloat.",
    "Five buttons work throughout: UP / DOWN choose; LEFT / RIGHT adjust; SELECT confirms; hold SELECT goes back. Your expedition saves automatically. No sound is used.",
    "LIGHTS / REMINDERS is on the title and camp menus. Campfire and river effects use four white case LEDs. Choose brightness or turn decorative lights off. TEST REMINDER previews an alert.",
    "Optional locally configured sessions alert 15 and 5 minutes before, using the real Pacific badge clock. SELECT dismisses; DOWN snoozes 5 minutes or until the start. The game pauses. Reminders need either custom app open and awake; not a stock app or powered-off badge.",
    "Reminders are optional. Title or camp > LIGHTS / REMINDERS > REMINDERS: OFF. SELECT changes ON/OFF. On an alert, RIGHT turns reminders off immediately. If Fallout is also installed, turn reminders off there too; each app saves separately. Agenda and decorative lights stay. Wait two seconds to save, or exit with HOME.",
)
