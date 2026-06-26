# KinoMimic plan protocol

Use `kinomimic.plan/v1` as the stable boundary between analysis and rendering.

```json
{
  "schema": "kinomimic.plan/v1",
  "project": {
    "name": "project-slug",
    "source_video": "/absolute/path/reference.mp4",
    "intent": "faithful-recreation"
  },
  "fidelity": {
    "must_preserve": [],
    "may_change": [],
    "uncertain_facts": []
  },
  "adaptation": {
    "user_requirements": [],
    "conflicts": [],
    "resolution": []
  },
  "script": {
    "overview": "",
    "segments": [],
    "shots": [
      {
        "number": 1,
        "time": "0.0-1.0s",
        "visual_prompt": "【景别，运镜】中文画面描述。",
        "voice": ""
      }
    ],
    "render_prompt": ""
  },
  "inputs": {
    "reference_images": [],
    "reference_videos": [],
    "reference_audio": [],
    "first_frame": null,
    "last_frame": null
  },
  "generation": {
    "prompt": "Chronological, production-ready prompt.",
    "model": null,
    "resolution": "720p",
    "ratio": "9:16",
    "duration": 10,
    "generate_audio": true,
    "watermark": false,
    "return_last_frame": false
  }
}
```

## Prompt requirements

Describe the complete video chronologically. For each segment specify:

- environment and continuity
- framing, angle, and camera movement
- subject count, roles, positions, and appearance continuity
- hand state, held objects, and exact action
- object or product appearance
- cause, visible result, and reaction
- pacing, speech, effects, and environmental audio

Do not omit a comparison, retest, proof, reveal, instruction step, or ending that carries the video's meaning.

## Script requirements

Create `recreation-script.md` before rendering and mirror its content in the optional `script` object. The script must be readable by the user without inspecting JSON.

For each independent shot:

- preserve the source shot order unless the user explicitly asks to change it
- include the time range
- start the visual prompt with `【景别，运镜】`
- describe scene, subjects, hand state, props, action, facial/body reaction, focus, and pacing in one sentence
- put spoken dialogue, voiceover, or lip-sync text only in the voice field

When the user supplies adaptation requirements, record them under `adaptation.user_requirements`. If a requirement conflicts with source fidelity or product correctness, record the conflict and the smallest safe resolution.

## Generation gate

Before rendering, confirm:

- what the video is doing overall
- the complete plot or procedure
- the human-readable script
- user-requested changes and how they were applied
- roles and relationships
- exact actions and visible success criteria
- must-preserve sequence
- unresolved facts
