# ccar

`ccar` is a Claude Code native build of `autoresearch`: an autonomous experiment loop that writes session files, benchmarks changes, logs results, and keeps iterating until interrupted.

It is built entirely from Claude Code-native primitives:

- project slash commands in `.claude/commands/`
- project hooks in `.claude/settings.json`
- a Stop hook for autonomous continuation
- a SessionStart hook for resume context injection
- shell helpers for init, run, log, and status

This stays local and works with local-model Claude Code setups such as local Qwen/vLLM routing.

## Features

- `/autoresearch` to start an autonomous optimization loop
- `/cancel-autoresearch` to stop the active loop
- `/autoresearch-status` to summarize the current session
- append-only `autoresearch.jsonl` history
- resumable `autoresearch.md` and `autoresearch.ideas.md`
- compact status line integration

## Requirements

- Claude Code
- `jq`
- a Unix-like shell environment

## Install

### Global install

This repo includes a one-shot global installer:

```bash
./install-global.sh
```

It copies the runtime to `~/.claude/autoresearch`, installs the slash commands into `~/.claude/commands`, and updates `~/.claude/settings.json` after creating a timestamped backup.

### Project-local usage

You can also copy the `.claude/` directory into a project and use the commands there directly.

## Usage

Inside Claude Code, in the project you want to optimize:

```text
/autoresearch Short optimization goal --max-iterations 0
```

Then provide the longer optimization brief as a normal message. The loop will create or refresh:

- `autoresearch.md`
- `autoresearch.sh`
- `autoresearch.jsonl`
- `autoresearch.ideas.md`

Use these commands during a session:

```text
/autoresearch
/autoresearch-status
/cancel-autoresearch
```

## Session Files

- `autoresearch.md`: objective, scope, constraints, and experiment history
- `autoresearch.sh`: benchmark harness that emits `METRIC name=value`
- `autoresearch.jsonl`: append-only experiment log
- `autoresearch.ideas.md`: deferred promising ideas

## Repository Layout

- `.claude/commands/`: project-local slash commands
- `.claude/hooks/`: Stop and SessionStart hooks
- `.claude/scripts/`: experiment runtime helpers
- `tests/smoke.sh`: end-to-end smoke test
- `install-global.sh`: global installer

## Development

Run the smoke test:

```bash
./tests/smoke.sh
```

## License

MIT
