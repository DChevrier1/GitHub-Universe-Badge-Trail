"""Original pixel illustrations for the silent, 320x240 Universe Trail.

The black screen, compact type, limited colors and line drawings evoke the
Apple II era. All sprites and landmarks below are drawn for this project;
there are no ROMs, screenshots or extracted game assets.
"""

INK = {"W": (245, 245, 235), "G": (40, 198, 74), "B": (54, 129, 246),
       "O": (233, 145, 55), "P": (196, 80, 221), "K": (0, 0, 0),
       "D": (102, 102, 102)}

WAGON = (
    "          WWWWWWWWWWW          ",
    "        WWWKKKKKKKKKWWW        ",
    "       WWKKWWWWWWWWWKKWW       ",
    "      WWKWWKKKKKKKKKWWKWW      ",
    "     WWKWKKKKKKKKKKKKKWKWW     ",
    "     WKWWKKKKKKKKKKKKKWWKW     ",
    "    WWKWKKKKKKKKKKKKKKKWKWW    ",
    "    WKKWKKKKKKKKKKKKKKKWKKW    ",
    "    WKKWKKKKKKKKKKKKKKKWKKW    ",
    "    WKKWKKKKKKKKKKKKKKKWKKW    ",
    "    WKKWKKKKKKKKKKKKKKKWKKW    ",
    "    WKKWKKKKKKKKKKKKKKKWKKW    ",
    "    WWWWWWWWWWWWWWWWWWWWWWW    ",
    "    OOOOOOOOOOOOOOOOOOOOOOO    ",
    "    OOOKOOOOOOOOOOKOOOOOOOOWWWW",
    "     OOOWWWOOOOOOOOWWWOOOO     ",
    "       WKKKWOOKOOOWKKKW        ",
    "      WKWWWKWOOOOWKWWWKW       ",
    "      WKWKWKW    WKWKWKW       ",
    "      WKWWWKW    WKWWWKW       ",
    "       WKKKW      WKKKW        ",
    "        WWW        WWW         ",
)
OX = (
    "                  W   W  ",
    "                 WW   WW ",
    "     WWWWWWWWWWW   WWWW  ",
    "   WWWKKKKKKKKKWWWWKKKW ",
    "  WWKKKKKKKKKKKKKKKKKKWW",
    " WWKKKKKKKKKKKKKKKKKKWWW",
    " WKKKKKKKKKKKKKKKKKWWW  ",
    " WKKKKKKKKKKKKKKKKWW    ",
    " WWWWWWWWWWWWWWWWWW     ",
    "   WW  WW     WW WW     ",
    "   W    W     W   W     ",
    "  WW    WW   WW   WW    ",
)
ANIMALS = {
    "bison": ("      OOOOOOO       ", "    OOOOOOOOOOO  O  ",
              "   OOOOOOOOOOOOOOOO ", " OOOOOOOOOOOOOOOOOKO", "OOOOOOOOOOOOOOOOOOO ",
              " OOOOOOOOOOOOOOOOO  ", "  OOO OOOO OOOOO    ", "   OO  OO   OO OO   ",
              "   OO  OO   OO OO   "),
    "deer": ("              O O O ", "               OOO  ", "                OO  ",
             "    OOOOOOOOO  OOO  ", "  OOOOOOOOOOOOOOO   ", " OOOOOOOOOOOOOOO    ",
             "   OO OOOOOOO       ", "   O O    O OO      ", "  OO  O   O  O      "),
    "rabbit": ("       W W ", "       W W ", "       WWW ", "   WWWWWWW ",
               " WWWWWWWW  ", " WWWWWWWW  ", "WWWW WWWWW "),
    "bear": ("    OO      OOO ", "   OOOO    OOOO ", "  OOOOOOOOOOOOO ",
             " OOOOOOOOOOOOOO ", " OOOOOOOOOOOO   ", " OOO OOO OOOO   ",
             " OOO  OO  OOO   "),
}


