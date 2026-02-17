from __future__ import annotations

from typing import Any


def evaluate_expression(expression: dict[str, Any], state: dict[str, float]) -> tuple[bool, str]:
    op = expression.get("op")
    field_name = expression.get("field")
    target = expression.get("value")
    current = state.get(field_name)
    if field_name is None:
        return False, "expression.field is required"
    if current is None:
        return False, f"state has no field '{field_name}'"
    if op == "lte":
        passed = current <= target
        return passed, f"{field_name}={current:.2f} <= {target}"
    if op == "gte":
        passed = current >= target
        return passed, f"{field_name}={current:.2f} >= {target}"
    if op == "eq":
        passed = abs(current - target) < 1e-9
        return passed, f"{field_name}={current:.2f} == {target}"
    if op == "between":
        low = expression.get("min")
        high = expression.get("max")
        passed = low <= current <= high
        return passed, f"{low} <= {field_name}={current:.2f} <= {high}"
    return False, f"unsupported op '{op}'"
