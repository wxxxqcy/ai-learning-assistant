from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable

from .state import EducationState
from .tools import (
    get_student_data,
    save_practice_questions,
    save_parent_feedback,
    output_weekly_report,
)


# Environment 允许 Agent 使用的工具
TOOL_REGISTRY: dict[str, Callable[..., dict[str, Any]]] = {
    "get_student_data": get_student_data,
    "save_practice_questions": save_practice_questions,
    "save_parent_feedback": save_parent_feedback,
    "output_weekly_report": output_weekly_report,
}


class EducationEnvironment:
    """
    教育 Agent 的业务环境。

    负责：
    1. 管理本次实验的独立 State
    2. 根据工具名称执行对应 Tool
    3. 自动记录完整执行 Trace
    """

    def __init__(self, initial_state: EducationState):
        # 保存一份永远不被修改的初始状态
        self._initial_state = initial_state.clone()

        # 当前这次实验真正操作的状态
        self.state = initial_state.clone()

        # Agent 的工具调用轨迹
        self._trace: list[dict[str, Any]] = []

    def execute(
        self,
        tool_name: str,
        arguments: dict[str, Any],
    ) -> dict[str, Any]:
        """
        统一执行工具。

        例如：

        env.execute(
            "get_student_data",
            {"student_name": "李明"}
        )
        """

        before_state = self.state.snapshot()

        # ---------- 1. 参数格式检查 ----------
        if not isinstance(arguments, dict):
            result = {
                "ok": False,
                "error": {
                    "code": "INVALID_TOOL_ARGUMENTS",
                    "message": "工具参数必须是一个对象",
                    "retryable": False,
                },
            }

        # ---------- 2. 工具是否存在 ----------
        elif tool_name not in TOOL_REGISTRY:
            result = {
                "ok": False,
                "error": {
                    "code": "UNKNOWN_TOOL",
                    "message": f"未知工具：{tool_name}",
                    "retryable": False,
                },
            }

        else:
            tool = TOOL_REGISTRY[tool_name]

            # ---------- 3. 执行工具 ----------
            try:
                result = tool(
                    self.state,
                    **arguments,
                )

            except TypeError as e:
                # 例如：
                # 少传 student_name
                # 多传了不存在的参数
                result = {
                    "ok": False,
                    "error": {
                        "code": "INVALID_TOOL_ARGUMENTS",
                        "message": str(e),
                        "retryable": False,
                    },
                }

        after_state = self.state.snapshot()

        # ---------- 4. 记录 Trace ----------
        trace_entry = {
            "step": len(self._trace) + 1,
            "tool": tool_name,
            "arguments": deepcopy(arguments),
            "result": deepcopy(result),
            "state_changed": before_state != after_state,
        }

        self._trace.append(trace_entry)

        return result

    def snapshot(self) -> dict[str, Any]:
        """
        返回当前环境最终状态。
        后面的 Grader 会使用。
        """
        return self.state.snapshot()

    def get_trace(self) -> list[dict[str, Any]]:
        """
        返回 Agent 的工具调用轨迹。
        """
        return deepcopy(self._trace)

    def reset(self) -> None:
        """
        恢复到本次 Environment 创建时的初始状态。
        同时清空 Trace。
        """
        self.state = self._initial_state.clone()
        self._trace = []
