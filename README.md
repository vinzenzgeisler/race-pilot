# RacePilot architecture

This repository currently contains the documentation-first architecture baseline for
RacePilot issues #34 and #38. It does **not** contain a deployable product, a Community
distribution, a Cloud control plane, or an active cross-edition CI implementation.

RacePilot is one product with one shared domain core and two explicit deployment
modes:

- **Community:** self-hosted, single tenant, exactly one organization per installation.
- **Cloud:** managed by RacePilot, multi-tenant, with strictly isolated organizations.

The following documents form the baseline:

- [ADR 0001: editions, shared core, and deployment modes](docs/adr/0001-editions-shared-core-and-deployment-modes.md)
- [Repository and module map](docs/architecture/repository-module-map.md)
- [Current coupling inventory](docs/architecture/current-couplings.md)
- [Required CI coverage and ownership](docs/architecture/ci-coverage.md)
- [Tenant resource inventory and isolation-test contract](docs/security/tenant-resource-inventory.md)
- [Machine-readable tenant resource inventory v1](docs/security/tenant-resource-inventory.v1.json)

## Status language

All architecture documents use these labels deliberately:

- **Current fact:** verified in the evidence snapshot; it describes what exists now.
- **Target decision:** accepted architecture for future implementation; it is not a
  claim that code or infrastructure already implements the decision.
- **Follow-up obligation:** work that must be implemented and verified before the
  affected mode can be called ready.

## Non-goals of this baseline

No product code, deployment manifests, billing code, tenant migration, repository
move, or product CI workflow is introduced here. In particular, this repository does
not make the current MSC application multi-tenant merely by documenting a target
design.

The only active workflow added by issue #38 validates the documentation inventory,
fixture, test references, global rationales, and relative links. It does not run or
claim product-level tenant isolation.
