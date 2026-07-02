# TODO — משימות פרויקט

מקרא סטטוס: `[ ]` טרם התחיל · `[~]` בתהליך · `[x]` הושלם

**עדכון (v1.01):** לאחר קריאת מסמך המטלה הרשמי `ex05-AirLLM.pdf.pdf`, נוספו
Phase 0.5 (PRD כלכלי), הרחבות Phase 1 (מדידת TTFT/TPOT אמיתית, ניתוח כלכלי,
Model Roofline), ו-Phase 4 עודכן לכלול בדיקת עשן, שאלות המחקר הנדרשות, ודרישת
"README כדוח".

**עדכון (v1.02):** Phase 4 הושלם במלואו — כל הניסויים המרכזיים (baseline רשמי,
AirLLM, קוונטיזציה ב-2 רמות, ניתוח כלכלי, Model Roofline) רצו בפועל עם נתונים
אמיתיים, `pytest`/`ruff` הורצו ואומתו נקיים, וה-README מוזג לדוח סופי מלא. נותרו
רק שלבים ידניים (מילוי טופס Word→PDF, הגשה במודל) שאינם ניתנים לביצוע אוטומטי.

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
`ruff check .` — **נקי (0 שגיאות)**, אומת בפועל ב-Phase 4.

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
`uv run pytest` — **49/49 עוברות, כיסוי 97%** (≥85% נדרש), אומת בפועל ב-Phase 4.
3 כשלים אמיתיים נמצאו בהרצה הראשונה בפועל ותוקנו (ר' Phase 4 למטה: dataclass
drift, טסט RAM-sampling חסר יציבות, matplotlib backend).

## Phase 3 — קבצי תשתית
- [x] `pyproject.toml` (deps, ruff, pytest, coverage config)
- [x] `config/setup.json` (כולל `airllm.layer_shards_saving_path`)
- [x] `config/rate_limits.json`
- [x] `config/economic_assumptions.json` (חדש — הנחות מחיר API/CAPEX/OPEX, ללא ערכים מוקשחים בקוד)
- [x] `.env-example`
- [x] `.gitignore`
- [x] `README.md`
- [x] `prompt_log.md`
- [x] `notebooks/results_analysis.ipynb` (מולא בתוצאות אמיתיות ב-Phase 4)
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
- [x] **Phi-3-medium (14B) דרך AirLLM — ההדגמה המרכזית: הצלחה מלאה.**
      תקלה נמצאה ותוקנה בדרך (`device="cuda:0"` ברירת מחדל של airllm, לא קיים
      GPU → תוקן ל-`device="cpu"` ב-`airllm_service.py`). תוצאה: peak RAM
      903.2MB, TTFT 79.4s, TPOT 43.1s/token, tokens/sec 0.023, סה"כ ~23 דקות.
      טקסט שנוצר תקין ורלוונטי לנושא. ראיות: `results/airllm_phi3_medium_success.json`,
      `results/airllm_phi3_medium_first_attempt_cuda_error.json`. תועד ב-README
      "יומן ניסויים" ניסוי 3 עם טבלת השוואה מלאה מול ניסוי 2.
- [x] **טבלת השוואה Baseline (נכשל) מול AirLLM (הצליח)** — ב-README, כולל ניתוח
      הקושר לשאלות מחקר #1/#2/#5.
- [x] **הרצת Baseline הרשמי דרך `ModelLoaderService`** (HF transformers ישיר,
      Phi-3-medium, FP32) — **קרס עם segfault (exit 139) תוך 17.3 שניות**,
      שוחזר פעמיים. עדות בלתי-תלויה (מסלול קוד שונה לגמרי מ-Ollama) לאותה
      מסקנה memory-bound שנצפתה עם `qwen2.5:72b`. ראיה:
      `results/baseline_official_phi3_medium_oom_crash.json`. תועד ב-README
      ניסוי 3, כולל טבלת השוואה מול הבייסליין השני (Ollama).
- [x] **קוונטיזציה: `phi3:medium` (Q4_0) דרך Ollama — הצלחה.** שתי תקלות נוספות
      נמצאו ותוקנו: (1) `ollama_tag` לא ניתן לגזירה מ-HF repo name → נוסף מפורש
      ל-`config/setup.json`; (2) `subprocess.run(["ollama","pull"])` נכשל
      (WinError 2, PATH) → הוחלף ב-`POST /api/pull`. **תקלת מדידה קריטית
      שלישית**: peak RAM נמדד בטעות מול תהליך הפייתון (36MB) במקום מול
      `llama-server.exe` (תהליך המודל בפועל, ~4GB) — תוקן ב-
      `BaseMetricsCollectorMixin` (`process_name_filter`, ר' PLAN.md ADR-3
      מעודכן). תוצאה סופית: peak RAM 3984.6MB, TTFT 29.1s, TPOT 18.7s/token,
      tokens/sec 0.052, ~9.8 דקות. ראיה: `results/quantized_phi3_medium_q4_0.json`.
      תועד ב-README ניסוי 5 עם טבלת השוואה מלאה.
