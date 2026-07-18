# Contributing

Contributions are welcome through GitHub issues and pull requests.

## Before Opening A Pull Request

1. Do not include passwords, cookies, tokens, browser profiles, live session
   data, private molecular structures, unpublished job URLs, or workstation
   paths.
2. Keep browser automation conservative: no CAPTCHA/MFA bypass, credential
   extraction, fabricated API calls, duplicate submissions, or production MD.
3. Add or update tests for behavior changes.
4. Run:

   ```bash
   python3 -m unittest discover -s scripts/tests -p 'test_*.py' -v
   python3 -m compileall -q scripts
   ```

5. Explain the evidence, failure mode, recovery behavior, and remaining
   scientific limits in the pull request.

## Licensing

By contributing, you confirm that you have the right to submit the contribution
and agree to license it under GNU AGPL v3.0 and the applicable permitted
additional terms in this repository. Copyright in your contribution remains
yours unless a separate written agreement says otherwise.

Large changes may require a separate contributor license agreement before
merge. No contributor agreement may be inferred from private credentials or
unpublished scientific data.

