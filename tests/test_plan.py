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

    def test_valid_plan_with_script(self):
        plan = {
            "schema": "kinomimic.plan/v1",
            "script": {
                "overview": "A short overview.",
                "shots": [
                    {
                        "number": 1,
                        "time": "0.0-1.0s",
                        "visual_prompt": "【特写，缓慢推镜头】厨房里一只手拿起产品。",
                        "voice": "",
                    }
                ],
            },
            "inputs": {"reference_images": []},
            "generation": {
                "prompt": "A detailed chronological prompt with enough information to render.",
                "duration": 5,
            },
        }
        MODULE.validate_plan_data(plan)

    def test_invalid_script_shape(self):
        plan = {
            "schema": "kinomimic.plan/v1",
            "script": {"shots": "not-a-list"},
            "inputs": {"reference_images": []},
            "generation": {
                "prompt": "A detailed chronological prompt with enough information to render.",
                "duration": 5,
            },
        }
        with self.assertRaises(MODULE.KinoMimicError):
            MODULE.validate_plan_data(plan)


if __name__ == "__main__":
    unittest.main()
