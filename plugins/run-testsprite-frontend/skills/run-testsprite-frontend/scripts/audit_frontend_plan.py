#!/usr/bin/env python3
"""Conservatively audit a TestSprite frontend plan before vendor lint/upload.

The auditor checks stable policy invariants, never prints suspected values, and does
not replace TestSprite `test lint`. Use --self-test only in maintainer/CI checks.
"""

from __future__ import annotations

import argparse
import ipaddress
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlparse

MAX_BYTES = 256 * 1024
MAX_STEPS = 200
MAX_NAME = 200
MAX_DESCRIPTION = 2000
PRIORITIES = {"p0", "p1", "p2", "p3"}
STEP_TYPES = {"action", "assertion"}
PLACEHOLDER_WORDS = {
    "changeme",
    "example",
    "placeholder",
    "replace-me",
    "replace_with",
    "replace-with",
    "sample-project",
    "your-project",
}
VACUOUS_ASSERTIONS = {
    "it works",
    "no errors",
    "page loads",
    "success",
    "test passes",
    "the button exists",
    "the page loads",
    "the page works",
    "the test passes",
}
SECRET_PATTERNS = (
    re.compile(r"\bBearer\s+[A-Za-z0-9._~+/=-]{8,}", re.I),
    re.compile(r"\bsk-[A-Za-z0-9_-]{12,}"),
    re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b"),
    re.compile(
        r"\b(?:api[_ -]?key|access[_ -]?token|auth[_ -]?token|password|secret|cookie|otp)"
        r"\s*(?:is|:|=)\s*[\"']?\S{4,}",
        re.I,
    ),
    re.compile(
        r"\b(?:enter|type|fill|use|paste|provide)\b.{0,20}"
        r"\b(?:api[_ -]?key|access[_ -]?token|auth[_ -]?token|password|secret|cookie|otp)\b"
        r"\s+(?!(?:from|using|stored|managed|authorized|test|field|input|account|role)\b)"
        r"[\"']?[A-Za-z0-9._~+/=-]{4,}",
        re.I,
    ),
    re.compile(r"\b(?:\d[ -]*?){13,19}\b"),
)
SAFE_SECRET_STATUS_PATTERNS = (
    re.compile(
        r"\b(?:password|otp|one[- ]time password|api[_ -]?key|cookie)\s+"
        r"(?:is|remains|must be)\s+"
        r"(?:required|masked|invalid|hidden|httponly|http-only|redacted|missing|empty|expired|"
        r"not shown|not displayed)\b",
        re.I,
    ),
)
SELECTOR_PATTERNS = (
    re.compile(r"\b(?:page|browser)\.(?:click|fill|goto|locator|query)", re.I),
    re.compile(r"\b(?:locator|querySelector|getByRole|getByText|getByTestId|get_by_role)\s*\(", re.I),
    re.compile(r"\[data-(?:test|testid|qa|cy)[^\]]*\]", re.I),
    re.compile(r"\b(?:xpath|css selector)\b", re.I),
    re.compile(r"//[A-Za-z*][A-Za-z0-9_/*\[\]@='\".-]*"),
    re.compile(r":nth-(?:child|of-type)\s*\(", re.I),
    re.compile(r"@e\d+\b", re.I),
    re.compile(r"\b(?:click|fill|select|locate|find|assert)\b.{0,40}#[A-Za-z][\w:-]*", re.I),
)
BYPASS_PATTERNS = (
    re.compile(r"\bbypass\b.{0,30}\b(?:captcha|mfa|2fa|otp|payment|human)", re.I),
    re.compile(r"\b(?:disable|skip|solve)\b.{0,30}\b(?:captcha|mfa|2fa|human verification)", re.I),
    re.compile(r"\buse\b.{0,20}\b(?:real|production)\b.{0,20}\b(?:card|bank|payment)", re.I),
    re.compile(
        r"\b(?:place|submit|confirm|complete|make|book|reserve|purchase|buy)\b.{0,45}"
        r"\b(?:order|purchase|booking|reservation|item|product|ticket|room|table|seat)\b.{0,60}"
        r"\b(?:real|production)\b.{0,20}\b(?:card|bank|payment)",
        re.I,
    ),
)
OUTWARD_PATTERNS = {
    "communication": (
        re.compile(
            r"\b(?:send|publish|post|invite|notify)\b.{0,45}"
            r"\b(?:email|message|notification|webhook|invitation|user|post|comment|content)\b",
            re.I,
        ),
        re.compile(r"\b(?:email|message)\b.{0,35}\b(?:user|customer|recipient|receipt|support|address)\b", re.I),
    ),
    "transaction": (
        re.compile(
            r"\b(?:pay|purchase|buy|charge|subscribe|book|reserve|place|submit|confirm|complete|make)\b"
            r".{0,45}\b(?:payment|purchase|order|booking|reservation|subscription)\b",
            re.I,
        ),
        re.compile(
            r"\b(?:purchase|buy|book|reserve)\b.{0,35}"
            r"\b(?:item|product|ticket|room|table|seat|appointment|trip|stay|service)\b",
            re.I,
        ),
        re.compile(r"\b(?:complete|submit|confirm)\b.{0,25}\bcheckout\b", re.I),
    ),
    "destructive": (
        re.compile(
            r"\b(?:delete|remove|archive)\b.{0,50}"
            r"\b(?:account|user|workspace|project|organization|order|record|item|resource|data)\b",
            re.I,
        ),
        re.compile(r"\b(?:delete|remove|archive)\s+(?:it|this)\b", re.I),
    ),
    "mutation": (
        re.compile(
            r"\b(?:create|add|update|edit|save|submit)\b.{0,50}"
            r"\b(?:account|user|workspace|project|organization|profile|address|order|record|item|"
            r"resource|settings|comment|review|application|request|data)\b",
            re.I,
        ),
    ),
    "upload": (
        re.compile(r"\b(?:upload|attach)\b.{0,35}\b(?:file|image|document|attachment)\b", re.I),
    ),
    "third-party": (
        re.compile(r"\b(?:oauth|third[- ]party)\b.{0,30}\b(?:authorize|connect|consent|redirect)\b", re.I),
    ),
}
NEGATIVE_VALIDATION_PATTERN = re.compile(
    r"\b(?:invalid|without|required|validation|not submitted|prevent(?:s|ed)?|reject(?:s|ed)?|"
    r"declin(?:e|ed)|error message)\b",
    re.I,
)
VALIDATION_CONTEXT_PATTERN = re.compile(r"\b(?:form|field|input|validation|error|address)\b", re.I)
URL_PATTERN = re.compile(r"https?://[^\s\"'<>]+", re.I)
EMAIL_PATTERN = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)
NUMERIC_HOST_PATTERN = re.compile(r"(?:0x[0-9a-f]+|[0-9]+)(?:\.(?:0x[0-9a-f]+|[0-9]+))*", re.I)


