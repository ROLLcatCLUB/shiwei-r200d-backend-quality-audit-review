from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.xiaobei_ai import prep_room_real_upload_entry_preview_1013R_R103 as r103


STAGE = "1013R_R97B_P2D_UPLOAD_PREVIEW_TEST_RECORDS"
OUT = ROOT / "outputs" / "PREP_ROOM_RENDER_CANVAS_DEEPEN_V1" / STAGE
JSONL = OUT / "r97b_upload_preview_test_records.jsonl"
LATEST = OUT / "r97b_upload_preview_test_record_latest.json"
HTML = (
    ROOT
    / "outputs"
    / "PREP_ROOM_RENDER_CANVAS_DEEPEN_V1"
    / "1013R_R97B_TEACHER_SHELL_EXPERIENCE_POLISH_AND_STALE_CONTENT_CLEANUP"
    / "r97b_clean_shell_context_preview.html"
)


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(read(path))


def last_jsonl(path: Path) -> dict[str, Any]:
    lines = [line.strip() for line in read(path).splitlines() if line.strip()]
    return json.loads(lines[-1]) if lines else {}


def sample_text() -> str:
    return "\n".join(
        [
            "课时1《P2D测试课》教案",
            "年级：四年级",
            "所属大单元：测试单元",
            "课时目标：学生能观察材料特征，并说明自己的发现。",
            "教学过程",
            "1 导入 3分钟 出示材料，引导学生说发现。",
            "2 实践 20分钟 学生尝试用材料完成一处造型变化。",
            "3 展评 7分钟 学生交流作品中的材料选择理由。",
            "材料说明：纸材、剪刀、胶水。",
            "评价要点：能说明材料选择与作品效果的关系。",
        ]
    )


def main() -> int:
    response, status_code = r103.handle_upload_entry_preview(
        {
            "raw_text": sample_text(),
            "file_name": "p2d_upload_preview_test_record.txt",
            "enable_teacher_readable_model": False,
        }
    )
    record = response.get("preview_test_record") or {}
    latest = load_json(LATEST) if LATEST.exists() else {}
    last_line = last_jsonl(JSONL) if JSONL.exists() else {}
    html = read(HTML)

    forbidden_record_keys = {"raw_text", "text", "document_text"}
    required_record_keys = {
        "record_id",
        "stage",
        "created_at",
        "trigger",
        "viewmodel_id",
        "session_id",
        "raw_sha256_short",
        "file_name",
        "lesson_title",
        "single_lesson_template_present",
        "template_episode_count",
        "source_status_counts",
        "runtime_progress_event_count",
        "runtime_progress_events",
        "raw_text_recorded",
        "formal_apply",
        "database_written",
    }
    required_stage_files = [
        "README.md",
        "r97b_p2d_upload_preview_test_record_contract.json",
        "r97b_p2d_test_record_usage.md",
        "REVIEW_PACKAGE_MANIFEST.json",
    ]

    checks = {
        "handler_returns_ok": status_code == 200 and response.get("ok") is True,
        "response_contains_preview_test_record": bool(record),
        "record_status_written": record.get("record_status") == "written",
        "jsonl_record_file_exists": JSONL.exists(),
        "latest_record_file_exists": LATEST.exists(),
        "latest_matches_response_record_id": latest.get("record_id") == record.get("record_id"),
        "jsonl_last_matches_response_record_id": last_line.get("record_id") == record.get("record_id"),
        "record_stage_is_p2d": latest.get("stage") == STAGE,
        "record_has_required_keys": required_record_keys.issubset(set(latest.keys())),
        "record_has_no_raw_text_keys": not forbidden_record_keys.intersection(set(latest.keys())),
        "record_raw_text_recorded_false": latest.get("raw_text_recorded") is False,
        "record_single_template_present": latest.get("single_lesson_template_present") is True,
        "record_template_episode_count_positive": int(latest.get("template_episode_count") or 0) > 0,
        "record_keeps_preview_only_boundary": latest.get("preview_only") is True
        and latest.get("formal_apply") is False
        and latest.get("database_written") is False,
        "record_reports_no_model_call": latest.get("provider_called") is False and latest.get("model_called") is False,
        "record_includes_runtime_progress_events": isinstance(latest.get("runtime_progress_events"), list)
        and int(latest.get("runtime_progress_event_count") or 0) >= 1,
        "html_has_p2d_metadata": "script-1013R-R97B-P2D-upload-preview-test-records" in html,
        "html_exposes_current_record_window": "__R97B_UPLOAD_PREVIEW_TEST_RECORD__" in html,
        "html_exposes_p2d_status_window": "__R97B_P2D_UPLOAD_PREVIEW_TEST_RECORDS__" in html,
        "html_has_p2d_document_marker": "data-1013r-r97b-p2d-upload-preview-test-records" in html,
        "html_bottom_context_mentions_test_record": "测试记录：" in html,
        "html_supports_explicit_upload_api_base": "uploadApiBase" in html
        and "apiBase" in html
        and "cleanedBase" in html
        and "endpointCandidates" in html,
        "all_stage_files_exist": all((OUT / name).exists() for name in required_stage_files),
        "no_formal_apply_marker": "formal_apply: false" in html or '"formal_apply":false' in html,
        "no_database_write_marker": "database_written: false" in html or '"database_written":false' in html,
    }

    result = {
        "stage": STAGE,
        "status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "latest_record": latest,
        "record_paths": {
            "jsonl": str(JSONL),
            "latest": str(LATEST),
        },
        "notes": {
            "scope": "Preview-only local diagnostic records for upload testing communication.",
            "privacy": "Raw lesson text is not written into the test record.",
            "boundary": "This is not formal apply, not database write, not Feishu write, and not memory write.",
        },
    }
    OUT.mkdir(parents=True, exist_ok=True)
    output_path = OUT / "validate_1013R_R97B_P2D_upload_preview_test_records_result.json"
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
