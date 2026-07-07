from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from statistics import mean
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.xiaobei_ai import prep_room_document_text_extractor_1013R_R107A as extractor
from backend.xiaobei_ai import prep_room_real_upload_entry_preview_1013R_R103 as r103


STAGE = "1013R_R200D_REAL_LESSON_QUALITY_REGRESSION"
OUT = ROOT / "outputs" / "PREP_ROOM_RENDER_CANVAS_DEEPEN_V1" / STAGE
RESULT = OUT / "validate_1013R_R200D_real_lesson_quality_regression_result.json"
REPORT = OUT / "r200d_real_lesson_quality_regression_report.md"


QUALITY_DIMENSIONS = [
    "topic_contamination_score",
    "section_depth_score",
    "basis_to_goal_chain_score",
    "episode_causality_score",
    "microstep_actionability_score",
    "curriculum_embedding_score",
    "teacher_usefulness_score",
]


GENERIC_PATTERNS = [
    "需教师确认",
    "结合本班情况",
    "本环节推进依据",
    "本环节证据需",
    "上传原文未提供",
    "具体因果需要",
    "下一环节过渡需",
    "完成本环节学习任务",
    "依据上传原文推进",
    "只提示教师观察证据",
]


CAUSAL_GENERIC_PATTERNS = [
    "用本环节证据支撑下一环节推进",
    "具体因果需要教师确认",
    "下一环节过渡需教师确认",
    "本环节推进依据需教师结合上传原文确认",
]


def _clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _items(value: Any) -> list[str]:
    if isinstance(value, list):
        return [_clean(item) for item in value if _clean(item)]
    text = _clean(value)
    return [text] if text else []


def _docx_text(pattern: str) -> tuple[str, str]:
    matches = sorted((ROOT / "knowledge-base" / "lesson-cases").glob(pattern))
    if not matches:
        raise AssertionError(f"missing lesson sample: {pattern}")
    path = matches[0]
    extracted = extractor.extract_document_text(str(path), original_filename=path.name, enable_model_ocr=False)
    if not extracted.get("ok"):
        raise AssertionError(f"document extraction failed: {path.name} {extracted.get('status')}")
    return str(extracted.get("text") or ""), path.name


def _shoe_upload_text() -> tuple[str, str]:
    return (
        "\n".join(
            [
                "课题：《足下生辉》教案",
                "年级：三年级",
                "单元：第五单元 足下生辉",
                "本课引导学生观察生活中的鞋，比较鞋的正面、侧面、后面和局部细节。",
                "教学目标：学生从不同角度观察一双鞋，说出鞋面、鞋底、鞋带和局部纹样的特点；用线条画出鞋的外形、结构和细节。",
                "教学过程",
                "1. 引入 5分钟 出示不同民族、不同时代的鞋，引导学生提出问题。",
                "2. 观察指导 10分钟 学生观察自己带来的鞋，比较正面、侧面和局部细节。",
                "3. 动手写生 20分钟 学生用线条画出鞋的外形、结构和主要细节。",
                "4. 展示与小结 5分钟 学生说出自己观察到的鞋的一个特点和画面调整。",
            ]
        ),
        "课时1_足下生辉_教案.txt",
    )


