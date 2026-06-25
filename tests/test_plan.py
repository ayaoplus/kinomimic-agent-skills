import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills/kinomimic-recreate/scripts/kinomimic_recreate.py"
SPEC = importlib.util.spec_from_file_location("kinomimic_recreate", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(MODULE)


class PlanValidationTest(unittest.TestCase):
    def test_valid_plan(self):
        plan = {
            "schema": "kinomimic.plan/v1",
            "inputs": {"reference_images": []},
            "generation": {
                "prompt": "A detailed chronological prompt with enough information to render.",
                "duration": 5,
            },
        }
        MODULE.validate_plan_data(plan)

    def test_invalid_schema(self):
        with self.assertRaises(MODULE.KinoMimicError):
            MODULE.validate_plan_data({"schema": "wrong"})


if __name__ == "__main__":
    unittest.main()
