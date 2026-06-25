# KinoMimic Agent Skills

Portable Agent Skills for reconstructing the logic of a complete reference video and rendering a structurally faithful AI-generated version.

## Skills

- `kinomimic-recreate` analyzes any complete reference video and produces a versioned generation plan.
- `kinomimic-render` renders that plan through a replaceable asynchronous video provider.

The bundled provider is Volcengine Ark Seedance. The plan protocol and analysis workflow are provider-neutral.

## Architecture

```text
reference video
  -> kinomimic-recreate
  -> kinomimic.plan/v1
  -> kinomimic-render
  -> provider adapter
  -> local video + result metadata
```

The two skills do not rely on absolute paths or direct imports from each other. Agents compose them through `kinomimic.plan/v1`.

## Install

```bash
./scripts/install.sh agents
```

Targets:

- `agents`: `~/.agents/skills`
- `codex`: `~/.codex/skills`
- `claude`: `~/.claude/skills`
- `copilot`: `~/.copilot/skills`

Project-local installation:

```bash
./scripts/install.sh path .agents/skills
```

## Requirements

- Python 3.9+
- ffmpeg and ffprobe
- optional Tesseract for OCR
- provider API key for rendering

## Quick start

Ask your Agent:

```text
Use $kinomimic-recreate to analyze this complete video and create a faithful generation plan.
Then use $kinomimic-render to render the confirmed plan.
```

Or call scripts directly:

```bash
python3 skills/kinomimic-recreate/scripts/kinomimic_recreate.py prepare input.mp4 \
  --output-dir ./project

python3 skills/kinomimic-render/scripts/kinomimic_render.py render-plan \
  ./project/generation-plan.json
```

## Security

Use environment variables or an operating-system secret store. Never commit API keys, generated signed URLs, or private media.

## Standard

The Skill folders follow the open [Agent Skills specification](https://agentskills.io/specification).

## License

MIT

