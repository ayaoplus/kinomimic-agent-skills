---
name: kinomimic-recreate
description: Analyze a complete user-selected reference video, recover its visual sequence, roles, actions, narrative or commercial logic, evidence chain, pacing, and audio design, then produce a structurally faithful but identity-safe kinomimic.plan/v1 generation plan. Use for recreating, adapting, reverse-engineering, storyboarding, or remixing any reference video, including ads, demos, skits, tutorials, hooks, and cinematic clips.
license: MIT
metadata:
  author: KinoMimic
  version: "1.0.0"
---

# KinoMimic Recreate

Treat the supplied file as the complete reference selected by the user. Analyze it from first frame to last frame; never auto-trim or search for a better segment unless explicitly requested.

Requires Python 3.9+, ffmpeg and ffprobe. Tesseract is optional for OCR. Generation requires a compatible renderer such as `kinomimic-render`.

## Workflow

1. Prepare deterministic local artifacts:

```bash
python3 scripts/kinomimic_recreate.py prepare SOURCE_VIDEO \
  --output-dir PROJECT_DIR
```

2. Inspect `source-analysis/storyboard.jpg`.
3. Read `source-analysis/media-analysis.json` and `source-analysis/ocr.txt`.
4. Analyze three layers:
   - visual: shots, framing, camera, staging, hands, props, actions, timing, audio
   - semantic: identities by role, relationships, cause and effect, tests, results
   - intent: narrative function, teaching logic, proof chain, sales logic, payoff
5. Record facts in `analysis.json`. Mark uncertainty instead of guessing.
6. Confirm critical facts with the user before any paid generation.
7. Create `generation-plan.json` following [references/plan-spec.md](references/plan-spec.md).
8. Validate it:

```bash
python3 scripts/kinomimic_recreate.py validate-plan generation-plan.json
```

9. Ask the Agent to invoke `$kinomimic-render` with the validated plan. Do not hardcode another Skill's filesystem path.

## Fidelity priority

Preserve, in order:

1. subject or product correctness
2. operating action and physical causality
3. narrative, educational, or commercial proof structure
4. character count, roles, and relationships
5. shot function, order, timing, and sound
6. non-core appearance

Do not substitute a different product or premise when facts are missing. Ask.

## Safety and originality

Preserve structural functions, not unauthorized identity. Avoid recognizable faces, watermarks, logos, copyrighted dialogue, or protected characters unless the user owns or is authorized to use them. Keep product use physically safe and accurate.
