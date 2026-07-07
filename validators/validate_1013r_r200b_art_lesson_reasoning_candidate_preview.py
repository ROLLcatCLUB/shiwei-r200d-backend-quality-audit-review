from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.xiaobei_ai import prep_room_document_text_extractor_1013R_R107A as extractor
from backend.xiaobei_ai import prep_room_real_upload_entry_preview_1013R_R103 as upload_preview


STAGE = "1013R_R200B_ART_LESSON_REASONING_CANDIDATE_PREVIEW"
OUTPUT_DIR = ROOT / "outputs" / "PREP_ROOM_RENDER_CANVAS_DEEPEN_V1" / STAGE
RESULT_PATH = OUTPUT_DIR / "validate_1013R_R200B_art_lesson_reasoning_candidate_preview_result.json"
HTML_PATH = ROOT / "outputs" / "PREP_ROOM_RENDER_CANVAS_DEEPEN_V1" / "1013R_R97B_TEACHER_SHELL_EXPERIENCE_POLISH_AND_STALE_CONTENT_CLEANUP" / "r97b_clean_shell_context_preview.html"


def _qinglv_docx() -> Path:
    matches = list((ROOT / "knowledge-base" / "lesson-cases").glob("*20952689b0*.docx"))
    if not matches:
        raise AssertionError("qinglv sample docx missing")
    return matches[0]


def _build_response(*, enable_art_reasoning_model: bool) -> dict:
    path = _qinglv_docx()
    extracted = extractor.extract_document_text(
        str(path),
        original_filename=path.name,
        enable_model_ocr=False,
    )
    if not extracted.get("ok"):
        raise AssertionError(f"document extraction failed: {extracted.get('status')}")
    session = upload_preview.build_upload_session(str(extracted.get("text") or ""), path.name)
    response = upload_preview.build_readonly_viewmodel_from_upload_session(
        session,
        enable_teacher_model=False,
        enable_art_reasoning_model=enable_art_reasoning_model,
    )
    response["document_extract"] = {key: value for key, value in extracted.items() if key != "text"}
    response["runtime_progress_events"] = upload_preview._build_preview_progress_events(
        response,
        trigger="document_upload",
        document_extract=response["document_extract"],
    )
    upload_preview._attach_upload_preview_test_record(response, "document_upload")
    return response


def _candidate_counts(candidate_preview: dict) -> dict[str, int]:
    candidate = candidate_preview.get("candidate") if isinstance(candidate_preview.get("candidate"), dict) else {}
    lesson_reasoning = candidate.get("lesson_reasoning") if isinstance(candidate.get("lesson_reasoning"), dict) else {}
    section_items = sum(len(value) for value in lesson_reasoning.values() if isinstance(value, list))
    episodes = candidate.get("episode_reasoning") if isinstance(candidate.get("episode_reasoning"), list) else []
    micro_steps = sum(len(item.get("micro_step_candidates") or []) for item in episodes if isinstance(item, dict))
    return {
        "section_items": section_items,
        "episode_reasoning": len(episodes),
        "micro_step_candidates": micro_steps,
    }


