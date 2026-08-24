# Install For OpenClaw

Install the tagged Git release into the active workspace:

```bash
openclaw skills install \
  git:ChenyanLiao/CHARMM-GUI-System-Builder@v2.2.0 \
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

The v2.2.0 closure commands require the Python packages declared in
`requirements.txt`. Install them into the Python environment used by the
OpenClaw terminal tool before running those commands.

OpenClaw skill roots have precedence rules, so remove naming conflicts or
confirm which copy wins before a scientific run. Read
[`adapters/openclaw.md`](../adapters/openclaw.md) and treat third-party skills
as untrusted until reviewed.
