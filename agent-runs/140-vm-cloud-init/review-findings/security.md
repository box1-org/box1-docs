# Security reviewer pass (fresh subagent), 2026-11-08

Reviewed box1-templates `1f3b8a3` and box1-docs `5d605b2` (read-only; no cluster calls). The reviewer ran `npm run validate`, `VM_BASELINE_REF=origin/main npm run validate` and the script tests, all passing. Its cloud-init and Backstage statements came from source knowledge, not execution.

| # | Severity | Finding | Disposition |
| --- | --- | --- | --- |
| 1 | Medium | `ssh` module installs user-data `ssh_authorized_keys` (to root with `users: []`, or to cloud-user with `users: [default]`) and `ssh_keys`, even with `allow_public_ssh_keys: false` | **Fixed** (templates `390cd79`): `ssh` removed; `sshd-keygen` override restores stock condition |
| 2 | Medium | Module lists are not a security boundary (user-data overrides, boothooks, part-handlers, `#include`); docs overstated "no commands" | **Fixed in docs**: runbook, README, template description and cfg comments state Secret write = guest root. Admission check on the Secret content left as a follow-up for #138/#139 |
| 3 | Medium | Re-applying after `oc replace`/`oc edit` fails on a server-side-apply conflict | **Fixed**: `--force-conflicts`; test asserts the argv |
| 4 | Low-Med | cloud-init keeps root-only copies of user-data (credential) under `/var/lib/cloud`; old instance dirs persist | **Documented** in runbook; revocation adds `cloud-init clean`; test plan counts non-root-readable copies |
| 5 | Low | First write of the credential briefly world-readable (umask) in a 0755 dir | **Fixed**: tmpfiles.d `d /etc/box1/credentials 0750 root box1-site` |
| 6 | Low | Runbook/test plan used `cat` to prove denial | **Fixed**: `test -r … && echo READABLE \|\| echo denied` |
| 7 | Low | TOCTOU/symlink on secret file; no owner check | **Fixed**: `O_NOFOLLOW` + `fstat` + uid check; tests for symlink and missing file |
| 8 | Low | `--client-secret-env` variable inherited by `oc` | **Fixed**: removed from child env (tested); runbook prefers a file filled with `read -rs` + `printf` |
| 9 | Low | Live ConfigMap decides the token URL | **Partly fixed**: untracked ConfigMap now refused unless `--allow-untracked`; runbook asks to confirm the Application is Synced. Host/realm pinning: follow-up |
| 10 | Low | Tracebacks on missing ConfigMap file, non-dict data | **Fixed**, tested |
| 11 | Low/Info | Stale `last-applied-configuration` annotation keeps old credential | **Documented** (removal command in runbook) |
| 12 | Info | Instance-id/firmware UUID behavior read from source, phrased as observed; `degraded done` possible on None | **Fixed wording**; test plan step 4 verifies; step 1 accepts `degraded done` |
| 13 | Info | `~` allowed in URL paths (tilde expansion if shell-sourced) | **Fixed**: `~` removed |
| 15 | Info | String `"false"` would be truthy in nunjucks | **Fixed**: `=== true`; validate.mjs checks non-booleans render off |
| 16 | Info | Vendor-data; `firmware.serial` starting `ds=` could redirect NoCloud | **Fixed** (`vendor_data: {enabled: false}`); serial rule handed to #139 |
| 14, 17 | Info | Script secret handling, injection resistance, test-plan hygiene | No change needed |

Post-repair results: `npm run validate` and `VM_BASELINE_REF=origin/main npm run validate` pass; `npm run test:onboarding` 57/57; script tests 16/16.