@dataclass(frozen=True)
class Finding:
    code: str
    location: str
    message: str
    severity: str = "error"

    def as_dict(self) -> dict[str, str]:
        return {
            "severity": self.severity,
            "code": self.code,
            "location": self.location,
            "message": self.message,
        }


def normalized(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().lower()).rstrip(".!?")


def is_placeholder(value: str) -> bool:
    lowered = value.lower()
    return any(word in lowered for word in PLACEHOLDER_WORDS) or "${" in value or "<" in value


def mask_patterns(text: str, patterns: tuple[re.Pattern[str], ...]) -> str:
    masked = list(text)
    for pattern in patterns:
        for match in pattern.finditer(text):
            masked[match.start() : match.end()] = " " * (match.end() - match.start())
    return "".join(masked)


def is_private_host(host: str) -> bool:
    canonical = host.lower().rstrip(".")
    if canonical in {"localhost", "home.arpa"}:
        return True
    if canonical.endswith((".localhost", ".local", ".lan", ".internal", ".home.arpa")):
        return True
    if NUMERIC_HOST_PATTERN.fullmatch(canonical):
        return True
    try:
        address = ipaddress.ip_address(canonical)
    except ValueError:
        return "." not in canonical
    return not address.is_global


def trim_url_candidate(value: str) -> str:
    return value.rstrip(".,);")


def inspect_urls(text: str, location: str, findings: list[Finding]) -> None:
    for match in URL_PATTERN.finditer(text):
        value = trim_url_candidate(match.group(0))
        try:
            parsed = urlparse(value)
            host = parsed.hostname or ""
            _ = parsed.port
        except ValueError:
            findings.append(Finding("invalid-url", location, "A URL is malformed."))
            continue
        if parsed.username is not None or parsed.password is not None:
            findings.append(
                Finding("credential-url", location, "A URL contains credential userinfo; remove it.")
            )
        if not host:
            findings.append(Finding("invalid-url", location, "A URL has no hostname."))
            continue
        if is_private_host(host):
            findings.append(
                Finding("private-target", location, "CLI plans must not target localhost or a private host.")
            )
        canonical = host.lower().rstrip(".")
        if (
            canonical in {"example.com", "example.net", "example.org"}
            or canonical.endswith((".example.com", ".example.net", ".example.org", ".example", ".invalid", ".test"))
        ):
            findings.append(
                Finding("placeholder-target", location, "Replace the placeholder URL with an authorized public target.")
            )


