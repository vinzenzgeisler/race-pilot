# Required CI coverage and ownership

This document is a **target decision** and release contract. It does not add a CI
workflow and must not be cited as proof that a check currently runs.

The edition architecture is accepted in
[ADR 0001](../adr/0001-editions-shared-core-and-deployment-modes.md). Current
repository ownership is mapped in [the repository/module map](repository-module-map.md).

## Current fact

- `MSC-Event-Backend/.github/workflows/ci-cd.yml` runs API tests and an infrastructure
  build as a common validation job, then performs AWS/CDK environment-specific work.
- `MSC-Event-Frontend/.github/workflows/ci-cd.yml` runs typecheck and build, then
  performs Vercel-specific deployments. No frontend test command is declared in its
  `package.json`.
- No workflow in the inspected sources runs a `community`/`cloud` deployment-mode
  matrix, starts a Community Compose installation, or provisions two Cloud tenants
  for negative isolation tests.
- No workflow was found in the marketing repository.

## Mandatory matrix

Every pull request that changes shared core behavior, public contracts, persistence,
workers, or product frontend behavior must run the applicable rows. “Same core” means
the same artifact or commit is tested in both columns, not two rebuilt forks.

| Gate / core process | Community job | Cloud job | Required assertion | Accountable owner |
|---|---|---|---|---|
| Core unit and contract tests | `mode=community`, provider fakes | `mode=cloud`, the same provider fakes | Registration, pricing, participant/vehicle validation, lifecycle, permissions, entitlement/capability evaluation, and API/message schemas produce mode-independent domain results | RacePilot Core maintainers |
| Server-authority tamper tests | Single configured organization | Two organizations, host and membership resolver | Client attempts to set mode, organization, role, permission, entitlement, or capability are ignored/rejected; server context wins | Backend/security owner |
| Registration integration | Fresh PostgreSQL, one organization | Fresh PostgreSQL, organizations A and B | Configure event/classes, submit and verify an entry, calculate price, and reject closed registration; Cloud repeats foreign-ID attempts | Registration owner; security owner signs Cloud isolation |
| Admin lifecycle and permissions | OIDC test identity in the one organization | Users with different memberships in A/B | Activate/close/archive event, update entry/payment/notes, and prove role permissions; an entitlement alone never grants access | Admin/IAM owner |
| Documents and signing | Filesystem/S3-compatible test adapter | Tenant-prefixed managed-storage test adapter | Generate/download entry confirmation, waiver, and inspection documents; complete signing; reject another tenant's ID/key/token | Documents/signing owner |
| Mail/outbox worker | SMTP capture adapter | Managed-mail test adapter with tenant sender rules | Queue, retry, render, attach, and deliver lifecycle/broadcast mail; job context is mandatory and tenant-scoped | Communication owner |
| Export worker | Local object adapter | Tenant-prefixed managed-storage adapter | Generate and download an export; reject cross-tenant job and object access | Export owner |
| Technical inspection | One organization and event | Inspectors scoped to A/B | Issue/consume inspection context and update history only with permission and matching organization | Inspection owner |
| Marshal planning | One organization and multiple events | Organizations A/B with colliding human-readable codes | Import, plan, assign, train, and print without organization leakage | Marshal owner |
| Retention and audit worker | Community retention configuration | Tenant-specific policy fixtures for A/B | Retain/delete/anonymize the intended rows only; audit includes server context; one tenant's run cannot affect another | Privacy owner |
| Product frontend E2E | Server bootstrap says `community` | Server bootstrap says `cloud` for A, then B | Public registration and admin happy paths render from server data; a mutated browser bootstrap cannot authorize an API action | Frontend owner with Backend owner |
| Community distribution smoke | Fresh host, published Compose inputs | Not applicable | Install from documentation, migrate, create the single organization/event, complete a test registration, run worker, back up and restore | Community distribution owner |
| Cloud control-plane contract | Not applicable | Ephemeral control plane + runtime contracts | Organization/domain/membership/subscription changes produce signed or authenticated server state; disabled/unknown tenant fails closed | Cloud platform owner |
| Migration | Existing MSC-shaped fixture becomes the one Community organization | Same fixture becomes an explicit Cloud tenant; add second tenant | Counts and relationships reconcile; storage and jobs acquire organization scope; rollback/restore is exercised | Data migration owner |

## Workflow shape

The implementing workflows must expose named, required checks rather than hiding
coverage in deployment jobs:

1. `core (community)` and `core (cloud)` run on every shared-core pull request.
2. `integration (community)` and `integration (cloud-two-tenant)` run when API,
   persistence, worker, contract, or adapter boundaries change.
3. `web-e2e (community)` and `web-e2e (cloud)` run when frontend or bootstrap/API
   contracts change.
4. `community-distribution-smoke` runs for distribution changes and release
   candidates.
5. `cloud-control-plane-contract` and destructive-environment tests run in the private
   repository, report an unambiguous commit/contract version, and gate Cloud release.
6. Migration, cross-tenant, backup/restore, dependency, secret, container, and IaC
   checks gate the relevant release candidate.

Tests must use synthetic fixtures. A Cloud isolation job needs at least two
organizations and deliberate foreign IDs for every affected resource group, including
database rows, object keys, queued jobs, caches, downloads, and audit queries.

## Ownership and evidence

- **RacePilot Core maintainers** own the matrix definition, required-check policy, and
  parity of shared business behavior.
- The **named process owner** owns fixtures and positive/negative assertions for that
  row. The same person need not maintain every adapter.
- The **Community distribution owner** owns install, upgrade, backup, restore, and
  rollback evidence.
- The **Cloud platform owner** owns control-plane, tenant resolver, managed adapter,
  isolation, and operational evidence. The **security owner** must approve changes to
  tenant or authorization boundaries.
- A release record links the workflow run, source SHA, migration version, container or
  deployment artifact digest, and contract version for both modes.

If a column is skipped, the shared change is not releasable for that mode. A temporary
waiver must be explicit, time-bounded, owned, and must not waive tenant isolation or
server-authority tests.

## Follow-up obligations

- Add testable deployment-mode/context seams before creating the matrix.
- Add Community provider fixtures and an installable Compose distribution.
- Add Cloud two-tenant fixtures, RLS/tenant-query checks, and control-plane contracts.
- Convert each row into required checks in the owning repository.
- Publish the first release evidence only after the workflows exist and pass; do not
  backfill an “active” claim from this design document.
