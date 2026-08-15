# ADR 0001: Editions, shared core, and deployment modes

- Status: Accepted
- Date: 2026-08-15
- Scope: Architecture decision only; implementation is pending
- Related: [repository and module map](../architecture/repository-module-map.md),
  [current coupling inventory](../architecture/current-couplings.md), and
  [required CI coverage](../architecture/ci-coverage.md), and the
  [tenant resource inventory and isolation-test contract](../security/tenant-resource-inventory.md)

## Context

**Current fact:** The existing application is split across an MSC backend, an MSC
product frontend, and a RacePilot marketing site. The backend has event-scoped data
but no organization or tenant model. It also contains AWS infrastructure and workers.
The detailed evidence is recorded in the
[repository and module map](../architecture/repository-module-map.md) and
[coupling inventory](../architecture/current-couplings.md).

**Target decision:** RacePilot is one product with a shared domain core. It supports
two deployment modes without duplicating domain behavior or maintaining edition
branches.

## Decision

### Edition and deployment boundaries

| Property | Community | Cloud |
|---|---|---|
| Deployment mode | `community` | `cloud` |
| Operation | Self-hosted by the operator | Managed by RacePilot |
| Tenancy | Single tenant; exactly one organization per installation | Multi-tenant; many isolated organizations |
| Events | Many for the one organization | Many per organization |
| Domain core | Complete shared core | The same complete shared core |
| Identity | Generic OIDC contract; documented reference provider | Managed identity adapter plus organization memberships |
| Database | Operator-owned PostgreSQL | Managed PostgreSQL with mandatory tenant isolation |
| Mail and object storage | Operator-configured adapters | Managed adapters and tenant-scoped configuration |
| Billing and subscription | Free to use; no RacePilot product license fee or subscription is required | Subscription lifecycle and entitlements are Cloud concerns |
| Operations | Updates, backups, monitoring, and recovery are operator responsibilities | RacePilot is responsible for platform operations |

Community is not a reduced or separate implementation of the business processes.
Optional paid consulting, support, hosting/operations, or other services from
RacePilot or third parties are separate from the free Community product license.
Cloud sells managed operation and Cloud-only platform services, not a fork of the
domain core.

### Shared public domain core

**Target decision:** The public product boundary contains domain entities, use cases,
validation, pricing, registration, participants and vehicles, documents and signing,
technical inspection, marshals, communication orchestration, exports, and the ports
used to reach identity, mail, storage, persistence, queues, and time.

The domain core must not import a Cloud control-plane SDK or a concrete AWS, Vercel,
Stripe, Cognito, SES, S3, or RDS client. Deployment-specific modules implement the
ports and assemble the process. An adapter may be public or private; its contract and
the core behavior remain public and provider-neutral.

Background work is part of the same product boundary. Queue and outbox messages for
tenant-owned work must include an immutable server-issued `organizationId`; workers
must reconstruct and enforce the same request context as synchronous API operations.

### Public and private modules

| Boundary | Visibility | Contents |
|---|---|---|
| Shared backend core and API contracts | Public | Domain model, use cases, ports, HTTP contracts, tenant-context contract, migrations, tests |
| Shared product web application | Public | Public event portal, admin workflows, design system, server-bootstrap consumer |
| Shared workers | Public | Mail/outbox, document, export, retention, and other domain job handlers using public ports |
| Community distribution | Public | Container images/build recipes, Compose configuration, example OIDC/SMTP/storage setup, migrations, backup/restore documentation |
| Community infrastructure examples | Public | Reverse-proxy and local deployment examples without operator secrets |
| Cloud control plane | Private | Organization lifecycle, subscriptions, billing integration, domain automation, support and platform administration |
| Cloud production infrastructure and operations | Private | Managed tenant routing, production IaC, observability, backups, incident and support automation |
| Marketing site | Public by default, operationally separate | Product information; never a runtime dependency of the product |

The concrete current and target repository assignments are in the
[repository and module map](../architecture/repository-module-map.md). Public does not
mean that secrets, customer data, production state, or private operational runbooks
are published.

### Server-authoritative mode, tenant, and capabilities

**Target decision:** Deployment mode and capabilities are resolved and supplied by
the server. Browser values are presentation hints only and are never authority.

At process startup, trusted server configuration fixes the deployment mode:

