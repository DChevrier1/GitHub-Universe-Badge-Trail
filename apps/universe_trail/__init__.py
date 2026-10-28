"""Universe Trail: a separate silent app for the Universe 2026 badge."""

# BUNDLE_IMPORTS_START
import os
import sys
import json
import time

for _path in ("/system/apps/universe_trail", "/remote/apps/universe_trail"):
    try:
        os.stat(_path + "/core.py")
        if _path not in sys.path:
            sys.path.insert(0, _path)
        break
    except OSError:
        pass

try:
    from .companion import CaseLightDriver, ReminderStore, pacific_clock
except (ImportError, ValueError, KeyError):
    try:
        from ..pipboy.companion import CaseLightDriver, ReminderStore, pacific_clock
    except (ImportError, ValueError, KeyError):
        from companion import CaseLightDriver, ReminderStore, pacific_clock

try:
    from .core import UniverseTrail
    from .display import TrailDisplay, TrailInputs
except (ImportError, ValueError, KeyError):
    from core import UniverseTrail
    from display import TrailDisplay, TrailInputs
# BUNDLE_IMPORTS_END

import json
import sys
import time


class TrailBadgeApp:
    def __init__(self, namespace, config=None):
        self.ns = namespace
        self.badge = namespace["badge"]
        self.state_api = namespace.get("State")
        saved = {}
        if self.state_api:
            try:
                self.state_api.load("universe_trail", saved)
            except (OSError, ValueError):
                pass
        self.core = UniverseTrail(state=saved, config=config)
        self.lights = CaseLightDriver(self.badge)
        self.reminders = ReminderStore(self.core.effects, self.state_api)
        self.clock_elapsed = 1
        self.battery_elapsed = 10
        self.telemetry = {}
        self.display = TrailDisplay(namespace["screen"], namespace["color"], namespace["vec2"], namespace["shape"])
        self.inputs = TrailInputs(self.badge, namespace)
        self.last_saved = self.core.serialize()
        self.last_frame = None
        self.draw_elapsed = 1
        self.save_elapsed = 0
        self.idle_elapsed = 0
        self.dirty = False

    def save(self):
        saved = self.core.serialize()
        if self.state_api and saved != self.last_saved:
            try:
                self.state_api.save("universe_trail", saved)
            except (OSError, ValueError):
                return
        self.last_saved = saved
        self.save_elapsed = 0
        self.dirty = False

    def update(self):
        dt = max(0, min(0.5, self.badge.ticks_delta / 1000.0))
        actions = self.inputs.read(dt)
        self.clock_elapsed += dt
        self.battery_elapsed += dt
        if self.clock_elapsed >= 1:
            self.clock_elapsed = 0
            self.telemetry.update(event_date='', event_time='')
            try:
                utc = time.gmtime()
                if 2025 <= utc[0] <= 2100:
                    fields = pacific_clock(utc)
                elif sys.platform == 'rp2' and self.ns.get('rtc'):
                    fields = self.ns['rtc'].datetime()[:6]
                else:
                    fields = None
                if fields:
                    year, month, day, hour, minute = fields[:5]
                    self.telemetry.update(event_date='%04d-%02d-%02d' % (year, month, day),
                                          event_time='%02d:%02d' % (hour, minute))
            except (OSError, ValueError, TypeError, AttributeError, IndexError):
                pass
        if self.battery_elapsed >= 10:
            self.battery_elapsed = 0
            try:
                self.telemetry['battery'] = self.badge.battery_level()
            except (OSError, ValueError, TypeError, AttributeError):
                self.telemetry['battery'] = None
        self.core.update(actions=actions, dt=dt, telemetry=self.telemetry, return_snapshot=False)
        self.reminders.save()
        self.save_elapsed += dt
        self.idle_elapsed += dt
        if actions:
            self.dirty = True
            self.idle_elapsed = 0
        if (self.dirty and self.idle_elapsed >= 1) or self.save_elapsed >= 20 or "home" in actions:
            self.save()
        self.draw_elapsed += dt
        if actions or self.draw_elapsed >= 0.1:
            self.draw_elapsed = 0
            frame = self.core.render()
            self.lights.write(self.core.effects.levels)
            if frame != self.last_frame:
                self.display.draw(frame)
                self.last_frame = frame


def _configuration():
    config = dict(TRAIL_CONFIG)
    for path in ('config.json', '/system/apps/universe_trail/config.json', '/remote/apps/universe_trail/config.json'):
        try:
            with open(path) as handle:
                value = json.load(handle)
            if isinstance(value, dict):
                config.update(value)
            break
        except (OSError, ValueError):
            pass
    return config


TRAIL_CONFIG = {}

_app = None


def on_exit():
    """The official launcher preserves its Home handler and invokes this hook."""
    if _app:
        _app.lights.close()
        _app.reminders.save()
        _app.save()


def _start():
    global _app
    namespace = dict(globals())
    for name in ("badge", "screen", "color", "vec2", "shape", "image", "run", "HIRES", "VSYNC", "State", "rtc",
                 "BUTTON_UP", "BUTTON_DOWN", "BUTTON_LEFT", "BUTTON_RIGHT", "BUTTON_SELECT",
                 "BUTTON_BACK", "BUTTON_MENU", "BUTTON_HOME", "BUTTON_A", "BUTTON_B", "BUTTON_C"):
        try:
            namespace[name] = eval(name)
        except NameError:
            pass
    if not all(key in namespace for key in ("badge", "screen", "run")):
        return
    namespace["badge"].mode(namespace["HIRES"] | namespace["VSYNC"])
    namespace["screen"] = eval("screen")
    image_api = namespace.get("image")
    if image_api is not None and hasattr(image_api, "OFF"):
        namespace["screen"].antialias = image_api.OFF
    namespace["badge"].default_clear = None
    try:
        from badgeware import State
        namespace["State"] = State
    except ImportError:
        pass
    _app = TrailBadgeApp(namespace, _configuration())
    namespace["run"](_app.update)


_start()
