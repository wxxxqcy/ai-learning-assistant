from __future__ import annotations

from typing import Any


def _read_path(
    data: dict[str, Any],
    path: str,
) -> tuple[bool, Any]:
    """
    根据类似 students.1.practice 的路径读取嵌套数据。

    返回：
    (True, value)   找到了
    (False, None)   路径不存在
    """

    current: Any = data

    for part in path.split("."):
        if not isinstance(current, dict):
            return False, None

        if part not in current:
            return False, None

        current = current[part]

    return True, current


def _is_empty(value: Any) -> bool:
    """
    判断一个值是否为空。
    """

    return value is None or value == "" or value == [] or value == {}


def grade_state(
    initial_state: dict[str, Any],
    final_state: dict[str, Any],
    checks: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    根据 Scenario 中的 expected.state 检查最终状态。

    当前支持：

    nonempty
        最终值必须非空

    empty
        最终值必须为空

    unchanged
        最终值必须与初始值完全一致

    eq
        最终值必须等于指定 value
    """

    results: list[dict[str, Any]] = []

    for check in checks:
        path = check["path"]
        op = check["op"]

        before_found, before = _read_path(
            initial_state,
            path,
        )

        after_found, after = _read_path(
            final_state,
            path,
        )

        passed = False
        error = None

        if not after_found:
            error = f"最终状态中不存在路径：{path}"

        elif op == "nonempty":
            passed = not _is_empty(after)

        elif op == "empty":
            passed = _is_empty(after)

        elif op == "unchanged":
            if not before_found:
                error = f"初始状态中不存在路径：{path}"
            else:
                passed = before == after

        elif op == "eq":
            passed = after == check.get("value")

        else:
            error = f"不支持的检查操作：{op}"

        result = {
            "path": path,
            "op": op,
            "passed": passed,
        }

        if error:
            result["error"] = error

        results.append(result)

    if not results:
        score = 1.0
    else:
        passed_count = sum(
            1 for result in results
            if result["passed"]
        )

        score = passed_count / len(results)

    return {
        "score": score,
        "passed": all(
            result["passed"]
            for result in results
        ),
        "checks": results,
    }