SAMPLES: list[dict[str, Any]] = [
    {
        "case_id": "shoe_observation",
        "source": _shoe_upload_text,
        "expected_focus": "shoe_observation_drawing_expression",
        "positive_terms": ["鞋", "角度", "结构", "局部", "线条", "观察"],
        "forbidden_terms": ["渐变", "色阶", "彩虹", "青绿", "石青", "石绿"],
    },
    {
        "case_id": "color_gradation",
        "source": lambda: _docx_text("*fd1b5bdf60*.docx"),
        "expected_focus": "color_gradation_expression",
        "positive_terms": ["渐变", "色彩", "颜色", "过渡", "色阶", "试色"],
        "forbidden_terms": ["鞋底", "鞋面", "鞋带", "青绿山水", "海洋"],
    },
    {
        "case_id": "qinglv_landscape",
        "source": lambda: _docx_text("*08f3e01f0b*.docx"),
        "expected_focus": "ink_or_traditional_color_exploration",
        "positive_terms": ["青绿", "山水", "石青", "石绿", "传统", "浓淡"],
        "forbidden_terms": ["足下生辉", "鞋底", "鞋面", "海洋生物", "废旧材料"],
    },
    {
        "case_id": "material_transformation",
        "source": lambda: _docx_text("*67d6ab622f*.docx"),
        "expected_focus": "material_transformation_expression",
        "positive_terms": ["材料", "结构", "剪贴", "拼摆", "连接", "造型"],
        "forbidden_terms": ["色阶", "石青", "石绿", "足下生辉", "鞋底"],
    },
    {
        "case_id": "ocean_theme",
        "source": lambda: _docx_text("*eeabeca815*.docx"),
        "expected_focus": "theme_observation_expression",
        "positive_terms": ["海洋", "生命", "动物", "环保", "主题", "特征"],
        "forbidden_terms": ["色阶", "足下生辉", "鞋底", "青绿山水"],
    },
    {
        "case_id": "weaving",
        "source": lambda: _docx_text("*39f6102808*.docx"),
        "expected_focus": "paper_weaving_structure_expression",
        "positive_terms": ["编", "穿", "经纬", "纸条", "纹样", "交织"],
        "forbidden_terms": ["足下生辉", "海洋", "青绿", "石青", "石绿", "渐变"],
    },
]


def _build_response(raw_text: str, file_name: str) -> dict[str, Any]:
    session = r103.build_upload_session(raw_text, file_name)
    response = r103.build_readonly_viewmodel_from_upload_session(
        session,
        enable_teacher_model=False,
        enable_art_reasoning_model=False,
    )
    r103._attach_upload_preview_test_record(response, "raw_text_upload")
    return response


def _section_body(template: dict[str, Any], key: str) -> list[str]:
    value = template.get(key)
    if not isinstance(value, list) or not value:
        return []
    first = value[0] if isinstance(value[0], dict) else {}
    if not isinstance(first, dict):
        return []
    return _items(first.get("body"))


def _all_visible_text(template: dict[str, Any]) -> list[str]:
    texts: list[str] = []
    for key in ["basis", "student_analysis", "objectives", "key_difficult_points", "preparation"]:
        texts.extend(_section_body(template, key))
    for episode in template.get("process_episodes") or []:
        if not isinstance(episode, dict):
            continue
        for key in ["episode_title", "episode_goal", "teacher_organization", "student_learning", "key_talk", "evidence"]:
            texts.extend(_items(episode.get(key)))
        basis = episode.get("derivation_basis") if isinstance(episode.get("derivation_basis"), dict) else {}
        for key in ["why_now", "transition_to_next", "assessment_evidence", "pedagogy_role", "curriculum_candidate_summary"]:
            texts.extend(_items(basis.get(key)))
        for micro in episode.get("micro_steps") or []:
            if not isinstance(micro, dict):
                continue
            for key in ["title", "step_name", "teacher_action", "student_action", "screen_or_materials", "scaffolds", "evidence"]:
                texts.extend(_items(micro.get(key)))
    return texts


def _hit_terms(text: str, terms: list[str]) -> list[str]:
    return [term for term in terms if term and term in text]


def _generic_hits(texts: list[str]) -> list[str]:
    hits = []
    for text in texts:
        if any(pattern in text for pattern in GENERIC_PATTERNS):
            hits.append(text[:160])
    return hits[:12]


def _topic_contamination_score(joined: str, forbidden_terms: list[str]) -> tuple[int, list[str]]:
    hits = _hit_terms(joined, forbidden_terms)
    if not hits:
        return 100, []
    return max(0, 100 - len(hits) * 25), hits


def _section_depth_score(template: dict[str, Any]) -> tuple[int, list[str]]:
    section_map = {
        "basis": "本课依据",
        "student_analysis": "学情分析",
        "objectives": "教学目标",
        "key_difficult_points": "教学重难点",
    }
    scores = []
    issues = []
    for key, label in section_map.items():
        items = _section_body(template, key)
        chars = sum(len(item) for item in items)
        generic_count = sum(1 for item in items if any(pattern in item for pattern in GENERIC_PATTERNS))
        score = 100
        if len(items) < 2:
            score -= 35
            issues.append(f"{label}条目偏少")
        if chars < 80:
            score -= 30
            issues.append(f"{label}正文偏薄")
        if generic_count:
            score -= min(30, generic_count * 10)
            issues.append(f"{label}含空泛/确认话术 {generic_count} 条")
        scores.append(max(0, score))
    return round(mean(scores)), issues[:12]