class Canvas:
    def __init__(self):
        self.commands = [["clear"]]

    def rect(self, x, y, w, h, shade=3):
        self.commands.append(["rect", int(x), int(y), int(w), int(h), shade])

    def rgb(self, x, y, w, h, ink):
        self.commands.append(["rgbrect", int(x), int(y), int(w), int(h)] + list(INK.get(ink, ink)))

    def line(self, x, y, x2, y2, shade=3):
        self.commands.append(["line", int(x), int(y), int(x2), int(y2), shade])

    def text(self, value, x, y, scale=1, shade=3):
        self.commands.append(["text", str(value), int(x), int(y), scale, shade])

    def center(self, value, y, scale=1, shade=3):
        self.text(value, (320 - len(str(value)) * 6 * scale) / 2, y, scale, shade)

    def sprite(self, rows, x, y, scale=1, flip=False):
        for j, source in enumerate(rows):
            row = source[::-1] if flip else source
            i = 0
            while i < len(row):
                char = row[i]
                end = i + 1
                while end < len(row) and row[end] == char:
                    end += 1
                if char != " ":
                    self.rgb(x + i * scale, y + j * scale, (end - i) * scale, scale, char)
                i = end

    def border(self, x, y, w, h, shade=3):
        self.line(x, y, x + w, y, shade)
        self.line(x, y + h, x + w, y + h, shade)
        self.line(x, y, x, y + h, shade)
        self.line(x + w, y, x + w, y + h, shade)


def wrap(value, width=48):
    result = []
    for paragraph in str(value).split("\n"):
        line = ""
        for word in paragraph.split():
            if len(line) + len(word) + bool(line) > width:
                result.append(line)
                line = ""
            while len(word) > width:
                if line:
                    result.append(line)
                    line = ""
                result.append(word[:width])
                word = word[width:]
            line += (" " if line else "") + word
        result.append(line)
    return result


def heading(c, title, subtitle=""):
    title = str(title).upper()
    scale = 1.5 if len(title) <= 31 else 1
    c.center(title[:50], 9, scale)
    c.line(10, 26, 310, 26)
    if subtitle:
        c.center(str(subtitle)[:48], 32)


def footer(c, hint):
    c.line(10, 220, 310, 220, 2)
    c.center(str(hint or "ARROWS: CHOOSE   SELECT: CONTINUE")[:50], 230, 1, 3)


