from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.xiaobei_ai import prep_room_document_text_extractor_1013R_R107A as extractor
from backend.xiaobei_ai import prep_room_real_upload_entry_preview_1013R_R103 as r103


STAGE = "1013R_R200A_ART_LESSON_DESIGN_KERNEL_PREVIEW"
OUT = ROOT / "outputs" / "PREP_ROOM_RENDER_CANVAS_DEEPEN_V1" / STAGE
HTML = (
    ROOT
    / "outputs"
    / "PREP_ROOM_RENDER_CANVAS_DEEPEN_V1"
    / "1013R_R97B_TEACHER_SHELL_EXPERIENCE_POLISH_AND_STALE_CONTENT_CLEANUP"
    / "r97b_clean_shell_context_preview.html"
)
QINGLV = ROOT / "knowledge-base" / "lesson-cases"
OCEAN = ROOT / "knowledge-base" / "_parsed" / "kb_art_g3_lesson_case_1_eeabeca815.txt"


def _build_qinglv() -> dict[str, Any]:
    path = sorted(QINGLV.glob("*20952689b0*.docx"))[0]
    extracted = extractor.extract_document_text(str(path), original_filename=path.name, enable_model_ocr=False)
    session = r103.build_upload_session(str(extracted.get("text") or ""), path.name)
    return r103.build_readonly_viewmodel_from_upload_session(session, enable_teacher_model=False)


def _build_ocean() -> dict[str, Any]:
    raw_text = OCEAN.read_text(encoding="utf-8")
    session = r103.build_upload_session(raw_text, OCEAN.name)
    return r103.build_readonly_viewmodel_from_upload_session(session, enable_teacher_model=False)


def _build_material_art() -> dict[str, Any]:
    path = sorted(QINGLV.glob("*67d6ab622f*.docx"))[0]
    extracted = extractor.extract_document_text(str(path), original_filename=path.name, enable_model_ocr=False)
    session = r103.build_upload_session(str(extracted.get("text") or ""), path.name)
    return r103.build_readonly_viewmodel_from_upload_session(session, enable_teacher_model=False)


def _build_shoe_observation_smoke() -> dict[str, Any]:
    raw_text = "\n".join(
        [
            "课题：《足下生辉》教案",
            "年级：三年级",
            "单元：第五单元 足下生辉",
            "本课引导学生观察生活中的鞋，也可以比较不同颜色和材料的鞋。",
            "教学目标：学生从正面、侧面、后面观察一双鞋，说出鞋面、鞋底、鞋带和局部纹样的特点。",
            "教学过程",
            "1. 引入 5分钟 出示不同民族、不同时代的鞋，引导学生提出问题。",
            "2. 观察指导 10分钟 学生观察自己带来的鞋，比较正面、侧面和局部细节。",
            "3. 动手写生 20分钟 学生用线条画出鞋的外形、结构和主要细节。",
            "4. 展示与小结 5分钟 学生说出自己观察到的鞋的一个特点和画面调整。",
        ]
    )
    session = r103.build_upload_session(raw_text, "课时1_走过四季_画画鞋_教案.docx")
    return r103.build_readonly_viewmodel_from_upload_session(session, enable_teacher_model=False)


def _function_body(html: str, fn_name: str) -> str:
    match = re.search(rf"function\s+{re.escape(fn_name)}\s*\([^)]*\)\s*\{{", html)
    if not match:
        return ""
    index = match.end()
    depth = 1
    while index < len(html) and depth:
        char = html[index]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
        index += 1
    return html[match.end() : index - 1]


