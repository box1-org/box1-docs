# 02 Local tests (2026-11-08, America/New_York)

## box1-templates `golden-path/140-cloud-init`

| Command | Result |
| --- | --- |
| `npm run validate` | 14 PASS lines, exit 0. Includes `PASS rhel-image-vm cloudInit: off renders byte-identical for every case; on changes only the image (rootfs-cloud-init/, Containerfile, README), GitOps bundle unchanged and accepted by the plugin gate` |
| `VM_BASELINE_REF=origin/main npm run validate` | Same, with `… and to origin/main` (origin/main = `5663eb3`) |
| `npm run test:onboarding` | 57 pass, 0 fail (unchanged plugin) |
| `diff -r` of main's `.validation/rhel-image-vm` (rendered before the change) against the branch's renders with the key omitted and with `cloudInit: false` | Identical, including file modes |

Mutation checks, reverted afterwards: a trailing space added outside the guard in the skeleton README made `VM_BASELINE_REF=origin/main npm run validate` fail with `byte-identical to origin/main`. Moving `cloud-init` outside its guard in the Containerfile failed the existing package-line check.

What `validate.mjs` now proves for `cloudInit`:

- `false`, omitted, and the non-booleans `"true"`, `"false"` and `1` render byte-identical to each other (and to `VM_BASELINE_REF` when set), for the three existing cases.
- With `false`, no rendered file mentions `cloud-init`, `cloudinit`, `nocloud`, `box1-site` or `/etc/cloud`.
- With `true`: only `rootfs-cloud-init/` (four files) is added; only `Containerfile` and `README.md` change; the GitOps bundle is identical and passes the plugin's `validateVmBundle`; the cloud-init config parses to exactly the expected settings; the sshd-keygen override and credential-directory tmpfiles line match.
- The form refuses non-boolean `cloudInit`; the default is `false`; only `fetchApplication` receives it.

Not run: an image build. It needs Red Hat entitlement material, which this run was not authorized to handle.

## box1-docs `golden-path/140-cloud-init-runbook`

`python3 -I scripts/vm-cloud-init/test_assemble_cloud_init_secret.py -v`: 16 tests, OK (Python 3.9.6). Each test generates a fake secret (`fake-` + 32 random URL-safe bytes) and checks it never appears on stdout, stderr or an `oc` command line, and that the secret environment variable is not passed to `oc`.

Cross-check: the user-data from a fake run parsed with the `yaml` npm package (YAML 1.2) to `write_files` with the expected paths, owners, modes and `b64` encoding, and the decoded credential equalled the fake secret.

Not run: PyYAML (cloud-init's parser) and `cloud-init schema`, which are not installed locally. The test plan runs `cloud-init schema --system` in the guest.
