"""Independent native renderer and five-button input for Universe Trail."""

try:
    from .font5x7 import GLYPHS
except (ImportError, ValueError):
    from font5x7 import GLYPHS

PALETTE = ((0, 0, 0), (35, 35, 35), (112, 112, 112), (242, 242, 235), (255, 255, 255))


class TrailDisplay:
    def __init__(self, screen, color, vec2, shape):
        self.screen, self.color, self.vec2, self.shape = screen, color, vec2, shape
        self.pens = [color.rgb(*rgb) for rgb in PALETTE]
        self.colors = {}
        self.glyphs = {}
        for char, rows in GLYPHS.items():
            runs = []
            for y, bits in enumerate(rows):
                x = 0
                while x < 5:
                    if bits & (16 >> x):
                        start = x
                        while x < 5 and bits & (16 >> x):
                            x += 1
                        runs.append((start, y, x - start))
                    else:
                        x += 1
            self.glyphs[char] = runs

    def text(self, value, x, y, scale):
        origin = x
        for char in str(value):
            if char == "\n":
                x, y = origin, y + 9 * scale
                continue
            for col, row, width in self.glyphs.get(char.upper(), self.glyphs["?"]):
                left, top = int(x + col * scale), int(y + row * scale)
                w, h = int(x + (col + width) * scale) - left, int(y + (row + 1) * scale) - top
                if w > 0 and h > 0:
                    self.screen.rectangle(left, top, w, h)
            x += 6 * scale

    def draw(self, commands):
        for command in commands:
            kind = command[0]
            if kind == "clear":
                self.screen.pen = self.pens[0]
                self.screen.rectangle(0, 0, 320, 240)
            elif kind == "rgbrect":
                rgb = tuple(command[5:8])
                if rgb not in self.colors:
                    self.colors[rgb] = self.color.rgb(*rgb)
                self.screen.pen = self.colors[rgb]
                self.screen.rectangle(*command[1:5])
            elif kind in ("rect", "line", "text"):
                self.screen.pen = self.pens[command[-1]]
                if kind == "rect":
                    self.screen.rectangle(*command[1:5])
                elif kind == "line":
                    self.screen.line(*command[1:5])
                else:
                    self.text(*command[1:5])
            elif kind == "poly":
                points, shade, fill = command[1:]
                self.screen.pen = self.pens[shade]
                if fill:
                    self.screen.shape(self.shape.custom([self.vec2(*point) for point in points]))
                else:
                    for i, point in enumerate(points):
                        other = points[(i + 1) % len(points)]
                        self.screen.line(int(point[0]), int(point[1]), int(other[0]), int(other[1]))


class TrailInputs:
    def __init__(self, badge, namespace):
        self.badge = badge
        self.keys = []
        for action, logical, fallback in (("up", "BUTTON_UP", None), ("down", "BUTTON_DOWN", None),
                                          ("left", "BUTTON_LEFT", "BUTTON_A"), ("right", "BUTTON_RIGHT", "BUTTON_C"),
                                          ("select", "BUTTON_SELECT", "BUTTON_B"), ("back", "BUTTON_BACK", None),
                                          ("menu", "BUTTON_MENU", None), ("home", "BUTTON_HOME", None)):
            key = namespace.get(logical, namespace.get(fallback))
            if key is not None:
                self.keys.append((action, key))
        self.repeats = {}
        self.select_active = False
        self.select_time = 0
        self.select_long = False

    def read(self, dt):
        actions = []
        for action, key in self.keys:
            pressed, held = self.badge.pressed(key), self.badge.held(key)
            if action == "select":
                if pressed:
                    self.select_active, self.select_long, self.select_time = True, False, 0
                elif self.select_active and held:
                    self.select_time += dt
                    if self.select_time >= 0.55 and not self.select_long:
                        actions.append("menu")
                        self.select_long = True
                if self.select_active and self.badge.released(key):
                    if not self.select_long:
                        actions.append("select")
                    self.select_active = False
            elif pressed:
                actions.append(action)
                self.repeats[action] = 0
            elif held and action in ("up", "down", "left", "right"):
                elapsed = self.repeats.get(action, 0) + dt
                if elapsed >= 0.25:
                    actions.append(action)
                    elapsed -= 0.09
                self.repeats[action] = elapsed
            elif not held:
                self.repeats.pop(action, None)
        return actions
