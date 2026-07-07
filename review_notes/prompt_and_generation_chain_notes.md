# Prompt And Generation Chain Notes

## Current Suspected Failure

The user reports that when testing `足下生辉`, the visible lesson draft still contains unrelated content such as:

```text
海洋生物
拼贴 / 拼板
材料收集
废旧材料
```

That means the current system can still leak cross-lesson material into teacher-visible fields, even after the R200D validator reports PASS.

## Current Upload Chain

The upload route is centered in:

```text
backend_chain/prep_room_real_upload_entry_preview_1013R_R103.py
```

Important flow:

```text
uploaded document
-> text extractor R107A
-> upload session
-> R112 import lesson understanding
-> R114A understanding graph
-> R114B teacher execution map
-> R114C field projection
-> R97B_P3 derivation spine
-> R200A art lesson design kernel
-> R200C curriculum candidate binding
-> R200B candidate reasoning
-> readonly response / frontend preview
```

The audit should verify which layer wins when multiple fields provide basis, student analysis, objectives, key points, episode reasoning, and micro-steps.

## Model Prompt Location

Provider-backed reasoning is in:

```text
backend_chain/prep_room_art_lesson_reasoning_candidate_1013R_R200B.py
```

Search for:

```text
system_prompt
_call_provider
_normalize_model_candidate
_normalize_episode_reasoning
build_art_lesson_reasoning_candidate_preview
```

Known contract:

```text
candidate_only = true
teacher_review_required = true
fallback_visible_as_main_text = false
official_curriculum_claim_created = false
```

Audit risk:

```text
Even if candidate-only is marked correctly, downstream normalization or frontend display may still make candidate text look like confirmed teacher draft.
```

## Deterministic Kernel Risk

R200A deterministic filling is in:

```text
backend_chain/prep_room_art_lesson_design_kernel_1013R_R200A.py
```

Search for:

```text
_lesson_focus
_refined_basis_body
_refined_student_analysis_body
_refined_objectives_body
_refined_keypoints_body
_generic_micro_candidates
_cross_topic_forbidden_terms
```

Audit risk:

```text
The kernel currently tries to create complete teaching text from incomplete upload evidence.
When uploaded evidence is thin, it may fall back to generic art-method phrases or another focus template.
```

## Why R200D Is Not Enough

R200D checks:

```text
topic_contamination
section_depth
basis_to_goal_chain
episode_causality
microstep_actionability
curriculum_embedding
teacher_usefulness
```

But the current validator uses synthetic `足下生辉` input and selected docx samples. It may not replay the user's exact uploaded document, exact runtime flags, exact persisted preview record, or exact frontend-visible projection.

Required next validator upgrade:

```text
R200E should capture exact frontend-visible fields after R103 response assembly:
- basis
- student_analysis
- objectives
- key_difficult_points
- preparation
- process_episodes
- right rail teacher-readable summary
- reasoning/candidate ledger
```

It should also include a hard deny-list per active lesson focus:

```text
足下生辉 forbids: 海洋, 海洋生物, 废旧材料, 拼贴, 拼板, 渐变, 青绿山水
走进海洋世界 forbids: 鞋底, 鞋面, 足下生辉, 青绿山水
青绿山水 forbids: 鞋底, 海洋生物, 废旧材料, 拼贴
```

## Recommended Next Step

Do not add more curriculum or export features before this is fixed.

Recommended next stage:

```text
1013R_R200E_FRONTEND_VISIBLE_CONTAMINATION_GUARD
```

Goal:

```text
Use the exact latest upload/session payload and assert that no forbidden cross-topic terms appear in any teacher-visible field.
```

