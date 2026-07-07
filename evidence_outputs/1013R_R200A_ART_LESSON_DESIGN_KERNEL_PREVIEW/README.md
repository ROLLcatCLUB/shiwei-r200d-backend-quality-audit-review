# 1013R_R200A_ART_LESSON_DESIGN_KERNEL_PREVIEW

## Purpose

R200A starts the next reasoning line after P3.

It does not call a provider model yet. It creates a readonly art lesson design kernel so later provider reasoning has a real structure to use instead of inventing teaching logic inside the renderer.

## What Changed

- Added `backend/xiaobei_ai/prep_room_art_lesson_design_kernel_1013R_R200A.py`.
- R103 now returns `art_lesson_design_kernel_preview`.
- `single_lesson_template` embeds `art_lesson_design_kernel_preview`.
- R200A-R1 now refines `basis` and `student_analysis` before rendering:
  - duplicate lesson-position sentences are demoted to `source_gap_notes`
  - textbook/version/page gaps no longer appear as numbered basis body
  - student analysis is split into grade cognition, prior experience, lesson difficulty, technique/material level, and real-class gap
- Template sections, process episodes, and micro-steps receive `art_kernel_basis`.
- Episode `derivation_basis` now carries:
  - `pedagogy_move`
  - `pedagogy_role`
  - `standard_alignment_status`
- Runtime progress includes `art_lesson_kernel_built`.
- Upload preview records now include:
  - `art_kernel_status`
  - `curriculum_standard_interpretation_status`
  - `official_curriculum_claim_created`
  - `real_curriculum_standard_full_text_parsed`
- The R97B process renderer shows:
  - 教学法
  - 课标状态

## Important Boundary

R200A is deliberately honest about the current curriculum-standard gap:

```text
curriculum_standard_interpretation_status = missing_structured_standard_ref
official_curriculum_claim_created = false
real_curriculum_standard_full_text_parsed = false
```

So this stage does not pretend that real official curriculum-standard text has been parsed.

It uses the older R6C curriculum-control contract as a control layer and adds elementary art pedagogy rules as a kernel preview.

## Boundary Flags

- Preview only.
- No provider/model call.
- No formal apply.
- No database write.
- No Feishu write.
- No memory write.
- No R21/R36 modification.
- No R95 export.
- No official curriculum claim.

## Validation

Commands run from `D:\Documents\SmartEdu\xiaobei-core`:

```powershell
python -m py_compile backend\xiaobei_ai\prep_room_art_lesson_design_kernel_1013R_R200A.py backend\xiaobei_ai\prep_room_real_upload_entry_preview_1013R_R103.py scripts\validate_1013r_r200a_art_lesson_design_kernel_preview.py
python scripts\validate_1013r_r200a_art_lesson_design_kernel_preview.py
python scripts\validate_1013r_r97b_p3_derivation_spine_single_lesson_template.py
python scripts\validate_1013r_r97b_p2h_runtime_progress_event_stream.py
python scripts\validate_1013r_r97b_p2d_upload_preview_test_records.py
python scripts\validate_1013r_r97b_p2i_episode_reading_flow_and_microstep_decomposition.py
python scripts\validate_1013r_r97b_p2f_upload_process_extraction_quality_repair.py
python scripts\validate_1013r_r97b_p2b_real_readonly_shell_single_template.py
python scripts\validate_1013r_r97b_p2c_adapter_completion_demotion.py
python scripts\validate_1013r_r97b_p2f_r2_source_grounded_student_xiaojiao_hints.py
python scripts\validate_1013r_r97b_p2f_r1_long_section_episode_split_repair.py
```

All listed validators passed.

The HTML inline scripts were checked with `node --check`; 20 scripts were checked and no failures were reported.

The validator also guards the concrete failure shown in manual review:

```text
material_art_kernel_classified_correctly = true
basis_deduped_and_gap_demoted = true
student_analysis_has_profile_layers = true
```

## Real Upload Smoke

Local service:

```text
http://127.0.0.1:18091
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
  "record_id": "p2d_20260707T104024Z_b2c5eb3cc9d3",
  "lesson_title": "青绿色阶练习",
  "kernel_status": "KERNEL_READY_WITH_STANDARD_GAP",
  "curriculum_status": "missing_structured_standard_ref",
  "official_curriculum_claim_created": false,
  "real_curriculum_standard_full_text_parsed": false,
  "episode_count": 7,
  "micro_step_count": 10,
  "all_episode_art_kernel_basis": true,
  "all_micro_art_kernel_basis": true,
  "model_called": false,
  "formal_apply": false
}
```

Additional material-transformation smoke:

```json
{
  "record_id": "p2d_20260707T112326Z_ef2f40999b0d",
  "lesson_title": "变废为宝的艺术",
  "focus_id": "material_transformation_expression",
  "basis": [
    "本课定位为“第二单元 守护生命的摇篮”中的《变废为宝的艺术》。",
    "本课的学习重心，是让学生带着前序设计进入制作现场，在材料选择、结构处理和作品说明中，把原来的想法做出来、说清楚。"
  ],
  "student_analysis_layer_count": 5,
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
art_lesson_kernel_built
source_gaps_checked
model_quality_checked
readonly_preview_ready
preview_test_record_written
```

## Next Stage

R200B should be the first provider-backed reasoning stage on top of this kernel:

```text
single_lesson_template
+ lesson_derivation_spine_preview
+ art_lesson_design_kernel_preview
-> provider candidate only
-> strict parser
-> teacher review
-> no formal apply
```

The model output must not directly write the lesson body. It should produce candidate reasoning updates or field patches that can be reviewed.
