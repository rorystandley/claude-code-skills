# claude-code-skills

A collection of skills for [Claude Code](https://claude.ai/code) that connect it to external services and APIs.

## What is a skill?

A Claude Code skill is a folder containing a `SKILL.md` file that teaches Claude how to interact with an external tool or API — what commands to run, how to authenticate, and how to present results. Claude reads the skill automatically when you ask relevant questions.

## Installation

### As a plugin (recommended)

Run this command inside Claude Code — this makes all skills available across your projects:

```
/plugin install rorystandley/claude-code-skills
```

### Manually

Copy any skill into your project's `.claude/skills/` directory:

```bash
# Clone the repo
git clone https://github.com/rorystandley/claude-code-skills.git

# Copy a skill into your project
cp -r claude-code-skills/skills/google-site-analytics your-project/.claude/skills/
```

Then follow the skill's own `README.md` for setup.

## Skills

| Skill | Description |
|---|---|
| [google-site-analytics](./skills/google-site-analytics) | Query Google Search Console and GA4 — rankings, traffic, events, realtime |

## Contributing

Contributions welcome. Each skill lives in its own folder under `skills/` and must include:

- `SKILL.md` — the Claude skill definition (with `name`, `description`, and usage instructions)
- `README.md` — human-readable setup guide
- `requirements.txt` or `package.json` — dependencies
- `.gitignore` — must exclude any credential files
- `auth/config.example.json` — a safe template for any config the user needs to fill in

Credential files (`*.json` keys, `token.json`, `.env`) must never be committed. The skill's `.gitignore` should exclude them, and your `README.md` should make clear what files to create locally.

## License

MIT
