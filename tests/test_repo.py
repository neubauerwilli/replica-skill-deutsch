import json
import os
import re
import unittest

from _load import ROOT

SKILLS = ["replica-erkundung", "replica-architekt", "replica-design", "replica-bau",
          "replica-backend", "replica-test", "replica-vergleich", "replica-unternehmer",
          "replica-marke", "replica-start", "replica-livegang"]
ABOUT = ("Elf kostenlose Claude-Skills auf Deutsch, die jede App nachbauen: auseinandernehmen, "
         "neu bauen, auf Fehler testen, dann beheben, was ihre Nutzer hassen. Kostenlos, MIT.")


def frontmatter(path):
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    return (m.group(1) if m else ""), text


class Repo(unittest.TestCase):
    def test_eleven_skill_folders_at_the_root(self):
        found = sorted(d for d in os.listdir(ROOT)
                       if os.path.isfile(os.path.join(ROOT, d, "SKILL.md")))
        self.assertEqual(found, sorted(SKILLS))

    def test_frontmatter_name_and_description(self):
        for s in SKILLS:
            fm, text = frontmatter(os.path.join(ROOT, s, "SKILL.md"))
            self.assertIn("name: %s\n" % s, fm + "\n", s)
            self.assertRegex(fm, r"description: ", s)
            self.assertGreater(len(fm), 200, "%s description is too thin" % s)
            self.assertGreater(len(text.splitlines()), 60, s)

    def test_plugin_manifest_points_at_the_root_skills(self):
        with open(os.path.join(ROOT, ".claude-plugin", "plugin.json")) as fh:
            plugin = json.load(fh)
        self.assertEqual(plugin["name"], "replica-skill-deutsch")
        self.assertEqual(plugin["skills"], "./")
        self.assertEqual(plugin["description"], ABOUT)
        with open(os.path.join(ROOT, ".claude-plugin", "marketplace.json")) as fh:
            market = json.load(fh)
        self.assertEqual(market["name"], "replica-skill-deutsch")
        self.assertEqual(market["plugins"][0]["name"], "replica-skill-deutsch")

    def test_readme_carries_the_reel_copy(self):
        with open(os.path.join(ROOT, "README.md"), encoding="utf-8") as fh:
            readme = " ".join(fh.read().split())
        self.assertTrue(readme.startswith("# Der Replica-Skill"))
        for line in (
            "Elf Claude-Skills auf Deutsch, die jede App nachbauen. Kostenlos, MIT, ohne "
            "Anmeldung, ohne API-Schlüssel, nichts zu verbinden.",
            "Einer nimmt die App auseinander, die du klonen willst. Einer baut sie neu. Einer "
            "testet sie auf Fehler. Und einer ist der Unternehmer: Er liest, was die Nutzer der "
            "App hassen, und behebt es in deiner, damit du eine App hast, die du verkaufen kannst.",
            "/plugin marketplace add neubauerwilli/replica-skill-deutsch",
            "/plugin install replica-skill-deutsch@replica-skill-deutsch",
            "## Das Kleingedruckte",
        ):
            self.assertIn(line, readme)
        for s in SKILLS:
            self.assertIn("`/%s`" % s, readme)

    def test_no_dashes_anywhere(self):
        bad = []
        for dirpath, dirnames, filenames in os.walk(ROOT):
            dirnames[:] = [d for d in dirnames if d not in (".git", "__pycache__", ".audit-tmp", "node_modules")]
            for fn in filenames:
                if fn.endswith((".md", ".py", ".json", ".ts", ".csv", ".gitattributes")):
                    path = os.path.join(dirpath, fn)
                    with open(path, encoding="utf-8") as fh:
                        txt = fh.read()
                        if chr(0x2014) in txt or chr(0x2013) in txt:
                            bad.append(os.path.relpath(path, ROOT))
        self.assertEqual(bad, [])


if __name__ == "__main__":
    unittest.main()
