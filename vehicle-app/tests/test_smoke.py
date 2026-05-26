"""
Smoke tests for the family vehicle browser.

Run from the vehicle-app directory:
    .venv/bin/python -m pytest tests/                 # if pytest installed
    .venv/bin/python -m unittest tests.test_smoke     # always works

These exercise every public route against the default user data dir
(VEHICLE_DATA_DIR unset → user-kaan-and-tess/). They use the Flask
test client and an isolated in-memory SQLite (TEST_DB_PATH=':memory:'
isn't used because the app holds connections, so we just point at a
throwaway file).
"""

import json, os, sys, tempfile, unittest
from pathlib import Path

# Make sure we import from the skill folder, not from any installed copy.
SKILL = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL))


def _bootstrap_app():
    """Import the app fresh with a throwaway DB so tests don't touch
    the user's real cache.db. Returns (app_module, flask_client)."""
    tmpdir = tempfile.mkdtemp(prefix="vbtest-")
    # Force a separate DB by pointing the data dir at a temp copy of the
    # canonical user dir (vehicles.json + weights.json copied in; images
    # are read-only and live wherever the real ones are, so we just leave
    # the test DB isolated and let images come from the real dir).
    real_data = (SKILL.parent / "user-kaan-and-tess").resolve()
    fake_data = Path(tmpdir) / "data"
    fake_data.mkdir()
    for fname in ("vehicles.json", "weights.json", "image_seeds.json"):
        src = real_data / fname
        if src.exists():
            (fake_data / fname).write_bytes(src.read_bytes())
    # Symlink images so we can verify the image route end-to-end.
    (fake_data / "images").symlink_to(real_data / "images")

    os.environ["VEHICLE_DATA_DIR"] = str(fake_data)
    # Force module re-import so it picks up the new env var.
    for mod in list(sys.modules):
        if mod in ("app", "scoring", "tco") or mod.startswith("scrapers"):
            del sys.modules[mod]
    import app  # noqa: E402
    app.init_db()
    return app, app.app.test_client()


class SmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app_module, cls.client = _bootstrap_app()

    def test_index_renders_all_vehicles(self):
        r = self.client.get("/")
        self.assertEqual(r.status_code, 200)
        body = r.data.decode()
        vehicles = self.app_module.load_vehicles()
        self.assertEqual(body.count('class="vehicle-card'), len(vehicles))
        self.assertIn('hx-post="/rerank"', body)

    def test_every_vehicle_detail_page(self):
        for v in self.app_module.load_vehicles():
            r = self.client.get(f"/vehicle/{v['id']}")
            self.assertEqual(r.status_code, 200, f"failed for {v['id']}")
            self.assertIn("Ranked #", r.data.decode())

    def test_unknown_vehicle_404(self):
        r = self.client.get("/vehicle/does-not-exist")
        self.assertEqual(r.status_code, 404)

    def test_custom_weights_change_rank(self):
        """The vehicle with the cohort's lowest TCO (tco_score=5.00)
        must land at #1 when weighting is TCO-only."""
        import re
        # Pick whichever vehicle has score=5 at the current horizon.
        leader = max(self.app_module.load_vehicles(),
                     key=lambda v: v["scores"]["tco"])
        self.assertAlmostEqual(leader["scores"]["tco"], 5.0, places=2)
        zero = "&".join(f"w_{k}=0" for k in
                        ["car_seat_fit","cargo","third_row","corridor",
                         "hitch","reliability","winter","fsr"])
        r = self.client.get(f"/vehicle/{leader['id']}?w_tco=5&{zero}")
        self.assertEqual(r.status_code, 200)
        m = re.search(r"Ranked #(\d+) of \d+", r.data.decode())
        self.assertIsNotNone(m)
        self.assertEqual(m.group(1), "1",
            f"TCO leader {leader['id']} should rank #1 under TCO-only weights")

    def test_rerank_tolerates_garbage(self):
        r = self.client.post("/rerank", data={
            "w_tco": "not-a-number", "w_reliability": "4"})
        self.assertEqual(r.status_code, 200)
        # Should still render the full card grid
        vehicles = self.app_module.load_vehicles()
        self.assertGreaterEqual(
            r.data.decode().count('class="vehicle-card'), len(vehicles))

    def test_compare_route(self):
        r = self.client.get("/compare?ids=sienna-used&ids=palisade-used")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data.decode().count('class="compare-col"'), 2)

    def test_health_reports_vehicle_count(self):
        r = self.client.get("/health")
        self.assertEqual(r.status_code, 200)
        vehicles = self.app_module.load_vehicles()
        self.assertIn(f"{len(vehicles)} vehicles", r.data.decode())

    def test_api_returns_ranked_list(self):
        r = self.client.get("/api/vehicles")
        self.assertEqual(r.status_code, 200)
        payload = json.loads(r.data)
        vehicles = self.app_module.load_vehicles()
        self.assertEqual(len(payload), len(vehicles))
        # Ranks should be 1..N
        self.assertEqual([v["rank"] for v in payload],
                         list(range(1, len(vehicles) + 1)))

    def test_favourite_toggle_roundtrip(self):
        r1 = self.client.post("/favourite/sienna-used")
        self.assertEqual(r1.status_code, 200)
        self.assertTrue(json.loads(r1.data)["is_favourite"])
        # Toggle back so the test is idempotent
        r2 = self.client.post("/favourite/sienna-used")
        self.assertFalse(json.loads(r2.data)["is_favourite"])

    def test_note_roundtrip(self):
        r = self.client.post("/note/sienna-used", data={"note": "hello world"})
        self.assertEqual(r.status_code, 200)
        self.assertTrue(json.loads(r.data)["saved"])
        self.assertEqual(self.app_module.get_note("sienna-used"), "hello world")

    def test_horizon_changes_tco_total(self):
        """At 8yr vs 10yr the TCO must drop (less fuel/maint/ins) and the
        Sienna's TCO must drop by a sensible amount (~$10-20k)."""
        import re
        def tco_for(horizon, vid="sienna-used"):
            r = self.client.get(f"/vehicle/{vid}?horizon={horizon}")
            self.assertEqual(r.status_code, 200, f"horizon={horizon}")
            m = re.search(r"Net %d-year TCO[^$]*\$([\d,]+)" % horizon, r.data.decode())
            self.assertIsNotNone(m, f"couldn't parse TCO at horizon={horizon}")
            return int(m.group(1).replace(",", ""))
        tco_10 = tco_for(10)
        tco_8  = tco_for(8)
        tco_12 = tco_for(12)
        self.assertLess(tco_8, tco_10, "shorter horizon should mean lower TCO")
        self.assertGreater(tco_12, tco_10, "longer horizon should mean higher TCO")
        # Sanity bounds: shifts should be in the thousands, not zero or wild.
        self.assertGreater(tco_10 - tco_8, 3000)
        self.assertLess(tco_10 - tco_8, 25000)

    def test_horizon_clamped_to_valid_range(self):
        """Out-of-range horizons clamp; garbage falls back to default."""
        import re
        for raw in ("0", "99", "abc", ""):
            r = self.client.get(f"/?horizon={raw}")
            self.assertEqual(r.status_code, 200)
            # The TCO column label echoes the in-use horizon — must be a
            # plausible value (4..15).
            labels = re.findall(r"(\d+)yr TCO", r.data.decode())
            self.assertTrue(labels, f"no horizon label rendered for {raw!r}")
            self.assertTrue(4 <= int(labels[0]) <= 15,
                            f"horizon {labels[0]} out of clamp for input {raw!r}")

    def test_horizon_renormalizes_tco_score(self):
        """tco_score is renormalized over the cohort at each horizon, so
        the API's score field for a given vehicle can shift with horizon."""
        import re
        r10 = self.client.get("/api/vehicles?horizon=10")
        r6  = self.client.get("/api/vehicles?horizon=6")
        self.assertEqual(r10.status_code, 200)
        self.assertEqual(r6.status_code, 200)
        scores_10 = {v["id"]: v["score"] for v in json.loads(r10.data)}
        scores_6  = {v["id"]: v["score"] for v in json.loads(r6.data)}
        # The Sorento has the best TCO; both horizons should rank it well.
        # But some vehicle's relative score MUST change between the two.
        diffs = [scores_10[k] - scores_6[k] for k in scores_10]
        self.assertTrue(any(abs(d) > 0.05 for d in diffs),
                        "no score shifted between horizon=10 and horizon=6")

    def test_weight_precision_accepts_one_decimal(self):
        """Build A: sidebar inputs use step="0.1" so the default winter
        weight of 1.3 is accepted on first render. Server also rounds
        hand-typed values past one decimal back to 1dp."""
        from werkzeug.datastructures import MultiDict
        # 1. HTML uses step="0.1", not step="0.5".
        body = self.client.get("/").data.decode()
        self.assertIn('step="0.1"', body)
        self.assertNotIn('step="0.5"', body)
        # 2. POST /rerank with a 2dp value still returns 200.
        r = self.client.post("/rerank", data={"w_winter": "1.34"})
        self.assertEqual(r.status_code, 200)
        # 3. parse_weights truncates the server-side value to 1dp.
        parsed = self.app_module.parse_weights(
            MultiDict([("w_winter", "1.34")]))
        self.assertEqual(parsed["winter"], 1.3)
        # And a value already on the grid is unchanged.
        parsed2 = self.app_module.parse_weights(
            MultiDict([("w_tco", "3.0")]))
        self.assertEqual(parsed2["tco"], 3.0)

    def test_warranty_cliff_in_maintenance(self):
        """Build B: maintenance follows a two-rate model that preserves
        the stored maint_10yr at N=10, undershoots linear pre-cliff, and
        overshoots linear post-cliff."""
        import tco
        v = next(x for x in self.app_module.load_vehicles()
                 if x["id"] == "grand-highlander-used")
        self.assertEqual(v["warranty_years_remaining"], 7)
        maint_10yr = v["maint_10yr"]

        m7  = tco.recompute_tco(v, 7)["maint"]
        m10 = tco.recompute_tco(v, 10)["maint"]
        m12 = tco.recompute_tco(v, 12)["maint"]

        # 1. N=10 returns the stored value within $5 rounding tolerance.
        self.assertLessEqual(abs(m10 - maint_10yr), 5,
            f"maint(10)={m10} should equal stored {maint_10yr}")
        # 2. N=7 (pure in-warranty for this vehicle) costs LESS than
        #    the linear model would predict.
        linear_7 = maint_10yr * 7 / 10
        self.assertLess(m7, linear_7,
            f"maint(7)={m7} should be < linear {linear_7:.0f} pre-cliff")
        # 3. N=12 (out-of-warranty multiplier compounds) costs MORE.
        linear_12 = maint_10yr * 12 / 10
        self.assertGreater(m12, linear_12,
            f"maint(12)={m12} should be > linear {linear_12:.0f} post-cliff")

    def test_image_serves(self):
        # Pick any vehicle that has at least one image on disk
        vehicles = self.app_module.load_vehicles()
        for v in vehicles:
            imgs = self.app_module.get_vehicle_images(v["id"])
            if imgs:
                r = self.client.get(imgs[0])
                self.assertEqual(r.status_code, 200)
                self.assertGreater(len(r.data), 1000)
                return
        self.skipTest("no images on disk to serve")


if __name__ == "__main__":
    unittest.main()
