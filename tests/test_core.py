"""
tests/test_core.py — Tests unitaires pour les modules core de Nour-Net.

Couvre :
  - core.scanner.is_proxy_target  : filtre de pertinence
  - core.validator.compute_score  : calcul du score
  - core.db                       : persistance SQLite (DB temporaire)
  - core.engine.extract_host      : extraction d'host
  - core.alerts._country_to_flag  : conversion code pays -> drapeau
"""

import sys
import os
import tempfile
import unittest

# S'assurer que le projet est dans le path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# ---------------------------------------------------------------------------
# Tests : is_proxy_target
# ---------------------------------------------------------------------------

class TestIsProxyTarget(unittest.TestCase):
    def setUp(self):
        from core.scanner import is_proxy_target
        self.fn = is_proxy_target

    def test_accepts_phproxy_url(self):
        self.assertTrue(self.fn("http://example.com/phproxy/index.php"))

    def test_accepts_cgi_proxy(self):
        self.assertTrue(self.fn("http://example.com/cgi-bin/nph-proxy.cgi"))

    def test_accepts_anonymizer(self):
        self.assertTrue(self.fn("https://example.com/anonymiz/browse.php"))

    def test_rejects_youtube(self):
        self.assertFalse(self.fn("https://youtube.com/watch?v=abc"))

    def test_rejects_github(self):
        self.assertFalse(self.fn("https://github.com/user/php-proxy"))

    def test_rejects_url_without_proxy_keyword(self):
        self.assertFalse(self.fn("https://example.com/about"))

    def test_rejects_hackerone(self):
        self.assertFalse(self.fn("https://hackerone.com/brave"))

    def test_rejects_stackoverflow(self):
        self.assertFalse(self.fn("https://stackoverflow.com/questions/35100993/php-proxy-script"))


# ---------------------------------------------------------------------------
# Tests : compute_score
# ---------------------------------------------------------------------------

class TestComputeScore(unittest.TestCase):
    def setUp(self):
        from core.validator import compute_score
        self.fn = compute_score

    def test_perfect_score(self):
        # 200 (50) + <2s latency (30) + 3 keywords: cgi-bin, nph-, proxy (12) = 92
        score = self.fn(200, 500, "http://example.com/cgi-bin/nph-proxy.cgi")
        self.assertEqual(score, 92)

    def test_redirect_slow(self):
        # 301 (30) + >5s but <10s latency (5) + 1 keyword (4) = 39
        score = self.fn(301, 7000, "http://example.com/proxy/index.php")
        self.assertEqual(score, 39)

    def test_dead_target(self):
        # 404 (0) + latency non comptee si dead + 0 keywords = 0
        score = self.fn(404, 100, "http://example.com/something")
        self.assertEqual(score, 0)

    def test_capped_at_100(self):
        # Even with many keywords, should not exceed 100
        score = self.fn(200, 100, "http://proxy.cgi-bin.phproxy.nph-anonymiz.tunnel.browse.com/glype")
        self.assertLessEqual(score, 100)

    def test_no_latency(self):
        # latency None should not crash
        score = self.fn(200, None, "http://example.com/proxy")
        self.assertEqual(score, 50 + 4)  # 200 + 1 keyword "proxy"


# ---------------------------------------------------------------------------
# Tests : SQLite DB
# ---------------------------------------------------------------------------

class TestDatabase(unittest.TestCase):
    def setUp(self):
        # Utiliser une DB temporaire pour les tests
        import core.db as db_module
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmp.close()
        self._orig_path = db_module.DB_PATH
        from pathlib import Path
        db_module.DB_PATH = Path(self.tmp.name)
        db_module.init_db()
        self.db = db_module

    def tearDown(self):
        self.db.DB_PATH = self._orig_path
        os.unlink(self.tmp.name)

    def test_insert_and_count(self):
        self.db.upsert_zombie(
            url="http://example.com/proxy",
            score=70,
            status="alive",
            status_code=200,
            latency_ms=500,
        )
        counts = self.db.count_zombies()
        self.assertEqual(counts["total"], 1)
        self.assertEqual(counts["alive"], 1)
        self.assertEqual(counts["dead"], 0)

    def test_upsert_returns_true_on_new(self):
        is_new = self.db.upsert_zombie(
            url="http://newproxy.com/nph-proxy.cgi",
            score=80,
            status="alive",
            status_code=200,
            latency_ms=300,
        )
        self.assertTrue(is_new)

    def test_upsert_returns_false_on_duplicate(self):
        url = "http://dup.com/proxy"
        self.db.upsert_zombie(url=url, score=50, status="alive", status_code=200, latency_ms=1000)
        is_new = self.db.upsert_zombie(url=url, score=60, status="alive", status_code=200, latency_ms=800)
        self.assertFalse(is_new)

    def test_mark_dead(self):
        url = "http://dead.com/cgi-bin/proxy.cgi"
        self.db.upsert_zombie(url=url, score=40, status="alive", status_code=200, latency_ms=2000)
        self.db.mark_dead(url)
        counts = self.db.count_zombies()
        self.assertEqual(counts["dead"], 1)
        self.assertEqual(counts["alive"], 0)

    def test_get_all_alive_ordered_by_score(self):
        self.db.upsert_zombie("http://a.com/proxy", 30, "alive", 200, 1000)
        self.db.upsert_zombie("http://b.com/nph-proxy.cgi", 90, "alive", 200, 100)
        self.db.upsert_zombie("http://c.com/phproxy", 60, "alive", 200, 500)
        rows = self.db.get_all_alive()
        scores = [r["score"] for r in rows]
        self.assertEqual(scores, sorted(scores, reverse=True))


# ---------------------------------------------------------------------------
# Tests : extract_host
# ---------------------------------------------------------------------------

class TestExtractHost(unittest.TestCase):
    def setUp(self):
        from core.engine import extract_host
        self.fn = extract_host

    def test_standard_url(self):
        self.assertEqual(self.fn("http://example.com/path"), "example.com")

    def test_https(self):
        self.assertEqual(self.fn("https://proxy.example.org/nph-proxy.cgi"), "proxy.example.org")

    def test_no_scheme(self):
        # Doit gerer l'absence de scheme
        result = self.fn("example.com/proxy")
        self.assertIsNotNone(result)

    def test_empty(self):
        self.assertIsNone(self.fn(""))

    def test_none_like(self):
        self.assertIsNone(self.fn(None))


# ---------------------------------------------------------------------------
# Tests : _country_to_flag
# ---------------------------------------------------------------------------

class TestCountryFlag(unittest.TestCase):
    def setUp(self):
        from core.alerts import _country_to_flag
        self.fn = _country_to_flag

    def test_fr(self):
        flag = self.fn("FR")
        self.assertEqual(len(flag), 2)  # 2 caracteres Unicode regionaux

    def test_empty(self):
        self.assertEqual(self.fn(""), "")

    def test_lowercase(self):
        # Doit fonctionner en minuscules aussi
        flag = self.fn("us")
        self.assertEqual(len(flag), 2)


if __name__ == "__main__":
    unittest.main()
