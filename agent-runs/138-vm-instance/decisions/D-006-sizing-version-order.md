# D-006 Instance sizing, plugin version, order of the sites

- **Sizing:** template defaults are 2 vCPU, 4Gi memory and a 20Gi root disk, matching the prompt's estimate. The choices are the same as `rhel-image-vm`: 1/2/4 vCPU, 2/4/8Gi memory, 12/20/40Gi root disk. Resource fit is in `evidence/01-discovery.md`. The use of a running instance has **not** been measured.
- **Plugin version:** 1.5.0, built on 1.4.0 (#137) and 1.3.0 (#136). Release it once, after all three template PRs merge.
- **Order:** create `site-west` (`site_ds9`) first, then `site-east` (`site_spacedock`). Each instance is checked end to end before the next one uses the remaining headroom. Neither was created by this run.
