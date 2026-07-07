from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.xiaobei_ai import prep_room_real_upload_entry_preview_1013R_R103 as r103
from backend.xiaobei_ai import prep_room_single_lesson_viewmodel_1013R_R10 as r10
from backend.xiaobei_ai import prep_room_uploaded_lesson_readonly_preview_1013R_R101A as r101a

STAGE = "1013R_R97B_P2B_REAL_READONLY_SHELL_USES_SINGLE_TEMPLATE"
OUT = ROOT / "outputs" / "PREP_ROOM_RENDER_CANVAS_DEEPEN_V1" / STAGE
HTML = (
    ROOT
    / "outputs"
    / "PREP_ROOM_RENDER_CANVAS_DEEPEN_V1"
    / "1013R_R97B_TEACHER_SHELL_EXPERIENCE_POLISH_AND_STALE_CONTENT_CLEANUP"
    / "r97b_clean_shell_context_preview.html"
)
CONTRACT = OUT / "r97b_p2b_readonly_payload_contract.json"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(read(path))


def body_of(text: str, fn_name: str) -> str:
    match = re.search(rf"function\s+{re.escape(fn_name)}\s*\([^)]*\)\s*\{{", text)
    if not match:
        return ""
    index = match.end()
    depth = 1
    while index < len(text) and depth:
        char = text[index]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
        index += 1
    return text[match.end() : index - 1]


def sample_upload_text() -> str:
    return "\n".join(
        [
            "课时1《穿穿编编》教案",
            "所属大单元：第二单元 编织·纸艺",
            "年级：四年级",
            "课时目标：学生能说出编织的1-2个历史应用；能正确进行经纬交织的编织操作。",
            "教学过程",
            "1 导入 3分钟 出示编织实物，引出编织主题。",
            "2 认识经纬 5分钟 认识经线和纬线，理解交织原理。",
            "3 学生练习 18分钟 在底稿上完成经纬交织练习。",
            "材料说明：各色纸条、剪刀、编织PPT、编织底稿纸。",
            "评价要点：能说出编织的应用；经纬交织操作基本正确。",
        ]
    )


def template_from_payload(payload: dict[str, Any]) -> dict[str, Any]:
    top = payload.get("single_lesson_template")
    nested = (payload.get("prep_view_patch") or {}).get("single_lesson_template")
    if not isinstance(top, dict):
        return {}
    if top != nested:
        return {}
    return top


def template_shape_ok(template: dict[str, Any], required_keys: set[str]) -> bool:
    return required_keys.issubset(set(template.keys())) and bool(template.get("process_episodes"))


def episode_shape_ok(template: dict[str, Any]) -> bool:
    required = {
        "episode_id",
        "episode_title",
        "episode_goal",
        "teacher_organization",
        "student_learning",
        "micro_steps",
        "provenance",
        "teacher_review_required",
        "preview_only",
    }
    return all(required.issubset(set(episode.keys())) for episode in template.get("process_episodes") or [])


