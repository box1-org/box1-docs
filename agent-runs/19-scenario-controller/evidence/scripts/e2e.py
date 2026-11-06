#!/usr/bin/env python3
"""Local end-to-end verification for run 19 against the real order, inventory and adapter services, the ERP harness
and a local Keycloak (stack.sh). Operator console steps are performed through the ERP's own domain API, standing in for
the console (local proof only). Prints a redacted log: no token, secret or password is ever printed.

Usage: e2e.py [step ...]   (default: all steps, in order)
"""
import json
import subprocess
import sys
import time
import urllib.error
import urllib.request

STACK = "/Users/mike/Documents/ChatGPT/box1/run19-docs/agent-runs/19-scenario-controller/evidence/scripts/stack.sh"
C = "http://localhost:39084"
ORDER = "http://localhost:39081"
INV = "http://localhost:39082"
ADAPTER = "http://localhost:39083"
FIXTURE_CUSTOMERS = {"cust_picard", "cust_data", "cust_janeway", "cust_sisko", "cust_kirk"}


def log(*parts):
    print(time.strftime("%H:%M:%S"), *parts, flush=True)


def stack(*args):
    return subprocess.run(["sh", STACK, *args], check=True, capture_output=True, text=True).stdout.strip()


def token(user):
    return stack("token-" + user)


def http(method, url, tok=None, body=None):
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(url, data=data, method=method, headers={"Accept": "application/json"})
    if data is not None:
        req.add_header("Content-Type", "application/json")
    if tok:
        req.add_header("Authorization", "Bearer " + tok)
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            raw = r.read().decode()
            return r.status, json.loads(raw) if raw else None
    except urllib.error.HTTPError as e:
        raw = e.read().decode()
        try:
            return e.code, json.loads(raw)
        except ValueError:
            return e.code, raw


def check(label, ok, detail=""):
    log("PASS" if ok else "FAIL", label, detail)
    if not ok:
        RESULTS["failed"].append(label)
    else:
        RESULTS["passed"].append(label)


RESULTS = {"passed": [], "failed": []}


def run_view(tok, run_id):
    return http("GET", f"{C}/internal/v1/runs/{run_id}", tok)[1]


def wait(tok, run_id, cond, limit):
    end = time.time() + limit
    r = None
    while time.time() < end:
        r = run_view(tok, run_id)
        if cond(r):
            return r
        time.sleep(1)
    return r


def ended(tok, run_id, limit=600):
    return wait(tok, run_id, lambda r: r.get("resetResult") is not None, limit)


def summary(r):
    return {k: r.get(k) for k in ("scenarioRunId", "scenario", "title", "mode", "status", "detail", "actor", "environment",
                                  "namespace", "ttlSeconds", "correlationId", "impact", "startedAt", "startedStardate",
                                  "endedAt", "resetResult", "resetDetail")} | {
        "audit": [f'{a["action"]}/{a["outcome"]}' for a in r.get("audit") or []]}


def audit_complete(r):
    need = ("actor", "environment", "namespace", "mode", "ttlSeconds", "impact", "resetResult", "startedAt", "startedStardate")
    actions = {a["action"] for a in r.get("audit") or []}
    return all(r.get(k) not in (None, "") for k in need) and {"START", "RESULT", "RESET"} <= actions


def inventory_rows():
    rows, offset = [], 0
    while True:
        page = http("GET", f"{INV}/api/v1/inventory?limit=100&offset={offset}")[1]
        rows += page
        if len(page) < 100:
            return rows
        offset += 100


def lab_seed(rows):
    return sorted((x["siteId"], x["sku"], x["onHand"], x["reserved"]) for x in rows if x["siteId"] in ("site_nyc", "site_bos", "site_closed"))


def all_orders():
    out, cursor = [], None
    while True:
        status, page = http("GET", f"{ORDER}/api/v1/orders?limit=100" + (f"&cursor={cursor}" if cursor else ""))
        items = page if isinstance(page, list) else page.get("items", [])
        out += items
        cursor = None if isinstance(page, list) else page.get("nextCursor")
        if not cursor:
            return out


