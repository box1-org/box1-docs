# Operator access on the cluster, 2026-11-06 ~13:40 EST

**Keycloak fix.** The user merged box1-gitops#79 at 12:58 EST, and Argo `keycloak` synced it (`3ddc6c3`). `scenario-controller` and `scenario-controller-cli` now report `ready=true`.

**Login.** The user issued a realm user holding `scenario-operator` to this run, for testing. It was used only for the read-only checks below. Its credential is not recorded anywhere.

**Device login needs PKCE.** The first attempt (the user's) failed with `invalid_request: Missing parameter: code_challenge_method`. With `pkce.code.challenge.method: S256` set on the client, RH-SSO 7.6 requires `code_challenge` on the device authorization request, and `code_verifier` on the token request. With both, the device grant works: device request 200, login, consent, token. That settles A-7's open question: RH-SSO 7.6 does enable the device grant from the client attribute.

**Token claims (decoded; the token itself is not recorded):**
- `azp=scenario-controller-cli`
- `aud=scenario-controller`
- `resource_access.scenario-controller.roles=[scenario-operator]`

**Read-only checks with that token:**

| Call | Expected | Observed |
|---|---|---|
| `GET /internal/v1/scenarios` | 200, ten scenarios with titles | 200. Five AVAILABLE: Make it so, The Trouble with Tribbles, Hold that order Number One, Impulse power only, Warp core breach. Five NOT_YET_POSSIBLE: The ERP has cloaked, Subspace interference, Q was here, Unsigned shuttlecraft denied docking, Red alert. IDs plain |
| `GET /internal/v1/fixtures` | 200, the Starfleet Feline Supply set | 200, five customers, four sites (neutral zone UNAVAILABLE), products |
| `GET /internal/v1/runs` | 200, empty | 200, `[]` |

**Not tested:**
- A token without a role (403) on the cluster: no such user was available.
- Whether the controller's service account token carries `inventory-admin`. That needs the client secret, which this run doesn't read; seeding (A-8) will show it.