def outward_categories(text: str) -> set[str]:
    categories = {
        category
        for category, patterns in OUTWARD_PATTERNS.items()
        if any(pattern.search(text) for pattern in patterns)
    }
    if (
        categories
        and categories <= {"communication", "transaction", "mutation"}
        and NEGATIVE_VALIDATION_PATTERN.search(text)
        and VALIDATION_CONTEXT_PATTERN.search(text)
    ):
        return set()
    return categories


def inspect_text(
    text: str,
    location: str,
    step_type: str | None,
    step_index: int | None,
    authorized_outward_steps: set[int],
    findings: list[Finding],
) -> None:
    secret_text = mask_patterns(text, SAFE_SECRET_STATUS_PATTERNS)
    if any(pattern.search(secret_text) for pattern in SECRET_PATTERNS):
        findings.append(
            Finding("possible-secret", location, "Possible credential, token, payment number, or OTP literal found.")
        )

    selector_text = mask_patterns(text, (URL_PATTERN,))
    if any(pattern.search(selector_text) for pattern in SELECTOR_PATTERNS):
        findings.append(
            Finding("selector-language", location, "Describe user intent, not CSS/XPath/Playwright selector mechanics.")
        )
    if any(pattern.search(text) for pattern in BYPASS_PATTERNS):
        findings.append(
            Finding("gate-bypass", location, "Do not bypass MFA, CAPTCHA, payment, or human verification gates.")
        )

    is_authorized_step = step_index is not None and step_index in authorized_outward_steps
    if step_type == "action" and outward_categories(text):
        if is_authorized_step:
            findings.append(
                Finding(
                    "authorized-outward-action",
                    location,
                    "This outward action is step-authorized; still verify the exact account, target, effect, cleanup, and rollback before execution.",
                    severity="warning",
                )
            )
        else:
            findings.append(
                Finding(
                    "outward-action",
                    location,
                    "High-impact/outward action needs exact step authorization, a safe account or sink, cleanup, and rollback; use --authorized-outward-step INDEX only after recording that gate.",
                )
            )

    if EMAIL_PATTERN.search(text):
        if is_authorized_step:
            findings.append(
                Finding(
                    "authorized-email-literal",
                    location,
                    "An email literal is present in this step-authorized action; verify it is synthetic, origin-bound, and approved for retention.",
                    severity="warning",
                )
            )
        else:
            findings.append(
                Finding(
                    "email-literal",
                    location,
                    "An email address appears in the plan; remove it or authorize this exact step for an approved synthetic/sink identity.",
                )
            )
    inspect_urls(text, location, findings)


def require_string(
    value: Any,
    location: str,
    findings: list[Finding],
    *,
    maximum: int | None = None,
) -> str | None:
    if not isinstance(value, str) or not value.strip():
        findings.append(Finding("invalid-string", location, "Expected a non-empty string."))
        return None
    if maximum is not None and len(value) > maximum:
        findings.append(Finding("string-too-long", location, f"String exceeds {maximum} characters."))
    return value


