# D-011 Read API access

**Status:** resolved 2026-11-05 by the agent under the user's delegation: option A, `permit`, in `box1-workloads-dev` `bf71c01`.

`01_DOMAIN_CONTRACTS.md` requires backend AuthN/AuthZ, and the issue says not to assume the #40 exception. `GET /api/v1/inventory` and `GET /api/v1/reservations/{id}` need a position. `INVENTORY_READ_POLICY` selects it at runtime, and the default in the image is `authenticated`.

| Option | Effect |
|---|---|
| **A (recommended): `permit`, tracked like #40** | Stock levels and reservation records are readable on the LAN without credentials. They hold no customer data, only opaque `orderId`s. Live read acceptance can run now. No new credential. |
| **B: `authenticated`** | Needs the D-010 Keycloak client and a read role or scope. Reads stay rejected until then, so ATP live proof waits. |

**Consequence for the first deploy:** the workloads PR ships `authenticated`. Option A means one more `env` line in that PR before merge.
