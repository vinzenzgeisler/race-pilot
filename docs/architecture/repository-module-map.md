# Repository and module map

This map separates observed repositories from accepted target ownership. Paths under
`/home/node/.openclaw/workspace` are read-only evidence paths from the 2026-08-15
snapshot; they are not links or dependencies of this repository.

Status terms follow the definitions in the [repository README](../../README.md).

## Current repository map

| Concern | Current repository/module | Status and evidence |
|---|---|---|
| Backend API and domain behavior | `MSC-Event-Backend/api/src/{domain,routes,docs,mail,http,db}` | **Current fact:** TypeScript API/domain implementation. Evidence: `MSC-Event-Backend/package.json` declares the `api` workspace; `MSC-Event-Backend/api/src/handler.ts` routes HTTP requests; the named source directories contain domain and service logic. |
| Database schema and migrations | `MSC-Event-Backend/api/src/db`, `MSC-Event-Backend/api/migrations` | **Current fact:** Drizzle/PostgreSQL schema and SQL migrations. The schema begins with `event` and has no organization/tenant table. |
| Workers | `MSC-Event-Backend/api/src/jobs` | **Current fact:** `emailWorker.ts`, `privacyRetentionWorker.ts`, and `paymentReminderScheduler.ts` exist. `infra/lib/stacks/api-stack.ts` currently deploys the email and retention handlers as scheduled Lambda functions; the payment reminder module exists but is not instantiated as a separate function in that stack. |
| Product frontend | `MSC-Event-Frontend/src` | **Current fact:** React/Vite public registration, admin, signing, inspection, communication, exports, and marshal UI. Evidence: `MSC-Event-Frontend/package.json`, `src/app/router.tsx`, `src/pages`, and `src/services`. |
| AWS infrastructure | `MSC-Event-Backend/infra` | **Current fact:** AWS CDK config and Auth, Data, Storage, API, and Migration Runner stacks. Evidence: `infra/bin/app.ts` and `infra/lib/stacks/*.ts`. It currently packages API and worker deployments together. |
| Frontend deployment automation | `MSC-Event-Frontend/.github/workflows/ci-cd.yml`, `vercel.json`, `scripts/cleanup-vercel-preview-deployments.mjs` | **Current fact:** Vercel-specific build/deploy/promotion and preview cleanup. |
| Backend deployment automation | `MSC-Event-Backend/.github/workflows/ci-cd.yml`, `scripts` | **Current fact:** AWS credentials, CDK synth/deploy/destroy, RDS lifecycle, migration, and seed automation. |
| Marketing site | `racepilot/app`, `racepilot/components` | **Current fact:** separate Next.js site containing product, Community, Cloud, pricing, contact, and MSC reference copy. It contains no product API or control plane. |
| Architecture coordination | `race-pilot` (this repository) | **Current fact:** documentation-only issue #34 baseline. No production module or deployment exists here. |
| Community distribution | None found | **Current fact:** no Docker Compose, Helm chart, container build, or generic self-host bundle was found in the inspected repositories. |
| Cloud control plane | None found | **Current fact:** no organization lifecycle, tenant/domain registry, subscription, billing, or entitlement module was found in the inspected repositories. |

The planning evidence is consistent with these observations:
`reports/racepilot-projektmasterplan-2026-08-13.md` lines 30–48 describe the
existing AWS backend, React/Vite frontend, marketing site, and the missing tenant and
SaaS foundations. `SAAS_CONCEPT.md` identifies multi-tenant deployment, Docker, and
billing as future work rather than implemented modules.

## Target repository and module ownership

These are **target decisions**, not claims that repository renames, extraction, or
implementation have happened.

