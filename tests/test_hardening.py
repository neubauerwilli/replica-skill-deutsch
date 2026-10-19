"""Regressionen aus der Sicherheits- und Fehlbedienungsprüfung."""
import contextlib
import csv
import io
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
import zlib

from _load import ROOT, load

contrast = load("replica-design", "contrast")
imgdiff = load("replica-vergleich", "imgdiff")
sweep = load("replica-marke", "sweep")
reviews = load("replica-unternehmer", "reviews")


def chunk(kind, data):
    return (struct.pack(">I", len(data)) + kind + data +
            struct.pack(">I", zlib.crc32(kind + data) & 0xffffffff))


def png(raw=b"\0\xff\xff\xff", width=1, height=1, depth=8, color=2):
    return (imgdiff.SIG + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height,
            depth, color, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(raw)) +
            chunk(b"IEND", b""))


class Hardening(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def put(self, name, data):
        path = self.root / name
        if isinstance(data, bytes):
            path.write_bytes(data)
        else:
            path.write_text(data, encoding="utf-8")
        return path

    def cli(self, folder, script, *args):
        result = subprocess.run([sys.executable, str(Path(ROOT) / folder / script),
                                 *map(str, args)], capture_output=True, text=True,
                                encoding="utf-8", timeout=15)
        self.assertNotIn("Traceback", result.stderr)
        return result

    def test_release_gate_blocks_missing_must_even_with_low_threshold(self):
        path = self.put("features.csv", "feature,priority,clone\nLogin,must,no\n")
        self.assertEqual(self.cli("replica-vergleich", "parity.py", path,
                                 "--require-ready", "--fail-under", "0").returncode, 1)

    def test_release_gate_rejects_empty_or_invalid_evidence(self):
        for body in ("feature,priority,clone\n", "feature,priority,clone\nLogin,musst,yes\n",
                     "feature,priority,original,clone\nLogin,must,yees,yes\n",
                     "feature,priority,clone,notes\nLogin,must,skip,\n"):
            with self.subTest(body=body):
                path = self.put("features.csv", body)
                self.assertEqual(self.cli("replica-vergleich", "parity.py", path,
                                         "--require-ready").returncode, 1)

    def test_release_gate_allows_complete_valid_matrix(self):
        path = self.put("features.csv", "feature,priority,clone\nLogin,must,yes\n")
        self.assertEqual(self.cli("replica-vergleich", "parity.py", path,
                                 "--require-ready").returncode, 0)

    def test_csv_extra_cells_return_input_error(self):
        for folder, script, body in (
            ("replica-vergleich", "parity.py", "feature,priority,clone\nLogin,must,yes,extra\n"),
            ("replica-unternehmer", "reviews.py", "url,text\nhttps://example.test/x,slow,extra\n")):
            with self.subTest(script=script):
                path = self.put("bad.csv", body)
                self.assertEqual(self.cli(folder, script, path).returncode, 2)

    def test_wrong_json_types_return_input_error(self):
        for folder, script, option in (("replica-design", "contrast.py", None),
                ("replica-start", "listing.py", None),
                ("replica-marke", "sweep.py", "--config"),
                ("replica-unternehmer", "reviews.py", "--themes")):
            for data in ([], None, "bad"):
                with self.subTest(script=script, data=data):
                    path = self.put("bad.json", json.dumps(data))
                    args = [option, path] if option else [path]
                    if script in ("reviews.py", "sweep.py"):
                        args.insert(0, self.root)
                    self.assertEqual(self.cli(folder, script, *args).returncode, 2)

    def test_contrast_rejects_malformed_pairs_instead_of_passing_zero_checks(self):
        for pairs in ([[]], [["text"]], ["text"], [["text", "bg", "lagre"]]):
            with self.subTest(pairs=pairs):
                path = self.put("tokens.json", json.dumps({"color": {"text": "#111", "bg": "#fff"},
                                                         "pairs": pairs}))
                self.assertEqual(self.cli("replica-design", "contrast.py", path).returncode, 2)

    def test_listing_rejects_whitespace_only_required_fields(self):
        path = self.put("listing.json", json.dumps({"app_store": {"name": "  ", "description": "\n"}}))
        self.assertEqual(self.cli("replica-start", "listing.py", path).returncode, 1)

    def test_listing_cli_avoid_adds_to_configured_names(self):
        path = self.put("listing.json", json.dumps({"avoid": ["Original"],
                "app_store": {"name": "Eigen", "description": "Original"}}))
        self.assertEqual(self.cli("replica-start", "listing.py", path, "--avoid", "Other").returncode, 1)

    def test_sweep_missing_root_is_not_clean(self):
        self.assertEqual(self.cli("replica-marke", "sweep.py", self.root / "missing",
                                 "--avoid", "Original").returncode, 2)

    def test_sweep_invalid_color_is_not_clean(self):
        self.put("index.html", "hello")
        self.assertEqual(self.cli("replica-marke", "sweep.py", self.root,
                                 "--colors", "garbage").returncode, 2)

    def test_sweep_does_not_emit_secret_values(self):
        self.put("index.html", "Eigenes Produkt")
        self.put(".env.local", "API_KEY=Original_PRIVATE_TEST_VALUE")
        hits = sweep.sweep(str(self.root), avoid=["Original"])
        self.assertNotIn("PRIVATE_TEST_VALUE", json.dumps(hits))

    def test_sweep_unreadable_file_is_not_silently_clean(self):
        self.put("index.html", "safe")
        with mock.patch("builtins.open", side_effect=PermissionError("not readable")):
            with self.assertRaises(OSError):
                sweep.sweep(str(self.root), avoid=["Original"])

    def test_png_crc_and_truncated_chunks_are_rejected(self):
        bad_crc = bytearray(png())
        bad_crc[29] ^= 1
        for data in (bytes(bad_crc), imgdiff.SIG + struct.pack(">I", 13) + b"IHDRx"):
            with self.subTest(data=data):
                path = self.put("bad.png", data)
                with self.assertRaises(imgdiff.PngError):
                    imgdiff.read_png(path)

    def test_png_excess_expansion_is_rejected(self):
        path = self.put("bomb.png", png(b"\0\xff\xff\xff" + b"a" * 1000000))
        with self.assertRaises(imgdiff.PngError):
            imgdiff.read_png(path)

    def test_png_zero_dimensions_and_illegal_depth_are_rejected(self):
        for data in (png(width=0), png(depth=1, color=2)):
            with self.subTest(data=data):
                path = self.put("bad.png", data)
                with self.assertRaises(imgdiff.PngError):
                    imgdiff.read_png(path)

    def test_imgdiff_invalid_parameters_return_input_error(self):
        path = self.put("a.png", png())
        for option, value in (("--width", "0"), ("--cols", "0"), ("--tolerance", "-1")):
            with self.subTest(option=option):
                self.assertEqual(self.cli("replica-vergleich", "imgdiff.py", path, path,
                                         option, value).returncode, 2)

    def test_layout_checks_rightmost_column(self):
        a = [[(255, 255, 255)] * 13 for _ in range(10)]
        b = [row[:] for row in a]
        for row in b:
            row[12] = (0, 0, 0)
        report, _ = imgdiff.compare((13, 10, a), (13, 10, b), cols=12)
        self.assertLess(report["score"], 100)

    def test_reviews_reject_links_without_a_real_host(self):
        path = self.root / "reviews.csv"
        with path.open("w", encoding="utf-8", newline="") as fh:
            writer = csv.writer(fh)
            writer.writerow(["url", "text"])
            for url in ("http://", "https:///path", "https://user:password@example.test/x"):
                writer.writerow([url, "too expensive"])
        kept, dropped, _ = reviews.load_reviews(path)
        self.assertEqual((len(kept), dropped), (0, 3))

    def test_review_report_does_not_render_imported_html_or_images(self):
        payload = '<img src="https://example.invalid/track"> ![bild](https://example.invalid/image)'
        result = {"reviews": 1, "sources": ["demo"], "rated": 0, "themes": [],
                  "requests": [{"quote": payload, "source": "demo", "rating": None,
                                "url": "https://example.test/review"}], "unthemed_negative": []}
        text = reviews.render(result)
        self.assertNotIn("<img", text)
        self.assertNotIn("![bild]", text)
        self.assertIn("https://example.test/review", text)

    def test_imgdiff_does_not_overwrite_input(self):
        data = png()
        path = self.put("input.png", data)
        self.assertEqual(self.cli("replica-vergleich", "imgdiff.py", path, path,
                                 "--out", path).returncode, 2)
        self.assertEqual(path.read_bytes(), data)

    def test_sweep_rejects_incomplete_large_text_scan(self):
        self.put("large.js", "safe" * 30)
        with self.assertRaises(ValueError):
            sweep.sweep(str(self.root), avoid=["Original"], max_size=10)


if __name__ == "__main__":
    unittest.main()
