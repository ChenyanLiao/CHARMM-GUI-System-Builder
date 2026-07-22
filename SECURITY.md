# Security Policy

## Supported Version

Security fixes target the latest release on the canonical `main` branch.

## Reporting

Use GitHub private vulnerability reporting or a private security advisory when
available. Do not place credentials, browser session data, private structures,
or live authenticated job URLs in a public issue.

For non-sensitive bugs, open a normal issue with a minimal synthetic fixture.

## Scope

Security reports are especially relevant for:

- archive path traversal, unsafe links, or special members;
- accidental credential or browser-state capture;
- plaintext credential storage, Keychain/reference confusion, or token
  persistence outside process memory;
- forged, expired, over-broad, or contract-mismatched execution authorization;
- duplicate submission after an uncertain API/browser response;
- undocumented API endpoints presented as official capabilities;
- unsafe native file-dialog behavior;
- command injection through file paths or archive members;
- false production approval or execution of `gmx mdrun`;
- automation that bypasses human authentication gates.
- cross-agent handoffs that copy credentials, sessions, or authenticated HTML;
- clients that claim browser/file actions despite missing runtime capabilities;
- writable shared skill roots that permit silent workflow drift.

Do not include a real credential, provider value, signing key, authorization
HMAC, JWT, cookie, private job response, or browser login artifact in a report.
Use fictional fixtures and the private disclosure route.
