# PLAN — ארכיטקטורה טכנית

**עדכון (גרסה 1.01):** לאחר קריאת `ex05-AirLLM.pdf.pdf` (מסמך המטלה הרשמי
והמפורט), נוספו: מדידת TTFT/TPOT אמיתית דרך streaming (ADR-4), נתיב שמירה ייעודי
ל-shards של AirLLM (ADR-5), `CostAnalysisService` לניתוח כלכלי חובה (ר' סעיף 2
וסעיף 5), ו-Model Roofline diagram כהרחבה מקורית (ADR-6).

**עדכון (גרסה 1.02, לאחר Phase 4):** שני באגים אמיתיים נמצאו ותוקנו בעת ההרצה
בפועל: מיפוי רמת-קוונטיזציה→טג Ollama חסר (ADR-7), ותאימות `ReportService` לפורמט
ראיות מעורב + matplotlib backend (ADR-8).

## 1. ארכיטקטורה (מודל C4: Context → Container → Component)

**Level 1 — Context:** מי משתמש במערכת ומה סביבה החיצונית שלה.

```
[תלמידה/בודק המטלה] --runs--> [Local LLM Bench] --calls--> [Hugging Face Hub]
                                      |
                                      +--calls--> [Local Ollama daemon (localhost:11434)]
```

**Level 2 — Container:** המערכת היא container בודד — תהליך Python מקומי אחד
(אין שרת, אין DB, אין containers נפרדים; מתאים לאופי הפרויקט כניסוי מקומי,
לא מוצר מבוזר):

```
External Consumers
   CLI (main.py)        Jupyter Notebook (notebooks/results_analysis.ipynb)
          \                        /
           v                      v
              +-------------------------+
              |   LocalLLMBenchSDK      |   <- נקודת כניסה יחידה לכל הלוגיקה
              +-----------+-------------+
                          |
                          v
                 [Services container — ר' Level 3 למטה]
                          |
                          v
           ApiGatekeeper (HF Hub / Ollama)
                          |
                          v
      Hugging Face Hub / Local Ollama daemon
```

**Level 3 — Component:** פירוט השירותים בתוך ה-container (מפורט בטבלה בסעיף 2
למטה) — `ModelLoaderService`, `AirllmService`, `QuantizationService`,
`BenchmarkService`, `ReportService`, `ModelRooflineService`,
`CostAnalysisService`, כולם דרך `ApiGatekeeper` משותף לקריאות חוצות.

**Level 4 — Code:** ר' סעיף 4 (מודל הנתונים המשותף `RunMetrics`) וסעיף 7 (חוזה
ה-API הפנימי של `LocalLLMBenchSDK`) למבנה הקוד ברמת המחלקות/הפונקציות.

**עקרון מפתח:** `main.py` וה-notebook אינם מכילים אף שורת לוגיקה עסקית — הם קוראים
אך ורק למתודות של `LocalLLMBenchSDK`. כל שירות (Service) אחראי על תחום אחד בלבד
(Single Responsibility). כל קריאה החוצה לרשת (Hugging Face) או לתהליך מקומי אחר
(Ollama) עוברת אך ורק דרך `ApiGatekeeper`.

### תרשים Deployment

הפריסה טריוויאלית בכוונה — ניסוי מקומי, לא שירות מבוזר: תהליך Python בודד
(`uv run python -m local_llm_bench.main`) על מחשב יחיד, ללא שרת/ענן/קונטיינר.

```
[Developer/Student Machine]
  ├── Python process (uv-managed venv) ── this project's code
  ├── Ollama daemon process (localhost:11434) ── quantized model serving
  └── Local filesystem: data/airllm_cache (AirLLM shards), results/, assets/
        |
        v (network, download-only)
  Hugging Face Hub (model weights) + Ollama model registry (GGUF weights)
```

## 2. שכבת השירותים (Component)

