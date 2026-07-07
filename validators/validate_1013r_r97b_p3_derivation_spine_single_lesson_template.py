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


STAGE = "1013R_R97B_P3_DERIVATION_SPINE_FOR_SINGLE_LESSON_TEMPLATE"
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


def _section_body(template: dict[str, Any], key: str) -> list[str]:
    value = template.get(key)
    if not isinstance(value, list) or not value:
        return []
    body = value[0].get("body")
    return [str(item) for item in body or [] if str(item).strip()]


def _inspect(payload: dict[str, Any]) -> dict[str, Any]:
    template = payload.get("single_lesson_template") or {}
    current_sections = ((payload.get("prep_view_patch") or {}).get("current_lesson") or {}).get("sections") or []
    spine = payload.get("lesson_derivation_spine_preview") or {}
    episodes = template.get("process_episodes") or []
    current_by_id = {section.get("id"): section for section in current_sections if isinstance(section, dict)}
    section_keys = {
        "basis": "basis",
        "analysis": "student_analysis",
        "goals": "objectives",
        "keypoints": "key_difficult_points",
    }
    section_lengths = {section_id: len(_section_body(template, template_key)) for section_id, template_key in section_keys.items()}
    current_lengths = {
        section_id: len(current_by_id.get(section_id, {}).get("items") or [])
        for section_id in section_keys
    }
    episode_basis = [
        bool(episode.get("derivation_basis"))
        and bool((episode.get("derivation_basis") or {}).get("why_now"))
        and bool((episode.get("derivation_basis") or {}).get("transition_to_next"))
        for episode in episodes
    ]
    micro_basis = [
        bool(micro.get("derivation_basis"))
        and bool((micro.get("derivation_basis") or {}).get("transition_role"))
        and bool((micro.get("derivation_basis") or {}).get("episode_why_now"))
        for episode in episodes
        for micro in (episode.get("micro_steps") or [])
    ]
    return {
        "spine_status": spine.get("status"),
        "chain_checks": spine.get("chain_checks") or {},
        "section_lengths": section_lengths,
        "current_section_lengths": current_lengths,
        "basis_body": _section_body(template, "basis"),
        "analysis_body": _section_body(template, "student_analysis"),
        "goal_body": _section_body(template, "objectives"),
        "keypoint_body": _section_body(template, "key_difficult_points"),
        "episode_count": len(episodes),
        "all_episodes_have_derivation_basis": bool(episode_basis) and all(episode_basis),
        "all_microsteps_have_derivation_basis": bool(micro_basis) and all(micro_basis),
        "runtime_event_ids": [event.get("event_id") for event in payload.get("runtime_progress_events") or []],
        "template_has_embedded_spine": isinstance(template.get("lesson_derivation_spine"), dict),
        "template_renderer_policy_marks_spine": (template.get("renderer_policy") or {}).get("derivation_spine_applied") is True,
        "boundary": payload.get("boundary") or {},
    }


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


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    html = HTML.read_text(encoding="utf-8")
    renderer = _function_body(html, "renderUnifiedLessonProcessStep")
    bridge_renderer = _function_body(html, "renderR97BP3DerivationBridge")
    qinglv = _build_qinglv()
    ocean = _build_ocean()
    q = _inspect(qinglv)
    o = _inspect(ocean)
    checks = {
        "html_has_p3_metadata": "script-1013R-R97B-P3-derivation-spine-single-lesson-template" in html,
        "html_renders_derivation_bridge": "renderR97BP3DerivationBridge(derivationBasis)" in renderer
        and "data-r97b-p3-derivation-bridge" in bridge_renderer,
        "html_renders_micro_basis": "r97bP3MicroBasisText(item.derivation_basis)" in renderer,
        "qinglv_spine_passes": q["spine_status"] == "PASS_WITH_GAPS" and all(q["chain_checks"].values()),
        "ocean_spine_passes": o["spine_status"] == "PASS_WITH_GAPS" and all(o["chain_checks"].values()),
        "qinglv_sections_are_thicker": q["section_lengths"]["basis"] >= 2
        and q["section_lengths"]["analysis"] >= 2
        and q["section_lengths"]["goals"] >= 2
        and q["section_lengths"]["keypoints"] >= 2,
        "ocean_sections_are_thicker": o["section_lengths"]["basis"] >= 2
        and o["section_lengths"]["analysis"] >= 2
        and o["section_lengths"]["goals"] >= 2
        and o["section_lengths"]["keypoints"] >= 2,
        "current_lesson_sections_also_receive_spine": all(value >= 2 for value in q["current_section_lengths"].values()),
        "template_embeds_spine": q["template_has_embedded_spine"] and q["template_renderer_policy_marks_spine"],
        "episodes_have_derivation_basis": q["all_episodes_have_derivation_basis"] and o["all_episodes_have_derivation_basis"],
        "microsteps_have_derivation_basis": q["all_microsteps_have_derivation_basis"] and o["all_microsteps_have_derivation_basis"],
        "runtime_progress_mentions_spine": "derivation_spine_built" in q["runtime_event_ids"],
        "no_model_added": q["boundary"].get("model_called") is False and o["boundary"].get("model_called") is False,
        "preview_only": q["boundary"].get("formal_apply_performed") is False
        and o["boundary"].get("formal_apply_performed") is False,
    }
    result = {
        "stage": STAGE,
        "status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "qinglv": q,
        "ocean": o,
        "notes": {
            "scope": "Apply R114A/B/C-derived spine into current lesson sections and single_lesson_template.",
            "not_done": "No curriculum-standard runtime, no provider model call, no formal apply.",
            "purpose": "Make basis, analysis, goals, keypoints, process episodes, and micro-steps share one verifiable derivation spine.",
        },
    }
    output = OUT / "validate_1013R_R97B_P3_derivation_spine_single_lesson_template_result.json"
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
