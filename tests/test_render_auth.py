import argparse
import importlib.util
from pathlib import Path
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills/kinomimic-render/scripts/kinomimic_render.py"
SPEC = importlib.util.spec_from_file_location("kinomimic_render", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(MODULE)


class RenderAuthTest(unittest.TestCase):
    def test_auth_status_redacts_key(self):
        with mock.patch.dict("os.environ", {"KINOMIMIC_API_KEY": "secret-value"}):
            status = MODULE.command_auth_status(argparse.Namespace())
        self.assertTrue(status["found"])
        self.assertEqual(status["source"], "environment")
        self.assertEqual(status["name"], "KINOMIMIC_API_KEY")
        self.assertTrue(status["key_is_redacted"])
        self.assertNotIn("value", status)
        self.assertNotIn("secret-value", repr(status))


if __name__ == "__main__":
    unittest.main()
