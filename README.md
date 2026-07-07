# 1013R R200D Backend Quality Audit Review

This is a narrow GitHub review package for GPT/human audit.

It is not a formal apply package and not a production merge. It contains the current backend lesson-generation chain, recent validators, real lesson samples, and evidence outputs needed to review a serious quality problem:

```text
User-tested lesson: 足下生辉
Observed issue: the generated analysis can still contain unrelated lesson material such as 海洋生物, 拼贴/拼板, 材料收集, 废旧材料.
Interpretation: the system still has cross-lesson contamination or overly generic backend completion logic.
```

## What To Review First

1. `backend_chain/prep_room_real_upload_entry_preview_1013R_R103.py`
   - Main upload preview entry.
   - Controls whether teacher model / R200B candidate model is enabled.
   - Attaches R112/R114/R97B_P3/R200A/R200B/R200C outputs into one response.

2. `backend_chain/prep_room_art_lesson_design_kernel_1013R_R200A.py`
   - Rule/kernel layer that fills basis, student analysis, objectives, key points, preparation, episodes, and micro-steps.
   - Suspect area for deterministic cross-topic fallback and generic completion.

3. `backend_chain/prep_room_art_lesson_reasoning_candidate_1013R_R200B.py`
   - Provider-backed candidate reasoning layer.
   - Contains the model prompt and candidate normalization.
   - Candidate-only by contract, but should be audited for whether candidate text can leak into teacher-visible sections.

4. `backend_chain/prep_room_art_curriculum_standard_candidate_1013R_R200C.py`
   - Curriculum-standard candidate slice binding.
   - Should provide candidate refs only, not pretend to be formal standard interpretation.

5. `validators/validate_1013r_r200d_real_lesson_quality_regression.py`
   - Latest regression validator.
   - It currently passes structurally, but it does not fully catch the live UI contamination reported by the user.

## Evidence Included

- `sample_inputs/`
  - Real lesson case `.docx` files used by the regression chain:
    - 渐变的魅力
    - 走进青绿山水
    - 变废为宝的艺术
    - 走进海洋世界
    - 穿穿编编
  - The synthetic 足下生辉 sample is embedded in the R200D validator.

- `evidence_outputs/1013R_R200D_REAL_LESSON_QUALITY_REGRESSION/`
  - `r200d_real_lesson_quality_regression_report.md`
  - `validate_1013R_R200D_real_lesson_quality_regression_result.json`

- `evidence_outputs/1013R_R200B_ART_LESSON_REASONING_CANDIDATE_PREVIEW/`
  - R200B candidate reasoning outputs.

- `evidence_outputs/1013R_R200C_CURRICULUM_STANDARD_SLICE_BINDING_PREVIEW/`
  - Curriculum candidate binding outputs.

## Latest Local Validation

Run from the original `xiaobei-core` root:

```powershell
python scripts\validate_1013r_r200a_art_lesson_design_kernel_preview.py
python scripts\validate_1013r_r200b1_source_guard_real_sample_smoke.py
python scripts\validate_1013r_r200d_real_lesson_quality_regression.py
```

Latest compact result before packaging:

```text
R200A: PASS
R200B1: PASS
R200D: PASS
R200D quality_average_score: 94
```

Important: this PASS is not sufficient. The user still observed live output contamination. The validator needs to be strengthened to reproduce the real uploaded lesson and the exact frontend-visible fields.

## Audit Questions

1. Where can unrelated lesson material enter the `single_lesson_template`?
2. Does R200A deterministic fallback reuse generic focus templates too aggressively?
3. Does R200B model/candidate output get normalized or projected into teacher-visible sections without enough source isolation?
4. Does R103 combine old R112/R114/R97B_P3/R200A/R200B/R200C outputs in a way that allows stale fields to win?
5. Why does R200D structural PASS not catch the live 足下生辉 contamination?
6. Which frontend-visible fields should be added to the validator snapshot?
7. Should previously uploaded or sample lesson cases be isolated from the active upload session more strictly?

## Boundary

```text
preview only
no formal apply
no database write
no R21/R36 modification
no export
candidate reasoning must not overwrite formal teacher draft
```