- [x] **רמת קוונטיזציה נוספת (Q2_K) — הורצה, וחשפה את "קו האדום" של הדיוק.**
      נדרשה תיקון קוד אמיתי: `quant_ollama_tags` נוסף ל-`config/setup.json`
      (מיפוי רמת-קוונטיזציה→טג Ollama מפורש — `sdk.run_quantized`/
      `BenchmarkService` השתמשו קודם בטג יחיד קבוע לכל הרמות, מה שהיה מריץ בטעות
      את אותו מודל Q4_0 גם כשמבקשים Q2_K). Q2_K: מהיר יותר (TPOT 7.5s מול
      18.7s/token) וקל יותר בזיכרון (3748MB מול 3985MB) **אך הפיק פלט לא שימושי**
      (סוטה מהנושא). ראיה: `results/quantized_phi3_medium_q2_k.json`. תועד
      ב-README ניסוי 5.
- [x] **בדיקת רגישות מצומצמת** (במקום `run_full_benchmark_suite` המלא — ר' נימוק
      היקף למטה): Q4_0 ב-16 טוקנים לעומת 30 הקיימים. תפוקה נמוכה יותר ב-16
      טוקנים (0.04 tok/s מול 0.052) עקב אמורטיזציה של TTFT על פחות טוקנים.
      ראיה: `results/quantized_phi3_medium_q4_0_16tok_sensitivity.json`.
