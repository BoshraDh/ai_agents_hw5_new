# TODO — משימות פרויקט

מקרא סטטוס: `[ ]` טרם התחיל · `[~]` בתהליך · `[x]` הושלם

## Phase 0 — תכנון (מסמכים)
- [x] `docs/PRD.md`
- [x] `docs/PLAN.md`
- [x] `docs/TODO.md` (קובץ זה)
- [x] `docs/PRD_model_loader.md`
- [x] `docs/PRD_airllm_execution.md`
- [x] `docs/PRD_quantization.md`
- [x] `docs/PRD_benchmark_reporting.md`
- [x] אישור כל מסמכי Phase 0 לפני מעבר ל-Phase 1

**Definition of Done:** כל 7 המסמכים קיימים, מכילים את כל הסעיפים הנדרשים לפי
`software_submission_guidelines-V3.pdf` §2.2-2.3, ו-commit לכל אחד.

## Phase 1 — שלד קוד (ללא הרצה)
- [x] מבנה תיקיות `src/local_llm_bench/{sdk,services,shared}` + `__init__.py`-ים
- [x] `shared/constants.py` (ב-`local_llm_bench/constants.py`)
- [x] `shared/version.py` (מתחיל מ-1.00)
- [x] `shared/config.py` — `ConfigManager`
- [x] `shared/gatekeeper.py` — `ApiGatekeeper`
- [x] `shared/hardware_probe.py` — `HardwareProbeMixin`
- [x] `shared/metrics.py` — `RunMetrics` dataclass + `BaseMetricsCollectorMixin`
- [x] `services/model_loader_service.py`
- [x] `services/airllm_service.py`
- [x] `services/quantization_service.py`
- [x] `services/benchmark_service.py`
- [x] `services/report_service.py`
- [x] `sdk/sdk.py` — `LocalLLMBenchSDK`
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
- [x] `tests/unit/test_sdk.py`
- [x] `tests/integration/test_full_suite_mocked.py`
- [x] `tests/integration/test_real_smoke.py` (מסומן `@pytest.mark.slow`, לא רץ כברירת מחדל)

**Definition of Done:** קוד הבדיקות כתוב ומכסה happy-path + edge cases לכל שירות.
הרצה בפועל של `uv run pytest` וּוידוא כיסוי ≥85% בפועל — ב-Phase 4 (דורש `uv sync`).

## Phase 3 — קבצי תשתית
- [x] `pyproject.toml` (deps, ruff, pytest, coverage config)
- [x] `config/setup.json`
- [x] `config/rate_limits.json`
- [x] `.env-example`
- [x] `.gitignore`
- [x] `README.md`
- [x] `prompt_log.md`
- [x] `notebooks/results_analysis.ipynb` (שלד, ללא תוצאות אמיתיות עדיין)
- [x] `data/.gitkeep`, `results/.gitkeep`, `assets/.gitkeep`

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