def _basis_to_goal_chain_score(template: dict[str, Any], positive_terms: list[str]) -> tuple[int, list[str]]:
    basis = " ".join(_section_body(template, "basis"))
    analysis = " ".join(_section_body(template, "student_analysis"))
    objectives = " ".join(_section_body(template, "objectives"))
    keypoints = " ".join(_section_body(template, "key_difficult_points"))
    issues = []
    score = 100
    for label, text in [("本课依据", basis), ("学情分析", analysis), ("教学目标", objectives), ("教学重难点", keypoints)]:
        hits = _hit_terms(text, positive_terms)
        if len(hits) < 1:
            score -= 18
            issues.append(f"{label}未命中本课核心词")
    if not (set(_hit_terms(objectives, positive_terms)) & set(_hit_terms(keypoints, positive_terms))):
        score -= 15
        issues.append("目标与重难点核心词没有形成呼应")
    if "课标候选" not in (basis + analysis + objectives + keypoints):
        score -= 12
        issues.append("前置字段未嵌入课标候选依据")
    return max(0, score), issues[:12]


def _episode_causality_score(template: dict[str, Any]) -> tuple[int, list[str]]:
    episodes = [item for item in template.get("process_episodes") or [] if isinstance(item, dict)]
    if not episodes:
        return 0, ["没有教学过程环节"]
    scores = []
    issues = []
    for episode in episodes:
        title = _clean(episode.get("episode_title"))
        basis = episode.get("derivation_basis") if isinstance(episode.get("derivation_basis"), dict) else {}
        why = _clean(basis.get("why_now"))
        transition = _clean(basis.get("transition_to_next") or basis.get("transition_from_previous"))
        evidence = _clean(basis.get("assessment_evidence"))
        score = 100
        if len(why) < 18 or any(pattern in why for pattern in CAUSAL_GENERIC_PATTERNS):
            score -= 35
            issues.append(f"{title}: 推进依据偏空")
        if len(transition) < 18 or any(pattern in transition for pattern in CAUSAL_GENERIC_PATTERNS):
            score -= 25
            issues.append(f"{title}: 过渡点题偏空")
        if len(evidence) < 16 or any(pattern in evidence for pattern in GENERIC_PATTERNS):
            score -= 25
            issues.append(f"{title}: 证据描述偏空")
        scores.append(max(0, score))
    return round(mean(scores)), issues[:12]


def _microstep_actionability_score(template: dict[str, Any]) -> tuple[int, list[str]]:
    episodes = [item for item in template.get("process_episodes") or [] if isinstance(item, dict)]
    if not episodes:
        return 0, ["没有环节可检查 micro-step"]
    scores = []
    issues = []
    for episode in episodes:
        title = _clean(episode.get("episode_title"))
        micro_steps = [item for item in episode.get("micro_steps") or [] if isinstance(item, dict)]
        score = 100
        if not micro_steps:
            score -= 55
            issues.append(f"{title}: 没有 micro-step")
        for micro in micro_steps:
            teacher = _clean(micro.get("teacher_action"))
            student = _clean(micro.get("student_action"))
            evidence = _clean(micro.get("evidence"))
            if len(teacher) < 12 or any(pattern in teacher for pattern in GENERIC_PATTERNS):
                score -= 12
                issues.append(f"{title}: micro 教师动作偏空")
            if len(student) < 10 or any(pattern in student for pattern in GENERIC_PATTERNS):
                score -= 10
                issues.append(f"{title}: micro 学生任务偏空")
            if len(evidence) < 10 or any(pattern in evidence for pattern in GENERIC_PATTERNS):
                score -= 10
                issues.append(f"{title}: micro 证据偏空")
        scores.append(max(0, score))
    return round(mean(scores)), issues[:12]