def _inspect(payload: dict[str, Any]) -> dict[str, Any]:
    template = payload.get("single_lesson_template") or {}
    current_sections = ((payload.get("prep_view_patch") or {}).get("current_lesson") or {}).get("sections") or []
    kernel = payload.get("art_lesson_design_kernel_preview") or {}
    curriculum = kernel.get("curriculum_standard_control") or {}
    cross_topic_guard = kernel.get("cross_topic_guard") if isinstance(kernel.get("cross_topic_guard"), dict) else {}
    episodes = template.get("process_episodes") or []
    micro_steps = [
        micro
        for episode in episodes
        for micro in (episode.get("micro_steps") or [])
        if isinstance(micro, dict)
    ]
    record = payload.get("preview_test_record") or {}
    basis = _section_body(template, "basis")
    analysis = _section_body(template, "student_analysis")
    objectives = _section_body(template, "objectives")
    keypoints = _section_body(template, "key_difficult_points")
    return {
        "kernel_status": kernel.get("kernel_status"),
        "lesson_focus": kernel.get("lesson_focus") or {},
        "cross_topic_guard": cross_topic_guard,
        "chain_checks": kernel.get("chain_checks") or {},
        "curriculum_interpretation_status": curriculum.get("interpretation_status"),
        "official_curriculum_claim_created": curriculum.get("official_curriculum_claim_created"),
        "real_curriculum_standard_full_text_parsed": curriculum.get("real_curriculum_standard_full_text_parsed"),
        "missing_required_fields": curriculum.get("missing_required_fields") or [],
        "basis_body": basis,
        "basis_source_gap_notes": ((template.get("basis") or [{}])[0] or {}).get("source_gap_notes") or [],
        "student_analysis_body": analysis,
        "objectives_body": objectives,
        "keypoints_body": keypoints,
        "basis_student_profile_refined": (template.get("renderer_policy") or {}).get("basis_student_profile_refined")
        is True,
        "episode_count": len(episodes),
        "micro_step_count": len(micro_steps),
        "micro_step_display_text": "\n".join(
            str(micro.get(key) or "")
            for micro in micro_steps
            for key in ["step_name", "teacher_action", "student_action", "screen_or_materials", "scaffolds", "evidence"]
        ),
        "empty_display_micro_step_count": sum(
            1
            for micro in micro_steps
            if not any(str(micro.get(key) or "").strip() for key in ["teacher_action", "student_action", "screen_or_materials", "scaffolds", "evidence"])
        ),
        "episode_method_count": len(kernel.get("episode_method_map") or []),
        "micro_method_count": len(kernel.get("microstep_method_map") or []),
        "all_episodes_have_art_kernel_basis": bool(episodes)
        and all(bool(episode.get("art_kernel_basis")) for episode in episodes),
        "all_microsteps_have_art_kernel_basis": bool(micro_steps)
        and all(bool(micro.get("art_kernel_basis")) for micro in micro_steps),
        "all_episodes_derivation_show_pedagogy": bool(episodes)
        and all(bool((episode.get("derivation_basis") or {}).get("pedagogy_role")) for episode in episodes),
        "provider_packet_preview_present": isinstance(kernel.get("provider_reasoning_packet_preview"), dict),
        "template_embeds_kernel": isinstance(template.get("art_lesson_design_kernel_preview"), dict),
        "template_renderer_policy_marks_kernel": (template.get("renderer_policy") or {}).get(
            "art_lesson_design_kernel_applied"
        )
        is True,
        "current_sections_have_kernel_basis": bool(current_sections)
        and all(bool(section.get("art_kernel_basis")) for section in current_sections if isinstance(section, dict)),
        "runtime_event_ids": [event.get("event_id") for event in payload.get("runtime_progress_events") or []],
        "record_art_kernel_status": record.get("art_kernel_status"),
        "record_curriculum_status": record.get("curriculum_standard_interpretation_status"),
        "boundary": payload.get("boundary") or {},
    }


def _visible_text(inspected: dict[str, Any]) -> str:
    return "\n".join(
        str(item)
        for key in ["basis_body", "student_analysis_body", "objectives_body", "keypoints_body", "micro_step_display_text"]
        for item in ([inspected.get(key)] if isinstance(inspected.get(key), str) else inspected.get(key) or [])
    )


