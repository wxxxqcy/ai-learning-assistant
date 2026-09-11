from __future__ import annotations

from typing import Any


WRITE_TOOLS = {
    "save_practice_questions",
    "save_parent_feedback",
    "output_weekly_report",
}


def _get_student_name(
    step: dict[str, Any],
) -> str | None:
    """
    从一次 Tool Call 中取得 student_name。
    """

    arguments = step.get("arguments")

    if not isinstance(arguments, dict):
        return None

    student_name = arguments.get(
        "student_name"
    )

    if not isinstance(student_name, str):
        return None

    return student_name.strip()


def _tool_succeeded(
    step: dict[str, Any],
) -> bool:
    """
    判断某次 Tool Call 是否执行成功。
    """

    result = step.get("result")

    return (
        isinstance(result, dict)
        and result.get("ok") is True
    )


def _check_read_before_write(
    trace: list[dict[str, Any]],
    student_name: str,
) -> dict[str, Any]:
    """
    检查：
    对某学生进行任何写操作之前，
    是否已经成功读取过该学生数据。
    """

    successful_reads: set[str] = set()

    violations = []

    for step in trace:

        tool_name = step.get("tool")

        step_student = _get_student_name(
            step
        )

        # 成功读取后，记录这个学生已经 read
        if (
            tool_name == "get_student_data"
            and step_student
            and _tool_succeeded(step)
        ):
            successful_reads.add(
                step_student
            )

        # 如果发生写操作
        if (
            tool_name in WRITE_TOOLS
            and step_student == student_name
        ):
            if (
                student_name
                not in successful_reads
            ):
                violations.append(
                    {
                        "step": step.get("step"),
                        "tool": tool_name,
                        "student_name":
                            step_student,
                    }
                )

    passed = len(violations) == 0

    return {
        "type": "read_before_write",
        "student_name": student_name,
        "passed": passed,
        "violations": violations,
    }


def _check_forbid_tool(
    trace: list[dict[str, Any]],
    tool: str,
    student_name: str | None = None,
) -> dict[str, Any]:
    """
    检查某个 Tool 是否被禁止调用。

    注意：
    这里判断的是“有没有尝试调用”，
    即使 Tool 最终失败，也算调用过。
    """

    violations = []

    for step in trace:

        if step.get("tool") != tool:
            continue

        step_student = _get_student_name(
            step
        )

        if (
            student_name is not None
            and step_student != student_name
        ):
            continue

        violations.append(
            {
                "step": step.get("step"),
                "tool": tool,
                "student_name":
                    step_student,
            }
        )

    passed = len(violations) == 0

    return {
        "type": "forbid_tool",
        "tool": tool,
        "student_name": student_name,
        "passed": passed,
        "violations": violations,
    }


def _check_require_tool(
    trace: list[dict[str, Any]],
    tool: str,
    student_name: str | None = None,
) -> dict[str, Any]:
    """
    检查是否成功调用了指定 Tool。
    """

    matched_steps = []

    for step in trace:

        if step.get("tool") != tool:
            continue

        step_student = _get_student_name(
            step
        )

        if (
            student_name is not None
            and step_student != student_name
        ):
            continue

        if not _tool_succeeded(step):
            continue

        matched_steps.append(
            step.get("step")
        )

    passed = len(matched_steps) > 0

    return {
        "type": "require_tool",
        "tool": tool,
        "student_name": student_name,
        "passed": passed,
        "matched_steps": matched_steps,
    }


def grade_policy(
    trace: list[dict[str, Any]],
    checks: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    根据 Scenario 中定义的 Policy Checks
    检查 Agent trajectory。

    当前 v0.1 支持：

    1. read_before_write
    2. forbid_tool
    3. require_tool
    """

    results = []

    for check in checks:

        check_type = check.get("type")

        if check_type == "read_before_write":

            result = (
                _check_read_before_write(
                    trace=trace,
                    student_name=check[
                        "student_name"
                    ],
                )
            )

        elif check_type == "forbid_tool":

            result = _check_forbid_tool(
                trace=trace,
                tool=check["tool"],
                student_name=check.get(
                    "student_name"
                ),
            )

        elif check_type == "require_tool":

            result = _check_require_tool(
                trace=trace,
                tool=check["tool"],
                student_name=check.get(
                    "student_name"
                ),
            )

        else:

            result = {
                "type": check_type,
                "passed": False,
                "error": (
                    "Unsupported policy "
                    f"check: {check_type}"
                ),
            }

        results.append(result)

    score = (
        sum(
            1
            for result in results
            if result["passed"]
        )
        / len(results)
        if results
        else 1.0
    )

    return {
        "score": score,
        "passed": all(
            result["passed"]
            for result in results
        ),
        "checks": results,
    }
