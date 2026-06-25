# Provider adapters

## Interface

The public contract is `kinomimic.plan/v1`. Provider-specific fields belong inside the renderer, not in the analysis Skill.

Select a provider with `KINOMIMIC_PROVIDER`.

## volcengine-ark

Current default:

- provider: `volcengine-ark`
- base URL: `https://ark.cn-beijing.volces.com/api/v3`
- default model: `doubao-seedance-2-0-260128`
- authentication: bearer API key
- task API: create, get, list, delete/cancel

Environment:

```bash
export KINOMIMIC_PROVIDER=volcengine-ark
export KINOMIMIC_API_KEY="..."
```

Current model constraints include:

- duration: 4–15 seconds or `-1`
- ratios: adaptive, 16:9, 4:3, 1:1, 3:4, 9:16, 21:9
- images: local data URL, public URL, or asset ID
- audio: local data URL, public URL, or asset ID
- video: public URL or asset ID

Add future providers as adapters while preserving the plan protocol and CLI commands.

