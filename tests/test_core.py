"""Gameplay contracts shared by the native app and web companion."""

import unittest

from apps.universe_trail.core import UniverseTrail
from apps.universe_trail.data import ROUTE, TOTAL_MILES


class TrailMechanicsTests(unittest.TestCase):
    def prepared_game(self, occupation="banker"):
        game = UniverseTrail(config={"seed": 12345})
        for option in ("new", occupation, "done", "month:4"):
            game.update("option:" + option)
        for item in ("oxen", "food", "clothes", "bullets", "wheels", "axles", "tongues"):
            game.update("option:buy:" + item)
        game.update("option:done")
        game.update("select")
        self.assertEqual(game.state["screen"], "travel")
        return game

    def test_new_expedition_requires_oxen_and_food(self):
        game = UniverseTrail()
        for option in ("new", "farmer", "done", "month:5", "done"):
            game.update("option:" + option)
        self.assertEqual(game.state["screen"], "store")
        self.assertFalse(game.state["started"])
        self.assertIn("two oxen", game.state["notice"])
        game.update("option:buy:oxen")
        game.update("option:done")
        self.assertIn("50 lb", game.state["notice"])
        game.update("option:buy:food")
        game.update("option:done")
        self.assertTrue(game.state["started"])
        self.assertEqual(game.state["supplies"]["oxen"], 2)
        self.assertEqual(game.state["supplies"]["food"], 50)
        self.assertEqual(game.state["money"], 350)

    def test_rest_consumes_rations_and_recovers_living_travelers(self):
        game = self.prepared_game()
        for person in game.state["party"]:
            person["health"] = 60
        game.state["party"][4]["alive"] = False
        game.state["rations"] = 1
        game.state["ox_health"] = 50
        self.assertTrue(game._day(resting=True))
        self.assertEqual(game.state["supplies"]["food"], 42)
        self.assertEqual(game.state["elapsed"], 1)
        self.assertEqual(game.state["day"], 2)
        self.assertGreater(game.state["party"][0]["health"], 60)
        self.assertEqual(game.state["party"][4]["health"], 60)
        self.assertGreater(game.state["ox_health"], 50)

    def test_outfitter_can_restart_after_spending_cash_without_required_supplies(self):
        game = UniverseTrail()
        for option in ("new", "farmer", "done", "month:5"):
            game.update("option:" + option)
        # Spend the entire $400 on food without buying the required oxen.
        game.state["store_qty"] = 20
        game.update(["option:buy:food", "option:buy:food", "option:done"])
        self.assertEqual(game.state["money"], 0)
        self.assertEqual(game.state["supplies"]["food"], 2000)
        self.assertEqual(game.state["screen"], "store")
        game.update("up")
        self.assertEqual(game.snapshot()["options"][game.state["selected"]]["id"], "new")
        restart_labels = [command for command in game.render()
                          if command[0] == "text" and command[1] == "> START OVER"]
        self.assertEqual(len(restart_labels), 1)
        self.assertLess(restart_labels[0][3] + 7, 220)
        game.update("select")
        self.assertEqual(game.state["screen"], "occupation")
        self.assertTrue(all(amount == 0 for amount in game.state["supplies"].values()))
        game.update("option:farmer")
        self.assertEqual(game.state["money"], 400)
        self.assertFalse(game.state["started"])

        # Stores visited during an expedition cannot reset its supplies or cash.
        game = self.prepared_game()
        game.update(["menu", "option:store"])
        self.assertEqual(game.state["screen"], "store")
        self.assertNotIn("new", [option["id"] for option in game.snapshot()["options"]])
        before = game.serialize()
        game.update("option:new")
        self.assertEqual(game.serialize(), before)

    def test_unfed_party_can_die_without_advancing_travel(self):
        game = self.prepared_game()
        game.state["supplies"]["food"] = 0
        for person in game.state["party"]:
            person["health"] = 1
        game.update(dt=1.25)
        self.assertEqual(game.state["screen"], "gameover")
        self.assertTrue(game.state["finished"])
        self.assertFalse(game.state["won"])
        self.assertEqual(game.state["miles"], 0)

    def test_saved_landmark_generates_its_actual_river_conditions(self):
        game = self.prepared_game()
        game.state.update(screen="landmark", landmark=2, miles=ROUTE[2]["miles"])
        restored = UniverseTrail(state=game.serialize())
        self.assertEqual(restored.state["river"], {})
        restored.update("option:continue")
        self.assertEqual(restored.state["screen"], "river")
        self.assertEqual(restored.state["river"]["ferry"], ROUTE[2]["ferry"])
        self.assertGreaterEqual(restored.state["river"]["width"], ROUTE[2]["width"] - 50)
        restored.update("option:ferry")
        self.assertIn(2, restored.state["crossed"])
        restored.update("select")
        self.assertEqual(restored.state["screen"], "travel")

    def test_hunt_aim_hit_and_carry_limit_survive_reload(self):
        game = self.prepared_game()
        game.update(["menu", "option:hunt"])
        self.assertEqual(game.state["elapsed"], 1)
        hunt = game.state["hunt"]
        hunt["animals"] = [{"kind": "bison", "x": 160, "y": 100, "vx": 0,
                            "alive": True, "respawn": 0}]
        food, bullets = game.state["supplies"]["food"], game.state["supplies"]["bullets"]
        game.update("select")
        self.assertEqual(hunt["meat"], 500)
        self.assertEqual(game.state["supplies"]["bullets"], bullets - 1)
        restored = UniverseTrail(state=game.serialize())
        restored.update("back")
        self.assertEqual(restored.state["screen"], "hunt_result")
        self.assertEqual(restored.state["supplies"]["food"], food + 100)
        restored.update("select")
        self.assertEqual(restored.state["supplies"]["food"], food + 100)

    def test_paused_trade_is_restored_and_repairs_wagon(self):
        game = self.prepared_game()
        game.state["broken"] = "axles"
        game.state["supplies"]["axles"] = 0
        game.update(["menu", "option:trade", "home"])
        offer = game.state["trade"].copy()
        restored = UniverseTrail(state=game.serialize())
        self.assertEqual(restored.state["trade"], offer)
        restored.update(["option:resume", "option:accept"])
        self.assertEqual(restored.state["broken"], "")
        self.assertEqual(restored.state["supplies"]["axles"], 0)
        self.assertIsNone(restored.state["trade"])

    def test_trade_without_resources_offers_work_for_repairs(self):
        game = self.prepared_game()
        game.state["money"] = 0
        for key in game.state["supplies"]:
            game.state["supplies"][key] = 0
        game.state["broken"] = "wheels"
        game.update(["menu", "option:trade"])
        self.assertEqual(game.state["trade"]["give"], "labor")
        restored = UniverseTrail(state=game.serialize())
        restored.update("option:accept")
        self.assertEqual(restored.state["elapsed"], 3)
        self.assertEqual(restored.state["broken"], "")

    def test_saved_travel_remains_deterministic(self):
        game = self.prepared_game()
        game.state["supplies"].update(food=2000, clothes=5, oxen=6)
        restored = UniverseTrail(state=game.serialize())
        self.assertEqual(game.serialize(), restored.serialize())
        for _ in range(50):
            for expedition in (game, restored):
                if expedition.state["screen"] == "river":
                    expedition.update("option:ferry")
                elif expedition.state["screen"] != "travel":
                    expedition.update("option:continue")
                expedition.update(dt=1.25)
            self.assertEqual(game.serialize(), restored.serialize())

    def test_final_toll_route_arrives_and_applies_occupation_score(self):
        game = self.prepared_game("carpenter")
        game.state.update(screen="final_route", landmark=len(ROUTE) - 2,
                          miles=ROUTE[-2]["miles"])
        game.state["supplies"]["food"] = 500
        cash = game.state["money"]
        game.update("option:toll")
        self.assertEqual(game.state["screen"], "arrival")
        self.assertEqual(game.state["miles"], TOTAL_MILES)
        self.assertEqual(game.state["elapsed"], 3)
        self.assertEqual(game.state["money"], cash - 20)
        self.assertTrue(game.state["won"])
        score = game.state["score"]
        game.state["occupation"] = 0
        self.assertEqual(score, game._score() * 2)

    def test_raft_collision_and_completion_are_resumable(self):
        game = self.prepared_game()
        game.state.update(screen="final_route", landmark=len(ROUTE) - 2,
                          miles=ROUTE[-2]["miles"])
        game.update("option:raft")
        raft = game.state["raft"]
        raft["obstacles"] = [{"x": raft["x"], "y": 166, "kind": "rock"}]
        game.update(dt=0.1)
        self.assertEqual(raft["lives"], 2)
        restored = UniverseTrail(state=game.serialize())
        restored.state["raft"].update(progress=99.9, obstacles=[])
        restored.update(dt=0.1)
        self.assertTrue(restored.state["won"])

    def test_hunter_draws_the_actual_aim_direction(self):
        game = self.prepared_game()
        game.update(["menu", "option:hunt", "left"])
        hunt = game.state["hunt"]
        self.assertIn(["line", hunt["x"] - 3, hunt["y"], hunt["x"] - 10, hunt["y"], 3], game.render())
        game.update("up")
        self.assertIn(["line", hunt["x"], hunt["y"] - 3, hunt["x"], hunt["y"] - 10, 3], game.render())

    def test_store_renders_purchase_failures_and_inventory(self):
        game = self.prepared_game()
        game.state.update(screen="store", money=0, selected=0)
        game.update("option:buy:oxen")
        labels = [command[1] for command in game.render() if command[0] == "text"]
        self.assertIn(game.state["notice"], labels)
        self.assertIn("ON HAND: 2 OXEN", labels)


if __name__ == "__main__":
    unittest.main()
