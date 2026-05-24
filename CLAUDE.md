# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

A Claude Code plugin (`/plugin install rorystandley/claude-code-skills`) that makes skills available across any project. Each skill lives under `skills/` and teaches Claude how to interact with an external API — what scripts to run, how to authenticate, and how to format results.

The plugin manifest is `.claude-plugin/plugin.json`. The `skills` field points to `./skills/`, so every subdirectory there is auto-discovered.

## Skill structure (required five files)

Every skill folder must contain exactly:

```
skills/<skill-name>/
├── SKILL.md                  # Claude-facing instructions (YAML frontmatter + markdown)
├── README.md                 # Human-facing setup guide
├── requirements.txt          # Python dependencies (or package.json for Node)
├── .gitignore                # Must exclude auth/*.json and any credential files
└── auth/
    └── config.example.json   # Safe config template; actual config.json is gitignored
```

Scripts live in `scripts/` inside the skill folder. Auth files go in `auth/` and are **never committed**.

## SKILL.md frontmatter

The YAML block at the top of `SKILL.md` is how Claude Code registers the skill:

```yaml
---
name: skill-name
description: "Natural-language description + trigger keywords for when Claude should use this skill"
argument-hint: "[option1|option2] [--flag value]"
allowed-tools: Bash
disable-model-invocation: false
---
```

`description` drives automatic activation — make it keyword-rich for the domains the skill covers.

## Running scripts (google-site-analytics)

Scripts are always run from the consuming project's root (where `.claude/skills/` lives), not from this repo:

```bash
# Install dependencies
pip3 install -r .claude/skills/google-site-analytics/requirements.txt

# Search Console
python3 .claude/skills/google-site-analytics/scripts/gsc-query.py --report queries --days 28
python3 .claude/skills/google-site-analytics/scripts/gsc-query.py --report pages --days 28
python3 .claude/skills/google-site-analytics/scripts/gsc-query.py --report url --url "https://example.com/page"

# Google Analytics 4
python3 .claude/skills/google-site-analytics/scripts/ga4-query.py --report overview --days 28
python3 .claude/skills/google-site-analytics/scripts/ga4-query.py --report realtime
```

Both scripts resolve credential paths relative to their own location (`../auth/`), so they work from any working directory.

## Credential pattern

Each skill that requires auth follows this pattern:
- `auth/gsc-service-account.json` / `auth/ga4-service-account.json` — Google Cloud service account JSON keys
- `auth/config.json` — site-specific config (copied from `config.example.json`, never committed)
- The skill's `.gitignore` excludes `auth/*.json` except `config.example.json`
- The consumer's project `.gitignore` should also exclude `.claude/skills/<skill-name>/auth/*.json`

## Adding a new skill

1. Create `skills/<new-skill-name>/` with the five required files
2. Write `SKILL.md` with frontmatter — `description` must include trigger keywords
3. Put scripts in `scripts/`, credentials template in `auth/config.example.json`
4. Add the skill to the table in the root `README.md`
5. Test by running the scripts directly, then verify Claude picks up the skill via natural language
