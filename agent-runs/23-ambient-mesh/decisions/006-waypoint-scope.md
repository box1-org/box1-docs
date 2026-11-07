# 006 Waypoint scope — recommendation (for the user to decide)

**Recommended:** keep waypoints on `operations-console-dev`, `order-service-dev` and `inventory-service-dev` only (user decision 5). Do not add them to fulfillment-adapter, notification, asset or scenario-controller.

**Evidence** (`evidence/phase7-waypoints.md`):
- The only HTTP between enrolled workloads is the console's fan-out.
- Notification and scenario-controller receive none.
- Most of the order flow is Kafka, which waypoints cannot see.
- Each waypoint costs about 2m CPU and 33Mi in use (100m / 128Mi requested) and adds about 0.6 ms per hop (one sample).

**Revisit if:**
- services start calling each other over HTTP;
- L7 authorization policy becomes a goal (out of scope here per user decision 10);
- or Route traffic to the order API should be L7 (`istio.io/ingress-use-waypoint`).