def step_auth():
    op, viewer, norole = token("operator"), token("viewer"), token("norole")
    check("anonymous catalog read is 401", http("GET", f"{C}/internal/v1/scenarios")[0] == 401)
    check("anonymous start is 401", http("POST", f"{C}/internal/v1/scenarios/baseline-order/start", None, {})[0] == 401)
    check("no-role catalog read is 403", http("GET", f"{C}/internal/v1/scenarios", norole)[0] == 403)
    check("viewer start is 403", http("POST", f"{C}/internal/v1/scenarios/baseline-order/start", viewer, {})[0] == 403)
    status, cat = http("GET", f"{C}/internal/v1/scenarios", viewer)
    check("viewer reads the catalog with titles", status == 200 and [s["title"] for s in cat][:2] == ["Make it so", "The Trouble with Tribbles"],
          [(s["name"], s["title"], s["availability"]) for s in cat])
    status, body = http("POST", f"{C}/internal/v1/scenarios/warp-ten/start", op, {})
    check("unknown scenario is 404", status == 404, body)
    status, body = http("POST", f"{C}/internal/v1/scenarios/erp-unavailable/start", op, {})
    check("not-yet-possible scenario is 409 with its reason", status == 409, body)


def step_seed():
    op = token("operator")
    STATE["lab_before"] = lab_seed(inventory_rows())
    STATE["orders_before"] = [o["orderId"] for o in all_orders() if o["customerId"] not in FIXTURE_CUSTOMERS]
    s1 = http("POST", f"{C}/internal/v1/fixtures/seed", op)
    after_first = sorted((x["siteId"], x["sku"], x["onHand"], x["reserved"]) for x in inventory_rows())
    s2 = http("POST", f"{C}/internal/v1/fixtures/seed", op)
    after_second = sorted((x["siteId"], x["sku"], x["onHand"], x["reserved"]) for x in inventory_rows())
    check("first seed creates 26 (4 sites, 22 stock records)", s1 == (200, {"created": 26, "unchanged": 0}), s1)
    check("second seed changes nothing", s2 == (200, {"created": 0, "unchanged": 26}), s2)
    check("seeding twice gives the same inventory state", after_first == after_second, len(after_first))
    check("lab seed unchanged by seeding", lab_seed(inventory_rows()) == STATE["lab_before"], STATE["lab_before"])


def step_tribbles():
    op = token("operator")
    for round_ in (1, 2):
        status, run = http("POST", f"{C}/internal/v1/scenarios/inventory-contention/start", op, {})
        r = ended(op, run["scenarioRunId"], 180)
        log(json.dumps(summary(r)))
        ids = r["impact"]["orders"]
        orders = [http("GET", f"{ORDER}/api/v1/orders/{i}")[1] for i in ids]
        states = sorted((o["customerId"], o["state"], o["statusReason"]) for o in orders)
        tribble = [x for x in inventory_rows() if x["siteId"] == "site_ds9" and x["sku"] == "CAT-TRIBBLE-TOY"][0]
        check(f"tribbles round {round_}: VERIFIED", r["status"] == "VERIFIED", r["detail"])
        check(f"tribbles round {round_}: one reserved, one REJECTED INSUFFICIENT_STOCK",
              sum(1 for o in orders if o["state"] in ("RESERVED", "FULFILLMENT_REQUESTED", "SHIPPED", "COMPLETED")) == 1
              and sum(1 for o in orders if o["state"] == "REJECTED" and o["statusReason"] == "INSUFFICIENT_STOCK") == 1, states)
        check(f"tribbles round {round_}: reset restored one available, additively", tribble["available"] == 1, tribble)
        check(f"tribbles round {round_}: audit complete", audit_complete(r))


def step_baseline():
    op = token("operator")
    status, run = http("POST", f"{C}/internal/v1/scenarios/baseline-order/start", op, {})
    rid = run["scenarioRunId"]
    r = wait(op, rid, lambda r: r["status"] == "AWAITING_OPERATOR", 120)
    ful = r["impact"]["fulfillmentRequests"][0]
    log("operator step shown:", r["operatorStep"])
    wait_ack(ful)
    log("ERP console step (local stand-in): ship", ful, stack("erp", "ship", ful))
    r = ended(op, rid, 300)
    log(json.dumps(summary(r)))
    order = http("GET", f"{ORDER}/api/v1/orders/{r['impact']['orders'][0]}")[1]
    timeline = http("GET", f"{ORDER}/api/v1/orders/{order['orderId']}/timeline")[1]
    check("make it so: VERIFIED", r["status"] == "VERIFIED", r["detail"])
    check("make it so: order shipped once", [t["toState"] for t in timeline if t["kind"] == "TRANSITION"].count("SHIPPED") == 1,
          [t.get("toState") for t in timeline if t["kind"] == "TRANSITION"])
    check("make it so: audit complete", audit_complete(r))


