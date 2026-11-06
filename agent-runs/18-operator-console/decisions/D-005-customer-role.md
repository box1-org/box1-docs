# D-005 Customer role

**Status:** decided: **out of scope for this run**. This needs the user's confirmation (O-5).

- Orders carry a `customerId` (`cust_…`) chosen by the caller. Nothing binds it to a verified identity: order-service has no auth (#40), and Keycloak users have no customer attribute. A "customer sees only their own orders" check would therefore filter on a value the customer could choose. That is security theatre, not authorization.
- No `console-customer` role is created, and all console roles are internal staff roles.
- **Acceptance criterion 2** ("browser role/customer checks"): the role checks are delivered. The **customer check is recorded as `blocked`** (CON-CUST-001), with this reason.
- The order detail shows only customer-safe metadata. `customerId` is an opaque ID, and no names, addresses or contact details exist in any upstream.
