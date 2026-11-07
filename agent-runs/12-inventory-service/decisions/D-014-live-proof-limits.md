# D-014 Limits on live proof

**Status:** planned defaults. The user can override them.

- **Traces:** carried in logs and events, and tested locally. A trace backend does not exist (box1-docs#22).
- **Metrics and logs:** live proof through `/q/metrics` and `oc logs`. No scraping is configured.
- **Fault scenarios:** local only. No named demo namespace exists, so there is no cluster fault injection.
- **Other services' events live:** nothing produces `shipment.*` live. Those paths are local with `box1-ops-contracts` fixtures. This run does not produce to shared topics.
- **Live acceptance:** one new order through the Order Route needs the user's approval. It will hold stock, and stays at `FULFILLMENT_REQUESTED`, since no fulfillment adapter exists.
- **Gate dependency checks:** the CI credentials are not issued to this run, so the working path is proven by the pipeline's own gated runs. The nearest such run and the first inventory release are the evidence.
