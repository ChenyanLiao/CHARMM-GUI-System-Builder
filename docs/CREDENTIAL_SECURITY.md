# Credential Security And Unattended Authorization

## Default

Manual login is the default and safest portable option. v2.1.0 adds an explicit
opt-in Credential Broker so a reviewed test-only contract can run when the user
is away from the workstation. This is a convenience boundary, not a guarantee
against compromise of the local account, operating system, or agent process.

## Supported Providers

| Provider | Persistence | Status |
|---|---|---|
| Manual interactive login | None | Stable operational default |
| macOS Keychain | OS vault | Opt-in; local security tests required |
| Python keyring / Secret Service | OS vault through optional dependency | Opt-in Beta |
| In-memory provider | Process only | Tests only |
| Plaintext file, `.env`, command argument, report, or repository | Forbidden | Unsupported |

Project records may contain only an opaque provider reference. They must never
contain an account password, API token, cookie, session data, CAPTCHA response,
or MFA code.

## Credential Broker Rules

- Storage and signing-key creation require an interactive terminal.
- Password entry uses a hidden prompt and is never accepted as a CLI argument.
- Retrieval and login occur in the same controlled process.
- API JWTs remain in memory and are discarded when the process exits.
- Login screenshots and DOM snapshots are suppressed.
- Browser cookies and session stores are never inspected, copied, or exported.
- Logs record only provider type, opaque reference, timestamp, and redacted
  outcome.

Example commands intentionally contain no secret values:

```bash
python3 scripts/credential_broker.py --provider macos-keychain \
  store-credential --reference charmmgui-primary

python3 scripts/credential_broker.py --provider macos-keychain \
  create-signing-key --reference charmmgui-authorization-signing

python3 scripts/credential_broker.py --provider macos-keychain \
  probe charmmgui-primary --kind credential
```

`probe` prints only `available`; it never prints the stored value. Use `delete`
to revoke a credential or signing-key reference.

## Authorization Is Separate From Authentication

A saved credential only proves that the account can attempt login. Every
side-effecting action still requires a signed authorization bound to:

- the locked build-contract SHA-256;
- approved input hashes, target, builder, route, and mode;
- an allowlist of actions;
- an expiry time;
- a maximum submission count, normally one.

The signing key is a different vault entry from the login credential. Minting
requires local interactive confirmation of the exact contract hash. An agent
may verify and consume an existing authorization, but may not mint or extend one
silently. Any material contract revision invalidates the old authorization.

Recognized origins are `local_os_confirmed`,
`preauthorized_signed_contract`, and `remote_user_confirmed`. An
`agent_generated` approval is invalid. Remote confirmation may authorize the
already reviewed test-only actions in the current task, but cannot clear ligand
identity, protein connectivity, membrane orientation, expert review, CAPTCHA,
MFA, terms acceptance, or production gates.

## Incident Response

If a secret appears in a report, screenshot, terminal transcript, repository,
or conversation:

1. stop execution and suppress further evidence capture;
2. revoke or rotate the credential outside this Skill;
3. delete the affected vault reference if appropriate;
4. quarantine the artifact without quoting its contents;
5. inspect Git history and published artifacts before resuming;
6. create a fresh contract authorization after the incident is resolved.

A disclaimer is not a security control. Keep the minimum privilege, minimum
retention, and one-submission rules active even on a trusted workstation.
