# Install For OpenClaw

Install the tagged Git release into the active workspace:

```bash
openclaw skills install \
  git:ChenyanLiao/CHARMM-GUI-System-Builder@v6.1.0 \
  --as charmm-gui-system-builder
```

Add `--global` to install into OpenClaw's shared managed skill directory. Git
installs are refreshed by reinstalling the desired tag; `openclaw skills
update` tracks ClawHub installs, not arbitrary Git sources.

Inspect the result:

```bash
openclaw skills info charmm-gui-system-builder
openclaw skills check
```

OpenClaw skill roots have precedence rules, so remove naming conflicts or
confirm which copy wins before a scientific run. Read
[`adapters/openclaw.md`](../adapters/openclaw.md) and treat third-party skills
as untrusted until reviewed.
