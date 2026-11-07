# D-015 Live acceptance input

**Status:** **open: approval required**.

A live round trip needs a real `fulfillment.requested.v1`. That means either a live order through order-service (which produces to shared topics through order and inventory) or producing directly to `box1.order.events.v1`. Both are writes to shared topics and need explicit approval, naming the request and its IDs. Neither helps until the ERP VM (#25), the SFTP credential (D-007) and the database (D-012) exist.
