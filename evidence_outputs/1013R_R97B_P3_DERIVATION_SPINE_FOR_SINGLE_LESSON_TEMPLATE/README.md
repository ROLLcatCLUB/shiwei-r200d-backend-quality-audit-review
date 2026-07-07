# 1013R_R97B_P3_DERIVATION_SPINE_FOR_SINGLE_LESSON_TEMPLATE

## Purpose

P3 adds a readonly derivation spine for the existing R97B single lesson template.

The goal is to make these parts belong to one inspectable chain:

- 本课依据
- 学情分析
- 教学目标
- 教学重难点
- 教学过程环节
- 环节内 micro-step

This is not a curriculum-standard runtime and not a new model reasoning stage.

## What Changed

- Added `backend/xiaobei_ai/prep_room_single_lesson_derivation_spine_1013R_R97B_P3.py`.
- R103 now builds `lesson_derivation_spine_preview` after R114A/B/C preview data is available.
- The spine is applied to both:
  - `single_lesson_template`
  - `prep_view_patch.current_lesson.sections`
- Each process episode receives `derivation_basis`.
- Each micro-step receives `derivation_basis`.
- The R97B renderer shows a small inline bridge for:
  - 推进依据
  - 过渡点题
  - 证据
- Micro-step expanded rows now include an `展开依据` line.
- Runtime progress events include `derivation_spine_built`.

## Boundary

- Preview only.
- No formal apply.
- No database write.
- No Feishu write.
- No memory write.
- No provider/model call added.
- No R21/R36 modification.
- No R95 export.
- No curriculum-standard runtime yet.

## Validation

Commands run from `D:\Documents\SmartEdu\xiaobei-core`:

```powershell
python -m py_compile backend\xiaobei_ai\prep_room_single_lesson_derivation_spine_1013R_R97B_P3.py backend\xiaobei_ai\prep_room_real_upload_entry_preview_1013R_R103.py scripts\validate_1013r_r97b_p3_derivation_spine_single_lesson_template.py
python scripts\validate_1013r_r97b_p3_derivation_spine_single_lesson_template.py
python scripts\validate_1013r_r97b_p2i_episode_reading_flow_and_microstep_decomposition.py
python scripts\validate_1013r_r97b_p2h_runtime_progress_event_stream.py
python scripts\validate_1013r_r97b_p2d_upload_preview_test_records.py
python scripts\validate_1013r_r97b_p2f_r2_source_grounded_student_xiaojiao_hints.py
python scripts\validate_1013r_r97b_p2b_real_readonly_shell_single_template.py
python scripts\validate_1013r_r97b_p2c_adapter_completion_demotion.py
python scripts\validate_1013r_r97b_p2f_upload_process_extraction_quality_repair.py
python scripts\validate_1013r_r97b_p2f_r1_long_section_episode_split_repair.py
```

All listed validators passed.

The HTML inline scripts were also checked with `node --check`; 20 scripts were checked and no failures were reported.

## Real Upload Smoke

Local service:

```text
http://127.0.0.1:18090
```

Route:

```text
POST /api/prep-room/uploaded-lesson-document-preview
```

Sample:

```text
knowledge-base/lesson-cases/kb_art_g3_lesson_case_2_20952689b0_课时2_青绿色阶练习_教学过程案例_试写稿.docx
```

Observed smoke result:

```json
{
  "ok": true,
  "record_id": "p2d_20260707T083238Z_b2c5eb3cc9d3",
  "lesson_title": "青绿色阶练习",
  "spine_status": "PASS_WITH_GAPS",
  "section_lengths": {
    "basis": 3,
    "analysis": 2,
    "goals": 3,
    "keypoints": 2
  },
  "episode_count": 7,
  "all_episode_derivation_basis": true,
  "all_micro_derivation_basis": true,
  "model_called": false,
  "formal_apply": false
}
```

Runtime events include:

```text
upload_input_received
document_text_extracted
upload_session_built
lesson_fields_projected
process_episodes_normalized
derivation_spine_built
source_gaps_checked
model_quality_checked
readonly_preview_ready
preview_test_record_written
```

## What This Does Not Solve Yet

P3 makes the current no-model chain more coherent and auditable. It does not yet provide a full curriculum-standard or teaching-method kernel.

The next larger reasoning stage should still be planned separately, likely after this order:

```text
single_lesson_template stable
-> derivation spine visible and validated
-> curriculum standard / art pedagogy kernel
-> provider-backed reasoning or graph takeover
-> export / formal apply
```
