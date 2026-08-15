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
    for field, values in seen.items():
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
    required_negative_tests = {
        "ISO-READ-FOREIGN-ID", "ISO-WRITE-FOREIGN-ID", "ISO-EXPORT-FOREIGN-ID",
        "ISO-DOCUMENT-FOREIGN-ID", "ISO-PRESIGNED-URL-FOREIGN-KEY",
        "ISO-BACKGROUND-FOREIGN-PAYLOAD", "ISO-SUPPORT-TOOL-FOREIGN-ID",
    }
    missing = required_negative_tests - test_ids
    if missing:
        raise ValidationError(f"matrix is missing required negative tests: {sorted(missing)}")
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
    for index, repository in enumerate(repositories):
        if not isinstance(repository, dict):
            raise ValidationError(f"evidenceRepositories[{index}] must be an object")
        nonempty_string(repository.get("name"), f"evidenceRepositories[{index}].name")
        commit = nonempty_string(repository.get("commit"), f"evidenceRepositories[{index}].commit")
        if not re.fullmatch(r"[0-9a-f]{40}", commit):
            raise ValidationError(f"evidenceRepositories[{index}].commit must be a full SHA")
        nonempty_string(repository.get("path"), f"evidenceRepositories[{index}].path")
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
            if members != sorted(set(members)) or len(members) < 60:
                raise ValidationError(f"{prefix}.members must be sorted, unique and contain the complete migration series")
            invalid = [name for name in members if not MIGRATION_NAME.fullmatch(name)]
            if invalid:
                raise ValidationError(f"{prefix}.members contains invalid migration names: {invalid}")
    if covered_categories != REQUIRED_CATEGORIES:
        raise ValidationError(f"inventory category coverage missing {sorted(REQUIRED_CATEGORIES - covered_categories)}")
    if migration_records != 1:
        raise ValidationError("inventory must contain exactly one complete migration-series record")
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