def _section_body(template: dict[str, Any], key: str) -> list[str]:
    value = template.get(key)
    if not isinstance(value, list) or not value:
        return []
    body = value[0].get("body") if isinstance(value[0], dict) else []
    return [str(item) for item in body or [] if str(item).strip()]


def _basis_has_no_duplicate_position(inspected: dict[str, Any]) -> bool:
    body = inspected["basis_body"]
    joined = "\n".join(body)
    return (
        len(body) >= 2
        and "所属学习位置" not in joined
        and "学习位置为" not in joined
        and "上传原稿定位" not in joined
        and "教材版本、册次、页码" not in joined
        and bool(inspected["basis_source_gap_notes"])
    )


def _student_analysis_has_profile_layers(inspected: dict[str, Any]) -> bool:
    body = inspected["student_analysis_body"]
    joined = "\n".join(body)
    return (
        len(body) >= 5
        and "三年级学生" in joined
        and any(token in joined for token in ["前置经验", "前序"])
        and any(token in joined for token in ["本课难点", "难点"])
        and any(token in joined for token in ["技法", "材料基础", "材料与表现基础", "绘画与表达基础"])
        and "真实学情缺口" in joined
        and "回顾引入" not in joined
        and "示范讲解" not in joined
    )


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    html = HTML.read_text(encoding="utf-8")
    bridge = _function_body(html, "renderR97BP3DerivationBridge")
    micro_text = _function_body(html, "r97bP3MicroBasisText")
    qinglv = _build_qinglv()
    ocean = _build_ocean()
    material_art = _build_material_art()
    shoe_observation = _build_shoe_observation_smoke()
    # Test records are attached by route handlers, not direct ViewModel builders.
    q_record_response, _status = r103.handle_upload_entry_preview(
        {
            "raw_text": "\n".join(
                [
                    "课题：《R200A测试课》教案",
                    "年级：三年级",
                    "单元：色彩测试单元",
                    "教学过程",
                    "1. 导入 3分钟 出示两组颜色图片，引导学生说一说颜色是怎样变化的。",
                    "2. 实践 15分钟 学生选择两种颜色，尝试画出一组由深到浅的色彩过渡。",
                    "3. 展评 5分钟 学生展示作品，说出哪里体现了颜色逐步变化。",
                ]
            ),
            "file_name": "r200a_kernel_record_smoke.txt",
        }
    )
    q = _inspect(qinglv)
    o = _inspect(ocean)
    m = _inspect(material_art)
    s = _inspect(shoe_observation)
    record_inspect = _inspect(q_record_response)
    shoe_visible_text = _visible_text(s)
    color_visible_text = _visible_text(q)
    checks = {
        "html_has_r200a_metadata": "script-1013R-R200A-art-lesson-design-kernel-preview" in html,
        "html_shows_pedagogy_and_standard_status": "教学法" in bridge
        and "课标候选依据" in bridge
        and "pedagogy_role" in micro_text,
        "qinglv_kernel_ready_with_curriculum_candidate_refs": q["kernel_status"] == "KERNEL_READY_WITH_CURRICULUM_CANDIDATE_REFS"
        and q["curriculum_interpretation_status"] == "candidate_interpretation_pending_teacher_review",
        "ocean_kernel_ready_with_curriculum_candidate_refs": o["kernel_status"] == "KERNEL_READY_WITH_CURRICULUM_CANDIDATE_REFS"
        and o["curriculum_interpretation_status"] == "candidate_interpretation_pending_teacher_review",
        "material_art_kernel_classified_correctly": m["kernel_status"] == "KERNEL_READY_WITH_CURRICULUM_CANDIDATE_REFS"
        and (m["lesson_focus"] or {}).get("focus_id") == "material_transformation_expression",
        "shoe_observation_not_misclassified_as_color_gradation": s["kernel_status"] == "KERNEL_READY_WITH_CURRICULUM_CANDIDATE_REFS"
        and (s["lesson_focus"] or {}).get("focus_id") == "shoe_observation_drawing_expression"
        and "渐变" not in "\n".join(s["basis_body"])
        and "颜色逐步" not in "\n".join(s["student_analysis_body"]),
        "cross_topic_guard_passed_for_all_smokes": all(
            (item.get("cross_topic_guard") or {}).get("passed") is True
            for item in [q, o, m, s, record_inspect]
        ),
        "cross_topic_guard_blocks_visible_old_topic_terms": not any(
            token in shoe_visible_text for token in ["色彩的渐变", "青绿山水", "青绿色阶", "石青", "石绿"]
        )
        and not any(token in color_visible_text for token in ["足下生辉", "画画鞋", "鞋底", "鞋带"]),
        "shoe_observation_objectives_and_keypoints_focus_specific": "鞋面结构" in "\n".join(s["objectives_body"])
        and "线描表达" in "\n".join(s["keypoints_body"])
        and "符号化的鞋" in "\n".join(s["keypoints_body"]),
        "shoe_observation_microsteps_have_focus_specific_display_fields": s["micro_step_count"] >= 3
        and s["empty_display_micro_step_count"] == 0
        and "观察角度" in s["micro_step_display_text"]
        and "鞋面" in s["micro_step_display_text"]
        and "线条" in s["micro_step_display_text"],
        "basis_deduped_and_gap_demoted": _basis_has_no_duplicate_position(m)
        and _basis_has_no_duplicate_position(q),
        "student_analysis_has_profile_layers": _student_analysis_has_profile_layers(m)
        and _student_analysis_has_profile_layers(q),
        "official_standard_not_faked": q["official_curriculum_claim_created"] is False
        and o["official_curriculum_claim_created"] is False
        and q["real_curriculum_standard_full_text_parsed"] is False
        and o["real_curriculum_standard_full_text_parsed"] is False,
        "remaining_standard_fields_visible": bool(q["missing_required_fields"])
        and "standard_ref_ids" not in q["missing_required_fields"],
        "episode_and_micro_methods_mapped": q["episode_method_count"] == q["episode_count"]
        and o["episode_method_count"] == o["episode_count"]
        and q["micro_method_count"] == q["micro_step_count"]
        and o["micro_method_count"] == o["micro_step_count"],
        "template_and_sections_embed_kernel": q["template_embeds_kernel"]
        and q["template_renderer_policy_marks_kernel"]
        and q["current_sections_have_kernel_basis"],
        "episodes_and_microsteps_embed_kernel_basis": q["all_episodes_have_art_kernel_basis"]
        and q["all_microsteps_have_art_kernel_basis"]
        and q["all_episodes_derivation_show_pedagogy"],
        "provider_packet_preview_only": q["provider_packet_preview_present"]
        and q["boundary"].get("provider_called") is False
        and q["boundary"].get("model_called") is False,
        "runtime_progress_mentions_kernel": "art_lesson_kernel_built" in q["runtime_event_ids"],
        "record_includes_kernel_status": record_inspect["record_art_kernel_status"] == "KERNEL_READY_WITH_CURRICULUM_CANDIDATE_REFS"
        and record_inspect["record_curriculum_status"] == "candidate_interpretation_pending_teacher_review",
        "preview_only": q["boundary"].get("formal_apply_performed") is False
        and o["boundary"].get("formal_apply_performed") is False,
    }
    result = {
        "stage": STAGE,
        "status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "qinglv": q,
        "ocean": o,
        "material_art": m,
        "shoe_observation": s,
        "record_smoke": record_inspect,
        "notes": {
            "scope": "Attach curriculum-control status, candidate curriculum slice refs, and elementary art pedagogy kernel before provider reasoning.",
            "not_done": "No official curriculum confirmation, no provider/model call, no formal apply.",
            "next_stage": "R200B can call provider with this kernel as candidate-only context.",
        },
    }
    output = OUT / "validate_1013R_R200A_art_lesson_design_kernel_preview_result.json"
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
