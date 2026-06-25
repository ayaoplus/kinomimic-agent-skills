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

## Generation gate

Before rendering, confirm:

- what the video is doing overall
- the complete plot or procedure
- roles and relationships
- exact actions and visible success criteria
- must-preserve sequence
- unresolved facts