- [ ] **`run_full_benchmark_suite` המלא — הוחלט במודע שלא להריץ.** הרשת המלאה
      (2 פרומפטים × 3 אורכי-פלט × 3 שיטות) הייתה נמשכת מעל 5 שעות לפי הזמן
      הנמדד בפועל ל-AirLLM (~43s/טוקן) — מנוגד ל-`ex05` §6/§1 ("אל תהפכו את
      המטלה לפרויקט גמר"). בוצעה בדיקת רגישות מצומצמת במקום (ר' לעיל).
- [x] **הרצת `generate_report` + `roofline`** → `assets/summary_table.csv`,
      `peak_ram_comparison.png`, `tokens_per_sec_vs_length.png`,
      `model_roofline.png` — כולם משובצים ב-README ניסויים 5/7.
      **תוקנו 2 באגים אמיתיים בדרך**: (1) `ReportService.load_results` ציפה
      אך ורק לקובצי JSON בפורמט list-of-records; קובצי הראיות שנשמרו ידנית
      (single-object) ו-`economic_analysis.json` (סכמה שונה לגמרי) שברו את
      הטעינה — תוקן לקבל את שני הפורמטים ולסנן רשומות שאינן RunMetrics. (2)
      `plot_model_roofline` נפל למלכודת "`NaN or x`" (NaN הוא truthy בפייתון)
      בניסיון ליפול-חזרה מ-`precision_or_quant` חסר ל-`quantization_level` —
      תוקן עם בדיקת `pd.isna` מפורשת; נוסף טסט ייעודי שמונע רגרסיה.
- [x] **ניתוח כלכלי (חובה, ex05 §5.5) — הושלם.** `run_economic_analysis` הורץ עם
      זמן ריצה אמיתי (585.9s, מ-Q4_0). נקודת איזון: **10,000 בקשות/חודש**.
      גרף: `assets/breakeven_analysis.png`, ראיה: `results/economic_analysis.json`.
      טבלת עלויות מלאה + המלצה מנומקת ב-README ניסוי 6 (עונה על שאלת מחקר #6).
- [x] מילוי `notebooks/results_analysis.ipynb` בתוצאות אמיתיות (טבלאות, כל
      הגרפים כולל Model Roofline, מסקנות מלאות לכל 6 שאלות המחקר).
- [x] **מענה מפורש לכל 6 שאלות המחקר** — טבלה מרוכזת ב-README ("מענה מרוכז
      לשאלות המחקר"), כולל שאלה #4 (Prefill/Decode דרך TTFT/TPOT).
- [x] קישור כל ממצא למושגי ההרצאה (Prefill/Decode, VRAM, Virtual Memory, Paging —
      ex05 §5.6) — משולב בתוך הניתוח של כל ניסוי ובטבלת שאלות המחקר.
- [x] **מיזוג הדוח הטכני המלא לתוך `README.md`** — כולל את כל ה-4 הגרפים
      וכל הטבלאות משובצים ישירות (ex05 §8), Model Roofline כהרחבה מקורית
      מתועדת (§5.7), ושמירה על הוראות ההתקנה/הפעלה הקיימות.
- [x] **תוקנו 3 כשלים נוספים שהתגלו בעת הרצת `pytest`/`ruff` לראשונה בפועל**
      (מעולם לא הורצו עד כה למרות שהקוד/הבדיקות נכתבו ב-Phase 1-2): (1)
      `tests/unit/test_benchmark_service.py` קרא ל-`BenchmarkSettings(...)`
      עם 3-4 שדות חובה חסרים (drift מאז הוספת שדות חדשים) — תוקן. (2)
      `test_ram_sampling_external_process_matches_current_process_by_name`
      חסר יציבות (flaky): מדד `time.sleep(0.05)` בעוד סריקת `psutil.process_iter`
      על כל תהליכי המערכת לוקחת ~1.4 שניות במחשב הזה — הוחלף בפולינג עם timeout.
      (3) `ReportService.plot_model_roofline`/`generate` השתמשו ב-matplotlib
      עם backend אינטראקטיבי (TkAgg) שקרס עם `TclError` כי התקנת ה-Python של
      `uv` הייתה חסרה קבצי `tk.tcl` — תוקן ל-backend `Agg` (headless), מתאים
      יותר ממילא לשירות ששומר גרפים לקובץ בלבד ואינו מציג אותם אינטראקטיבית.
      **תוקן גם**: `tests/integration/test_full_suite_mocked.py` היה כותב
      קבצי mock אמיתיים לתוך `results/` האמיתי (ולא ל-`tmp_path` המבודד) בגלל
      שה-fixture `project_root` לא ביצע `chdir` — כל הרצת `pytest` זיהמה את
      תיקיית הראיות האמיתית. תוקן עם `monkeypatch.chdir(tmp_path)` ב-`conftest.py`.
- [x] **בדיקה יזומה מול `software_submission_guidelines-V3.pdf` חשפה עוד תקלה
      אמיתית**: `report_service.py` חצה את מגבלת ה-150 שורות המחייבת (הגיע ל-175
      לאחר התיקונים לעיל). תוקן — פוצל ל-`report_service.py` (120 שורות) +
      קובץ/מחלקה נפרדים `model_roofline_service.py`/`ModelRooflineService` (73
      שורות) לפי ADR-9. עודכנו `sdk.py`, הבדיקות (`test_model_roofline_service.py`
      חדש), ו-`docs/PLAN.md`/`docs/PRD_benchmark_reporting.md` בהתאם.
- [x] `prompt_log.md` עודכן לכלול את כל שלב Phase 4 (עד לכתיבת שורה זו) — היה
      נעצר ב"שלב 6" בלבד.
- [ ] מילוי טופס ה-Word הרשמי → שמירה כ-`bb-ai-12-ex05.pdf` (ידני, ללא שינוי שדות)
- [ ] הגשה במודל (כל חבר/ת קבוצה בנפרד) + עדכון קישור GitHub סופי

## Phase 5 — ליטוש וסגירה
- [x] וידוא ש-`README.md` קריא לקורא חיצוני ועומד בכל דרישות ex05 §8
- [x] **בדיקת רשימת הבדיקה הסופית מול §17/20.9 ב-`software_submission_guidelines-V3.pdf`**
      — בוצעה בפועל: קבצי חובה קיימים (README/PRD/PLAN/TODO/PRD ייעודיים/
      prompt_log), ארכיטקטורת SDK+Gatekeeper+mixins ללא כפילות קוד, כל קבצי
      הקוד ≤150 שורות (אומת מחדש לאחר התיקון לעיל), `pytest`/`ruff` נקיים,
      `uv.lock`/`.env-example` קיימים ו-`.env` לא ב-git, C4-style architecture
      diagram + deployment diagram נוספו ל-`PLAN.md` (Context/Container/
      Component/Code). **שני פערים ידועים ונותרו במודע**: (1) "צילומי מסך" —
      לא ניתן להפיק כסוכן AI ללא ממשק גרפי; הוחלף בפלט טרמינל מלא ומצוטט (מצוין
      במפורש ב-README). (2) טבלת עלויות/tokens עבור השימוש בסוכן ה-AI עצמו
      לבניית הפרויקט (`software_submission_guidelines` §11) לא הופקה — לא
      נדרשת ב-ex05 עצמו (שדורש ניתוח כלכלי אחר, של הרצת ה-LLM הנבדק, שכן בוצע
      במלואו), ומדובר בסעיף כללי-לא-מחייב לפי הצהרת §19 של ההנחיות.
- [x] tag גרסה (`v1.00`) ב-git
- [x] Push סופי ל-`origin main`
