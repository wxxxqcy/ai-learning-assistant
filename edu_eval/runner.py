from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from edu_eval.agents.deepseek_agent import DeepSeekAgent
from edu_eval.environment.environment import EducationEnvironment
from edu_eval.environment.state import EducationState
from edu_eval.graders.policy_grader import grade_policy
from edu_eval.graders.safety_grader import grade_safety
from edu_eval.graders.state_grader import grade_state


RESULTS_FILE = Path("results/latest_run.jsonl")
SCENARIO_FILE = Path("edu_eval/scenarios/v0.1/learning_management.jsonl")
DEFAULT_TRIALS_PER_CASE = 3


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run EduAgent Eval scenarios."
    )
    parser.add_argument(
        "--trials",
        type=int,
        default=DEFAULT_TRIALS_PER_CASE,
        help="每个 Case 重复运行次数，默认 3",
    )
    parser.add_argument(
        "--cases",
        type=str,
        default="",
        help="指定运行的 Case 序号，例如 4,5,6,7,8；为空则运行全部",
    )
    return parser.parse_args()


def load_scenarios(path: Path) -> list[dict[str, Any]]:
    scenarios = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                scenarios.append(json.loads(line))

    if not scenarios:
        raise ValueError(f"Scenario 文件为空：{path}")

    return scenarios


def run_trial(
    agent: DeepSeekAgent,
    scenario: dict[str, Any],
    trial_index: int,
) -> dict[str, Any]:
    initial_state = EducationState.from_json(
        scenario["initial_state_ref"]
    )
    initial_snapshot = initial_state.snapshot()

    env = EducationEnvironment(initial_state)

    agent_result = agent.run(
        env=env,
        user_instruction=scenario["user_instruction"],
    )

    final_snapshot = env.snapshot()
    trace = env.get_trace()

    # 1. StateGrader
    state_grade = grade_state(
        initial_state=initial_snapshot,
        final_state=final_snapshot,
        checks=scenario["expected"]["state"],
    )

    # 2. PolicyGrader
    policy_checks = scenario["expected"].get("policy", [])
    if policy_checks:
        policy_grade = grade_policy(
            trace=trace,
            checks=policy_checks,
        )
    else:
        policy_grade = None

    # 3. SafetyGrader
    safety_checks = scenario["expected"].get("safety", [])
    if safety_checks:
        safety_grade = grade_safety(
            trace=trace,
            final_state=final_snapshot,
            final_response=agent_result["final_response"],
            checks=safety_checks,
        )
    else:
        safety_grade = None

    # Safety 作为 Hard Gate
    overall_passed = (
        state_grade["passed"]
        and (
            policy_grade is None
            or policy_grade["passed"]
        )
        and (
            safety_grade is None
            or safety_grade["passed"]
        )
    )

    return {
        "scenario_id": scenario["id"],
        "category": scenario.get("category"),
        "difficulty": scenario.get("difficulty"),
        "instruction": scenario["user_instruction"],
        "trial": trial_index,
        "agent_result": agent_result,
        "trace": trace,
        "initial_state": initial_snapshot,
        "final_state": final_snapshot,
        "state_grade": state_grade,
        "policy_grade": policy_grade,
        "safety_grade": safety_grade,
        "passed": overall_passed,
    }


def print_trial_result(result: dict[str, Any]) -> None:
    print()
    print(f"Trial {result['trial']}")
    print("-" * 60)

    print("Agent Trace:")
    trace = result["trace"]

    if not trace:
        print("  No tool calls")

    for step in trace:
        tool_result = step["result"]
        ok = (
            tool_result.get("ok")
            if isinstance(tool_result, dict)
            else False
        )
        print(
            f"  Step {step['step']}: "
            f"{step['tool']} "
            f"| ok={ok} "
            f"| state_changed={step['state_changed']}"
        )

    print()
    print(
        "Final Response:",
        result["agent_result"]["final_response"],
    )

    # State
    print()
    print("State Checks:")
    for check in result["state_grade"]["checks"]:
        symbol = "PASS" if check["passed"] else "FAIL"
        print(
            f"  [{symbol}] "
            f"{check['path']} "
            f"({check['op']})"
        )

    # Policy
    print()
    print("Policy Checks:")
    policy_grade = result["policy_grade"]

    if policy_grade is None:
        print("  N/A - No policy checks defined")
    else:
        for check in policy_grade["checks"]:
            symbol = "PASS" if check["passed"] else "FAIL"
            parts = [check.get("type", "unknown")]

            tool = check.get("tool")
            student_name = check.get("student_name")

            if tool:
                parts.append(f"tool={tool}")
            if student_name:
                parts.append(f"student={student_name}")

            print(f"  [{symbol}] " + " | ".join(parts))

    # Safety
    print()
    print("Safety Checks:")
    safety_grade = result["safety_grade"]

    if safety_grade is None:
        print("  N/A - No safety checks defined")
    else:
        for check in safety_grade["checks"]:
            symbol = "PASS" if check["passed"] else "FAIL"
            parts = [check.get("type", "unknown")]

            student_name = check.get("student_name")
            allowed = check.get("allowed_student_names")
            paths = check.get("paths")

            if student_name:
                parts.append(f"student={student_name}")
            if allowed:
                parts.append("allowed=" + ",".join(allowed))
            if paths:
                parts.append("paths=" + ",".join(paths))

            print(f"  [{symbol}] " + " | ".join(parts))

            for violation in check.get("violations", []):
                print(
                    "      violation: "
                    + json.dumps(
                        violation,
                        ensure_ascii=False,
                    )
                )

    # Scores / Gate
    print()
    print(
        f"State Score: "
        f"{result['state_grade']['score']:.3f}"
    )

    if policy_grade is None:
        print("Policy Score: N/A")
    else:
        print(
            f"Policy Score: "
            f"{policy_grade['score']:.3f}"
        )

    if safety_grade is None:
        print("Safety Score: N/A")
        print("Safety Gate: N/A")
    else:
        print(
            f"Safety Score: "
            f"{safety_grade['score']:.3f}"
        )
        print(
            "Safety Gate:",
            "PASS" if safety_grade["passed"] else "FAIL",
        )

    print(
        "Overall Result:",
        "PASS" if result["passed"] else "FAIL",
    )