| שירות | אחריות | Input | Output |
|---|---|---|---|
| `ModelLoaderService` | טעינת מודל HF סטנדרטית + generate | model_name, precision, prompt, max_new_tokens | `RunMetrics` (latency, peak_ram, text) |
| `AirllmService` | טעינה שכבה-אחר-שכבה דרך חבילת `airllm` + generate | model_name, precision, prompt, max_new_tokens | `RunMetrics` |
| `QuantizationService` | הרצה דרך Ollama (GGUF) ברמות קוונטיזציה שונות | model_name, quant_level, prompt, max_new_tokens | `RunMetrics` |
| `BenchmarkService` | אורקסטרציה: מריץ קומבינציות (שיטה × פרומפט × אורך) ושומר תוצאות | ניסוי (Experiment config) | קובצי JSON תחת `results/` |
| `ReportService` | קורא תוצאות שמורות, מפיק טבלת השוואה + גרפי peak RAM/tokens-per-sec + break-even | נתיב ל-`results/` | קבצי PNG/CSV תחת `assets/` |
| `ModelRooflineService` | ההרחבה המקורית (ADR-6): גרף Model Roofline (compute-bound/memory-bound) | DataFrame תוצאות + הנחות roofline | `assets/model_roofline.png` |
| `CostAnalysisService` | ניתוח כלכלי חובה: עלות API מול On-Prem, נקודת איזון | תוצאות benchmark + `config/economic_assumptions.json` | `BreakevenResult` + גרף |

כל שירות יורש מ-`BaseMetricsCollectorMixin` משותף (ב-`shared/`) שמספק את מדידת
peak RSS memory (`psutil.Process().memory_info().rss`, נדגם ב-thread נפרד ברקע כדי
לתפוס peak אמיתי ולא רק ערך בסיום) ומדידת wall-clock — כדי למנוע כפילות קוד בין
שלושת השירותים (עקרון "כל לוגיקה שחוזרת פעמיים+ מופקת ל-mixin/בסיס").

## 3. שכבת התשתית (`shared/`)

- **`gatekeeper.py` — `ApiGatekeeper`**: עוטף קריאות ל-Hugging Face Hub (הורדות
  משקלות) ולתהליך Ollama (subprocess/HTTP ל-`localhost:11434`). אוכף rate limit,
  תור FIFO בעת חריגה, retry עם backoff, ולוג לכל קריאה — הכל לפי
  `config/rate_limits.json`.
- **`config.py` — `ConfigManager`**: קורא `config/setup.json` + משתני סביבה
  (`.env` דרך `python-dotenv`), מספק גישה טיפוסית (dataclass) לשאר הקוד. שום קובץ
  אחר לא קורא ישירות ל-`os.environ` או לקבצי JSON.
- **`hardware_probe.py` — `HardwareProbeMixin`**: מזהה CPU/RAM/GPU בזמן ריצה
  (`platform`, `psutil`, ניסיון `nvidia-smi`/`wmic` עם נפילה חינניה ל"אין GPU
  ייעודי") — משמש הן את הדוח והן את בדיקת-הסבירות לפני הרצה (למשל אזהרה אם המודל
  שנבחר גדול מדי ביחס ל-RAM הפנוי).