def audit(payload: Any, authorized_outward_steps: set[int] | None = None) -> list[Finding]:
    authorized = set() if authorized_outward_steps is None else set(authorized_outward_steps)
    findings: list[Finding] = []
    if not isinstance(payload, dict):
        return [Finding("invalid-root", "$", "Plan input must be a JSON object.")]

    full_plan = any(key in payload for key in ("projectId", "type", "name", "description", "priority"))
    if full_plan:
        project_id = require_string(payload.get("projectId"), "$.projectId", findings)
        if project_id is not None and is_placeholder(project_id):
            findings.append(
                Finding("placeholder-project", "$.projectId", "Replace the placeholder with the real frontend project ID.")
            )
        if payload.get("type") != "frontend":
            findings.append(Finding("invalid-type", "$.type", "Full frontend plans require type 'frontend'."))
        name = require_string(payload.get("name"), "$.name", findings, maximum=MAX_NAME)
        if name is not None:
            inspect_text(name, "$.name", None, None, authorized, findings)
        if "description" in payload:
            description = require_string(
                payload.get("description"), "$.description", findings, maximum=MAX_DESCRIPTION
            )
            if description is not None:
                inspect_text(description, "$.description", None, None, authorized, findings)
        if "priority" in payload:
            priority = payload.get("priority")
            if not isinstance(priority, str) or priority not in PRIORITIES:
                findings.append(
                    Finding("invalid-priority", "$.priority", "Priority must be p0, p1, p2, or p3.")
                )

    steps = payload.get("planSteps")
    if not isinstance(steps, list):
        findings.append(Finding("invalid-steps", "$.planSteps", "planSteps must be an array."))
        return findings
    if not 1 <= len(steps) <= MAX_STEPS:
        findings.append(
            Finding("step-count", "$.planSteps", f"Plan must contain 1–{MAX_STEPS} steps.")
        )

    for index in sorted(authorized - set(range(len(steps)))):
        findings.append(
            Finding(
                "invalid-authorized-step",
                f"$.planSteps[{index}]",
                "Authorized outward step index does not identify an existing plan step.",
            )
        )

    seen_types: set[str] = set()
    for index, step in enumerate(steps):
        location = f"$.planSteps[{index}]"
        if not isinstance(step, dict):
            findings.append(Finding("invalid-step", location, "Each step must be a JSON object."))
            continue
        raw_step_type = step.get("type")
        if not isinstance(raw_step_type, str) or raw_step_type not in STEP_TYPES:
            findings.append(
                Finding("invalid-step-type", f"{location}.type", "Step type must be action or assertion.")
            )
            step_type = None
        else:
            step_type = raw_step_type
            seen_types.add(step_type)
        description = require_string(step.get("description"), f"{location}.description", findings)
        if description is None:
            continue
        inspect_text(
            description,
            f"{location}.description",
            step_type,
            index,
            authorized,
            findings,
        )
        if step_type == "assertion" and normalized(description) in VACUOUS_ASSERTIONS:
            findings.append(
                Finding("vacuous-assertion", f"{location}.description", "Assertion does not name a material visible contract.")
            )

    if "assertion" not in seen_types:
        findings.append(
            Finding("missing-assertion", "$.planSteps", "Skill policy requires at least one observable assertion.")
        )
    return findings


def decode_json(
    text: str,
    loader: Callable[[str], Any] = json.loads,
) -> tuple[Any | None, Finding | None]:
    try:
        return loader(text), None
    except json.JSONDecodeError as exc:
        return None, Finding("invalid-json", f"line {exc.lineno}", "Plan is not valid JSON.")
    except RecursionError:
        return None, Finding("invalid-json", "$", "Plan JSON is too deeply nested to parse safely.")


def plan_with(step_description: str, step_type: Any = "assertion", **overrides: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "projectId": "proj_real",
        "type": "frontend",
        "name": "Visible frontend contract",
        "priority": "p1",
        "planSteps": [{"type": step_type, "description": step_description}],
    }
    payload.update(overrides)
    return payload


def finding_codes(findings: list[Finding]) -> set[str]:
    return {finding.code for finding in findings}


