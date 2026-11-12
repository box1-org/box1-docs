# hostname-codemod

Rewrites Box1 hostnames across the `box1-org` repositories from an explicit rule file. It handles two moves:
- **Git hosting:** GitHub to GitLab.
- **Cluster:** a new apps domain, and optionally a new image registry such as Quay.

Run it as a dry run first. Then apply it per repository and open one PR each through the normal checks.

`box1-gitops` is excluded: it is migrated separately.

## Rules (`--config`, JSON)

| Type | What it rewrites | What it keeps |
|---|---|---|
| `git` | `github.com/<org>/<repo>` links to `to_base/<repo>` in GitLab shapes. Covers the repository, `.git`, `blob`, `tree`, `commit`, `blame` and `commits` (each gets `/-/`) and `raw.githubusercontent.com` links (to `/-/raw/`). Also `github.com/project-slug` becomes `slug_annotation`. Repositories in `keep_repos` are left alone. | Links to pull requests, issues, releases, compare, actions, wiki and similar. These exist only on GitHub, because the mirror copies git refs, not PRs or issues; the backlog stays on GitHub. |
| `domain` | One DNS suffix (`from`) to another (`to`), only on label boundaries. For example, `order-service-dev.apps.ocp.box1.org` becomes `order-service-dev.<to>`. | `box1.org/<key>` annotation and label keys: they are not hostnames and never match. |
| `registry` | An image repository prefix, for example the internal registry `image-registry.openshift-image-registry.svc:5000/box1-ci/` to `quay.io/<org>/`. | Digests: they are never touched. |

**Rules run in the order listed, and they chain.** With `git` before `domain`, the new Git host is itself moved to the new domain, which suits GitLab moving with the cluster. If GitLab keeps its current host, list the `domain` rules first.

`exclude_repos` and `exclude_paths` (globs; `**` matches across directories) protect history and evidence: achievements, agent runs, `VERIFICATION*.md`, `verification/`, evidence JSON, fixtures, cluster-config backups and lock files. Only files tracked by git and with a text extension are read.

## Report

For each repository, the report shows the files and replacements per rule. It also shows:
- **rebuild:** `YES` when a changed file is an image input (`src/`, `Containerfile`, `pom.xml`, `package.json`, app Python). Those images have hostnames built in, such as CORS origins, OIDC issuer and OpenAPI servers. They must be rebuilt, or rebuilt and published, for example to Quay. `.tekton/` and `deploy/` don't count.
- **Manual follow-up:** `api.github.com` and `codeload.github.com` use. These are API calls that need a code port, not a hostname swap.
- **Unmapped hosts:** `*.box1.org` hosts that no rule covers.

## Usage

```bash
# one clone per repository under ./repos
for r in $(gh repo list box1-org --limit 100 --no-archived --json name -q '.[].name'); do
  git clone -q https://github.com/box1-org/$r.git repos/$r
done

python3 codemod.py --config my-rules.json --repos repos --diff-dir diffs --json report.json   # dry run
python3 codemod.py --config my-rules.json --repos repos --only order-service --apply           # write one repository
python3 codemod.py --config my-rules.json --repos repos --apply --commit hostnames-update      # branch and commit each (no push)

python3 -m unittest -v   # tests
```

## Rollout notes

- **Order:** templates (`box1-templates`) first, then the services, then `box1-workloads-dev`. The image changes reach `box1-workloads-dev` through each service's normal build and promotion, not by editing digests.
- **Merge spacing:** wait about 10 seconds between merges (box1-docs#64).
- **GitHub stays the source of truth while the github-mirror CronJob runs.** Edits made on GitLab are overwritten. Stop the mirror before switching the source of truth.
- **Provenance:** commit SHAs are identical on the mirror, so `box1.org/source-revision` provenance stays valid after a Git host change.