def _curriculum_embedding_score(template: dict[str, Any], curriculum: dict[str, Any], joined: str) -> tuple[int, list[str]]:
    issues = []
    score = 100
    if not curriculum.get("candidate_available"):
        score -= 45
        issues.append("未匹配课标候选切片")
    if len(curriculum.get("candidate_refs") or []) <= 0:
        score -= 35
        issues.append("课标候选 refs 为空")
    if "课标状态" in joined:
        score -= 25
        issues.append("教师正文仍出现空泛课标状态")
    embedded_sections = sum(
        1
        for key in ["basis", "student_analysis", "objectives", "key_difficult_points"]
        if "课标候选" in " ".join(_section_body(template, key))
    )
    if embedded_sections < 2:
        score -= 25
        issues.append("课标候选未嵌入多个前置字段")
    return max(0, score), issues


def _teacher_usefulness_score(template: dict[str, Any]) -> tuple[int, list[str]]:
    texts = _all_visible_text(template)
    joined = " ".join(texts)
    action_terms = ["观察", "说出", "指出", "比较", "选择", "完成", "调整", "展示", "说明", "记录", "尝试"]
    evidence_terms = ["证据", "作品", "学习单", "画面", "细节", "过程", "表达", "发现", "痕迹"]
    score = 100
    issues = []
    if len(_hit_terms(joined, action_terms)) < 4:
        score -= 30
        issues.append("教师/学生动作词不足")
    if len(_hit_terms(joined, evidence_terms)) < 3:
        score -= 25
        issues.append("可观察证据词不足")
    generic = _generic_hits(texts)
    if len(generic) > 8:
        score -= 25
        issues.append("空泛/确认话术过多")
    return max(0, score), issues[:12]


def _case_quality(case: dict[str, Any], response: dict[str, Any]) -> dict[str, Any]:
    template = response.get("single_lesson_template") if isinstance(response.get("single_lesson_template"), dict) else {}
    kernel = response.get("art_lesson_design_kernel_preview") if isinstance(response.get("art_lesson_design_kernel_preview"), dict) else {}
    curriculum = response.get("curriculum_standard_candidate_preview") if isinstance(response.get("curriculum_standard_candidate_preview"), dict) else {}
    record = response.get("preview_test_record") if isinstance(response.get("preview_test_record"), dict) else {}
    focus = kernel.get("lesson_focus") if isinstance(kernel.get("lesson_focus"), dict) else {}
    texts = _all_visible_text(template)
    joined = "\n".join(texts)
    topic_score, contamination_hits = _topic_contamination_score(joined, case["forbidden_terms"])
    section_score, section_issues = _section_depth_score(template)
    chain_score, chain_issues = _basis_to_goal_chain_score(template, case["positive_terms"])
    causality_score, causality_issues = _episode_causality_score(template)
    micro_score, micro_issues = _microstep_actionability_score(template)
    curriculum_score, curriculum_issues = _curriculum_embedding_score(template, curriculum, joined)
    usefulness_score, usefulness_issues = _teacher_usefulness_score(template)
    scores = {
        "topic_contamination_score": topic_score,
        "section_depth_score": section_score,
        "basis_to_goal_chain_score": chain_score,
        "episode_causality_score": causality_score,
        "microstep_actionability_score": micro_score,
        "curriculum_embedding_score": curriculum_score,
        "teacher_usefulness_score": usefulness_score,
    }
    issues = {
        "topic_contamination": contamination_hits,
        "section_depth": section_issues,
        "basis_to_goal_chain": chain_issues,
        "episode_causality": causality_issues,
        "microstep_actionability": micro_issues,
        "curriculum_embedding": curriculum_issues,
        "teacher_usefulness": usefulness_issues,
        "generic_text_examples": _generic_hits(texts),
        "focus_mismatch_flags": record.get("focus_mismatch_flags") or [],
    }
    expected_focus = _clean(case.get("expected_focus"))
    focus_id = _clean(focus.get("focus_id"))
    focus_ok = (not expected_focus) or focus_id == expected_focus
    overall = round(mean(scores.values()))
    hard_failures = []
    if not focus_ok:
        hard_failures.append(f"focus expected {expected_focus}, got {focus_id}")
    if contamination_hits:
        hard_failures.append(f"topic contamination: {', '.join(contamination_hits)}")
    if record.get("focus_mismatch_flags"):
        hard_failures.append("focus mismatch flags present")
    return {
        "case_id": case["case_id"],
        "file_name": response.get("upload_session", {}).get("file_name"),
        "lesson_title": (template.get("lesson_header") or {}).get("lesson_title"),
        "focus_id": focus_id,
        "expected_focus": expected_focus,
        "focus_ok": focus_ok,
        "quality_overall_score": overall,
        "scores": scores,
        "quality_band": "pass" if overall >= 78 and not hard_failures else ("watch" if overall >= 68 and not contamination_hits else "fail"),
        "hard_failures": hard_failures,
        "issues": issues,
        "template_episode_count": len(template.get("process_episodes") or []),
        "micro_step_count": sum(
            len(item.get("micro_steps") or [])
            for item in template.get("process_episodes") or []
            if isinstance(item, dict)
        ),
        "curriculum_candidate_count": len(curriculum.get("candidate_refs") or []) if isinstance(curriculum, dict) else 0,
        "preview_only": True,
        "formal_apply": False,
    }