def main() -> int:
    default_response = _build_response(enable_art_reasoning_model=False)
    model_response = _build_response(enable_art_reasoning_model=True)
    html = HTML_PATH.read_text(encoding="utf-8")

    default_candidate = default_response.get("art_lesson_reasoning_candidate_preview") or {}
    model_candidate = model_response.get("art_lesson_reasoning_candidate_preview") or {}
    model_boundary = model_candidate.get("boundary") if isinstance(model_candidate.get("boundary"), dict) else {}
    response_boundary = model_response.get("boundary") or {}
    counts = _candidate_counts(model_candidate)
    events = model_response.get("runtime_progress_events") or []
    model_log = model_candidate.get("model_log") if isinstance(model_candidate.get("model_log"), dict) else {}
    packet_preview = model_candidate.get("provider_reasoning_packet_preview") if isinstance(model_candidate.get("provider_reasoning_packet_preview"), dict) else {}
    provider_status = model_log.get("provider_status") if isinstance(model_log.get("provider_status"), dict) else {}
    credentials_available = bool(provider_status.get("credential_available"))

    checks = {
        "default_response_has_r200b_disabled": default_candidate.get("status") == "disabled"
        and default_candidate.get("provider_called") is False
        and default_candidate.get("model_called") is False,
        "model_response_has_r200b_preview": model_candidate.get("stage") == STAGE,
        "provider_credentials_available_for_live_candidate": credentials_available,
        "provider_called_when_enabled": model_candidate.get("provider_called") is True,
        "model_called_when_enabled": model_candidate.get("model_called") is True,
        "candidate_status_success": model_candidate.get("status") == "model_success",
        "candidate_available": model_candidate.get("candidate_available") is True,
        "candidate_has_deepening_sections": counts["section_items"] >= 4,
        "candidate_has_episode_microsteps": counts["micro_step_candidates"] >= max(1, counts["episode_reasoning"]),
        "packet_includes_curriculum_candidate_refs": int(packet_preview.get("curriculum_candidate_ref_count") or 0) > 0,
        "packet_includes_curriculum_source_documents": packet_preview.get("curriculum_source_documents_included") is True,
        "packet_includes_cross_topic_guard": packet_preview.get("cross_topic_guard_included") is True,
        "candidate_is_preview_only": model_candidate.get("preview_only") is True
        and model_candidate.get("formal_apply") is False
        and model_boundary.get("candidate_only") is True
        and model_boundary.get("formal_apply_performed") is False,
        "candidate_not_written_to_template_or_current_lesson": model_boundary.get("single_lesson_template_written") is False
        and model_boundary.get("current_lesson_sections_overwritten") is False,
        "response_boundary_counts_r200b_provider_call": response_boundary.get("provider_called") is True
        and response_boundary.get("model_called") is True,
        "runtime_event_mentions_r200b_candidate": any(
            event.get("event_id") == "art_reasoning_candidate_built"
            and event.get("status") == "completed"
            and event.get("candidate_only") is True
            for event in events
            if isinstance(event, dict)
        ),
        "html_has_r200b_metadata": "script-1013R-R200B-art-lesson-reasoning-candidate-preview" in html,
        "html_renders_r200b_candidate_panel": "renderR200BReasoningCandidate" in html
        and "R200B 美术推理候选" in html,
        "html_loading_trace_has_r200b_event": "art_reasoning_candidate_built" in html,
        "raw_chain_of_thought_hidden": model_boundary.get("raw_chain_of_thought_exposed") is False
        and '"raw_chain_of_thought_exposed":false' in html,
    }

    result = {
        "stage": STAGE,
        "status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "sample": {
            "lesson_title": (model_response.get("prep_view_patch") or {}).get("current_lesson", {}).get("lesson_title"),
            "candidate_id": model_candidate.get("candidate_id"),
            "candidate_status": model_candidate.get("status"),
            "candidate_counts": counts,
            "provider_called": model_candidate.get("provider_called"),
            "model_called": model_candidate.get("model_called"),
            "provider_meta": {
                key: value
                for key, value in ((model_log.get("provider_meta") or {}) if isinstance(model_log.get("provider_meta"), dict) else {}).items()
                if key not in {"token", "api_key", "authorization"}
            },
            "model_payload_shape": model_candidate.get("model_payload_shape"),
            "provider_reasoning_packet_preview": packet_preview,
            "model_log": {
                key: value
                for key, value in model_log.items()
                if key not in {"provider_status", "provider_meta"}
            },
            "record_id": (model_response.get("preview_test_record") or {}).get("record_id"),
        },
        "notes": {
            "scope": "R200B uses a provider call only for candidate preview; it does not write or apply the candidate.",
            "old_model_chains": "validator calls build_readonly_viewmodel with enable_teacher_model=False and enable_art_reasoning_model=True to isolate R200B.",
        },
    }
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
