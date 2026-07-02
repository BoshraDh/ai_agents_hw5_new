# TODO — משימות פרויקט

מקרא סטטוס: `[ ]` טרם התחיל · `[~]` בתהליך · `[x]` הושלם

**עדכון (v1.01):** לאחר קריאת מסמך המטלה הרשמי `ex05-AirLLM.pdf.pdf`, נוספו
Phase 0.5 (PRD כלכלי), הרחבות Phase 1 (מדידת TTFT/TPOT אמיתית, ניתוח כלכלי,
Model Roofline), ו-Phase 4 עודכן לכלול בדיקת עשן, שאלות המחקר הנדרשות, ודרישת
"README כדוח".

## Phase 0 — תכנון (מסמכים)
- [x] `docs/PRD.md` (עודכן v1.01 עם דרישות ex05 המלאות)
- [x] `docs/PLAN.md` (עודכן v1.01 עם ADR-4/5/6)
- [x] `docs/TODO.md` (קובץ זה)
- [x] `docs/PRD_model_loader.md`
- [x] `docs/PRD_airllm_execution.md`
- [x] `docs/PRD_quantization.md`
- [x] `docs/PRD_benchmark_reporting.md`
- [x] `docs/PRD_economic_analysis.md` (חדש — ניתוח כלכלי חובה, ex05 §5.5)
- [x] אישור כל מסמכי Phase 0 לפני מעבר ל-Phase 1

**Definition of Done:** כל 8 המסמכים קיימים ומכסים את כל דרישות `ex05-AirLLM.pdf`
+ `software_submission_guidelines-V3.pdf`, commit לכל אחד.

## Phase 1 — שלד קוד (ללא הרצה)
- [x] מבנה תיקיות `src/local_llm_bench/{sdk,services,shared}` + `__init__.py`-ים
- [x] `shared/constants.py`
- [x] `shared/version.py` (מתחיל מ-1.00)
- [x] `shared/config.py` — `ConfigManager`
- [x] `shared/gatekeeper.py` — `ApiGatekeeper`
- [x] `shared/hardware_probe.py` — `HardwareProbeMixin`
- [x] `shared/metrics.py` — `RunMetrics` (עם `ttft_sec`/`tpot_sec`/`estimated_power_wh` מתוקנים)
- [x] `shared/generation_timing.py` — `StreamingTimingMixin` (TTFT/TPOT אמיתיים דרך TextIteratorStreamer)
- [x] `services/model_loader_service.py` (מעודכן לשימוש ב-streaming timing)
- [x] `services/airllm_service.py` (מעודכן לשימוש ב-streaming timing + `layer_shards_saving_path`)
- [x] `services/quantization_service.py` (מעודכן לחלץ TTFT/TPOT מהשדות הטבעיים של Ollama)
- [x] `services/benchmark_service.py`
- [x] `services/report_service.py` (מורחב: `plot_breakeven`, `plot_model_roofline`)
- [x] `services/cost_analysis_service.py` — `CostAnalysisService` (חדש)
- [x] `sdk/sdk.py` — `LocalLLMBenchSDK` (מורחב: `run_economic_analysis`)
- [x] `main.py` — CLI (argparse), קורא רק ל-SDK

**Definition of Done:** כל קובץ ≤150 שורות, docstrings מלאים ✓ (נבדק ידנית).
`ruff check` בפועל וכיסוי בדיקות בפועל — ימתינו ל-`uv sync` בשלב ההרצה (Phase 4).

## Phase 2 — בדיקות (עם mocks, ללא רשת)
- [x] `tests/conftest.py` — fixtures משותפים + mocks ל-HF/AirLLM/Ollama
- [x] `tests/unit/test_config.py`
- [x] `tests/unit/test_gatekeeper.py`
- [x] `tests/unit/test_hardware_probe.py`
- [x] `tests/unit/test_metrics.py`
- [x] `tests/unit/test_model_loader_service.py`
- [x] `tests/unit/test_airllm_service.py`
- [x] `tests/unit/test_quantization_service.py`
- [x] `tests/unit/test_benchmark_service.py`
- [x] `tests/unit/test_report_service.py`
- [x] `tests/unit/test_cost_analysis_service.py` (חדש)
- [x] `tests/unit/test_sdk.py`
- [x] `tests/integration/test_full_suite_mocked.py`
- [x] `tests/integration/test_real_smoke.py` (מסומן `@pytest.mark.slow`, לא רץ כברירת מחדל)

**Definition of Done:** קוד הבדיקות כתוב ומכסה happy-path + edge cases לכל שירות.
הרצה בפועל של `uv run pytest` וּוידוא כיסוי ≥85% בפועל — ב-Phase 4 (דורש `uv sync`).

## Phase 3 — קבצי תשתית
- [x] `pyproject.toml` (deps, ruff, pytest, coverage config)
- [x] `config/setup.json` (כולל `airllm.layer_shards_saving_path`)
- [x] `config/rate_limits.json`
- [x] `config/economic_assumptions.json` (חדש — הנחות מחיר API/CAPEX/OPEX, ללא ערכים מוקשחים בקוד)
- [x] `.env-example`
- [x] `.gitignore`
- [x] `README.md`
- [x] `prompt_log.md`
- [x] `notebooks/results_analysis.ipynb` (שלד, ללא תוצאות אמיתיות עדיין)
- [x] `data/.gitkeep`, `results/.gitkeep`, `assets/.gitkeep`

