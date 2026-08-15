#!/usr/bin/env python3
"""Validate the versioned tenant inventory and its isolation fixtures."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SECURITY = ROOT / "docs" / "security"
INVENTORY_PATH = SECURITY / "tenant-resource-inventory.v1.json"
MATRIX_PATH = SECURITY / "tenant-isolation-test-matrix.v1.json"
FIXTURE_PATH = SECURITY / "fixtures" / "two-tenant.v1.json"

REQUIRED_CATEGORIES = {
    "database-table", "database-view", "database-function", "database-migration",
    "http-public", "http-admin", "export", "presigned-url", "object-storage",
    "queue-outbox", "scheduler-worker", "worker-payload", "cache",
    "idempotency-key", "audit-log", "metric", "support-tool",
}
REQUIRED_DIMENSIONS = {
    "reads", "writes", "exports", "documents-presigned-links",
    "background-jobs", "foreign-identifiers",
}
RESOURCE_ID = re.compile(r"^[a-z0-9]+(?:[.-][a-z0-9]+)*$")
TEST_ID = re.compile(r"^ISO-[A-Z0-9]+(?:-[A-Z0-9]+)*$")
MIGRATION_NAME = re.compile(r"^\d{4}_[a-z0-9_]+\.sql$")

# Version 1 is a closed, source-reconciled snapshot. These embedded manifests make
# completeness enforceable in dependency-free CI without checking out sibling repos.
EXPECTED_EVIDENCE_COMMITS = {
    "MSC-Event-Backend": "4a96266f13f43b43fc76292193924d491bdf8673",
    "MSC-Event-Frontend": "b42ab84f2123a4860f4dbc9ad1c5a24f4d1b14cb",
    "MSC-Event-CLI": "43b8dbb1a101c55355e2f55da57cac51bd26ad7d",
    "MSC-Event-Signing-Terminal": "8f92b42230dd2e04cee029a748cb428db1e6eedf",
}
EXPECTED_BACKEND_TABLE_IDS = frozenset("""
db.table.event db.table.app-config db.table.public-rate-limit db.table.class
db.table.person db.table.geo-location-cache db.table.vehicle db.table.entry
db.table.registration-group db.table.registration-group-email-verification
db.table.public-entry-submission db.table.consent-evidence
db.table.data-subject-request db.table.invoice db.table.event-pricing-rule
db.table.class-pricing-rule db.table.invoice-payment db.table.audit-log
db.table.technical-inspector-assignment db.table.technical-inspection-decision
db.table.email-outbox db.table.email-delivery db.table.mail-attachment-upload
db.table.email-outbox-attachment db.table.email-template
db.table.email-template-version db.table.document db.table.signing-device-session
db.table.signing-session db.table.marshal-person
db.table.marshal-event-participation db.table.marshal-event-day
db.table.marshal-section db.table.marshal-post db.table.marshal-day-assignment
db.table.marshal-qualification db.table.marshal-training-session
db.table.marshal-training-participant db.table.marshal-import-run
db.table.export-job db.table.vehicle-image-upload db.table.document-generation-job
""".split())
EXPECTED_CLI_SQLITE_IDS = frozenset("""
db.sqlite.approval-records db.sqlite.approval-audit db.sqlite.durable-outbox
db.sqlite.durable-outbox-audit db.sqlite.webauthn-credentials
db.sqlite.webauthn-challenges db.sqlite.webauthn-registration-challenges
db.sqlite.passkey-bootstrap-grants db.sqlite.passkey-bootstrap-audit
""".split())
EXPECTED_MIGRATIONS = tuple("""
0000_init.sql 0001_phase3.sql 0002_phase4_documents.sql
0003_phase4_email_templates.sql 0004_phase4_outbox_hardening.sql
0005_phase4_checkin.sql 0006_phase4_email_template_seed.sql
0007_phase5_event_pricing_exports.sql 0008_phase5_workflow_gaps.sql
0009_phase6_upload_and_outbox.sql 0010_phase7_contract_readiness.sql
0011_phase8_admin_notes_and_confirmation.sql
0012_phase9_registration_verify_link.sql
0013_phase10_public_pricing_and_contacts.sql 0014_phase11_entry_soft_delete.sql
0015_payment_reminder_amount.sql
0016_lifecycle_accepted_open_payment_driver_note.sql
0017_lifecycle_rejected_driver_note.sql 0018_entry_deleted_by_display.sql
0019_entry_backup_vehicle.sql 0020_entry_active_driver_email_unique.sql
0021_registration_group_batch_and_verify.sql
0022_privacy_consent_and_retention_foundations.sql
0023_person_policy_flags_backfill.sql
0024_group_verification_backfill_from_entry_tokens.sql
0025_drop_entry_email_verification.sql
0026_mail_template_html_text_and_send_audit_foundation.sql
0027_email_template_version_status.sql 0028_mail_additional_template_keys.sql
0029_remove_smoke_tests_template.sql 0030_disable_preselection_template.sql
0031_email_design_template_refresh.sql
0032_campaign_template_additional_text_fields.sql
0033_mail_add_followup_and_confirmation_templates.sql
0034_mail_umlaut_normalization.sql 0035_mail_add_codriver_info_template.sql
0038_entry_confirmation_pdf_pipeline.sql 0039_codriver_info_restore_copy.sql
0040_mail_copy_informative_event_tone.sql
0041_codriver_info_professional_copy.sql
0042_event_entry_confirmation_config.sql 0043_app_config.sql
0044_entry_orga_code.sql 0045_entry_orga_code_base36.sql
0046_vehicle_image_upload_security.sql
0047_public_consent_and_verification_hardening.sql
0048_seed_email_confirmation_reminder.sql
0049_public_legal_texts_and_rate_limit.sql 0050_person_country.sql
0051_class_allows_codriver.sql 0052_geo_location_cache.sql
0053_signing_sessions.sql 0054_signing_session_timeout.sql
0055_doublestarter_migration_notice.sql 0056_event_payment_due_at.sql
0057_class_registration_closed.sql
0058_technical_inspection_access_and_history.sql
0059_backup_vehicle_technical_inspection.sql 0060_technical_inspector_note.sql
0061_backup_inspection_note.sql 0062_waiver_v3_consent_hashes.sql
0063_waiver_signed_mail_template.sql 0064_marshal_management.sql
0065_fix_orphaned_registration_groups.sql
""".split())
EXPECTED_OTHER_RESOURCE_IDS = frozenset("""
db.views.none-found db.function.to-base36 db.migrations.0000-0065
http.public.registration http.public.uploads http.public.legal-brand-assets
http.public.signing-device http.admin.events-config
http.admin.entries-finance-dashboard http.admin.documents-exports
http.admin.communication http.admin.signing-inspection http.admin.marshals
http.admin.iam-support-diagnostics http.health export.entries-csv-family
export.document-pdf-family presign.documents-download
presign.assets-upload-download s3.bucket.assets s3.bucket.documents
s3.prefix.vehicle-images s3.prefix.mail-attachments s3.prefix.documents
s3.prefix.exports s3.prefix.signing s3.prefix.mail-static-assets
queue.external.none-found queue.backend-email-outbox queue.cli-durable-outbox
scheduler.email-worker scheduler.privacy-retention-worker
scheduler.dev-cost-cleanup scheduler.payment-reminder-module
scheduler.cli-host-and-cron payload.backend-scheduled-workers
payload.backend-dev-cost-cleanup payload.cli-approved-actions
payload.cli-telegram-approval-notification cache.backend-geolocation
cache.frontend-event-context cache.frontend-browser-state
cache.signing-terminal-browser-state cache.cli-response.none
idempotency.public-entry-submission idempotency.email-outbox
idempotency.cli-approval-and-outbox audit.backend-audit-log
audit.backend-signing-evidence audit.cli-approval-outbox
audit.cli-passkey-bootstrap audit.runtime-cloudwatch-logs
metric.custom.none-found support.cli-readonly-admin-query
support.cli-approved-mutations support.backend-object-repair-restore
support.backend-migration-seed support.signing-terminal
""".split())
EXPECTED_RESOURCE_IDS = (
    EXPECTED_BACKEND_TABLE_IDS | EXPECTED_CLI_SQLITE_IDS | EXPECTED_OTHER_RESOURCE_IDS
)
EXPECTED_TEST_IDS = frozenset("""
ISO-READ-COLLECTION ISO-READ-FOREIGN-ID ISO-WRITE-FOREIGN-ID
ISO-EXPORT-FOREIGN-ID ISO-DOCUMENT-FOREIGN-ID
ISO-PRESIGNED-URL-FOREIGN-KEY ISO-BACKGROUND-FOREIGN-PAYLOAD
ISO-CACHE-NAMESPACE ISO-IDEMPOTENCY-NAMESPACE ISO-AUDIT-METRIC-SCOPE
ISO-NOTIFICATION-FOREIGN-PAYLOAD ISO-SUPPORT-TOOL-FOREIGN-ID
ISO-GLOBAL-NONINTERFERENCE ISO-MIGRATION-TENANT-SCOPE
ISO-DOD-INVENTORY-COVERAGE
""".split())


class ValidationError(Exception):
    pass


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValidationError(f"{path.relative_to(ROOT)}: {error}") from error
    if not isinstance(value, dict):
        raise ValidationError(f"{path.relative_to(ROOT)}: root must be an object")
    return value


def nonempty_string(value: Any, field: str, minimum: int = 1) -> str:
    if not isinstance(value, str) or len(value.strip()) < minimum:
        raise ValidationError(f"{field}: expected a non-empty string of at least {minimum} characters")
    return value.strip()


def string_list(value: Any, field: str) -> list[str]:
    if not isinstance(value, list) or not value:
        raise ValidationError(f"{field}: expected a non-empty array")
    result = []
    for index, item in enumerate(value):
        result.append(nonempty_string(item, f"{field}[{index}]"))
    return result


def validate_fixture(fixture: dict[str, Any]) -> None:
    if fixture.get("schemaVersion") != 1 or fixture.get("syntheticOnly") is not True:
        raise ValidationError("two-tenant fixture must be schemaVersion 1 and syntheticOnly=true")
    organizations = fixture.get("organizations")
    if not isinstance(organizations, list) or len(organizations) != 2:
        raise ValidationError("two-tenant fixture must contain exactly two organizations")
    seen: dict[str, set[str]] = {}
    required = {
        "organizationId", "slug", "host", "adminSubject", "eventId", "entryId",
        "documentId", "exportJobId", "outboxId", "objectPrefix", "idempotencyKey",
        "approvalActionId", "approvalPayloadReference",
    }
    for index, organization in enumerate(organizations):
        if not isinstance(organization, dict) or set(organization) != required:
            raise ValidationError(f"fixture organizations[{index}] must contain exactly {sorted(required)}")
        for field in required:
            value = nonempty_string(organization[field], f"fixture organizations[{index}].{field}")
            seen.setdefault(field, set()).add(value)
        expected_prefix = f"tenant/{organization['organizationId']}/"
        if organization["objectPrefix"] != expected_prefix:
            raise ValidationError(f"fixture organizations[{index}].objectPrefix must be {expected_prefix}")
        if not organization["host"].endswith(".invalid"):
            raise ValidationError(f"fixture organizations[{index}].host must use the reserved .invalid domain")
    colliding_fields = {"idempotencyKey"}
    for field, values in seen.items():
        if field in colliding_fields:
            if len(values) != 1:
                raise ValidationError(
                    f"fixture field {field} must intentionally collide between organizations"
                )
            continue
        if len(values) != 2:
            raise ValidationError(f"fixture field {field} must be unique between organizations")
    string_list(fixture.get("invariants"), "fixture invariants")


def validate_matrix(matrix: dict[str, Any]) -> set[str]:
    if matrix.get("schemaVersion") != 1:
        raise ValidationError("isolation matrix schemaVersion must be 1")
    if matrix.get("fixture") != "fixtures/two-tenant.v1.json":
        raise ValidationError("isolation matrix must reference fixtures/two-tenant.v1.json")
    declared_dimensions = set(string_list(matrix.get("requiredDimensions"), "matrix requiredDimensions"))
    if declared_dimensions != REQUIRED_DIMENSIONS:
        raise ValidationError(f"matrix requiredDimensions must equal {sorted(REQUIRED_DIMENSIONS)}")
    tests = matrix.get("tests")
    if not isinstance(tests, list) or not tests:
        raise ValidationError("matrix tests must be a non-empty array")
    test_ids: set[str] = set()
    covered_dimensions: set[str] = set()
    for index, test in enumerate(tests):
        prefix = f"matrix tests[{index}]"
        if not isinstance(test, dict):
            raise ValidationError(f"{prefix}: expected object")
        test_id = nonempty_string(test.get("id"), f"{prefix}.id")
        if not TEST_ID.fullmatch(test_id) or test_id in test_ids:
            raise ValidationError(f"{prefix}.id: invalid or duplicate test ID {test_id!r}")
        test_ids.add(test_id)
        dimensions = set(string_list(test.get("dimensions"), f"{prefix}.dimensions"))
        if not dimensions <= REQUIRED_DIMENSIONS:
            raise ValidationError(f"{prefix}.dimensions contains undeclared values")
        covered_dimensions.update(dimensions)
        nonempty_string(test.get("actor"), f"{prefix}.actor", 8)
        nonempty_string(test.get("attempt"), f"{prefix}.attempt", 12)
        assertions = string_list(test.get("assertions"), f"{prefix}.assertions")
        if len(assertions) < 2:
            raise ValidationError(f"{prefix}.assertions must contain at least two assertions")
    if covered_dimensions != REQUIRED_DIMENSIONS:
        raise ValidationError(f"matrix test coverage must equal {sorted(REQUIRED_DIMENSIONS)}")
    if test_ids != EXPECTED_TEST_IDS:
        missing = sorted(EXPECTED_TEST_IDS - test_ids)
        unexpected = sorted(test_ids - EXPECTED_TEST_IDS)
        raise ValidationError(
            f"matrix test manifest mismatch; missing={missing}, unexpected={unexpected}"
        )
    return test_ids


def validate_inventory(inventory: dict[str, Any], test_ids: set[str]) -> int:
    if inventory.get("schemaVersion") != 1:
        raise ValidationError("inventory schemaVersion must be 1")
    nonempty_string(inventory.get("inventoryId"), "inventoryId")
    nonempty_string(inventory.get("snapshotDate"), "snapshotDate")
    nonempty_string(inventory.get("scope"), "scope", 20)
    repositories = inventory.get("evidenceRepositories")
    if not isinstance(repositories, list) or len(repositories) != 4:
        raise ValidationError("inventory must name all four evidence repositories")
    evidence_commits: dict[str, str] = {}
    for index, repository in enumerate(repositories):
        if not isinstance(repository, dict):
            raise ValidationError(f"evidenceRepositories[{index}] must be an object")
        name = nonempty_string(repository.get("name"), f"evidenceRepositories[{index}].name")
        commit = nonempty_string(repository.get("commit"), f"evidenceRepositories[{index}].commit")
        if not re.fullmatch(r"[0-9a-f]{40}", commit):
            raise ValidationError(f"evidenceRepositories[{index}].commit must be a full SHA")
        nonempty_string(repository.get("path"), f"evidenceRepositories[{index}].path")
        if name in evidence_commits:
            raise ValidationError(f"evidenceRepositories contains duplicate name {name!r}")
        evidence_commits[name] = commit
    if evidence_commits != EXPECTED_EVIDENCE_COMMITS:
        raise ValidationError("evidenceRepositories must match the source-reconciled v1 commits")
    declared_categories = set(string_list(inventory.get("requiredCategories"), "requiredCategories"))
    if declared_categories != REQUIRED_CATEGORIES:
        raise ValidationError(f"requiredCategories must equal {sorted(REQUIRED_CATEGORIES)}")

    resources = inventory.get("resources")
    if not isinstance(resources, list) or not resources:
        raise ValidationError("resources must be a non-empty array")
    seen_ids: set[str] = set()
    covered_categories: set[str] = set()
    migration_records = 0
    for index, resource in enumerate(resources):
        prefix = f"resources[{index}]"
        if not isinstance(resource, dict):
            raise ValidationError(f"{prefix}: expected object")
        resource_id = nonempty_string(resource.get("id"), f"{prefix}.id")
        if not RESOURCE_ID.fullmatch(resource_id) or resource_id in seen_ids:
            raise ValidationError(f"{prefix}.id: invalid or duplicate resource ID {resource_id!r}")
        seen_ids.add(resource_id)
        category = nonempty_string(resource.get("category"), f"{prefix}.category")
        if category not in REQUIRED_CATEGORIES:
            raise ValidationError(f"{prefix}.category: unknown category {category!r}")
        if (
            resource_id in EXPECTED_BACKEND_TABLE_IDS | EXPECTED_CLI_SQLITE_IDS
            and category != "database-table"
        ):
            raise ValidationError(f"{prefix}.category: reconciled table must be database-table")
        covered_categories.add(category)
        nonempty_string(resource.get("currentStatus"), f"{prefix}.currentStatus", 6)
        nonempty_string(resource.get("source"), f"{prefix}.source", 8)
        nonempty_string(resource.get("owner"), f"{prefix}.owner", 3)
        string_list(resource.get("accessPaths"), f"{prefix}.accessPaths")
        nonempty_string(resource.get("isolationMechanism"), f"{prefix}.isolationMechanism", 20)
        isolation_test = nonempty_string(resource.get("isolationTest"), f"{prefix}.isolationTest")
        if isolation_test not in test_ids:
            raise ValidationError(f"{prefix}.isolationTest: unknown matrix test {isolation_test!r}")
        classification = resource.get("classification")
        if not isinstance(classification, dict):
            raise ValidationError(f"{prefix}.classification: expected object")
        kind = classification.get("kind")
        if kind == "tenant":
            nonempty_string(classification.get("tenantKey"), f"{prefix}.classification.tenantKey", 8)
            if "rationale" in classification:
                raise ValidationError(f"{prefix}.classification: tenant records must use tenantKey, not rationale")
        elif kind == "global":
            nonempty_string(classification.get("rationale"), f"{prefix}.classification.rationale", 30)
            if "tenantKey" in classification:
                raise ValidationError(f"{prefix}.classification: global records must use rationale, not tenantKey")
        else:
            raise ValidationError(f"{prefix}.classification.kind must be 'tenant' or 'global'")
        if category == "database-migration":
            migration_records += 1
            members = string_list(resource.get("members"), f"{prefix}.members")
            if tuple(members) != EXPECTED_MIGRATIONS:
                raise ValidationError(
                    f"{prefix}.members must exactly match the 64 source-reconciled migrations"
                )
            invalid = [name for name in members if not MIGRATION_NAME.fullmatch(name)]
            if invalid:
                raise ValidationError(f"{prefix}.members contains invalid migration names: {invalid}")
    if covered_categories != REQUIRED_CATEGORIES:
        raise ValidationError(f"inventory category coverage missing {sorted(REQUIRED_CATEGORIES - covered_categories)}")
    if migration_records != 1:
        raise ValidationError("inventory must contain exactly one complete migration-series record")
    if seen_ids != EXPECTED_RESOURCE_IDS:
        missing = sorted(EXPECTED_RESOURCE_IDS - seen_ids)
        unexpected = sorted(seen_ids - EXPECTED_RESOURCE_IDS)
        raise ValidationError(
            f"inventory resource manifest mismatch; missing={missing}, unexpected={unexpected}"
        )
    backend_table_ids = {
        resource["id"] for resource in resources
        if resource["id"] in EXPECTED_BACKEND_TABLE_IDS
    }
    cli_sqlite_ids = {
        resource["id"] for resource in resources
        if resource["id"] in EXPECTED_CLI_SQLITE_IDS
    }
    if backend_table_ids != EXPECTED_BACKEND_TABLE_IDS or len(backend_table_ids) != 42:
        raise ValidationError("inventory must contain exactly the 42 reconciled backend tables")
    if cli_sqlite_ids != EXPECTED_CLI_SQLITE_IDS or len(cli_sqlite_ids) != 9:
        raise ValidationError("inventory must contain exactly the 9 reconciled CLI SQLite tables")
    return len(resources)


def main() -> int:
    try:
        fixture = load_json(FIXTURE_PATH)
        matrix = load_json(MATRIX_PATH)
        inventory = load_json(INVENTORY_PATH)
        validate_fixture(fixture)
        test_ids = validate_matrix(matrix)
        resource_count = validate_inventory(inventory, test_ids)
    except ValidationError as error:
        print(f"tenant inventory validation failed: {error}", file=sys.stderr)
        return 1
    print(
        f"tenant inventory validation passed: {resource_count} resources, "
        f"{len(test_ids)} isolation tests, 2 synthetic tenants"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
