#!/usr/bin/env sh
set -eu

repo_dir=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
mode=${1:-agents}

case "$mode" in
  agents) target="${HOME}/.agents/skills" ;;
  codex) target="${HOME}/.codex/skills" ;;
  claude) target="${HOME}/.claude/skills" ;;
  copilot) target="${HOME}/.copilot/skills" ;;
  path)
    target=${2:?usage: install.sh path TARGET_DIRECTORY}
    ;;
  *)
    echo "usage: install.sh [agents|codex|claude|copilot|path TARGET]" >&2
    exit 2
    ;;
esac

mkdir -p "$target"
for skill in kinomimic-recreate kinomimic-render; do
  if [ -e "$target/$skill" ]; then
    echo "$target/$skill already exists; move it aside before reinstalling." >&2
    exit 1
  fi
done

for skill in kinomimic-recreate kinomimic-render; do
  cp -R "$repo_dir/skills/$skill" "$target/$skill"
done

echo "Installed KinoMimic skills to $target"