def run_self_test() -> int:
    cases: list[tuple[str, bool]] = []

    cases.append(("non-string-priority", "invalid-priority" in finding_codes(audit(plan_with("A heading is visible", priority=[])))))
    cases.append(("non-string-step-type", "invalid-step-type" in finding_codes(audit(plan_with("A heading is visible", step_type=[])))))
    cases.append(("name-limit", "string-too-long" in finding_codes(audit(plan_with("A heading is visible", name="N" * (MAX_NAME + 1))))))
    cases.append(("description-limit", "string-too-long" in finding_codes(audit(plan_with("A heading is visible", description="D" * (MAX_DESCRIPTION + 1))))))

    url_findings = audit(plan_with("Open https://public.example.dev/path//section and verify the heading"))
    cases.append(("url-not-xpath", "selector-language" not in finding_codes(url_findings)))

    payment_findings = audit(plan_with("Place an order using a real production card", step_type="action"))
    cases.append(("real-payment-action", {"gate-bypass", "outward-action"} <= finding_codes(payment_findings)))
    for phrase in ("Make a purchase", "Purchase the item", "Book a room", "Reserve a table"):
        findings = audit(plan_with(phrase, step_type="action"))
        cases.append((f"narrow-outward-{normalized(phrase)}", "outward-action" in finding_codes(findings)))

    for host in ("127.1", "0x7f000001", "0177.0.0.1"):
        findings = audit(plan_with(f"Open http://{host}/ and verify the page"))
        cases.append((f"private-host-{host}", "private-target" in finding_codes(findings)))
    public_findings = audit(plan_with("Open https://app.public-domain.com and verify the heading"))
    cases.append(("public-dns-preserved", "private-target" not in finding_codes(public_findings)))

    safe_navigation = audit(plan_with("Navigate to the checkout page and inspect the email field", step_type="action"))
    cases.append(("safe-navigation-nouns", "outward-action" not in finding_codes(safe_navigation)))
    negative_validation = audit(plan_with("Attempt to send an email with an invalid address and verify the validation error", step_type="action"))
    cases.append(("negative-validation", "outward-action" not in finding_codes(negative_validation)))

    statuses = (
        "The password is required",
        "The password is masked",
        "The OTP is invalid",
        "The API key is hidden",
        "The cookie is HttpOnly",
    )
    for status in statuses:
        findings = audit(plan_with(status))
        cases.append((f"semantic-status-{normalized(status)}", "possible-secret" not in finding_codes(findings)))

    ipv6_findings = audit(plan_with("Open http://[::1]/ and verify the page"))
    cases.append(("balanced-ipv6", "private-target" in finding_codes(ipv6_findings) and "invalid-url" not in finding_codes(ipv6_findings)))
    cases.append(("vacuous-the-test-passes", "vacuous-assertion" in finding_codes(audit(plan_with("The test passes.")))))

    _, recursion_finding = decode_json("{}", loader=lambda _: (_ for _ in ()).throw(RecursionError()))
    cases.append(("recursion-error", recursion_finding is not None and recursion_finding.code == "invalid-json"))

    two_actions = plan_with(
        "Send a notification to the approved sink",
        step_type="action",
        planSteps=[
            {"type": "action", "description": "Send a notification to the approved sink"},
            {"type": "action", "description": "Publish a post to the sandbox workspace"},
            {"type": "assertion", "description": "The sandbox activity log shows both actions"},
        ],
    )
    scoped = audit(two_actions, {0})
    scoped_codes = [(finding.code, finding.location, finding.severity) for finding in scoped]
    cases.append(("authorized-step-warning", ("authorized-outward-action", "$.planSteps[0].description", "warning") in scoped_codes))
    cases.append(("unlisted-step-error", ("outward-action", "$.planSteps[1].description", "error") in scoped_codes))

    email_plan = plan_with("Send confirmation to sink@example.dev", step_type="action")
    cases.append(("email-default-error", "email-literal" in finding_codes(audit(email_plan))))
    cases.append(("email-step-warning", "authorized-email-literal" in finding_codes(audit(email_plan, {0}))))

    for name, passed in cases:
        if not passed:
            print(f"SELF-TEST FAILED: {name}", file=sys.stderr)
            return 1
    print(f"audit_frontend_plan self-test: {len(cases)} cases passed")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", nargs="?", type=Path, help="full plan JSON or {planSteps: [...]} JSON")
    parser.add_argument(
        "--authorized-outward-step",
        action="append",
        type=int,
        default=[],
        metavar="INDEX",
        help="repeat for each zero-based plan step with recorded outward-action authorization",
    )
    parser.add_argument("--json", action="store_true", help="emit machine-readable findings")
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="run deterministic maintainer/CI regression cases without reading a plan",
    )
    args = parser.parse_args()
    if args.self_test:
        if args.path is not None or args.authorized_outward_step or args.json:
            parser.error("--self-test cannot be combined with a plan or output/authorization options")
    elif args.path is None:
        parser.error("path is required unless --self-test is used")
    if any(index < 0 for index in args.authorized_outward_step):
        parser.error("--authorized-outward-step must be zero or greater")
    return args


def main() -> int:
    args = parse_args()
    if args.self_test:
        return run_self_test()

    try:
        size = args.path.stat().st_size
    except OSError as exc:
        raise SystemExit(f"cannot read {args.path}: {exc}") from exc
    if size > MAX_BYTES:
        findings = [Finding("file-too-large", "$", f"Plan exceeds {MAX_BYTES} bytes.")]
    else:
        try:
            text = args.path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            raise SystemExit(f"cannot read {args.path}: {exc}") from exc
        payload, parse_finding = decode_json(text)
        if parse_finding is not None:
            findings = [parse_finding]
        else:
            findings = audit(payload, set(args.authorized_outward_step))

    errors = [finding for finding in findings if finding.severity == "error"]
    warnings = [finding for finding in findings if finding.severity == "warning"]
    if args.json:
        print(
            json.dumps(
                {
                    "ok": not errors,
                    "errors": [finding.as_dict() for finding in errors],
                    "warnings": [finding.as_dict() for finding in warnings],
                },
                indent=2,
                sort_keys=True,
            )
        )
    else:
        for finding in findings:
            print(f"{finding.severity.upper()} [{finding.code}] {finding.location}: {finding.message}")
        print("audit_frontend_plan: ok" if not errors else f"audit_frontend_plan: {len(errors)} error(s)")
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
