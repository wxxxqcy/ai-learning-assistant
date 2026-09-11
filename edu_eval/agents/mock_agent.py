from __future__ import annotations

from typing import Any

from edu_eval.environment.environment import EducationEnvironment


class MockAgent:
    """
    一个确定性的“假 Agent”。

    它不调用任何 LLM。
    它的唯一作用是验证：
    Scenario -> Agent -> Environment -> Tools -> Grader
    这条 Eval 链路是否能够完整跑通。
    """

    name = "mock-agent"

    def run(
        self,
        env: EducationEnvironment,
        user_instruction: str,
    ) -> dict[str, Any]:

        # 当前先从指令中找到唯一匹配的学生姓名
        student_names = [
            student["profile"]["name"]
            for student in env.state.students.values()
            if student["profile"]["name"] in user_instruction
        ]

        student_names = list(dict.fromkeys(student_names))

        if len(student_names) != 1:
            return {
                "ok": False,
                "final_response": "无法确定需要处理的学生。",
            }

        student_name = student_names[0]

        # 1. 读取学生数据
        read_result = env.execute(
            "get_student_data",
            {
                "student_name": student_name,
            },
        )

        if not read_result["ok"]:
            return {
                "ok": False,
                "final_response": read_result["error"]["message"],
            }

        student_data = read_result["data"]

        # 2. 有薄弱点就保存专项练习
        if student_data["weak_points"]:
            practice_result = env.execute(
                "save_practice_questions",
                {
                    "student_name": student_name,
                    "questions": (
                        "1. 一次函数专项练习题1\n"
                        "2. 一次函数专项练习题2\n"
                        "3. 待定系数法专项练习题3\n"
                        "4. 待定系数法专项练习题4\n"
                        "5. 综合应用专项练习题5"
                    ),
                },
            )

            if not practice_result["ok"]:
                return {
                    "ok": False,
                    "final_response": practice_result["error"]["message"],
                }

        # 3. 保存家长反馈
        feedback_result = env.execute(
            "save_parent_feedback",
            {
                "student_name": student_name,
                "feedback": (
                    f"{student_name}本周整体学习状态稳定。"
                    f"目前需要重点关注的内容是："
                    f"{student_data['weak_points'] or '暂无明确薄弱点'}。"
                    f"建议后续继续结合课堂学习情况进行针对性巩固。"
                ),
            },
        )

        if not feedback_result["ok"]:
            return {
                "ok": False,
                "final_response": feedback_result["error"]["message"],
            }

        # 4. 保存周报
        report_result = env.execute(
            "output_weekly_report",
            {
                "student_name": student_name,
                "report": (
                    f"{student_name}本周学管周报："
                    f"出勤 {student_data['attendance']['present']}/"
                    f"{student_data['attendance']['total']}；"
                    f"作业完成 {student_data['homework']['completed']}/"
                    f"{student_data['homework']['total']}；"
                    f"薄弱点："
                    f"{student_data['weak_points'] or '暂无明确记录'}。"
                ),
            },
        )

        if not report_result["ok"]:
            return {
                "ok": False,
                "final_response": report_result["error"]["message"],
            }

        return {
            "ok": True,
            "final_response": f"{student_name}本周学管工作已完成。",
        }
