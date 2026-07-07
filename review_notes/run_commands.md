# Run Commands

Run these from the original `xiaobei-core` root, not from this review package:

```powershell
python scripts\validate_1013r_r200a_art_lesson_design_kernel_preview.py
python scripts\validate_1013r_r200b_art_lesson_reasoning_candidate_preview.py
python scripts\validate_1013r_r200c_curriculum_standard_slice_binding_preview.py
python scripts\validate_1013r_r200b1_source_guard_real_sample_smoke.py
python scripts\validate_1013r_r200d_real_lesson_quality_regression.py
```

Compact result helper:

```powershell
@'
import json, subprocess, sys
scripts = [
  r"scripts\validate_1013r_r200a_art_lesson_design_kernel_preview.py",
  r"scripts\validate_1013r_r200b1_source_guard_real_sample_smoke.py",
  r"scripts\validate_1013r_r200d_real_lesson_quality_regression.py",
]
for script in scripts:
    p = subprocess.run([sys.executable, script], text=True, capture_output=True, encoding="utf-8", errors="replace", timeout=120)
    print(script, "returncode", p.returncode)
    try:
        data = json.loads(p.stdout)
        failed = [k for k, v in data.get("checks", {}).items() if not v]
        print(json.dumps({"status": data.get("status"), "failed": failed, "quality_average_score": data.get("quality_average_score")}, ensure_ascii=False))
    except Exception:
        print(p.stdout[:1000])
        print(p.stderr[:1000])
'@ | python -
```

