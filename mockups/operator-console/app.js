// box1 Operations console MOCKUP — hash router + renderers. Discussion artifact; not production code.
(() => {
  const M = window.MOCK;
  const $ = (s) => document.querySelector(s);
  const h = (v) => String(v ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const time = (iso) => (iso ? new Date(iso).toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit", second: "2-digit", timeZone: "America/New_York" }) + " ET" : "—");
  const cap = (...ids) => ids.map((c) => `<span class="cap" title="Capability ${c} in CAPABILITIES.md">${c}</span>`).join(" ");
  const assumed = (t = "assumed field") => `<span class="assumed">${h(t)}</span>`;
  const chip = (o) => `<span class="chip" data-s="${o.state}" data-stuck="${!!o.stuck}">${h(M.stateLabels[o.state])}</span>`;
  const announce = (msg) => { $("#live").textContent = ""; setTimeout(() => ($("#live").textContent = msg), 30); };

  const ui = { role: "operator", data: "normal", sort: { key: "createdAt", dir: -1 }, page: 0, filters: { state: "", site: "", q: "", attn: false } };
  const CUSTOMER_ID = "cust_demo_1";
  const isCustomer = () => ui.role === "customer";
  const allowed = (route) => M.roles[ui.role].routes.includes(route);

  const NAV = [
    ["home", "#/home", "Home"], ["orders", "#/orders", "Orders"], ["new", "#/orders/new", "Place order"],
    ["incidents", "#/incidents", "Incidents"], ["sites", "#/sites", "Sites & assets"],
    ["demo", "#/demo", "Demo control"], ["delivery", "#/delivery", "Delivery"],
  ];

  // ---------- data-state wrapper (C15) ----------
  function withData(title, caps, body, emptyMsg = "Nothing to show yet.") {
    if (ui.data === "loading") return panel(title, caps, `<div aria-busy="true" aria-label="Loading">${'<div class="skeleton"></div>'.repeat(4)}</div>`);
    if (ui.data === "empty") return panel(title, caps, `<div class="empty">${h(emptyMsg)}</div>`);
    if (ui.data === "error") return `<section class="alert" role="alert"><h2>${h(title)} unavailable ${cap("C15")}</h2>
      <p>The Operations service could not load this view. Nothing on this page is assumed to have changed.</p>
      <pre class="problem">{
  "type": "https://box1.example/problems/upstream-unavailable",
  "title": "Upstream service unavailable",
  "status": 503,
  "detail": "order-service did not respond within 2 s",
  "instance": "/api/v1/orders",
  "correlationId": "corr-ui-7f3a"
}</pre><div class="actions"><button type="button" data-act="retry">Retry</button></div></section>`;
    return panel(title, caps, body());
  }
  const panel = (title, caps, inner, extra = "") => `<section class="panel" ${extra}><h2>${h(title)} ${caps}</h2>${inner}</section>`;

  // ---------- pages ----------
  function pageHome() {
    const o = M.orders;
    const count = (f) => o.filter(f).length;
    const stuck = o.filter((x) => x.stuck || x.state === "EXCEPTION");
    const activeAlerts = M.assets.flatMap((a) => a.alerts.filter((al) => al.status === "ACTIVE")).length;
    return head("Operator home", "Business health for orders-demo") +
      withData("Business indicators", cap("C3"), () => `<dl class="kpis">
        ${kpi("Submitted today", o.length, "#/orders")}
        ${kpi("Awaiting ERP ack", count((x) => x.state === "FULFILLMENT_REQUESTED"), "#/orders?state=FULFILLMENT_REQUESTED", count((x) => x.stuck) > 0)}
        ${kpi("Stuck > 10 min", count((x) => x.stuck), "#/orders?attn=1", true)}
        ${kpi("Exceptions", count((x) => x.state === "EXCEPTION"), "#/orders?state=EXCEPTION", true)}
        ${kpi("Shipped / completed", count((x) => ["SHIPPED", "COMPLETED"].includes(x.state)), "#/orders")}
        ${kpi("Active equipment alerts", activeAlerts, "#/sites")}
      </dl>
      <p class="muted" style="margin:.75rem 0 0">Sources: orders <span class="chip src-OK">OK</span> inventory <span class="chip src-OK">OK</span>
      assets <span class="chip src-OK">OK</span> change feed <span class="chip src-UNAVAILABLE">Unavailable</span>. Indicators omit sources that did not answer; they are not shown as zero.</p>`) +
      `<div class="columns">` +
      withData("Exception queue", cap("C4"), () => table(["Order", "State", "Reason / attempts", "Age", "Incident"], stuck.map((x) => [
        `<a href="#/orders/${x.orderId}">${x.orderId}</a>`, chip(x),
        x.stuck ? `${x.fulfillmentAttempts.filter((a) => a.result !== "ACKNOWLEDGED").length} ERP attempts outstanding` : h(x.statusReason),
        h(time(x.updatedAt)), x.incidentId ? `<a href="#/incidents/${x.incidentId}">${x.incidentId}</a>` : "—"]), "Orders needing attention"), "No stuck or exception orders.") +
      withData("Open incidents", cap("C10"), () => table(["Incident", "Severity", "Opened"], M.incidents.filter((i) => i.status !== "RESOLVED").map((i) => [
        `<a href="#/incidents/${i.incidentId}">${h(i.title)}</a>`, `<span class="chip sev-${i.severity}">${i.severity}</span>`, time(i.openedAt)]), "Open incidents"), "No open incidents.") +
      `</div>`;
  }
  const kpi = (label, n, href, attn) => `<div class="${attn && n ? "attn" : ""}"><dt><a href="${href}">${h(label)}</a></dt><dd>${n}</dd></div>`;

  function pageOrders(params) {
    if (params.get("state") !== null) ui.filters.state = params.get("state");
    if (params.get("attn")) ui.filters.attn = true;
    const f = ui.filters;
    let rows = M.orders.filter((o) => (!isCustomer() || o.customerId === CUSTOMER_ID)
      && (!f.state || o.state === f.state) && (!f.site || o.siteId === f.site) && (!f.attn || o.stuck || o.state === "EXCEPTION")
      && (!f.q || (o.orderId + o.customerId + o.sku).toLowerCase().includes(f.q.toLowerCase())));
    rows.sort((a, b) => (a[ui.sort.key] > b[ui.sort.key] ? 1 : -1) * ui.sort.dir);
    const size = 5, pages = Math.max(1, Math.ceil(rows.length / size));
    ui.page = Math.min(ui.page, pages - 1);
    const slice = rows.slice(ui.page * size, ui.page * size + size);
    const sortTh = (key, label) => {
      const dir = ui.sort.key === key ? (ui.sort.dir > 0 ? "ascending" : "descending") : "none";
      return { html: `<button class="sort" data-sort="${key}">${label}${dir === "none" ? "" : dir === "ascending" ? " ▲" : " ▼"}</button>`, aria: dir };
    };
    const opt = (v, l, cur) => `<option value="${v}" ${v === cur ? "selected" : ""}>${h(l)}</option>`;
    return head(isCustomer() ? "My orders" : "Orders", isCustomer() ? "Showing orders for cust_demo_1 only (enforced by BFF)" : "All orders in orders-demo",
      allowed("new") ? `<a class="btn primary" href="#/orders/new">Place order</a>` : "") +
      withData("Order list", cap("C5"), () => `
      <form class="filters" role="search" aria-label="Filter orders" onsubmit="return false">
        <label>State<select data-filter="state">${opt("", "Any state", f.state)}${Object.entries(M.stateLabels).map(([k, v]) => opt(k, v, f.state)).join("")}</select></label>
        <label>Site<select data-filter="site">${opt("", "Any site", f.site)}${M.sites.map((s) => opt(s.siteId, s.siteId, f.site)).join("")}</select></label>
        <label>Search<input type="search" data-filter="q" value="${h(f.q)}" placeholder="order, customer, SKU"></label>
        ${isCustomer() ? "" : `<label style="text-transform:none;letter-spacing:0;display:flex;gap:.4rem;align-items:center"><input type="checkbox" data-filter="attn" ${f.attn ? "checked" : ""}> Needs attention only</label>`}
        <button type="button" data-act="clear-filters">Clear</button>
      </form>
      ${rows.length === 0 ? `<div class="empty">No orders match these filters.</div>` : `
      <div class="table-wrap"><table class="stack-sm"><caption>${rows.length} orders · page ${ui.page + 1} of ${pages}</caption><thead><tr>
        ${[sortTh("orderId", "Order"), { html: "State", aria: null }, { html: "Customer", aria: null }, { html: "Item", aria: null }, { html: "Site", aria: null }, sortTh("createdAt", "Created"), sortTh("updatedAt", "Updated")]
          .map((c) => `<th scope="col" ${c.aria ? `aria-sort="${c.aria}"` : ""}>${c.html}</th>`).join("")}
      </tr></thead><tbody>
        ${slice.map((o) => `<tr><td data-label="Order"><a href="#/orders/${o.orderId}">${o.orderId}</a></td><td data-label="State">${chip(o)}</td>
          <td data-label="Customer" class="mono">${o.customerId}</td><td data-label="Item" class="mono">${o.sku} × ${o.quantity}</td>
          <td data-label="Site" class="mono">${o.siteId}</td><td data-label="Created">${time(o.createdAt)}</td><td data-label="Updated">${time(o.updatedAt)}</td></tr>`).join("")}
      </tbody></table></div>
      <div class="pager"><button type="button" data-page="-1" ${ui.page === 0 ? "disabled" : ""}>Previous</button>
        <span>Page ${ui.page + 1} / ${pages}</span><button type="button" data-page="1" ${ui.page >= pages - 1 ? "disabled" : ""}>Next</button></div>`}`,
      "No orders yet. Place an order or run the baseline-order scenario.");
  }

  function pageNewOrder() {
    const skus = ["SKU-42", "SKU-7", "SKU-LAST"];
    return head("Place order", "Submits through the BFF to order-service (POST /api/v1/orders)") +
      panel("Seeded order", cap("C6"), `<form id="order-form" novalidate>
        <div class="form-grid">
          <label>Customer<select name="customerId" ${isCustomer() ? "disabled" : ""}>${M.customers.map((c) => `<option value="${c.id}">${h(c.name)}</option>`).join("")}</select></label>
          <label>SKU<select name="sku">${skus.map((s) => `<option>${s}</option>`).join("")}</select></label>
          <label>Quantity<input type="number" name="quantity" value="2" min="1" max="10" aria-describedby="qty-err"><span id="qty-err" class="field-error" hidden></span></label>
          <label>Site<select name="siteId">${M.sites.map((s) => `<option value="${s.siteId}">${s.siteId} (${s.status})</option>`).join("")}</select></label>
        </div>
        <p class="muted">Idempotency key is generated per submission so a double-click cannot create two orders.</p>
        <div class="actions"><button class="primary" type="submit">Submit order</button><a class="btn" href="#/orders">Cancel</a></div>
      </form>`);
  }

  function pageOrder(id) {
    const o = M.orders.find((x) => x.orderId === id);
    if (!o) return notFound(`Order ${id}`);
    if (isCustomer() && o.customerId !== CUSTOMER_ID) return forbidden(`/api/v1/orders/${id}/summary`, "This order belongs to another customer.");
    const terminal = ["COMPLETED", "REJECTED", "CANCELLED", "EXCEPTION"].includes(o.state);
    const idx = M.happyPath.indexOf(o.state);
    const rail = `<ol class="rail" aria-label="Order progress">${M.happyPath.map((s, i) => {
      const cls = o.state === s ? "current" + (o.stuck ? " stuck" : "") : idx > i ? "done" : "";
      return `<li class="${cls}" ${o.state === s ? 'aria-current="step"' : ""}>${h(M.stateLabels[s])}</li>`; }).join("")}</ol>`;
    const outstanding = o.fulfillmentAttempts.filter((a) => a.result !== "ACKNOWLEDGED").length;
    const banner = o.stuck ? `<section class="alert" role="status"><h2>Awaiting ERP acknowledgement ${cap("C9")}</h2>
        <p>${outstanding} ERP attempts outstanding since ${time(o.timeline[2]?.occurredAt)}. Retries are automatic; no action is needed unless the incident escalates.</p>
        ${o.incidentId && !isCustomer() ? `<p>Linked incident: <a href="#/incidents/${o.incidentId}">${o.incidentId}</a></p>` : ""}</section>`
      : o.state === "EXCEPTION" ? `<section class="alert" role="alert"><h2>Manual reconciliation required ${cap("C4")}</h2><p>Reason <span class="mono">${h(o.statusReason)}</span>. The console does not resolve exceptions; reconciliation is a backend workflow ${assumed("not yet specified")}.</p></section>` : "";
    const internal = !isCustomer();
    return head(`Order ${o.orderId}`, `${M.stateLabels[o.state]} · updated ${time(o.updatedAt)}`, chip(o), `<a href="#/orders">Orders</a> /`) +
      (ui.data !== "normal" ? withData("Order summary", cap("C7"), () => "") : banner +
      panel("Progress", cap("C7"), rail +
        (!terminal || o.state === "SHIPPED" ? `<div class="actions" style="margin-top:.75rem"><button class="mock-only" type="button" data-act="advance" data-id="${o.orderId}">Simulate next backend event (mockup only)</button></div>` : "")) +
      `<div class="columns">` +
      panel("Order", cap("C7"), `<dl class="kv">
        <dt>Item</dt><dd>${o.sku} × ${o.quantity}</dd><dt>Site</dt><dd>${o.siteId}</dd><dt>Customer</dt><dd>${o.customerId}</dd>
        <dt>Reservation</dt><dd>${h(o.reservationId || "— not yet reserved")}</dd>
        ${internal ? `<dt>Correlation</dt><dd>${o.correlationId}</dd>` : ""}
        <dt>Notification</dt><dd>${o.notification ? `${h(o.notification.channel)} · ${h(o.notification.outcome)}` : "— none yet"}</dd></dl>
        ${internal ? "" : `<p class="muted">Customer view: internal identifiers, traces and attempt detail are omitted by the BFF.</p>`}`) +
      (internal ? panel("Fulfilment attempts", cap("C7", "C9"), o.fulfillmentAttempts.length ? table(["#", "Sent", "Result"], o.fulfillmentAttempts.map((a) => [a.attempt, time(a.at), h(a.result)]), "ERP fulfilment attempts") : `<div class="empty">No fulfilment requested yet.</div>`) : "") +
      `</div>` +
      panel("Timeline", cap("C8"), `<ol class="timeline">${o.timeline.map((e) => `
        <li class="${e.kind === "TRANSITION" ? "transition" : "note"}"><div class="tl-head"><span class="tl-time">${time(e.occurredAt)}</span>
          <span class="tl-title">${e.kind === "TRANSITION" ? h(M.stateLabels[e.toState]) : h(e.note || e.reasonCode)}</span>
          ${e.reasonCode && e.kind === "TRANSITION" ? `<span class="mono muted">${h(e.reasonCode)}</span>` : ""}</div>
          ${internal ? `<div class="tl-links"><span>${h(e.eventType)}</span><a href="#/orders/${o.orderId}" title="Opens trace in observability UI (link target assumed)">trace ${e.traceId.slice(-8)}</a>
            <a href="#/orders/${o.orderId}" title="Logs filtered by correlation ID (link target assumed)">logs ${o.correlationId}</a></div>` : ""}</li>`).join("")}
        ${o.stuck ? `<li class="pending"><div class="tl-head"><span class="tl-time">now</span><span class="tl-title muted">Waiting for ERP acknowledgement…</span></div></li>` : ""}
      </ol>`));
  }

  function pageIncidents() {
    return head("Incidents", "Exceptions and alerts with linked evidence") +
      withData("Incidents", cap("C10"), () => table(["Incident", "Status", "Severity", "Opened", "Linked orders"], M.incidents.map((i) => [
        `<a href="#/incidents/${i.incidentId}">${h(i.title)}</a>`, h(i.status), `<span class="chip sev-${i.severity}">${i.severity}</span>`, time(i.openedAt),
        i.linkedOrders.map((x) => `<a href="#/orders/${x}">${x}</a>`).join(", ") || "—"]), "Incidents"), "No incidents recorded.");
  }

  function pageIncident(id) {
    const i = M.incidents.find((x) => x.incidentId === id);
    if (!i) return notFound(`Incident ${id}`);
    const partial = i.evidence.some((e) => e.sourceStatus !== "OK");
    const r = i.recovery;
    const recovery = r.confirmedByBackend
      ? `<p role="status"><span class="chip" data-s="COMPLETED">Recovered</span> Backend confirmed recovery; linked orders completed.</p>`
      : r.requested ? `<p role="status"><span class="chip" data-s="FULFILLMENT_REQUESTED" data-stuck="true">Recovery requested — awaiting backend confirmation</span></p>
          <p class="muted">Requested by ${h(r.requestedBy)}. The incident stays OPEN until the backend observes orders completing.</p>
          <button class="mock-only" type="button" data-act="confirm-recovery" data-id="${i.incidentId}">Simulate backend confirmation (mockup only)</button>`
      : i.scenarioRunId ? `<p>Controlled recovery stops scenario <span class="mono">${h(i.scenarioRunId)}</span> through the scenario controller.</p>
          <button class="danger" type="button" data-act="request-recovery" data-id="${i.incidentId}">Request controlled recovery</button>` : `<p class="muted">No automated recovery action is defined for this incident.</p>`;
    return head(i.title, `${i.incidentId} · opened ${time(i.openedAt)}`, `<span class="chip sev-${i.severity}">${i.severity}</span>`, `<a href="#/incidents">Incidents</a> /`) +
      (ui.data !== "normal" ? withData("Evidence", cap("C10"), () => "") :
      (partial ? `<section class="alert partial" role="status"><h2>Partial evidence ${cap("C10")}</h2><p>${i.evidence.filter((e) => e.sourceStatus !== "OK").map((e) => `${h(e.source)}: ${h(e.sourceStatus.toLowerCase())}`).join("; ")}. Conclusions below exclude these sources.</p></section>` : "") +
      `<div class="columns">` +
      panel("Diagnosis", `${cap("C10")} ${assumed("incident schema assumed")}`, `<dl class="kv">
        <dt>SLO</dt><dd>${h(i.slo?.name || "—")}</dd><dt>Observed</dt><dd>${h(i.slo?.observed || "—")}</dd>
        <dt>Scenario run</dt><dd>${h(i.scenarioRunId || "— none")}</dd>
        <dt>Linked orders</dt><dd>${i.linkedOrders.map((x) => `<a href="#/orders/${x}">${x}</a>`).join(", ") || "—"}</dd></dl>`) +
      panel("Recovery", cap("C11", "C13"), `<div id="recovery">${recovery}</div>`) + `</div>` +
      panel("Evidence by source", cap("C10"), table(["Source", "Status", "Finding", "Link"], i.evidence.map((e) => [
        h(e.source), `<span class="chip src-${e.sourceStatus}">${h(e.sourceStatus)}</span>`, h(e.summary),
        e.link ? `<span class="mono">${h(e.link)}</span>` : `<span class="muted">unknown</span>`]), "Evidence gathered per source")));
  }

  function pageSites() {
    return head("Sites & assets", "Stock by site and equipment telemetry") +
      `<div class="columns">` +
      withData("Sites", cap("C12"), () => table(["Site", "Status", "Stock"], M.sites.map((s) => [
        `<span class="mono">${s.siteId}</span><br><span class="muted">${h(s.name)}</span>`,
        s.status === "ACTIVE" ? `<span class="chip src-OK">ACTIVE</span>` : `<span class="chip src-UNAVAILABLE">UNAVAILABLE</span>`,
        Object.entries(s.stock).map(([k, v]) => `<span class="mono">${k}: ${v}</span>`).join("<br>")]), "Fulfilment sites")) +
      withData("Assets", cap("C12"), () => table(["Asset", "Site", "Last reading", "Alerts"], M.assets.map((a) => [
        `<span class="mono">${a.assetId}</span><br><span class="muted">${h(a.kind)}</span>`, `<span class="mono">${a.siteId}</span>`,
        a.lastReading ? `<span class="mono">${a.lastReading.metric} ${a.lastReading.value}</span><br><span class="muted">${time(a.lastReading.at)}</span>` : `<span class="muted"><em>No reading received — unknown</em></span>`,
        a.alerts.map((al) => `<span class="chip sev-${al.status === "ACTIVE" ? al.severity : "CLEARED"}">${al.severity} · threshold ${al.threshold}, peak ${al.peak}</span>`).join("<br>") || "—"]), "Assets"), "No assets reporting.") +
      `</div>`;
  }

  function pageDemo() {
    return head("Demo control", "Named, bounded fault scenarios through the scenario controller. No generic commands.") +
      `<section class="alert" role="note"><h2>Demo environment only ${cap("C13")}</h2><p>Target: <span class="mono">${M.env.cluster} / ${M.env.namespace}</span>. Every action asks for confirmation, is audited, and auto-resets after its TTL. The backend rejects non-demo namespaces.</p></section>` +
      panel("Scenarios", cap("C13"), table(["Scenario", "Effect", "TTL", "Status", ""], M.scenarios.map((s) => [
        `<span class="mono">${s.name}</span>`, h(s.effect), s.ttl,
        s.running ? `<span class="chip" data-s="FULFILLMENT_REQUESTED">Running ${h(s.running.runId)}</span>` : `<span class="muted">Idle</span>`,
        s.running ? `<button type="button" data-act="scenario" data-op="stop" data-name="${s.name}">Stop</button>` : `<button type="button" data-act="scenario" data-op="start" data-name="${s.name}">Start…</button>`]), "Scenario catalog")) +
      panel("Audit trail", cap("C13"), table(["Run", "Scenario", "Action", "Actor", "Environment", "When", "Result"], M.scenarioAudit.map((a) => [
        `<span class="mono">${a.runId}</span>`, a.scenario, a.action, a.actor, `<span class="mono">${a.env}</span>`, time(a.at), h(a.result)]), "Scenario audit records"));
  }

  function pageDelivery() {
    return head("Delivery", "Deployed revisions and GitOps sync (developer panel, P1)") +
      panel("Services", `${cap("C14")} ${assumed("data source not defined")}`, table(["Service", "Revision", "Image digest", "Argo CD sync", "Health", "Deployed"], M.delivery.map((d) => [
        `<span class="mono">${d.service}</span>`, `<span class="mono">${h(d.revision)}</span>`, `<span class="mono">${h(d.digest)}</span>`,
        d.sync === "Synced" ? `<span class="chip src-OK">Synced</span>` : d.sync === "OutOfSync" ? `<span class="chip src-PARTIAL">OutOfSync</span>` : `<span class="chip src-UNAVAILABLE">Unknown</span>`,
        h(d.health), time(d.at)]), "Deployed services"));
  }

  // ---------- shared fragments ----------
  const head = (title, sub, right = "", crumbs = "") => `<div class="page-head"><div>${crumbs ? `<div class="crumbs">${crumbs}</div>` : ""}<h1 tabindex="-1">${h(title)}</h1><div class="muted">${h(sub)}</div></div><div class="actions">${right}</div></div>`;
  const table = (cols, rows, caption) => rows.length ? `<div class="table-wrap"><table class="stack-sm"><caption class="visually-hidden">${h(caption)}</caption><thead><tr>${cols.map((c) => `<th scope="col">${c}</th>`).join("")}</tr></thead>
    <tbody>${rows.map((r) => `<tr>${r.map((c, i) => `<td data-label="${h(cols[i])}">${c}</td>`).join("")}</tr>`).join("")}</tbody></table></div>` : `<div class="empty">Nothing to show.</div>`;
  const forbidden = (path, why = "Your role is not permitted to view this page.") => head("Forbidden", "403 from the Operations service") +
    `<section class="alert" role="alert"><h2>You don't have access ${cap("C2")}</h2><p>${h(why)} Signed in as <strong>${h(M.roles[ui.role].label)}</strong>.</p>
    <pre class="problem">{ "type": "https://box1.example/problems/forbidden", "title": "Forbidden", "status": 403, "instance": "${h(path)}" }</pre>
    <p class="muted">The page is hidden from navigation for convenience, but this response comes from the server check, not the hidden link.</p>
    <div class="actions"><a class="btn" href="#/${M.roles[ui.role].routes[0] === "orders" ? "orders" : "home"}">Go to my start page</a></div></section>`;
  const notFound = (what) => head("Not found", "") + `<section class="alert" role="alert"><h2>${h(what)} was not found ${cap("C15")}</h2><p>It may have been removed, or the link is wrong.</p></section>`;

  // ---------- router ----------
  function route() {
    const [path, qs] = (location.hash.slice(1) || "/home").split("?");
    const params = new URLSearchParams(qs || "");
    const seg = path.split("/").filter(Boolean);
    let key = seg[0] || "home", html;
    if (key === "orders" && seg[1] === "new") key = "new";
    else if (key === "orders" && seg[1]) key = "order";
    else if (key === "incidents" && seg[1]) key = "incident";
    if (!allowed(key)) html = forbidden(location.hash.slice(1));
    else html = ({ home: pageHome, orders: () => pageOrders(params), new: pageNewOrder, order: () => pageOrder(seg[1]), incidents: pageIncidents,
      incident: () => pageIncident(seg[1]), sites: pageSites, demo: pageDemo, delivery: pageDelivery }[key] || (() => notFound(path)))();
    $("#main").innerHTML = html;
    const navKey = key === "order" ? "orders" : key === "incident" ? "incidents" : key;
    $("#nav").innerHTML = NAV.filter(([k]) => allowed(k)).map(([k, href, label]) => `<li><a href="${href}" ${k === navKey ? 'aria-current="page"' : ""}>${label}</a></li>`).join("");
    $("#env").textContent = `${M.env.cluster} / ${M.env.namespace}`;
    $("#fresh").textContent = ui.data === "error" ? "Data stale — last good 10:41:30 ET" : `Data as of ${time(M.now)}`;
    $("#fresh").dataset.state = ui.data === "error" ? "stale" : "fresh";
    $("#who").textContent = `demo.${ui.role} · ${M.roles[ui.role].label}`;
    const h1 = $("#main h1"); if (h1 && route.focus) h1.focus(); route.focus = true;
    document.title = `${h1 ? h1.textContent + " · " : ""}box1 Operations — MOCKUP`;
  }

  // ---------- confirm dialog ----------
  function confirmDialog(title, bodyHtml, okLabel, onOk) {
    const d = $("#confirm");
    d.innerHTML = `<h2 id="confirm-title">${h(title)}</h2>${bodyHtml}
      <label style="display:flex;gap:.5rem;margin:.75rem 0"><input type="checkbox" id="ack"> I understand this affects the shared demo environment.</label>
      <div class="actions"><button class="danger" id="ok" disabled>${h(okLabel)}</button><button id="cancel" autofocus>Cancel</button></div>`;
    d.querySelector("#ack").onchange = (e) => (d.querySelector("#ok").disabled = !e.target.checked);
    d.querySelector("#cancel").onclick = () => d.close();
    d.querySelector("#ok").onclick = () => { d.close(); onOk(); };
    d.showModal();
  }

  // ---------- mock backend effects ----------
  const stamp = () => new Date().toISOString();
  function advance(o) {
    const n = Number(o.orderId.slice(4));
    const push = (from, to, ev) => o.timeline.push({ sequence: o.timeline.length + 1, kind: "TRANSITION", fromState: from, toState: to, occurredAt: stamp(), eventType: ev, traceId: `4bf92f3577b34da6a3ce929d0e0e${n}` });
    const next = { SUBMITTED: ["RESERVED", "inventory.reserved.v1"], RESERVED: ["FULFILLMENT_REQUESTED", "fulfillment.requested.v1"],
      FULFILLMENT_REQUESTED: ["SHIPPED", "shipment.confirmed.v1"], SHIPPED: ["COMPLETED", "order.completed.v1"] }[o.state];
    if (!next) return;
    if (next[0] === "RESERVED") o.reservationId = `res_${n}`;
    if (next[0] === "FULFILLMENT_REQUESTED") o.fulfillmentAttempts.push({ attempt: 1, at: stamp(), result: "PENDING" });
    if (next[0] === "SHIPPED") { o.stuck = false; o.fulfillmentAttempts.forEach((a) => a.result === "PENDING" && (a.result = "ACKNOWLEDGED")); }
    if (next[0] === "COMPLETED") o.notification = { channel: "email", outcome: "SENT", at: stamp() };
    push(o.state, next[0], next[1]); o.state = next[0]; o.updatedAt = stamp();
    announce(`Order ${o.orderId} is now ${M.stateLabels[o.state]}`);
  }

  // ---------- events ----------
  document.addEventListener("click", (e) => {
    const t = e.target.closest("[data-act],[data-sort],[data-page]");
    if (!t) return;
    if (t.dataset.sort) { ui.sort = { key: t.dataset.sort, dir: ui.sort.key === t.dataset.sort ? -ui.sort.dir : 1 }; route(); return; }
    if (t.dataset.page) { ui.page += Number(t.dataset.page); route(); return; }
    const act = t.dataset.act;
    if (act === "retry") { ui.data = "normal"; $("#datastate").value = "normal"; route(); }
    if (act === "clear-filters") { ui.filters = { state: "", site: "", q: "", attn: false }; location.hash = "#/orders"; route(); }
    if (act === "advance") { advance(M.orders.find((o) => o.orderId === t.dataset.id)); route(); }
    if (act === "request-recovery") {
      const i = M.incidents.find((x) => x.incidentId === t.dataset.id);
      if (!M.roles[ui.role].routes.includes("demo")) {
        $("#recovery").insertAdjacentHTML("beforeend", `<div class="alert" role="alert" style="margin-top:.75rem"><p>403 Forbidden: the scenario controller allows operator or admin only. The button is visible, but the server decides.</p></div>`);
        return;
      }
      confirmDialog("Request controlled recovery?", `<p>Stops <span class="mono">${h(i.scenarioRunId)}</span> in <span class="mono">${M.env.cluster} / ${M.env.namespace}</span>.</p><p class="muted">The incident will not be marked resolved until the backend confirms that linked orders completed.</p>`,
        "Request recovery", () => { i.recovery = { requested: true, requestedBy: `demo.${ui.role}`, confirmedByBackend: false }; announce("Recovery requested, awaiting backend confirmation"); route(); });
    }
    if (act === "confirm-recovery") {
      const i = M.incidents.find((x) => x.incidentId === t.dataset.id);
      i.recovery.confirmedByBackend = true; i.status = "RESOLVED";
      i.linkedOrders.forEach((id) => { const o = M.orders.find((x) => x.orderId === id); for (let k = 0; k < 4 && o.state !== "COMPLETED"; k++) advance(o); });
      const s = M.scenarios.find((x) => x.running); if (s) { M.scenarioAudit.unshift({ runId: s.running.runId, scenario: s.name, action: "stop", actor: i.recovery.requestedBy, at: stamp(), env: `${M.env.cluster} / ${M.env.namespace}`, result: "VERIFIED" }); delete s.running; }
      announce("Backend confirmed recovery"); route();
    }
    if (act === "scenario") {
      const s = M.scenarios.find((x) => x.name === t.dataset.name), op = t.dataset.op;
      confirmDialog(`${op === "start" ? "Start" : "Stop"} scenario ${s.name}?`, `<p>${h(s.effect)}.</p><dl class="kv"><dt>Environment</dt><dd>${M.env.cluster} / ${M.env.namespace}</dd><dt>TTL</dt><dd>${s.ttl} (auto-reset)</dd><dt>Actor</dt><dd>demo.${ui.role}</dd></dl>`,
        op === "start" ? "Start scenario" : "Stop scenario", () => {
          const runId = op === "start" ? `scn_run_${String(13 + M.scenarioAudit.length).padStart(4, "0")}` : s.running.runId;
          if (op === "start") s.running = { runId, by: `demo.${ui.role}`, at: stamp() }; else delete s.running;
          M.scenarioAudit.unshift({ runId, scenario: s.name, action: op, actor: `demo.${ui.role}`, at: stamp(), env: `${M.env.cluster} / ${M.env.namespace}`, result: op === "start" ? "RUNNING" : "STOPPED — reset pending verification" });
          announce(`Scenario ${s.name} ${op} recorded`); route();
        });
    }
  });
  document.addEventListener("change", (e) => {
    const f = e.target.dataset.filter;
    if (f) { ui.filters[f] = e.target.type === "checkbox" ? e.target.checked : e.target.value; ui.page = 0; history.replaceState(null, "", "#/orders"); route(); const el = document.querySelector(`[data-filter="${f}"]`); el && el.focus(); }
  });
  document.addEventListener("input", (e) => { if (e.target.dataset.filter === "q") { ui.filters.q = e.target.value; ui.page = 0; route(); const el = $('[data-filter="q"]'); el.focus(); el.setSelectionRange(el.value.length, el.value.length); } });
  document.addEventListener("submit", (e) => {
    if (e.target.id !== "order-form") return;
    e.preventDefault();
    const fd = new FormData(e.target), qty = Number(fd.get("quantity")), err = $("#qty-err");
    if (!(qty >= 1 && qty <= 10)) { err.textContent = "Quantity must be between 1 and 10."; err.hidden = false; e.target.quantity.setAttribute("aria-invalid", "true"); e.target.quantity.focus(); return; }
    const id = `ord_${1050 + M.orders.length - 7}`;
    M.orders.unshift({ orderId: id, state: "SUBMITTED", customerId: isCustomer() ? CUSTOMER_ID : fd.get("customerId"), sku: fd.get("sku"), quantity: qty, siteId: fd.get("siteId"),
      correlationId: `corr-${id.slice(4)}`, createdAt: stamp(), updatedAt: stamp(), fulfillmentAttempts: [], notification: null,
      timeline: [{ sequence: 1, kind: "TRANSITION", fromState: null, toState: "SUBMITTED", occurredAt: stamp(), eventType: "order.submitted.v1", traceId: "4bf92f3577b34da6a3ce929d0e0e9999" }] });
    if (fd.get("siteId") === "site_closed") { const o = M.orders[0]; o.state = "REJECTED"; o.statusReason = "SITE_UNAVAILABLE";
      o.timeline.push({ sequence: 2, kind: "TRANSITION", fromState: "SUBMITTED", toState: "REJECTED", reasonCode: "SITE_UNAVAILABLE", occurredAt: stamp(), eventType: "inventory.rejected.v1", traceId: "4bf92f3577b34da6a3ce929d0e0e9999" }); }
    announce(`Order ${id} submitted`); location.hash = `#/orders/${id}`;
  });
  $("#role").addEventListener("change", (e) => { ui.role = e.target.value; const start = M.roles[ui.role].routes[0] === "orders" ? "#/orders" : "#/home"; if (location.hash === "#/home" || location.hash === "") location.hash = start; route(); });
  $("#datastate").addEventListener("change", (e) => { ui.data = e.target.value; route(); });
  window.addEventListener("hashchange", () => { if (location.hash === "" || location.hash.startsWith("#/")) route(); });
  document.querySelector(".skip").addEventListener("click", (e) => { e.preventDefault(); $("#main").focus(); });
  route.focus = false; if (!location.hash.startsWith("#/")) history.replaceState(null, "", "#/home"); route();
})();
