from __future__ import annotations

from typing import Any

from .state import EducationState


def get_student_data(
    state: EducationState,
    student_name: str,
) -> dict[str, Any]:
    """
    根据学生姓名读取学管数据。

    成功：
    {
        "ok": True,
        "data": {...}
    }

    失败：
    {
        "ok": False,
        "error": {...}
    }
    """

    student_name = student_name.strip()

    if not student_name:
        return {
            "ok": False,
            "error": {
                "code": "INVALID_ARGUMENT",
                "message": "student_name 不能为空",
                "retryable": False,
            },
        }

    matches = state.find_students_by_name(student_name)

    if len(matches) == 0:
        return {
            "ok": False,
            "error": {
                "code": "STUDENT_NOT_FOUND",
                "message": f"未找到学生：{student_name}",
                "retryable": False,
            },
        }

    if len(matches) > 1:
        return {
            "ok": False,
            "error": {
                "code": "AMBIGUOUS_STUDENT",
                "message": f"存在多位同名学生：{student_name}",
                "retryable": False,
            },
        }

    student = matches[0]

    attendance = student["attendance"]
    homework = student["homework"]
    exams = student["exams"]

    attendance_rate = (
        attendance["present"] / attendance["total"]
        if attendance["total"] > 0
        else None
    )

    homework_rate = (
        homework["completed"] / homework["total"]
        if homework["total"] > 0
        else None
    )

    latest_exam = exams[-1] if exams else None

    return {
        "ok": True,
        "data": {
            "student": student["profile"],
            "knowledge_points": student["knowledge_points"],
            "weak_points": student["weak_points"],
            "attendance": {
                **attendance,
                "rate": attendance_rate,
            },
            "homework": {
                **homework,
                "rate": homework_rate,
            },
            "participation": student["participation"],
            "latest_exam": latest_exam,
            "recent_exams": exams,
        },
    }


def save_practice_questions(
    state: EducationState,
    student_name: str,
    questions: str,
) -> dict[str, Any]:
    """
    为指定学生保存专项练习题。

    这是一个写工具：
    成功后会修改 state 中该学生的 practice 字段。
    """

    student_name = student_name.strip()
    questions = questions.strip()

    if not student_name:
        return {
            "ok": False,
            "error": {
                "code": "INVALID_ARGUMENT",
                "message": "student_name 不能为空",
                "retryable": False,
            },
        }

    if not questions:
        return {
            "ok": False,
            "error": {
                "code": "INVALID_ARGUMENT",
                "message": "questions 不能为空",
                "retryable": False,
            },
        }

    matches = state.find_students_by_name(student_name)

    if len(matches) == 0:
        return {
            "ok": False,
            "error": {
                "code": "STUDENT_NOT_FOUND",
                "message": f"未找到学生：{student_name}",
                "retryable": False,
            },
        }

    if len(matches) > 1:
        return {
            "ok": False,
            "error": {
                "code": "AMBIGUOUS_STUDENT",
                "message": f"存在多位同名学生：{student_name}",
                "retryable": False,
            },
        }

    student = matches[0]

    student["practice"] = questions

    return {
        "ok": True,
        "data": {
            "student": student["profile"],
            "saved_field": "practice",
        },
    }


def save_parent_feedback(
    state: EducationState,
    student_name: str,
    feedback: str,
) -> dict[str, Any]:
    """
    为指定学生保存家长反馈。
    成功后修改该学生的 parent_feedback 字段。
    """

    student_name = student_name.strip()
    feedback = feedback.strip()

    if not student_name:
        return {
            "ok": False,
            "error": {
                "code": "INVALID_ARGUMENT",
                "message": "student_name 不能为空",
                "retryable": False,
            },
        }

    if not feedback:
        return {
            "ok": False,
            "error": {
                "code": "INVALID_ARGUMENT",
                "message": "feedback 不能为空",
                "retryable": False,
            },
        }

    matches = state.find_students_by_name(student_name)

    if len(matches) == 0:
        return {
            "ok": False,
            "error": {
                "code": "STUDENT_NOT_FOUND",
                "message": f"未找到学生：{student_name}",
                "retryable": False,
            },
        }

    if len(matches) > 1:
        return {
            "ok": False,
            "error": {
                "code": "AMBIGUOUS_STUDENT",
                "message": f"存在多位同名学生：{student_name}",
                "retryable": False,
            },
        }

    student = matches[0]

    student["parent_feedback"] = feedback

    return {
        "ok": True,
        "data": {
            "student": student["profile"],
            "saved_field": "parent_feedback",
        },
    }


def output_weekly_report(
    state: EducationState,
    student_name: str,
    report: str,
) -> dict[str, Any]:
    """
    为指定学生保存周度学管报告。
    成功后修改该学生的 weekly_report 字段。
    """

    student_name = student_name.strip()
    report = report.strip()

    if not student_name:
        return {
            "ok": False,
            "error": {
                "code": "INVALID_ARGUMENT",
                "message": "student_name 不能为空",
                "retryable": False,
            },
        }

    if not report:
        return {
            "ok": False,
            "error": {
                "code": "INVALID_ARGUMENT",
                "message": "report 不能为空",
                "retryable": False,
            },
        }

    matches = state.find_students_by_name(student_name)

    if len(matches) == 0:
        return {
            "ok": False,
            "error": {
                "code": "STUDENT_NOT_FOUND",
                "message": f"未找到学生：{student_name}",
                "retryable": False,
            },
        }

    if len(matches) > 1:
        return {
            "ok": False,
            "error": {
                "code": "AMBIGUOUS_STUDENT",
                "message": f"存在多位同名学生：{student_name}",
                "retryable": False,
            },
        }

    student = matches[0]

    student["weekly_report"] = report

    return {
        "ok": True,
        "data": {
            "student": student["profile"],
            "saved_field": "weekly_report",
        },
    }