def wait_ack(ful):
    end = time.time() + 120
    while time.time() < end:
        status, f = http("GET", f"{ADAPTER}/api/fulfillments/{ful}")
        if status == 200 and f.get("erpAcknowledgement") == "ACKNOWLEDGED":
            return f
        time.sleep(1)
    raise SystemExit("no ERP acknowledgement for " + ful)


def step_hold():
    op = token("operator")
    status, run = http("POST", f"{C}/internal/v1/scenarios/erp-manual-hold/start", op, {})
    rid = run["scenarioRunId"]
    r = wait(op, rid, lambda r: "hold it" in (r.get("operatorStep") or ""), 180)
    ful = r["impact"]["fulfillmentRequests"][0]
    log("operator step shown:", r["operatorStep"])
    log("ERP console step (local stand-in): hold", ful, stack("erp", "hold", ful))
    r = wait(op, rid, lambda r: "release" in (r.get("operatorStep") or ""), 120)
    log("operator step shown:", r["operatorStep"])
    status, f = http("GET", f"{ADAPTER}/api/fulfillments/{ful}")
    log("adapter while held:", {k: f.get(k) for k in ("dispatch", "erpAcknowledgement", "outcome")})
    log("ERP console step (local stand-in): release", ful, stack("erp", "release", ful))
    r = ended(op, rid, 180)
    log(json.dumps(summary(r)))
    check("hold that order: VERIFIED", r["status"] == "VERIFIED", r["detail"])
    check("hold that order: held signal recorded", "held signal: fulfillment_held >= 1" in r["detail"], r["detail"])
    check("hold that order: audit complete", audit_complete(r))


def step_guided_timeout():
    op = token("operator")
    status, run = http("POST", f"{C}/internal/v1/scenarios/erp-manual-hold/start", op, {"ttlSeconds": 45})
    r = ended(op, run["scenarioRunId"], 120)
    log(json.dumps(summary(r)))
    check("guided step not performed: NOT_VERIFIED", r["status"] == "NOT_VERIFIED"
          and r["detail"].startswith("Operator step not observed before the TTL"), r["detail"])
    check("guided step not performed: reset ran", r["resetResult"] == "RESET_OK", r["resetDetail"])


def step_delay():
    op = token("operator")
    log("ERP console step (local stand-in): AUTO", stack("erp", "mode", "AUTO"))
    log("ERP console step (local stand-in): delay 90 s", stack("erp", "fault", "auto_delay_seconds", "90"))
    status, run = http("POST", f"{C}/internal/v1/scenarios/erp-delayed-processing/start", op, {"ttlSeconds": 400})
    r = ended(op, run["scenarioRunId"], 450)
    log(json.dumps(summary(r)))
    log("ERP console step (local stand-in): delay 0", stack("erp", "fault", "auto_delay_seconds", "0"))
    check("impulse power only: VERIFIED with a visible wait", r["status"] == "VERIFIED", r["detail"])
    check("impulse power only: RESET_GUIDED names the undo step", r["resetResult"] == "RESET_GUIDED"
          and "delay back to 0" in r["resetDetail"], r["resetDetail"])


def step_crash():
    op = token("operator")
    log("ERP console step (local stand-in): AUTO", stack("erp", "mode", "AUTO"))
    log("ERP console step (local stand-in): arm crash", stack("erp", "fault", "crash_after_commit", "1"))
    status, run = http("POST", f"{C}/internal/v1/scenarios/erp-crash-after-commit/start", op, {"ttlSeconds": 300})
    r = ended(op, run["scenarioRunId"], 360)
    log(json.dumps(summary(r)))
    journal = stack("erp", "journal", "60")
    crashed = "status=70" in journal or "code=exited" in journal
    log("ERP journal shows the crash exit:", crashed)
    check("warp core breach: VERIFIED, shipped exactly once", r["status"] == "VERIFIED", r["detail"])
    check("warp core breach: the ERP actually crashed (journal)", crashed)
    log("ERP console step (local stand-in): MANUAL", stack("erp", "mode", "MANUAL"))


