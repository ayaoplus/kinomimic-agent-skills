---
name: kinomimic-render
description: Render versioned kinomimic.plan/v1 files through an asynchronous AI video provider, then poll, download, inspect, list, cancel, or delete jobs. Use for text-to-video, image-guided video, first/last-frame generation, multimodal references, task management, and provider usage inspection. The public interface is provider-neutral; the bundled adapter currently supports Volcengine Ark Seedance.
license: MIT
metadata:
  author: KinoMimic
  version: "1.0.0"
---

# KinoMimic Render

Use `scripts/kinomimic_render.py` as the deterministic provider boundary.

Requires Python 3.9+ and network access. Configure `KINOMIMIC_API_KEY`. The current provider adapter is `volcengine-ark`.

## Render a plan

```bash
python3 scripts/kinomimic_render.py render-plan generation-plan.json \
  --output-dir ./kinomimic-output
```

The default behavior creates a billable task, polls it, downloads the result, and preserves `result.json`.

## Task operations

```bash
python3 scripts/kinomimic_render.py get TASK_ID
python3 scripts/kinomimic_render.py wait TASK_ID --download
python3 scripts/kinomimic_render.py list --status succeeded
python3 scripts/kinomimic_render.py delete TASK_ID
```

## Authentication and providers

Set:

```bash
export KINOMIMIC_PROVIDER=volcengine-ark
export KINOMIMIC_API_KEY="..."
```

Optional overrides:

```bash
export KINOMIMIC_BASE_URL="https://provider.example/api/v3"
export KINOMIMIC_MODEL="provider-model-id"
```

The Volcengine adapter also accepts legacy `SEEDANCE_API_KEY` and `ARK_API_KEY`.

Read [references/providers.md](references/providers.md) for provider details and limits.

## Rules

- Treat rendering as a billable external action.
- Never place secrets in plan files, prompts, logs, source code, or command arguments.
- Download successful results immediately when provider URLs expire.
- Validate local reference media before submission.
- Do not silently drop unsupported parameters; fail with a clear error.