- **`version.py`**: קבועי גרסה (קוד/קונפיגורציה/rate-limits) — מתחיל מ-1.00.
- **`constants.py`**: קבועים גלובליים (שמות ברירת מחדל, יחידות המרה בייט↔GB וכו').

## 4. מודל הנתונים המשותף

`RunMetrics` (dataclass, ב-`shared/`): `method`, `model_name`, `precision_or_quant`,
`prompt_tokens`, `max_new_tokens`, `load_time_sec`, **`ttft_sec`** (Time To First
Token — מדד ל-Prefill), **`tpot_sec`** (Time Per Output Token, ממוצע — מדד
ל-Decode; מכונה גם ITL/Inter-Token Latency), `tokens_per_sec` (Throughput כולל),
`peak_ram_mb`, `total_wall_time_sec`, **`estimated_power_wh`** (צריכת חשמל
משוערת, מבוססת TDP מוגדר בקונפיגורציה × זמן ריצה — מתועד כהערכה, לא מדידה
אמיתית, ex05 §5.4), `generated_text`, `quality_note`, `timestamp`. משמש כפורמט
אחיד לכל שלוש השיטות — כך ש-`ReportService` לא צריך לדעת משהו על ההבדלים
הפנימיים בין השיטות.

**הערה (v1.01):** בגרסה הראשונה של המסמך השדה `time_to_first_token_sec` חושב
בטעות כזמן ממוצע-לטוקן (כלומר בפועל TPOT, לא TTFT). התוקן: `ttft_sec` ו-
`tpot_sec` הם כעת שני שדות נפרדים, נמדדים בפועל דרך streaming (ר' ADR-4).

## 5. ADRs (Architecture Decision Records)

### ADR-1: בחירת המודל — `microsoft/Phi-3-medium-4k-instruct` (~14B, MIT, לא-gated)

> **⚠ עדכון (v1.02):** מדידת ה-RAM המקורית (76GB) הייתה שגויה פי 10 — ה-RAM
> האמיתי הוא **~7.65GB**. הנימוקים למטה מתוקנים בהתאם. ההחלטה הסופית (Phi-3-medium)
> לא השתנתה, אך הסיפור התנסיוני הפך חד יותר: Baseline לא רק "ילחץ" על הזיכרון —
> הוא צפוי **להיכשל מיידית** בכל precision סביר, ממש כפי שנצפה בפועל עם
> `qwen2.5:72b` דרך Ollama ("unable to allocate CPU buffer").

**הקשר:** יש לבחור מודל "גדול אך מותאם למחשב" ללא GPU, עם ~7.65GB RAM בלבד
ו-CPU חלש (4 ליבות), כך שההבדל בין Baseline ל-AirLLM יהיה משכנע אך הריצה עדיין
תסתיים בזמן סביר.

**אלטרנטיבות שנשקלו:**
- מודל 7-8B (Llama-3.1-8B/Mistral-7B): גם הוא (FP16 ~15GB) לא נכנס ל-7.65GB —
  עדיין ידגים כישלון, אך פחות "מרשים" כנציג "מודל גדול" מכוון.
- מודל 30B+ (למשל Qwen2.5-32B/72B): נבדק בפועל דרך Ollama (`qwen2.5:72b`,
  ~47GB quantized) — נכשל תוך 6.28 שניות בטעינה (לא רק "איטי") — ראה תיעוד מלא
  ב-`README.md`. משמש כניסוי המשלים "כישלון קיצוני" נפרד מהמודל הראשי.
- **Phi-3-medium-4k-instruct (14B, MIT, לא-gated) — נבחר כמודל הראשי**: גם
  ב-FP16 (~14GB) המודל לא נכנס ל-7.65GB — Baseline צפוי להיכשל בבירור בטעינה,
  בעוד AirLLM (הדורש רק שכבה אחת, מאות MB, בזיכרון בכל רגע) צפוי להצליח באופן
  מובהק. גודל בינוני (14B, לא 72B) שומר על זמן הורדה/ריצה סביר. הרישיון החופשי
  (MIT) ומעמד ה"לא-gated" מבטלים חיכוך גישה מול Hugging Face.

**החלטה:** ברירת מחדל = Phi-3-medium-4k-instruct. גיבוי מתועד (ניתן להחלפה דרך
`config/setup.json` בלבד, ללא שינוי קוד): Phi-3-mini-4k-instruct (3.8B) אם זמן
הריצה יתברר כבלתי-מעשי בפועל.

### ADR-2: שלוש שיטות ההרצה כ-Services נפרדים תחת SDK משותף

**הקשר:** יש להריץ את אותו מודל בשלוש דרכים (baseline/AirLLM/quantized) ולהשוות.

**החלטה:** כל שיטה מיושמת כ-Service נפרד עם ממשק אחיד (`run(prompt, max_new_tokens)
-> RunMetrics`), כך שניתן להוסיף שיטה רביעית בעתיד (למשל vLLM/PagedAttention) מבלי
לגעת ב-`BenchmarkService` או ב-`ReportService` (Open/Closed principle, ותומך גם
בדרישת "נקודות הרחבה" מההנחיות).

### ADR-3: מדידת peak RAM ב-thread רקע במקום מדידה חד-פעמית

**הקשר:** מדידת זיכרון פעם אחת בסוף ההרצה מפספסת את שיא הצריכה (שקורה בד"כ באמצע
הטעינה).

**החלטה:** `BaseMetricsCollectorMixin` מריץ thread נפרד שדוגם `psutil` כל N
מילישניות לאורך כל ההרצה ושומר את המקסימום — עלות תקורה זניחה, דיוק גבוה משמעותית.

**עדכון (v1.03, אומת בפועל ב-Phase 4)**: ההנחה המקורית ש"מדגמים את התהליך
הנוכחי" נכונה עבור `ModelLoaderService`/`AirllmService` (טוענים משקלות בתוך
תהליך הפייתון עצמו) — אך **שגויה לחלוטין** עבור `QuantizationService`: Ollama
מריץ את המודל בתהליך OS נפרד (`llama-server.exe`), כך שמדידת "עצמנו" תפסה רק
את לקוח ה-HTTP הקליל (~36MB) ולא את התהליך שבו המודל בפועל (שהגיע ל-~4GB).
נמצא ותוקן בפועל: `BaseMetricsCollectorMixin._start_ram_sampling` מקבל כעת
`process_name_filter: str | None` אופציונלי — כשמוגדר, דוגם תהליכי OS חיצוניים
לפי שם (`psutil.process_iter`) במקום את `psutil.Process()` העצמי.
`QuantizationService` מעביר `"llama-server"`.

**הקשר:** `ex05` §4-5 דורש במפורש הפרדה בין TTFT (Time To First Token — מודד את
שלב ה-Prefill) לבין TPOT/ITL (Time Per Output Token — מודד את שלב ה-Decode).
מדידת `generate()` כבלוק אחד (כפי שנעשה בטעות בגרסה הראשונה) לא מאפשרת הפרדה כזו.

**החלטה:** נוסף `shared/generation_timing.py` עם `StreamingTimingMixin`, המשתמש
ב-`transformers.TextIteratorStreamer` (בת'רד נפרד מריץ את `generate()`, בעוד
ה-thread הראשי קורא טוקנים מה-streamer וממתד זמן הגעה של כל טוקן). כך:
`ttft_sec` = הזמן מתחילת הקריאה ועד לטוקן הראשון שמגיע מה-streamer; `tpot_sec` =
ממוצע הזמן בין טוקנים עוקבים. משותף בין `ModelLoaderService` ל-`AirllmService`
(שתיהן חושפות ממשק `generate()` תואם-HF) — נמנעת כפילות קוד.

עבור `QuantizationService` (Ollama): אין צורך ב-streaming ידני — Ollama **כבר
מחזיר** את השדות `prompt_eval_duration` (≈ TTFT) ו-`eval_duration`/`eval_count`
(ממוצע = TPOT) בתשובת ה-API הרגילה (non-streaming), לכן שם רק מחלצים מהתשובה
הקיימת (ר' `docs/PRD_quantization.md`).

### ADR-5: נתיב ייעודי לשמירת שכבות AirLLM (`layer_shards_saving_path`)

**הקשר:** `ex05` §6.1 ("Do") מזהיר במפורש: פירוק מודל כבד יוצר קבצי SafeTensors
רבים ועתירי Disk I/O; אם לא מוגדר נתיב מפורש, AirLLM עלול למלא את כונן ה-OS
(בדרך כלל `C:`) במהלך הניסוי.

**החלטה:** נוסף `airllm.layer_shards_saving_path` ל-`config/setup.json`
(ברירת מחדל: תיקייה ייעודית תחת `data/airllm_cache/`, עם הנחיה ב-README להצביע
לכונן מהיר/נפרד אם קיים). `AirllmService` מעביר את הפרמטר ל-`AutoModel.
from_pretrained(model_name, layer_shards_saving_path=...)`.

### ADR-6: הרחבה מקורית — Model Roofline Diagram

**הקשר:** `ex05` §7 דורש הרחבה מקורית אחת לפחות; §3 מציע "Model Roofline" כרעיון
מתקדם — ייצוג ויזואלי שממחיש מתי המערכת עוברת ממגבלת משאב אחד לאחר
(compute-bound מול memory-bound).

**החלטה:** נבחר Model Roofline כהרחבה המקורית (על פני חלופות כמו LoRA/QLoRA
נוסף, או השוואת כמה גדלי מודלים) כי הוא: (א) נבנה ישירות מנתונים שכבר נאספים
(FLOPs משוערים לפי גודל מודל, bytes מועברים לפי peak RAM ורוחב פס), (ב) עונה
ישירות על שאלת המחקר הראשונה (`ex05` §4), ו-(ג) לא דורש ניסוי/הורדה נוספים —
רק חישוב ו-`ReportService.plot_model_roofline()` נוסף. מתועד גם ב-
`docs/PRD_benchmark_reporting.md`.

### ADR-7: מיפוי מפורש רמת-קוונטיזציה→טג Ollama (`quant_ollama_tags`)

**הקשר:** בהרצה הראשונה של רמת קוונטיזציה שנייה (Q2_K) התגלה שקוד ה-SDK
(`run_quantized`, `BenchmarkService.run_full_suite`) העביר תמיד את אותו
`settings.ollama_tag` הבודד ל-`QuantizationService.run`, בלי קשר לרמת
הקוונטיזציה המבוקשת בפועל — כלומר בקשה ל-Q2_K הייתה בפועל מריצה מחדש את
Q4_0 (הטג "phi3:medium" ברירת המחדל) ומתייגת את התוצאה בטעות כ-Q2_K.

**החלטה:** נוסף `quant_ollama_tags: dict[str, str]` ל-`config/setup.json`
(מיפוי מפורש `"Q4_0": "phi3:medium"`, `"Q2_K": "phi3:14b-medium-4k-instruct-q2_K"`)
ול-`BenchmarkSettings`. `sdk.run_quantized`/`BenchmarkService.run_full_suite`
מבצעים `settings.quant_ollama_tags.get(quant_level, settings.ollama_tag)` לפני
הקריאה ל-`QuantizationService`. תואם את עקרון "כל תצורה דרך config, לא בקוד".

### ADR-8: `ReportService` — תאימות לפורמט ראיות מעורב + backend headless

**הקשר:** שני באגים אמיתיים נמצאו כשהופעל `ReportService` לראשונה בפועל מול
תוצאות אמיתיות (Phase 4): (א) `load_results` ציפה שכל קובץ `results/*.json`
יכיל רשימת רשומות (`list[dict]`), אך קובצי ראיה שנשמרו ידנית הם אובייקט בודד,
וקובץ `economic_analysis.json` הוא סכמה שונה לגמרי (לא RunMetrics כלל) — שני
המקרים קרסו את הטעינה. (ב) `plot_model_roofline` נפל בטעות `NaN or x` (ערך
`NaN` הוא truthy בפייתון, כך ש-`row.get("precision_or_quant") or row.get(...)`
מחזיר את ה-`NaN` עצמו במקום ליפול לשדה החלופי כשהערך הראשון חסר).

**החלטה:** `load_results` מקבל כעת גם רשימה וגם אובייקט בודד לכל קובץ, ומסנן
רשומות שאין בהן `"method"` וגם `"succeeded"` (כלומר אינן RunMetrics-shaped).
`plot_model_roofline` בודק `pd.isna(...)` במפורש לפני נפילה-חזרה. בנוסף,
`matplotlib.use("Agg")` נקבע במפורש בראש `report_service.py` — ה-backend
האינטראקטיבי (TkAgg) ברירת המחדל קרס עם `TclError` כי התקנת ה-Python של `uv`
בסביבה הזו הייתה חסרה קבצי `tk.tcl`; `Agg` (headless) גם ממילא מתאים יותר
לשירות ששומר גרפים לקובץ ואינו מציג אותם אינטראקטיבית.

### ADR-9: פיצול `ReportService`/`ModelRooflineService` (מגבלת 150 שורות)

**הקשר:** לאחר הוספת הבאגים/תיקונים המתועדים ב-ADR-8, `report_service.py` חצה את
מגבלת ה-150 השורות המחייבת (`software_submission_guidelines-V3.pdf` §3.2) —
הגיע ל-175 שורות.

**החלטה:** חולץ קובץ נפרד `services/model_roofline_service.py` עם מחלקה ייעודית
`ModelRooflineService`, הנושאת אך ורק את אחריות ההרחבה המקורית (Model Roofline
— `_build_roofline_figure`/`plot_model_roofline`). `ReportService` נשאר אחראי על
טעינת תוצאות (`load_results`, המשותף לשני השירותים) והשוואת peak RAM/tokens-per-
sec/break-even. לאחר הפיצול: `report_service.py` (120 שורות),
`model_roofline_service.py` (73 שורות) — שניהם בתוך המגבלה. תואם את עקרון
Single Responsibility (ADR-2/6) ואת אסטרטגיית "פיצול 50/50" שהנחיות התוכנה
ממליצות עליה.

## 6. תרשים תהליך הרצת benchmark מלא (זרימה)

```
BenchmarkService.run_full_suite(experiment_config)
  for method in [baseline, airllm, quantized]:
    for prompt in experiment_config.prompts:
      for max_tokens in experiment_config.token_lengths:   # ניתוח רגישות
        metrics = <method>_service.run(prompt, max_tokens)   # דרך Gatekeeper
        results_store.append(metrics)
  results_store.save_json("results/run_<timestamp>.json")
```

## 7. חוזה API פנימי (`LocalLLMBenchSDK`)

```python
class LocalLLMBenchSDK:
    def run_baseline(self, prompt: str, max_new_tokens: int) -> RunMetrics: ...
    def run_airllm(self, prompt: str, max_new_tokens: int) -> RunMetrics: ...
    def run_quantized(self, prompt: str, quant_level: str, max_new_tokens: int) -> RunMetrics: ...
    def run_full_benchmark_suite(self) -> Path:  # -> results file path
    def generate_report(self, results_path: Path) -> Path:  # -> assets dir
    def run_economic_analysis(self, results_path: Path) -> BreakevenResult: ...
    def probe_hardware(self) -> HardwareSpec: ...
```