def main() -> int:
    contract = load_json(CONTRACT)
    required_keys = set(contract["template_required_keys"])
    html = read(HTML)
    template_render_body = body_of(html, "renderSingleLessonTemplateEpisodes")
    apply_body = body_of(html, "applyBackendPayload")

    free_payload = r10.build_single_lesson_viewmodel()
    uploaded_fixture_payload = r101a.build_uploaded_lesson_viewmodel_for_sample("sample_sparse_weaving")
    upload_session = r103.build_upload_session(sample_upload_text(), "p2b_sparse_weaving.txt")
    real_upload_payload = r103.build_readonly_viewmodel_from_upload_session(upload_session, enable_teacher_model=False)

    payloads = {
        "free_lesson_readonly": free_payload,
        "uploaded_fixture_readonly": uploaded_fixture_payload,
        "real_upload_document_preview": real_upload_payload,
    }
    templates = {name: template_from_payload(payload) for name, payload in payloads.items()}

    inference_tokens = [
        "r97bP2InferEpisodeType",
        "r97bP2TeacherThreeSteps",
        "r97bP2StudentOutput",
        "r97bP2XiaojiaoReminder",
        "r97bP2ExtractKeyTalk",
        "r97bP2ImportedLessonP6Episode",
        "microStepsForBackendStep",
        "r114dExecutionForStep",
    ]

    required_stage_files = [
        "README.md",
        "r97b_p2b_readonly_payload_contract.json",
        "r97b_p2b_backend_payload_matrix.md",
        "r97b_p2b_frontend_template_first_smoke.md",
        "r97b_p2b_compatibility_notes.md",
        "REVIEW_PACKAGE_MANIFEST.json",
    ]

    checks = {
        "all_stage_files_exist": all((OUT / name).exists() for name in required_stage_files),
        "contract_exists": CONTRACT.exists(),
        "free_payload_has_single_lesson_template": bool(templates["free_lesson_readonly"]),
        "uploaded_fixture_payload_has_single_lesson_template": bool(templates["uploaded_fixture_readonly"]),
        "real_upload_payload_has_single_lesson_template": bool(templates["real_upload_document_preview"]),
        "all_templates_match_contract_shape": all(template_shape_ok(template, required_keys) for template in templates.values()),
        "all_templates_have_episode_shape": all(episode_shape_ok(template) for template in templates.values()),
        "backend_payloads_keep_template_in_prep_view_patch": all(
            payload.get("single_lesson_template") == (payload.get("prep_view_patch") or {}).get("single_lesson_template")
            for payload in payloads.values()
        ),
        "render_contract_mentions_single_lesson_template": all(
            "single_lesson_template_slot" in payload.get("render_contract", {})
            or "single_lesson_template" in payload.get("render_contract", {}).get("renderer_should_consume", [])
            for payload in payloads.values()
        ),
        "frontend_has_p2b_metadata": "script-1013R-R97B-P2B-real-readonly-shell-single-template" in html,
        "frontend_has_template_first_functions": "function r97bP2BSingleLessonTemplateFromPayload" in html
        and "function renderSingleLessonTemplateEpisodes" in html,
        "frontend_template_renderer_uses_shared_renderer": "renderUnifiedLessonProcessStep" in template_render_body,
        "frontend_template_renderer_does_not_infer_pedagogy": bool(template_render_body)
        and not any(token in template_render_body for token in inference_tokens),
        "apply_backend_payload_prefers_template_before_legacy": "renderSingleLessonTemplateEpisodes(singleLessonTemplate, payload)" in apply_body
        and "renderBackendEpisodes(legacySteps, payload)" in apply_body,
        "legacy_process_steps_compatibility_only_marker": "data-r97b-p2b-legacy-process-steps-compatibility-only" in html,
        "window_p2b_status_exists": "__R97B_P2B_REAL_READONLY_SHELL_USES_SINGLE_TEMPLATE__" in html,
        "no_formal_apply": all(payload.get("formal_apply") is False or payload.get("boundary", {}).get("formal_apply_performed") is False for payload in payloads.values()),
        "no_database_write": all(payload.get("boundary", {}).get("database_written") is False for payload in payloads.values()),
        "no_feishu_write": all(payload.get("boundary", {}).get("feishu_written") is False for payload in payloads.values()),
        "no_memory_write": all(payload.get("boundary", {}).get("memory_written") is False for payload in payloads.values()),
        "no_R21_R36_core_modified": contract["boundary"]["R21_modified"] is False and contract["boundary"]["R36_modified"] is False,
        "no_provider_model_call_added": contract["boundary"]["provider_model_call_added"] is False,
        "no_R95_executed": contract["boundary"]["R95_executed"] is False,
    }

    result = {
        "stage": STAGE,
        "status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "payload_summary": {
            name: {
                "viewmodel_type": payload.get("viewmodel_type"),
                "template_type": templates[name].get("template_type"),
                "route": templates[name].get("route"),
                "episode_count": len(templates[name].get("process_episodes") or []),
                "boundary_provider_called": payload.get("boundary", {}).get("provider_called"),
                "boundary_model_called": payload.get("boundary", {}).get("model_called"),
            }
            for name, payload in payloads.items()
        },
        "notes": {
            "p2b_scope": "backend owns single_lesson_template; frontend renders template object first",
            "compatibility": "legacy process_steps remain for existing panels and fallback only",
            "next_stage": "R97B_P2C_ADAPTER_COMPLETION_DEMOTION should classify and thin adapter-side completion helpers",
        },
        "boundary": contract["boundary"],
    }
    OUT.mkdir(parents=True, exist_ok=True)
    output_path = OUT / "validate_1013R_R97B_P2B_real_readonly_shell_single_template_result.json"
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
