from __future__ import annotations

import json
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class EducationState:
    data: dict[str, Any]

    @classmethod
    def from_json(cls, path: str | Path) -> "EducationState":
        """
        从 JSON 文件加载教育环境状态。
        """
        path = Path(path)

        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        if "students" not in data:
            raise ValueError("State 文件缺少 students 字段")

        if not isinstance(data["students"], dict):
            raise ValueError("students 必须是一个对象")

        return cls(data=data)

    @property
    def students(self) -> dict[str, Any]:
        """
        快捷访问学生数据库。
        """
        return self.data["students"]

    def get_student_by_id(self, student_id: str | int) -> dict[str, Any] | None:
        """
        根据学生 ID 查询。
        JSON 中的 key 是字符串，所以统一转为 str。
        """
        return self.students.get(str(student_id))

    def find_students_by_name(self, name: str) -> list[dict[str, Any]]:
        """
        根据姓名查询学生。

        返回 list 是故意的：
        以后可以支持“重名学生”的评测场景。
        """
        target_name = name.strip()

        return [
            student
            for student in self.students.values()
            if student.get("profile", {}).get("name") == target_name
        ]

    def clone(self) -> "EducationState":
        """
        创建完全独立的状态副本。

        每个 eval trial 都应该使用自己的 clone，
        避免不同实验之间互相污染。
        """
        return EducationState(data=deepcopy(self.data))

    def snapshot(self) -> dict[str, Any]:
        """
        获取当前状态快照。

        grader 后面会用它比较：
        initial_state vs final_state
        """
        return deepcopy(self.data)