| Concern | Target repository/module assignment | Visibility | Migration obligation |
|---|---|---|---|
| Architecture, cross-repository contracts, and decision index | `vinzenzgeisler/race-pilot` (`docs`, future versioned contracts only after a separate implementation decision) | Public | Keep this repository documentation-first for issue #34. Do not place speculative product code here. |
| Backend domain core and HTTP application | Current `MSC-Event-Backend/api`, renamed or transferred to a public RacePilot product repository later | Public | Split internal modules into `core` (domain/use cases/ports), `application` (HTTP/context), and provider adapters. Remove MSC identity and Cloud provider dependencies from `core`. |
| Database schema and migrations | Same public backend product repository | Public | Add organization ownership and tenant-safe migrations; Community and Cloud consume the same schema contract, with mode-specific deployment profiles. |
| Domain workers | Same public backend product repository under an explicit `workers` boundary | Public | Preserve shared job behavior; require server-issued organization context and provider ports. Do not copy worker logic into the Cloud control plane. |
| Product frontend | Current `MSC-Event-Frontend`, renamed or transferred to a public RacePilot product repository later | Public | Consume a server bootstrap and shared API contracts. Remove client-owned authority and MSC defaults. One build serves organizations; no per-customer build. |
| Community deployment and infrastructure examples | A public `community` deployment module/repository owned by RacePilot Core maintainers; physical repository creation is a follow-up | Public | Compose first: web, API, workers, PostgreSQL, and reference OIDC/SMTP/storage adapters. Include upgrades, migrations, backup/restore, and health checks. |
| Cloud runtime adapters | Private Cloud runtime/infrastructure repository, depending only on public ports/contracts | Private | Move production AWS/Vercel assembly and operational policy out of the shared core boundary. A provider adapter may remain public when reusable and secret-free. |
| Cloud control plane | Private `racepilot-cloud-control-plane` repository/module | Private | Implement tenant and membership lifecycle, domain mapping, subscriptions/entitlements, billing integration, platform support, and audit. It calls public product contracts; it does not own copied domain logic. |
| Marketing | Current `racepilot` repository | Public by default; separate deployable | Keep independent of product uptime and authentication. Claims about Community/Cloud availability must track release evidence. |

Names for not-yet-created physical repositories are allocation labels. Creating or
renaming them requires a separate, reviewed change. Until then, directory-level
boundaries in the existing backend and frontend are authoritative.

## Dependency direction

The allowed target dependency direction is:

```text
product frontend -> public API/bootstrap contracts
HTTP application + workers -> shared domain core -> public ports
community assembly -> public application/workers + community adapters
cloud runtime assembly -> public application/workers + cloud adapters
private control plane -> public contracts
marketing site -> no product runtime dependency
```

The domain core must not depend on a deployment assembly, private control plane, or
marketing site. Community must not depend on private modules. Cloud-only operational
code may depend on public contracts but may not redefine domain behavior.

## Evidence scope

The factual mapping was produced from the following repository snapshots. Repository
and commit links make the source snapshot reproducible without access to the local
inspection workspace.

| Repository | Inspected ref | Inspected full SHA | Stable source |
|---|---|---|---|
| [`vinzenzgeisler/MSC-Event-Backend`](https://github.com/vinzenzgeisler/MSC-Event-Backend) | `fix/editor-class-filter` | `4a96266f13f43b43fc76292193924d491bdf8673` | [Inspected commit](https://github.com/vinzenzgeisler/MSC-Event-Backend/commit/4a96266f13f43b43fc76292193924d491bdf8673) |
| [`vinzenzgeisler/MSC-Event-Frontend`](https://github.com/vinzenzgeisler/MSC-Event-Frontend) | `feat/marshal-planning-refinements` | `b42ab84f2123a4860f4dbc9ad1c5a24f4d1b14cb` | [Inspected commit](https://github.com/vinzenzgeisler/MSC-Event-Frontend/commit/b42ab84f2123a4860f4dbc9ad1c5a24f4d1b14cb) |
| [`vinzenzgeisler/racepilot`](https://github.com/vinzenzgeisler/racepilot) | `main` | `33364c9d8dd0c5cfe6c53e987e876f55439dd39a` | [Inspected commit](https://github.com/vinzenzgeisler/racepilot/commit/33364c9d8dd0c5cfe6c53e987e876f55439dd39a) |

The sources were inspected at these local read-only evidence paths:

- `/home/node/.openclaw/workspace/MSC-Event-Backend`
- `/home/node/.openclaw/workspace/MSC-Event-Frontend`
- `/home/node/.openclaw/workspace/racepilot`
- `/home/node/.openclaw/workspace/reports/racepilot-projektmasterplan-2026-08-13.md`
- `/home/node/.openclaw/workspace/SAAS_CONCEPT.md`

The more granular evidence and search limitations are recorded in the
[current coupling inventory](current-couplings.md).