- A Community installation accepts only `community` and binds all tenant-owned work
  to its single server-configured organization.
- A Cloud deployment accepts only `cloud`. Public requests resolve an organization
  from a verified host/domain mapping. Authenticated requests resolve it from the
  authenticated identity, membership, and server-side organization selection.

The server creates a request/job context containing at least `deploymentMode`,
`organizationId`, authenticated subject (when present), permissions, subscription
entitlements, and effective capabilities. Repository and service methods operating on
tenant data require that context. Database queries, object keys, cache keys, messages,
and audit records are scoped with its server-resolved organization.

The server may expose a bootstrap projection to the web application containing mode,
branding, organization, event, and effective capabilities. It must ignore or reject a
client-supplied deployment mode, organization ID, capability, entitlement, role, or
permission when making an authorization decision. This includes headers, query
parameters, local storage, cookies not protected by the server, request bodies, and
mutated runtime JavaScript configuration. Every protected action is checked again at
the API or worker boundary.

Unknown hosts, mismatched membership, missing tenant context, or ambiguous tenant
resolution fail closed. Cloud cross-tenant access is denied even when an object has a
globally unique ID.

### Permissions, entitlements, and capabilities

**Target decision:** Permissions and subscription entitlements are separate concepts.

- A **permission** answers whether this actor may perform an action in this
  organization, based on server-side identity, membership, and role/policy.
- An **entitlement** answers whether the organization's Cloud subscription includes a
  commercial or service-level feature. It never grants an actor access.
- A **capability** is the server-computed effective availability used by application
  flows. It can depend on deployment support, validated configuration, operational
  state, and—only in Cloud—an entitlement.

For a protected feature the server requires both the necessary permission and the
effective capability. In Cloud it also validates the relevant entitlement while
computing that capability. Community has no paid subscription gate; capabilities may
still be unavailable when a required local adapter is not configured. A UI hiding a
button is not enforcement.

### Extension policy

**Target decision:** Customer-specific forks, permanent customer branches, customer
builds, and copied editions are explicitly rejected as extension mechanisms. Changes
must use one of these paths:

1. configuration or validated branding;
2. a versioned public port/adapter or event contract;
3. a reusable, reviewed domain capability available from the shared core; or
4. a Cloud-only control-plane feature that does not duplicate domain logic.

Consulting may fund an extension, but the resulting domain behavior follows the same
shared path. Unsupported requests are declined or productized; they do not create a
fork.

### CI is a release boundary

**Target decision:** A change to shared behavior is releasable only after the relevant
core processes pass in both deployment modes. The required test matrix, owners, and
gates are specified in [required CI coverage](../architecture/ci-coverage.md).

**Current fact:** That matrix is not active today. Existing workflows provide useful
backend tests/builds and frontend typecheck/build checks, but they are not a
Community/Cloud mode matrix. Documentation of the target must not be used as evidence
that the tests ran.

## Consequences

- Domain changes are implemented and reviewed once, with mode-specific assembly and
  adapters around them.
- Cloud can remain operationally private without making core processes proprietary.
- Tenant context becomes mandatory even in Community, where it deterministically
  identifies the only organization; this keeps core call signatures identical.
- The current global event model, mutable browser runtime configuration, MSC defaults,
  provider imports, and non-tenant storage keys require migration work.
- A repository rename or monorepo move is not a prerequisite. Enforced module
  boundaries and contracts come first.

## Follow-up obligations

Before Community is called distributable:

- introduce the organization and server context contracts;
- extract provider-neutral identity, mail, storage, database, and queue ports;
- remove or migrate MSC-specific defaults and assets;
- provide and test the Community distribution, migrations, backup, restore, and
  generic OIDC configuration; and
- implement the Community columns of the CI matrix.

Before Cloud is called multi-tenant:

- implement the private control plane and authoritative host/membership resolution;
- add organization scoping to schema, queries, storage, messages, caches, and audit;
- add defense-in-depth database isolation and negative cross-tenant tests;
- replace the current public database target profile with an approved private profile;
- implement subscription entitlements independently of permissions; and
- implement the Cloud columns of the CI matrix, restore tests, and operational gates.

Every newly tenant-capable resource is also subject to the versioned inventory and
negative-test Definition of Done in the
[tenant isolation contract](../security/tenant-resource-inventory.md#definition-of-done).