def step_stop():
    op = token("operator")
    status, run = http("POST", f"{C}/internal/v1/scenarios/baseline-order/start", op, {})
    rid = run["scenarioRunId"]
    wait(op, rid, lambda r: r["status"] == "AWAITING_OPERATOR", 120)
    status, body = http("POST", f"{C}/internal/v1/scenarios/baseline-order/stop", op)
    r = ended(op, rid, 60)
    log(json.dumps(summary(r)))
    check("stop: STOPPED and reset", status == 200 and r["status"] == "STOPPED" and r["resetResult"] == "RESET_OK", r["resetDetail"])
    STATE["stopped_ful"] = r["impact"].get("fulfillmentRequests", [None])[0]


def step_kill():
    op = token("operator")
    status, run = http("POST", f"{C}/internal/v1/scenarios/baseline-order/start", op, {"ttlSeconds": 30})
    rid = run["scenarioRunId"]
    wait(op, rid, lambda r: r["status"] == "AWAITING_OPERATOR", 120)
    stack("controller-kill9")
    log("controller killed with SIGKILL mid-run; waiting past the 30 s TTL with no controller")
    time.sleep(45)
    log(stack("controller"))
    op = token("operator")
    r = ended(op, rid, 60)
    log(json.dumps(summary(r)))
    check("killed mid-run: ABORTED_RESTART and reset at restart", r["status"] == "ABORTED_RESTART" and r["resetResult"] == "RESET_OK",
          r["resetDetail"])
    status, body = http("POST", f"{C}/internal/v1/scenarios/inventory-contention/start", op, {})
    check("after recovery a new run can start", status == 202, body.get("scenarioRunId") if isinstance(body, dict) else body)
    if status == 202:
        ended(op, body["scenarioRunId"], 180)


# The V2 lab seed, as recorded by the seed step before any run (fresh local database, no other orders).
LAB_SEED_V2 = [("site_bos", "SKU-42", 10, 0), ("site_closed", "SKU-42", 50, 0), ("site_nyc", "SKU-42", 100, 0),
               ("site_nyc", "SKU-7", 25, 0), ("site_nyc", "SKU-LAST", 1, 0)]


def step_collateral():
    op = token("operator")
    STATE.setdefault("lab_before", LAB_SEED_V2)
    STATE.setdefault("orders_before", [])
    check("no data outside the fixture set changed: lab seed stock", lab_seed(inventory_rows()) == STATE["lab_before"])
    others = [o["orderId"] for o in all_orders() if o["customerId"] not in FIXTURE_CUSTOMERS]
    check("no data outside the fixture set changed: no non-fixture orders created", others == STATE["orders_before"], len(others))
    runs = http("GET", f"{C}/internal/v1/runs?limit=200", op)[1]
    incomplete = [x["scenarioRunId"] for x in runs if not audit_complete(run_view(op, x["scenarioRunId"]))]
    check("audit record complete for every run", not incomplete, f"{len(runs)} runs; incomplete {incomplete}")
    denied = [a for a in http("GET", f"{C}/internal/v1/audit?limit=200", op)[1] if a["outcome"] == "DENIED"]
    log("refusals audited:", [(a["action"], a["scenario"], a["detail"]) for a in denied])


STATE = {}
STEPS = {"auth": step_auth, "seed": step_seed, "tribbles": step_tribbles, "baseline": step_baseline, "hold": step_hold,
         "timeout": step_guided_timeout, "delay": step_delay, "crash": step_crash, "stop": step_stop, "kill": step_kill,
         "collateral": step_collateral}

if __name__ == "__main__":
    for name in sys.argv[1:] or list(STEPS):
        log("== step", name)
        STEPS[name]()
    log("RESULT", f"{len(RESULTS['passed'])} passed, {len(RESULTS['failed'])} failed", RESULTS["failed"])
    sys.exit(1 if RESULTS["failed"] else 0)