def save_results(
    results: list[dict[str, Any]],
    path: Path,
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with path.open(
        "w",
        encoding="utf-8",
    ) as f:
        for result in results:
            f.write(
                json.dumps(
                    result,
                    ensure_ascii=False,
                )
                + "\n"
            )


def main() -> None:
    args = parse_args()

    if args.trials < 1:
        raise ValueError("--trials 必须大于等于 1")

    print("=" * 70)
    print("EduAgent Eval v0.1 - DeepSeek Reliability Run")
    print("=" * 70)

    all_scenarios = load_scenarios(SCENARIO_FILE)

    if args.cases:
        case_indexes = [
            int(x.strip())
            for x in args.cases.split(",")
            if x.strip()
        ]

        for index in case_indexes:
            if index < 1 or index > len(all_scenarios):
                raise ValueError(
                    f"Case 序号超出范围：{index}"
                )

        scenarios = [
            all_scenarios[index - 1]
            for index in case_indexes
        ]
    else:
        scenarios = all_scenarios

    trials_per_case = args.trials

    print(f"Loaded {len(scenarios)} scenarios.")
    print(f"Trials per case: {trials_per_case}")
    print(
        f"Total trials: "
        f"{len(scenarios) * trials_per_case}"
    )

    agent = DeepSeekAgent()

    all_results = []
    case_summaries = []

    for case_index, scenario in enumerate(
        scenarios,
        start=1,
    ):
        print()
        print("=" * 70)
        print(
            f"Case {case_index}/{len(scenarios)}: "
            f"{scenario['id']}"
        )
        print("=" * 70)
        print(f"Task: {scenario['user_instruction']}")

        case_results = []

        for trial_index in range(
            1,
            trials_per_case + 1,
        ):
            result = run_trial(
                agent=agent,
                scenario=scenario,
                trial_index=trial_index,
            )

            case_results.append(result)
            all_results.append(result)

            print_trial_result(result)

        passed_trials = sum(
            1
            for result in case_results
            if result["passed"]
        )

        case_pass_rate = (
            passed_trials / trials_per_case
        )

        case_summary = {
            "scenario_id": scenario["id"],
            "passed_trials": passed_trials,
            "total_trials": trials_per_case,
            "pass_rate": case_pass_rate,
        }

        case_summaries.append(case_summary)

        print()
        print(
            f"Case Summary: "
            f"{passed_trials}/{trials_per_case} PASS "
            f"({case_pass_rate:.1%})"
        )

    total_trials = len(all_results)

    total_passed = sum(
        1
        for result in all_results
        if result["passed"]
    )

    overall_pass_rate = (
        total_passed / total_trials
        if total_trials
        else 0
    )

    stable_cases = sum(
        1
        for summary in case_summaries
        if summary["passed_trials"]
        == trials_per_case
    )

    print()
    print("=" * 70)
    print("Overall Reliability Summary")
    print("=" * 70)

    for summary in case_summaries:
        print(
            f"{summary['scenario_id']}: "
            f"{summary['passed_trials']}/"
            f"{summary['total_trials']} "
            f"PASS "
            f"({summary['pass_rate']:.1%})"
        )

    print()
    print(
        f"Total Passed Trials: "
        f"{total_passed}/{total_trials}"
    )
    print(
        f"Trial Pass Rate: "
        f"{overall_pass_rate:.1%}"
    )
    print(
        f"Fully Stable Cases: "
        f"{stable_cases}/"
        f"{len(case_summaries)}"
    )

    save_results(
        all_results,
        RESULTS_FILE,
    )

    print()
    print(
        f"Results saved to: "
        f"{RESULTS_FILE.resolve()}"
    )


if __name__ == "__main__":
    main()
