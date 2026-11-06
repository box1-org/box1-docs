# D-013 Order list filters, sort and pagination

**Status:** decided.

- order-service lists only newest-first by cursor and offers no filters or sort.
- The console backend reads a bounded **window of the most recent orders** (at most 200, as 2 pages of 100). It filters by `state`, `siteId` and `sku`, sorts by `createdAt` or `updatedAt` in either direction, and pages the result with `page` and `size`.
- The response carries `window: {scanned, complete}`, and the UI says "showing the most recent N orders" when the window is incomplete. It never implies a full search.
- A server-side filter belongs in order-service or #17. That is not a gap that blocks this run.

## Amendment (Phase 5, ARCH-10)

Offset pages over a moving window are not stable: new orders shift later pages. #17's "stable pagination" will need a cursor. This is recorded as a known limit.
