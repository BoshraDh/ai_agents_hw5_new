# TODO — משימות פרויקט

מקרא סטטוס: `[ ]` טרם התחיל · `[~]` בתהליך · `[x]` הושלם

## Phase 0 — תכנון (מסמכים)
- [x] `docs/PRD.md`
- [x] `docs/PLAN.md`
- [~] `docs/TODO.md` (קובץ זה)
- [ ] `docs/PRD_model_loader.md`
- [ ] `docs/PRD_airllm_execution.md`
- [ ] `docs/PRD_quantization.md`
- [ ] `docs/PRD_benchmark_reporting.md`
- [ ] אישור כל מסמכי Phase 0 לפני מעבר ל-Phase 1

**Definition of Done:** כל 7 המסמכים קיימים, מכילים את כל הסעיפים הנדרשים לפי
`software_submission_guidelines-V3.pdf` §2.2-2.3, ו-commit לכל אחד.

## Phase 1 — שלד קוד (ללא הרצה)
- [ ] מבנה תיקיות `src/local_llm_bench/{sdk,services,shared}` + `__init__.py`-ים
- [ ] `shared/constants.py`
- [ ] `shared/version.py` (מתחיל מ-1.00)
- [ ] `shared/config.py` — `ConfigManager`
- [ ] `shared/gatekeeper.py` — `ApiGatekeeper`
- [ ] `shared/hardware_probe.py` — `HardwareProbeMixin`
- [ ] `shared/metrics.py` — `RunMetrics` dataclass + `BaseMetricsCollectorMixin`
- [ ] `services/model_loader_service.py`
- [ ] `services/airllm_service.py`
- [ ] `services/quantization_service.py`
- [ ] `services/benchmark_service.py`
- [ ] `services/report_service.py`
- [ ] `sdk/sdk.py` — `LocalLLMBenchSDK`
- [ ] `main.py` — CLI (argparse), קורא רק ל-SDK

**Definition of Done:** כל קובץ ≤150 שורות, docstrings מלאים, `ruff check` נקי
(ייבדק בשלב ההרצה), ללא ערכים מוקשחים (מאומת ידנית בסקירת קוד).

## Phase 2 — בדיקות (עם mocks, ללא רשת)
- [ ] `tests/conftest.py` — fixtures משותפים + mocks ל-HF/AirLLM/Ollama
- [ ] `tests/unit/test_config.py`
- [ ] `tests/unit/test_gatekeeper.py`
- [ ] `tests/unit/test_hardware_probe.py`
- [ ] `tests/unit/test_metrics.py`
- [ ] `tests/unit/test_model_loader_service.py`
- [ ] `tests/unit/test_airllm_service.py`
- [ ] `tests/unit/test_quantization_service.py`
- [ ] `tests/unit/test_benchmark_service.py`
- [ ] `tests/unit/test_report_service.py`
- [ ] `tests/unit/test_sdk.py`
- [ ] `tests/integration/test_full_suite_mocked.py`
- [ ] `tests/integration/test_real_smoke.py` (מסומן `@pytest.mark.slow`, לא רץ כברירת מחדל)

**Definition of Done:** `uv run pytest` (בשלב ההרצה) מעביר את כל הבדיקות הלא-slow,
כיסוי ≥85%.

## Phase 3 — קבצי תשתית
- [ ] `pyproject.toml` (deps, ruff, pytest, coverage config)
- [ ] `config/setup.json`
- [ ] `config/rate_limits.json`
- [ ] `.env-example`
- [ ] `.gitignore`
- [ ] `README.md`
- [ ] `prompt_log.md`
- [ ] `notebooks/results_analysis.ipynb` (שלד)
- [ ] `data/.gitkeep`, `results/.gitkeep`, `assets/.gitkeep`

## Phase 4 — הרצה בפועל (שלב המשך, מחוץ להיקף השיחה הנוכחית)
- [ ] `uv sync`
- [ ] הגדרת `HF_TOKEN` ב-`.env` (אם נדרש)
- [ ] הורדת Phi-3-medium-4k-instruct, הרצת Baseline (FP32) + מדידה
- [ ] הרצת AirLLM על אותו מודל + מדידה
- [ ] התקנת Ollama, `ollama pull phi3:medium`, הרצה בקוונטיזציה + מדידה
- [ ] הרצת `run_full_benchmark_suite` (ניתוח רגישות: אורכי פרומפט/טוקנים)
- [ ] הרצת `generate_report` → גרפים תחת `assets/`
- [ ] מילוי `notebooks/results_analysis.ipynb` בתוצאות אמיתיות
- [ ] כתיבת הדוח המסכם (ניתוח לעומק של ההבדלים, לפי דרישת המטלה)
- [ ] מילוי טופס ה-Word הרשמי → שמירה כ-`uoh-rl07-ex05.pdf` (ידני, ללא שינוי שדות)
- [ ] הגשה במודל (כל חבר/ת קבוצה בנפרד) + עדכון קישור GitHub סופי

## Phase 5 — ליטוש וסגירה
- [ ] עדכון README.md עם תוצאות/גרפים סופיים וצילומי מסך
- [ ] בדיקת רשימת הבדיקה הסופית מול §17/20.9 בהנחיות
- [ ] tag גרסה (`v1.00`) ב-git
- [ ] Push סופי ל-`origin main`
