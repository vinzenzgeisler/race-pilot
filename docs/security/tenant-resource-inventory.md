# Tenant resource inventory and isolation-test contract

This document is the human-readable security contract for RacePilot issue #38. The
normative, versioned artifacts are:

- [tenant resource inventory v1](tenant-resource-inventory.v1.json), containing 106
  classified resource records;
- [two-tenant fixture v1](fixtures/two-tenant.v1.json), containing synthetic
  organizations A and B; and
- [tenant isolation-test matrix v1](tenant-isolation-test-matrix.v1.json), containing
  the named negative tests referenced by every inventory record.

The standalone [inventory validator](../../scripts/validate_tenant_inventory.py)
checks all three artifacts without installing dependencies. The
[relative Markdown-link checker](../../scripts/check_relative_markdown_links.py) and
[tenant inventory workflow](../../.github/workflows/tenant-inventory.yml) make the
documentation checks repository-native.

## Status and evidence boundary

The inventory separates two kinds of statement:

- **Current fact:** a resource, access path, or absence was found by static inspection
  of the checked-out source snapshots.
- **Target decision:** the `tenantKey`, isolation mechanism, and named negative test
  state what implementation must enforce; they do not claim that the current MSC
  application is multi-tenant or that the product isolation tests exist yet.

The evidence snapshot is 2026-08-15:

| Repository | Inspected commit |
|---|---|
| `MSC-Event-Backend` | `4a96266f13f43b43fc76292193924d491bdf8673` |
| `MSC-Event-Frontend` | `b42ab84f2123a4860f4dbc9ad1c5a24f4d1b14cb` |
| `MSC-Event-CLI` | `2e75b722216d3d72a2ea65654f15084bb275f2d7` |
| `MSC-Event-Signing-Terminal` | `8f92b42230dd2e04cee029a748cb428db1e6eedf` |

Inspection covered backend schema/migrations, route registration and handlers, object
storage, workers/schedules, infrastructure source and operational scripts; frontend
API clients and browser state; CLI SQLite state, approval/outbox workers, wrappers and
support operations; and signing-terminal API/local state/evidence generation. Source
repositories were read-only. The CLI and signing-terminal worktrees already contained
uncommitted package-manifest changes; those changes were not used as resource evidence
and were not modified. Nested CLI worktrees and generated/dependency outputs such as
`.git`, `node_modules`, `dist`, `cdk.out`, `__pycache__`, and TypeScript build metadata
were excluded from factual discovery.

This is not exhaustive runtime truth. No production account, deployed database,
bucket contents, log group contents, provider console, secret, untracked external
resource, other branch, or private repository was inspected. Static absence records
therefore mean “not defined in the inspected source,” not “cannot exist in an account.”
In particular, no persistent PostgreSQL view, external queue declaration, or custom
application metric emission was found. Those absences have inventory records so the
categories cannot disappear silently.

Runtime-generated instances are represented by their stable resource family and key
contract, not by enumerating transient customer data. This includes S3 objects,
presigned URLs, upload/session tokens, outbox/job rows, worker work units, cache keys,
audit events and log/metric emissions. The inventory records both the shared global
container where appropriate and the tenant-owned object/payload namespace inside it.

## Inventory model

Every resource record has a stable `id`, `category`, current source/status, accountable
`owner`, access paths, expected isolation mechanism and a named test from the matrix.
Its classification is exactly one of:

- `tenant`, with a required `tenantKey` describing direct or inherited ownership; or
- `global`, with a required rationale explaining why tenant ownership is not
  applicable and what data is forbidden from entering the resource.

The inventory includes all 42 backend PostgreSQL tables and all nine discovered CLI
SQLite tables individually. It lists the full 64-file SQL migration series, the one
migration-only `to_base36` helper, and the verified absence of persistent views. Route
families preserve every current access surface while avoiding a false claim that each
handler is independently isolated: public registration/upload/legal/signing; admin
events/config, entries/finance/dashboard, documents/exports, mail, signing/inspection,
marshals, IAM/support diagnostics; and the global payload-free health endpoint.

The remaining records cover export formats and generated PDFs, presigning helpers,
both bucket containers and every discovered object-key family, database and local
outboxes, schedules/workers and their payload boundaries, browser/database caches,
idempotency keys, audit/log resources, metrics absence, and support/maintenance tools.

Important current gaps made explicit by the catalog include:

- event is the highest backend business separator; no `organization_id` exists;
- mutable app config, people, templates, signing devices and marshal people are
  currently global;