def _write_report(result: dict[str, Any]) -> None:
    lines = [
        f"# {STAGE}",
        "",
        f"Status: `{result['status']}`",
        f"Overall average: `{result['quality_average_score']}`",
        "",
        "## Checks",
        "",
    ]
    for key, value in result["checks"].items():
        lines.append(f"- `{key}`: `{str(value).lower()}`")
    lines.extend(["", "## Cases", ""])
    for case in result["cases"]:
        lines.append(
            f"### {case['case_id']} - {case['lesson_title']} "
            f"({case['quality_band']}, {case['quality_overall_score']})"
        )
        lines.append("")
        lines.append(f"- focus: `{case['focus_id']}` expected `{case['expected_focus'] or 'not_fixed'}`")
        lines.append(f"- episodes/micro: `{case['template_episode_count']}` / `{case['micro_step_count']}`")
        lines.append(f"- curriculum candidates: `{case['curriculum_candidate_count']}`")
        for name in QUALITY_DIMENSIONS:
            lines.append(f"- `{name}`: `{case['scores'][name]}`")
        if case["hard_failures"]:
            lines.append(f"- hard failures: {', '.join(case['hard_failures'])}")
        notable = []
        for issue_values in case["issues"].values():
            if isinstance(issue_values, list):
                notable.extend(str(item) for item in issue_values[:2])
        if notable:
            lines.append("- notable issues:")
            for item in notable[:8]:
                lines.append(f"  - {item}")
        lines.append("")
    REPORT.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    cases = []
    for sample in SAMPLES:
        raw_text, file_name = sample["source"]()
        response = _build_response(raw_text, file_name)
        cases.append(_case_quality(sample, response))
    checks = {
        "all_cases_generated": len(cases) == len(SAMPLES),
        "all_cases_have_focus": all(bool(case["focus_id"]) for case in cases),
        "all_fixed_focus_cases_match_expected": all(case["focus_ok"] for case in cases),
        "no_topic_contamination": all(not case["issues"]["topic_contamination"] for case in cases),
        "no_focus_mismatch_flags": all(not case["issues"]["focus_mismatch_flags"] for case in cases),
        "all_curriculum_candidates_present": all(case["curriculum_candidate_count"] > 0 for case in cases),
        "all_microsteps_present": all(case["micro_step_count"] >= case["template_episode_count"] for case in cases),
        "all_quality_scores_above_watch_floor": all(case["quality_overall_score"] >= 68 for case in cases),
        "preview_only_no_formal_apply": all(case["preview_only"] and case["formal_apply"] is False for case in cases),
    }
    result = {
        "stage": STAGE,
        "status": "PASS" if all(checks.values()) else "FAIL",
        "quality_average_score": round(mean(case["quality_overall_score"] for case in cases)),
        "quality_dimensions": QUALITY_DIMENSIONS,
        "checks": checks,
        "cases": cases,
        "output_files": {
            "result": str(RESULT),
            "report": str(REPORT),
        },
        "notes": {
            "scope": "Quality regression baseline for real or representative lesson uploads. This does not call provider models and does not write formal lesson data.",
            "quality_gate": "PASS requires no cross-topic contamination, curriculum candidates, microsteps, and per-case score >= 68.",
            "next_stage": "Use failing dimensions to target R200E/R200F fixes before allowing model candidates into main text.",
        },
    }
    OUT.mkdir(parents=True, exist_ok=True)
    RESULT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    _write_report(result)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
