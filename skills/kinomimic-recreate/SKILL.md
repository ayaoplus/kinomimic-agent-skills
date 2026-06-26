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
  --output-dir PROJECT_DIR \
  --requirement "Replace the original product with the supplied product image"
```

2. Inspect `source-analysis/storyboard.jpg`.
3. Read `source-analysis/media-analysis.json` and `source-analysis/ocr.txt`.
4. Read `user-requirements.md`. Treat these as explicit user constraints for role, product, scene, language, shot-level, or style changes.
5. Analyze three layers:
   - visual: shots, framing, camera, staging, hands, props, actions, timing, audio
   - semantic: identities by role, relationships, cause and effect, tests, results
   - intent: narrative function, teaching logic, proof chain, sales logic, payoff
6. Record facts in `analysis.json`. Mark uncertainty instead of guessing.
7. Fill `recreation-script.md` from `recreation-script.template.md` and output it to the user before rendering. The script is the human-auditable source of truth.
8. Confirm critical facts, the shot script, and requested changes with the user before any paid generation.
9. Create `generation-plan.json` following [references/plan-spec.md](references/plan-spec.md). Keep the filled script in the optional `script` field and condense it into `generation.prompt`.
10. Validate it:

```bash
python3 scripts/kinomimic_recreate.py validate-plan generation-plan.json
```

11. Ask the Agent to invoke `$kinomimic-render` with the validated plan. Do not hardcode another Skill's filesystem path.

## User-directed adaptation

Support natural-language requirements such as:

- replace one person, role, product, scene, prop, clothing style, or spoken language
- preserve specific shots exactly
- remove or soften a risky action
- change a product use action only when required for product correctness
- modify a specific shot by number after the script is shown

Apply requirements with this priority:

1. legal/safety/product correctness
2. explicit user requirements
3. source video structure and shot order
4. non-core appearance

When a requested change conflicts with the reference video, state the conflict in the script's adaptation blueprint and make the smallest viable change.

## Script output contract

Always output a filled `recreation-script.md` or equivalent Markdown before rendering. Include:

1. video overview: one concise sentence
2. adaptation blueprint: user requirements, preserved elements, changed elements, unresolved facts
3. shot script: every independent shot in source order
4. render prompt: condensed chronological prompt used in `generation.prompt`

For each shot, include time range, visual prompt, and voice/spoken line. Start the visual prompt with framing and camera movement, such as `【特写，缓慢推镜头】`. Use Chinese visual descriptions by default unless the user asks for another language. Leave voice blank when no speech is needed.

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