## Phase 4 — הרצה בפועל (שלב המשך — עדיין לא בוצע)

זמנים משוערים לפי `ex05` §11 (End-to-End כולל המתנה פסיבית; בפועל יכול להשתנות):

| תת-שלב | זמן משוער | זמן עבודה אקטיבי |
|---|---|---|
| 4.1 התקנות + הורדות | 1.5–3 שעות | ~15 דקות |
| 4.2 הרצות/ניסויים/מדידות | 3–5 שעות | 30–45 דקות |
| 4.3 עיבוד נתונים + ניתוח כלכלי | 1–1.5 שעות | ~30 דקות |
| 4.4 כתיבת README כדוח | 1–1.5 שעות | ~60 דקות |

- [x] `uv sync --extra dev` — הותקנו 175 חבילות בפועל, כולל `airllm==3.0.1`,
      `torch==2.12.1+cpu`, `transformers==5.12.1` (Python 3.14.5 שנבחר על ידי uv;
      עבד ללא בעיות תאימות)
- [x] **תוקנה תקלה שהתגלתה**: `UnicodeEncodeError` בקונסולת Windows כי נתיב
      הפרויקט מכיל תווים בעברית — נפתר ב-`main.py` (`_ensure_utf8_console`,
      commit `66bc00a`)
- [ ] הגדרת `HF_TOKEN` ב-`.env` (אם עוברים למודל gated; לא נדרש עבור Phi-3-medium)
- [ ] וידוא `airllm.layer_shards_saving_path` מצביע לכונן עם מקום פנוי מספק
- [x] **בדיקת עשן (ex05 §6.1 "Do")**: `phi3:mini` דרך Ollama רץ בהצלחה —
      total 24.95s (load 19.26s), TTFT 1.77s, TPOT ~0.153s/token (~6.8 tok/sec).
      תוצאה נשמרה ב-`results/ollama_smoke_test_phi3_mini.json`. הצנרת עובדת.
- [x] **מודל גדול מדי ל-Ollama** (לפי בקשת המשתמשת): `qwen2.5:72b` (47GB) הורד
      והורץ — **נכשל תוך 6.28 שניות** ("unable to allocate CPU buffer",
      ~19.2GB allocation מול ~7.65GB RAM זמין). ראיה: `results/ollama_qwen72b_fail_evidence.json`
      + תועד ב-README "יומן ניסויים" ניסוי 2.
- [x] **תיקון קריטי**: התגלה שמדידת ה-RAM המקורית (76GB) הייתה שגויה פי 10 —
      בפועל ~7.65GB. תוקן ב-PRD/PLAN/README (v1.02).
- [ ] אותו מודל גדול (או Phi-3-medium), הפעם דרך AirLLM (Hugging Face SafeTensors)
      — הרצה + תיעוד הצלחה עם peak RAM נמוך משמעותית
- [ ] הרצת Baseline הרשמי (FP32, Phi-3-medium-4k-instruct) + מדידת TTFT/TPOT/RAM —
      **לתעד בפירוט חי גם אם המודל נכשל/נתקע/איטי מדי** (זו תוצאה לגיטימית)
- [ ] הרצת AirLLM על Phi-3-medium בדיוק + אותן מדידות (להשוואה כמותית מלאה)
- [ ] `ollama pull` למודל/גרסה קוונטזית מקבילה, הרצה בלפחות 2 רמות קוונטיזציה
      (למשל Q4_K_M, Q2_K) + הערכת איכות פלט איכותנית
- [ ] הרצת `run_full_benchmark_suite` (ניתוח רגישות: אורכי פרומפט/טוקנים, OAT)
- [ ] הרצת `generate_report` → טבלה + גרפי peak RAM, tokens/sec, **Model Roofline**
- [ ] הרצת `run_economic_analysis` → גרף נקודת-איזון (break-even) + המלצה מנומקת
- [ ] מילוי `notebooks/results_analysis.ipynb` בתוצאות אמיתיות
- [ ] **מענה מפורש לכל 6 שאלות המחקר** מ-`docs/PRD.md` §1.1 (בתוך הדוח)
- [ ] קישור כל ממצא למושגי ההרצאה (Prefill/Decode, VRAM, Virtual Memory, Paging —
      ex05 §5.6)
- [ ] **כתיבת/מיזוג הדוח הטכני המלא לתוך `README.md`** (לא כמסמך נפרד!) — כולל
      גרפים/טבלאות/צילומי מסך משובצים בתוך הקובץ עצמו (ex05 §8), תוך שמירה על
      הוראות ההתקנה/הפעלה הקיימות
- [ ] מילוי טופס ה-Word הרשמי → שמירה כ-`uoh-rl07-ex05.pdf` (ידני, ללא שינוי שדות)
- [ ] הגשה במודל (כל חבר/ת קבוצה בנפרד) + עדכון קישור GitHub סופי

## Phase 5 — ליטוש וסגירה
- [ ] וידוא ש-`README.md` קריא לקורא חיצוני ועומד בכל דרישות ex05 §8
- [ ] בדיקת רשימת הבדיקה הסופית מול §17/20.9 ב-`software_submission_guidelines-V3.pdf`
- [ ] tag גרסה (`v1.00`) ב-git
- [ ] Push סופי ל-`origin main`
