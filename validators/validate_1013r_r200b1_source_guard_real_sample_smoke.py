from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.xiaobei_ai import prep_room_document_text_extractor_1013R_R107A as extractor
from backend.xiaobei_ai import prep_room_real_upload_entry_preview_1013R_R103 as r103


STAGE = "1013R_R200B1_SOURCE_GUARD_REAL_SAMPLE_SMOKE"
OUT = ROOT / "outputs" / "PREP_ROOM_RENDER_CANVAS_DEEPEN_V1" / STAGE
RESULT = OUT / "validate_1013R_R200B1_source_guard_real_sample_smoke_result.json"


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


def _build_response(raw_text: str, file_name: str) -> dict[str, Any]:
    session = r103.build_upload_session(raw_text, file_name)
    response = r103.build_readonly_viewmodel_from_upload_session(
        session,
        enable_teacher_model=False,
        enable_art_reasoning_model=False,
    )
    r103._attach_upload_preview_test_record(response, "raw_text_upload")
    return response


def _candidate_packet(response: dict[str, Any]) -> dict[str, Any]:
    candidate = response.get("art_lesson_reasoning_candidate_preview")
    if not isinstance(candidate, dict):
        return {}
    packet = candidate.get("provider_reasoning_packet_preview")
    return packet if isinstance(packet, dict) else {}


def _case_summary(case_id: str, response: dict[str, Any]) -> dict[str, Any]:
    template = response.get("single_lesson_template") if isinstance(response.get("single_lesson_template"), dict) else {}
    kernel = response.get("art_lesson_design_kernel_preview") if isinstance(response.get("art_lesson_design_kernel_preview"), dict) else {}
    curriculum = response.get("curriculum_standard_candidate_preview") if isinstance(response.get("curriculum_standard_candidate_preview"), dict) else {}
    record = response.get("preview_test_record") if isinstance(response.get("preview_test_record"), dict) else {}
    packet = _candidate_packet(response)
    guard = kernel.get("cross_topic_guard") if isinstance(kernel.get("cross_topic_guard"), dict) else {}
    boundary = response.get("boundary") if isinstance(response.get("boundary"), dict) else {}
    lesson_header = template.get("lesson_header") if isinstance(template.get("lesson_header"), dict) else {}
    return {
        "case_id": case_id,
        "lesson_title": lesson_header.get("lesson_title"),
        "focus_id": (kernel.get("lesson_focus") or {}).get("focus_id") if isinstance(kernel.get("lesson_focus"), dict) else None,
        "template_episode_count": len(template.get("process_episodes") or []),
        "cross_topic_guard_passed": guard.get("passed") is True,
        "cross_topic_guard_hit_count": guard.get("hit_count"),
        "curriculum_candidate_count": len(curriculum.get("candidate_refs") or []),
        "curriculum_source_documents_present": bool(curriculum.get("source_documents")),
        "r200b_packet_curriculum_ref_count": packet.get("curriculum_candidate_ref_count"),
        "r200b_packet_has_source_documents": packet.get("curriculum_source_documents_included") is True,
        "r200b_packet_has_cross_topic_guard": packet.get("cross_topic_guard_included") is True,
        "focus_mismatch_flags": record.get("focus_mismatch_flags") or [],
        "provider_called": boundary.get("provider_called"),
        "model_called": boundary.get("model_called"),
        "formal_apply": boundary.get("formal_apply_performed"),
    }


def main() -> int:
    cases = []
    for case_id, source in [
        ("shoe_observation", _shoe_upload_text()),
        ("color_gradation", _docx_text("*fd1b5bdf60*.docx")),
        ("material_transformation", _docx_text("*67d6ab622f*.docx")),
        ("ocean_theme", _docx_text("*eeabeca815*.docx")),
    ]:
        raw_text, file_name = source
        response = _build_response(raw_text, file_name)
        cases.append(_case_summary(case_id, response))

    checks = {
        "all_cases_have_template_episodes": all(case["template_episode_count"] > 0 for case in cases),
        "all_cross_topic_guards_pass": all(case["cross_topic_guard_passed"] for case in cases),
        "no_focus_mismatch_flags": all(not case["focus_mismatch_flags"] for case in cases),
        "all_cases_have_curriculum_candidates": all(int(case["curriculum_candidate_count"] or 0) > 0 for case in cases),
        "all_cases_have_curriculum_source_documents": all(case["curriculum_source_documents_present"] for case in cases),
        "all_r200b_packets_have_curriculum_refs": all(int(case["r200b_packet_curriculum_ref_count"] or 0) > 0 for case in cases),
        "all_r200b_packets_have_source_documents": all(case["r200b_packet_has_source_documents"] for case in cases),
        "all_r200b_packets_have_cross_topic_guard": all(case["r200b_packet_has_cross_topic_guard"] for case in cases),
        "preview_only_no_model_in_smoke": all(case["provider_called"] is False and case["model_called"] is False for case in cases),
        "no_formal_apply": all(case["formal_apply"] is False for case in cases),
    }
    result = {
        "stage": STAGE,
        "status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "cases": cases,
        "notes": {
            "scope": "Four-case smoke for R103/R200A/R200C/R200B packet readiness and source guard. Provider model is intentionally disabled here; R200B live provider is covered by validate_1013r_r200b_art_lesson_reasoning_candidate_preview.py.",
            "shoe_case_source": "synthetic upload text because no local 足下生辉 docx was found in knowledge-base/lesson-cases.",
        },
    }
    OUT.mkdir(parents=True, exist_ok=True)
    RESULT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