- object keys use `eventId` but no organization prefix;
- scheduled backend workers receive no tenant payload and discover work globally;
- frontend event caches and browser keys have no trusted organization namespace;
- CLI approval/outbox state and action payloads contain no organization identifier;
  and
- current support repair/restore scripts can address rows and object keys without a
  tenant boundary.

## Two-tenant fixture

The fixture uses reserved synthetic UUIDs and `.invalid` hosts only. Tenant A and B
have distinct server-issued organization, event, entry, document, export and outbox
IDs, while human-readable event codes, start numbers, email local parts and object leaf
names deliberately collide. That combination proves isolation rather than accidental
uniqueness.

Before each negative attempt, the implementing test snapshots both tenants' relevant
database rows, object listings/hashes, job/outbox states, cache values and audit counts.
Afterward it asserts both confidentiality and integrity:

> A foreign identifier yields no tenant data and no state change in either tenant.

An allowed denial audit may be appended only to the requester's tenant when it contains
no foreign payload. A `403` by itself is insufficient evidence if a row, object, job,
cache or mail side effect occurred.

## Isolation-test matrix

The machine-readable matrix is the source of test IDs and assertions. It covers:

| Surface | Named negative test | Essential assertion |
|---|---|---|
| Collection reads/aggregates | `ISO-READ-COLLECTION` | Tenant B rows, counts and aggregates are absent. |
| Direct foreign IDs | `ISO-READ-FOREIGN-ID` | Not-found-equivalent response, no disclosure or state change. |
| Mutations and foreign parents | `ISO-WRITE-FOREIGN-ID` | Zero affected foreign rows and no side effects. |
| Export create/poll/download | `ISO-EXPORT-FOREIGN-ID` | No foreign rows, job claim, object or URL. |
| Documents/signing | `ISO-DOCUMENT-FOREIGN-ID` | No foreign evidence generation, read or mutation. |
| Presigned upload/download | `ISO-PRESIGNED-URL-FOREIGN-KEY` | No foreign URL and no object operation. |
| Workers/jobs | `ISO-BACKGROUND-FOREIGN-PAYLOAD` | Missing/mismatched tenant context fails before mutation. |
| Browser/process caches | `ISO-CACHE-NAMESPACE` | Tenant switch cannot reuse data or authority. |
| Idempotency/deduplication | `ISO-IDEMPOTENCY-NAMESPACE` | Same key in A and B does not collide. |
| Audit/metrics/support evidence | `ISO-AUDIT-METRIC-SCOPE` | Tenant queries and emitted dimensions do not leak. |
| CLI/maintenance/signing tools | `ISO-SUPPORT-TOOL-FOREIGN-ID` | Foreign targets are neither printed nor changed. |
| Deliberately global resources | `ISO-GLOBAL-NONINTERFERENCE` | No tenant payload or cross-tenant interference. |
| Migrations/backfills | `ISO-MIGRATION-TENANT-SCOPE` | Explicit ownership reconciliation for both tenants. |
| Inventory governance | `ISO-DOD-INVENTORY-COVERAGE` | Missing classification/test/global rationale fails CI. |

The matrix specifies the test contract; product tests remain a follow-up because this
repository contains no application implementation or deployable two-tenant runtime.

## Definition of Done

Every change that introduces or makes a resource tenant-capable is complete only when:

1. the resource has a versioned inventory entry before merge;
2. the entry names its tenant key, ownership path and expected isolation mechanism, or
   gives an explicit reviewed global rationale;
3. a negative two-tenant isolation test is implemented under a stable matrix ID;
4. deliberate tenant-B identifiers used from tenant A return no data and cause no
   state change across rows, objects, jobs, caches, mail and audit side effects; and
5. the inventory validator and the owning product's negative test pass in CI.

This rule applies to tables, views, functions that access data, migrations, routes,
exports, object keys, presigned URLs, queues/outboxes, schedules/workers/payloads,
caches, idempotency keys, audit/log/metric records and support tools. A schema or API
change without both the inventory entry and negative test is not done and is not
releasable. Deliberately global resources are not exempt from tests; they use the
global non-interference contract and must remain free of tenant-owned payload.

## Running the repository checks

From the repository root:

```text
python3 scripts/validate_tenant_inventory.py
python3 scripts/check_relative_markdown_links.py
git diff --check
```

These checks validate the catalog and links only. They are not evidence that the
future product-level isolation matrix has executed.
