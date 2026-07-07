# 1013R_R200B_ART_LESSON_REASONING_CANDIDATE_PREVIEW

## Goal

Run provider-backed art lesson reasoning on top of the R200A kernel, but expose the result only as a review candidate.

## What R200B Means

R200B is not formal lesson generation. It asks the provider to produce a candidate package that deepens:

- lesson basis
- student analysis
- objectives
- key/difficult points
- episode reasoning
- candidate micro-steps
- transition / point-back wording
- Xiaojiao reminder candidates

The candidate remains pending teacher review.

## Safety Boundary

- Candidate only.
- Preview only.
- Teacher review required.
- No formal apply.
- No database write.
- No memory or Feishu write.
- Does not overwrite `single_lesson_template`.
- Does not overwrite `current_lesson.sections`.
- Does not expose raw chain-of-thought.

## Runtime Event

R200B adds one progress event:

```text
art_reasoning_candidate_built
```

This event reports whether the candidate was generated, skipped, or failed. It does not mean the candidate was adopted into the formal lesson.

## Episode Repair

MiniMax-M3 sometimes returns section deepening but omits `episode_reasoning`.
R200B therefore has a narrow repair pass:

```text
first call: full art lesson reasoning candidate
repair call: only episode_reasoning / micro_steps, only when missing
```

The repair pass is still candidate-only and does not write into the lesson body.

## Validation

```powershell
python scripts\validate_1013r_r200b_art_lesson_reasoning_candidate_preview.py
python scripts\validate_1013r_r97b_p2j_runtime_progress_loading_ledger_consistency.py
python scripts\validate_1013r_r97b_p2h_runtime_progress_event_stream.py
python scripts\validate_1013r_r200a_art_lesson_design_kernel_preview.py
python scripts\validate_1013r_r97b_p3_derivation_spine_single_lesson_template.py
```

Latest live provider smoke passed with MiniMax-M3 and returned candidate content for section deepening and episode micro-step candidates. The latest pass produced 17 section-deepening items, 7 episode reasoning rows, and 12 micro-step candidates.