def choices(c, state, y, rows=None):
    options = state.get("options", [])
    if not options:
        return
    selected = state.get("selected_index", 0)
    count = max(1, min(rows or 8, (216 - y) // 18))
    start = min(max(0, selected - count + 1), max(0, len(options) - count))
    for index in range(start, min(len(options), start + count)):
        label = options[index].get("label", str(options[index])) if isinstance(options[index], dict) else str(options[index])
        label = str(label)[:45]
        current = index == selected
        if current:
            c.rect(10, y - 4, 300, 16, 3)
        c.text(("> " if current else "  ") + label, 14, y, 1, 0 if current else 3)
        y += 18
    if start:
        c.text("^", 302, y - count * 18, 1, 0 if selected == start else 3)
    if start + count < len(options):
        c.text("V", 302, y - 18, 1, 0 if selected == start + count - 1 else 3)


def tree(c, x, y, scale=1, color="G"):
    c.rgb(x + 4 * scale, y, 2 * scale, 2 * scale, color)
    c.rgb(x + 2 * scale, y + 2 * scale, 6 * scale, 2 * scale, color)
    c.rgb(x, y + 4 * scale, 10 * scale, 2 * scale, color)
    c.rgb(x + 4 * scale, y + 6 * scale, 2 * scale, 5 * scale, "O")


def mountain(c, x, y, width=80, height=42):
    for i in range(height):
        left = x + width // 2 - i * width // (height * 2)
        w = max(2, i * width // height)
        c.rgb(left, y + i, w, 1, "W" if i < height // 5 else "O")
        if i > height // 5:
            c.rgb(left + w // 2, y + i, max(1, w // 3), 1, "K")


def bridge(c, y=84):
    for x in (90, 230):
        c.rgb(x, y - 31, 4, 49, "O")
        c.rgb(x + 8, y - 31, 4, 49, "O")
        c.rgb(x - 1, y - 33, 14, 3, "O")
        c.rgb(x, y - 17, 12, 3, "O")
    c.rgb(35, y + 5, 252, 3, "O")
    for x in range(40, 285, 6):
        distance = min(abs(x - 96), abs(x - 236))
        cable_y = y - 28 + min(30, distance // 2)
        c.rgb(x, cable_y, 6, 2, "O")
        c.rgb(x, cable_y, 1, y + 5 - cable_y, "O")


def scenery(c, scene, y=62, phase=0, landmark=""):
    """Compact horizon drawings keep the bottom half free for trail statistics."""
    if scene == "city":
        for x, w, h in ((14, 18, 29), (39, 18, 19), (67, 13, 36), (268, 18, 24), (291, 16, 39)):
            c.border(x, y + 46 - h, w, h, 2)
            for wy in range(y + 50 - h, y + 43, 7):
                c.rgb(x + 4, wy, 2, 2, "W")
        if "UNIVERSE" in str(landmark).upper() or "FRANCISCO" in str(landmark).upper():
            bridge(c, y + 40)
        else:
            for x, width, height in ((88, 35, 29), (129, 30, 41), (167, 45, 24), (219, 30, 35)):
                c.border(x, y + 46 - height, width, height, 3)
                for wy in range(y + 52 - height, y + 42, 9):
                    for wx in range(x + 5, x + width - 4, 7):
                        c.rgb(wx, wy, 2, 3, "O")
        c.rgb(12, y + 50, 296, 2, "B")
    elif scene in ("coast", "river"):
        for x in range(12, 304, 22):
            offset = (x // 22 + int(phase * 3)) % 3
            c.rgb(x, y + 40 + offset * 5, 12, 1, "B")
            c.rgb(x + 5, y + 54 + offset * 3, 8, 1, "B")
        if scene == "coast":
            c.border(35, y + 15, 73, 31)
            c.commands.append(["poly", [(32, y + 15), (71, y + 1), (111, y + 15)], 3, False])
            c.rect(64, y + 30, 11, 16, 3)
            for x in (43, 87):
                c.rect(x, y + 24, 9, 8, 3)
            c.text("TRAIL", 55, y + 18)
            c.line(272, y + 10, 272, y + 39)
            c.commands.append(["poly", [(270, y + 12), (247, y + 34), (270, y + 34)], 3, False])
            c.line(240, y + 40, 289, y + 40)
            c.line(245, y + 44, 284, y + 44)
        else:
            for x in (18, 52, 272, 294):
                tree(c, x, y + 22)
            c.line(10, y + 37, 72, y + 40, 2)
            c.line(250, y + 40, 310, y + 33, 2)
    elif scene == "mountain":
        mountain(c, 25, y + 3, 119, 51)
        mountain(c, 106, y - 5, 108, 61)
        mountain(c, 205, y + 8, 87, 47)
        tree(c, 14, y + 38, 2)
        tree(c, 282, y + 36, 2)
    else:
        c.line(12, y + 49, 63, y + 41, 2)
        c.line(63, y + 41, 131, y + 50, 2)
        c.line(131, y + 50, 212, y + 39, 2)
        c.line(212, y + 39, 308, y + 48, 2)
        tree(c, 37, y + 30, 2)
        tree(c, 269, y + 33)
        for x in (16, 104, 148, 191, 253, 294):
            c.rgb(x, y + 59, 3, 1, "G")
            c.rgb(x + 1, y + 56, 1, 4, "G")
        if "CHIMNEY" in str(landmark).upper():
            c.rgb(181, y + 7, 5, 38, "O")
            for row in range(20):
                c.rgb(168 - row, y + 32 + row, 27 + row * 2, 1, "O")
        elif "LARAMIE" in str(landmark).upper():
            for x in range(103, 231, 6):
                c.rgb(x, y + 30, 4, 24, "O")
            c.rgb(152, y + 39, 21, 15, "K")


def wagon(c, x, y, phase=0, scale=1, oxen=True):
    bob = int(phase * 3) % 2
    c.sprite(WAGON, x, y + bob, scale)
    if oxen:
        c.line(x + 28 * scale, y + 15 * scale, x + 44 * scale, y + 15 * scale)
        c.sprite(OX, x + 40 * scale, y + 9 * scale, scale)
        if bob:
            for dx in (43, 48, 54, 59):
                c.rgb(x + dx * scale, y + 20 * scale, 3 * scale, 1 * scale, "K")
                c.rgb(x + (dx + 1) * scale, y + 20 * scale, 2 * scale, 1 * scale, "W")


def draw_title(c, s, phase):
    c.border(8, 8, 304, 210)
    c.border(12, 12, 296, 202, 2)
    c.center("THE", 23, 1.5)
    c.center("UNIVERSE", 45, 3)
    c.center("TRAIL", 76, 3)
    c.center("CAPE COD TO SAN FRANCISCO", 105)
    c.line(42, 122, 278, 122, 2)
    wagon(c, 82, 128, phase, 2)
    c.line(32, 174, 288, 174, 2)
    options = s.get("options", [])
    selected = s.get("selected_index", 0)
    if options:
        label = options[selected].get("label", "TRAVEL THE TRAIL")
        c.center("<  " + label[:35].upper() + "  >", 188)
    else:
        c.center("PRESS SELECT TO BEGIN", 188)
    c.center("A SILENT EXPEDITION TO GITHUB UNIVERSE", 203, 0.75, 2)
    footer(c, s.get("hint", "ARROWS: CHOOSE   SELECT: BEGIN"))


def draw_travel(c, s, phase):
    heading(c, "THE UNIVERSE TRAIL", s.get("date", ""))
    scenery(c, s.get("scene", "plains"), 41, phase, s.get("location", ""))
    wagon(c, 104, 103, phase, 1.5)
    c.line(12, 139, 308, 139, 2)
    stats = (("WEATHER", s.get("weather", "FAIR")), ("HEALTH", s.get("health", "GOOD")),
             ("FOOD", str(s.get("food", 0)) + " LBS"),
             ("NEXT LANDMARK", str(s.get("next_distance", 0)) + " MILES"),
             ("MILES TRAVELED", str(s.get("miles", 0))))
    for i, (label, value) in enumerate(stats):
        c.text(label + ":", 25, 149 + i * 13)
        c.text(str(value).upper()[:23], 169, 149 + i * 13)
    footer(c, s.get("hint", "SELECT: STOP AND LOOK AROUND"))


def draw_map(c, s):
    heading(c, "YOUR TRAIL WEST", str(s.get("miles", 0)) + " OF " + str(s.get("total_miles", 0)) + " MILES")
    # Hand-drawn contiguous-US outline and a route that begins on Cape Cod.
    outline = [(36, 52), (70, 58), (90, 58), (132, 63), (159, 63), (176, 73),
               (193, 69), (206, 79), (222, 77), (233, 67), (257, 63), (271, 53),
               (279, 57), (275, 75), (289, 87), (278, 91), (284, 97), (274, 102),
               (269, 113), (258, 128), (249, 139), (245, 159), (249, 178),
               (242, 177), (232, 157), (221, 154), (206, 162), (187, 155),
               (180, 165), (168, 163), (159, 171), (144, 165), (136, 145),
               (116, 144), (106, 137), (82, 135), (72, 127), (52, 123), (46, 110),
               (35, 100), (28, 78)]
    c.commands.append(["poly", outline, 2, False])
    points = [(283, 90), (264, 100), (248, 105), (230, 109), (208, 107), (184, 108),
              (161, 104), (138, 104), (117, 112), (99, 111), (81, 107), (61, 109), (40, 112)]
    fraction = min(1, max(0, s.get("miles", 0) / max(1, s.get("total_miles", 1))))
    for i in range(len(points) - 1):
        x, y = points[i]
        x2, y2 = points[i + 1]
        for step in range(0, 21, 2):
            c.rgb(x + (x2 - x) * step / 20, y + (y2 - y) * step / 20, 2, 2,
                  "G" if i / (len(points) - 1) < fraction else "O")
    index = min(len(points) - 2, int(fraction * (len(points) - 1)))
    local = fraction * (len(points) - 1) - index
    x = points[index][0] + (points[index + 1][0] - points[index][0]) * local
    y = points[index][1] + (points[index + 1][1] - points[index][1]) * local
    c.border(x - 4, y - 4, 9, 9)
    c.text("CAPE", 264, 113, 0.75)
    c.text("COD", 264, 123, 0.75)
    c.text("SAN FRANCISCO", 16, 139, 0.75)
    c.center(str(s.get("location", ""))[:47], 190)
    c.center("NEXT: " + str(s.get("next_landmark", "GITHUB UNIVERSE"))[:40], 204, 1, 2)
    footer(c, s.get("hint", "SELECT / BACK: RETURN TO TRAIL"))


def draw_hunt(c, s, phase):
    h = s.get("hunt") or {}
    heading(c, "HUNTING", "AMMUNITION: " + str(s.get("supplies", {}).get("bullets", 0)))
    c.border(9, 47, 302, 160, 2)
    for x, y in ((26, 61), (277, 59), (45, 170), (262, 167), (138, 59)):
        tree(c, x, y, 1.5)
    for x, y in ((80, 87), (238, 129), (156, 181), (39, 126)):
        c.rgb(x, y, 6, 2, "G")
        c.rgb(x + 2, y - 3, 1, 3, "G")
    for animal in h.get("animals", []):
        if not animal.get("alive", True):
            continue
        kind = animal.get("kind", "deer")
        rows = ANIMALS.get(kind, ANIMALS["deer"])
        ax, ay = animal.get("x", 200), animal.get("y", 100)
        c.sprite(rows, ax - len(rows[0]) // 2, ay - len(rows) // 2,
                 flip=animal.get("vx", 1) < 0)
    px, py = h.get("x", 160), h.get("y", 140)
    c.sprite((" WW ", " WW ", "WWWW", " WW ", " WW ", "W  W", "W  W"), px - 2, py - 3)
    direction = h.get("direction")
    if isinstance(direction, dict):
        dx, dy = direction.get("dx", 1), direction.get("dy", 0)
    elif isinstance(direction, (list, tuple)) and len(direction) >= 2:
        dx, dy = direction[0], direction[1]
    else:
        dx, dy = h.get("dx", 1), h.get("dy", 0)
    c.line(px + dx * 3, py + dy * 3, px + dx * 10, py + dy * 10)
    ax, ay = px + dx * 22, py + dy * 22
    c.line(ax - 3, ay, ax + 3, ay, 2)
    c.line(ax, ay - 3, ax, ay + 3, 2)
    shot = h.get("shot")
    if shot and shot.get("ttl", 0) > 0:
        sx, sy = shot.get("x", px), shot.get("y", py)
        c.rgb(sx - 2, sy - 2, 4, 4, "O")
    c.text("MEAT: " + str(h.get("meat", h.get("harvest", 0))) + " LBS", 17, 196, 1)
    remaining = h.get("remaining", h.get("time", 0))
    if remaining:
        c.text(str(int(remaining)) + " SEC", 257, 196)
    footer(c, s.get("hint", "ARROWS: MOVE/AIM SELECT: FIRE BACK: END"))


def draw_raft(c, s, phase):
    r = s.get("raft") or {}
    heading(c, "THE FINAL RIVER RUN", "SAN FRANCISCO BAY")
    for y in range(46, 217, 5):
        offset = int((y + phase * 16) % 30)
        c.rgb(18 + offset // 3, y, 11, 5, "G")
        c.rgb(291 - offset // 3, y, 11, 5, "G")
    for y in range(53, 211, 15):
        for x in range(46, 281, 36):
            c.rgb(x + (y % 11), 51 + int(y + phase * 32) % 152, 9, 1, "B")
    for obstacle in r.get("obstacles", []):
        x, y = obstacle.get("x", 140), obstacle.get("y", 100)
        c.sprite(("  WWWW  ", " WWWWWW ", "WWKWWKWW", "WWWWWWWW", " BBBBBB "), x - 8, y - 5, 2)
    x, y = r.get("x", 160), r.get("y", 170)
    c.rgb(x - 17, y + 16, 39, 3, "O")
    c.rgb(x - 20, y + 21, 42, 3, "O")
    c.sprite(WAGON, x - 15, y - 1, 1)
    progress = min(100, max(0, r.get("progress", 0)))
    c.rect(52, 211, 215, 3, 1)
    c.rect(52, 211, int(progress * 2.15), 3, 3)
    c.text("HULL " + str(r.get("lives", 3)), 42, 49)
    c.text(str(int(progress)) + "%", 250, 49)
    footer(c, s.get("hint", "LEFT / RIGHT: STEER CLEAR OF ROCKS"))


def draw_terminal(c, s, phase, won=False):
    heading(c, "GITHUB UNIVERSE" if won else "THE TRAIL ENDS HERE")
    if won:
        scenery(c, "city", 30, phase, "GITHUB UNIVERSE")
        c.center("YOU MADE IT TO SAN FRANCISCO!", 100)
    else:
        c.commands.append(["poly", [(120, 100), (120, 65), (126, 52), (139, 44), (178, 44), (192, 52), (198, 65), (198, 100)], 3, False])
        c.center("HERE LIES", 59)
        c.center("THE PARTY", 73)
        c.line(105, 102, 213, 102)
        for x in (95, 115, 204, 224):
            c.rgb(x, 98, 1, 7, "G")
    y = 116
    for value in s.get("text", [])[:6]:
        for line in wrap(value, 48)[:2]:
            c.center(line, y)
            y += 12
    choices(c, s, max(184, y + 5), 2)
    footer(c, s.get("hint", "SELECT: CONTINUE"))


def draw_menu(c, s, phase):
    screen = s.get("screen", "menu")
    heading(c, s.get("title", "THE UNIVERSE TRAIL"))
    y = 40
    if screen == "store":
        c.text("CASH: $" + str(s.get("money", 0)), 16, y)
        c.text("QUANTITY X" + str(s.get("store_qty", 1)), 211, y, 1, 2)
        options = s.get("options", [])
        selected = s.get("selected_index", 0)
        option = options[selected] if 0 <= selected < len(options) else {}
        item = option.get("id", "").partition("buy:")[2]
        if item:
            c.text("ON HAND: " + str(s.get("supplies", {}).get(item, 0)) + " " + item.upper(), 16, 55)
        for index, line in enumerate(wrap(s.get("notice", ""))[:2]):
            c.text(line, 16, 70 + index * 12)
        choices(c, s, 105)
        footer(c, s.get("hint", "ARROWS: CHOOSE   SELECT: CONTINUE"))
        return
    elif screen in ("landmark", "river"):
        scenery(c, "river" if screen == "river" else s.get("scene", "plains"), 30, phase, s.get("location", ""))
        if screen == "river":
            wagon(c, 112 + int(phase * 3) % 25, 74, phase, 1, False)
        y = 108
    elif screen == "keyboard":
        c.center("ARROWS CHANGE LETTER / POSITION", y, 1, 2)
        y += 18
    lines = []
    for value in s.get("text", []):
        lines.extend(wrap(value))
    option_count = len(s.get("options", []))
    if screen == "help":
        limit = 13
    elif screen in ("landmark", "river"):
        limit = 3
    elif option_count > 6:
        limit = 2
    else:
        limit = max(1, (205 - y - min(5, option_count) * 18) // 12)
    for line in lines[:limit]:
        c.text(line, 16, y)
        y += 12
    if lines:
        y += 9
    choices(c, s, y)
    footer(c, s.get("hint", "ARROWS: CHOOSE   SELECT: CONTINUE"))


def draw_supplies(c, s):
    heading(c, "YOUR PARTY AND SUPPLIES")
    c.text("TRAVELER", 17, 39, 1, 2)
    c.text("CONDITION", 174, 39, 1, 2)
    for i, person in enumerate(s.get("party", [])[:5]):
        y = 55 + i * 15
        c.text(str(person.get("name", "TRAVELER"))[:20], 17, y)
        condition = person.get("illness") or (str(person.get("health", "GOOD")) + "%" if isinstance(person.get("health"), (int, float)) else "GOOD")
        if not person.get("alive", True):
            condition = "DECEASED"
        c.text(str(condition).upper()[:21], 174, y)
    c.line(12, 133, 308, 133, 2)
    supplies = s.get("supplies", {})
    rows = (("OXEN", supplies.get("oxen", 0), "FOOD", str(s.get("food", supplies.get("food", 0))) + "LB"),
            ("CLOTHES", supplies.get("clothes", 0), "BULLETS", supplies.get("bullets", 0)),
            ("WHEELS", supplies.get("wheels", 0), "AXLES", supplies.get("axles", 0)),
            ("TONGUES", supplies.get("tongues", 0), "CASH", "$" + str(s.get("money", 0))))
    for i, (left, value, right, value2) in enumerate(rows):
        y = 145 + i * 17
        c.text(left + ": " + str(value), 17, y)
        c.text(right + ": " + str(value2), 171, y)
    footer(c, s.get("hint", "SELECT / BACK: RETURN"))


def render_game(game):
    s = game.snapshot()
    phase = getattr(game, "phase", 0)
    c = Canvas()
    screen = s.get("screen", "title")
    if screen == "title":
        draw_title(c, s, phase)
    elif screen == "travel":
        draw_travel(c, s, phase)
    elif screen == "map":
        draw_map(c, s)
    elif screen == "supplies":
        draw_supplies(c, s)
    elif screen == "hunt":
        draw_hunt(c, s, phase)
    elif screen == "raft":
        draw_raft(c, s, phase)
    elif screen in ("arrival", "gameover"):
        draw_terminal(c, s, phase, screen == "arrival")
    else:
        draw_menu(c, s, phase)
    return c.commands
