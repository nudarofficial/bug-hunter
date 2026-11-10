# Security Policy

Bug Hunter is a set of Markdown instructions plus small helper scripts. The scripts run only during development and CI. The installed skill runs no code of its own.

## Reporting a vulnerability

If you find a problem with security impact, report it privately. Examples:

- instructions that could lead an agent to run destructive or exfiltrating commands
- a script in this repository that is unsafe to run

Use the **Report a vulnerability** button on the repository's **Security** tab if it is enabled. Otherwise, open a minimal public issue that asks a maintainer for a private contact, and leave out the details.

Please include the affected file, the behavior you observed, and steps to reproduce.

## Auditing before installing

As with any Agent Skill, read every file before you install it. The installable skill is the `bug-hunter/` directory: `SKILL.md` plus Markdown reference files. It contains no executable scripts and makes no network calls.
