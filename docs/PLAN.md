# PLAN — ארכיטקטורה טכנית

## 1. סקירת שכבות (Context/Container)

```
External Consumers
   CLI (main.py)        Jupyter Notebook (notebooks/results_analysis.ipynb)
          \                        /
           v                      v
              +-------------------------+
              |   LocalLLMBenchSDK      |   <- נקודת כניסה יחידה לכל הלוגיקה
              +-----------+-------------+
                          |
        +-----------------+------------------+-----------------+
        v                 v                  v                 v
  ModelLoaderService  AirllmService  QuantizationService  BenchmarkService
        |                 |                  |                 |
        +--------+--------+---------+--------+                 |
                 v                  v                           v
           ApiGatekeeper (HF Hub / Ollama)              ReportService
                 |                                              |
                 v                                              v
      Hugging Face Hub / Local Ollama daemon              results/*.json -> graphs
```

**עקרון מפתח:** `main.py` וה-notebook אינם מכילים אף שורת לוגיקה עסקית — הם קוראים
אך ורק למתודות של `LocalLLMBenchSDK`. כל שירות (Service) אחראי על תחום אחד בלבד
(Single Responsibility). כל קריאה החוצה לרשת (Hugging Face) או לתהליך מקומי אחר
(Ollama) עוברת אך ורק דרך `ApiGatekeeper`.

## 2. שכבת השירותים (Component)

| שירות | אחריות | Input | Output |
|---|---|---|---|
| `ModelLoaderService` | טעינת מודל HF סטנדרטית + generate | model_name, precision, prompt, max_new_tokens | `RunMetrics` (latency, peak_ram, text) |
| `AirllmService` | טעינה שכבה-אחר-שכבה דרך חבילת `airllm` + generate | model_name, precision, prompt, max_new_tokens | `RunMetrics` |
| `QuantizationService` | הרצה דרך Ollama (GGUF) ברמות קוונטיזציה שונות | model_name, quant_level, prompt, max_new_tokens | `RunMetrics` |
| `BenchmarkService` | אורקסטרציה: מריץ קומבינציות (שיטה × פרומפט × אורך) ושומר תוצאות | ניסוי (Experiment config) | קובצי JSON תחת `results/` |
| `ReportService` | קורא תוצאות שמורות, מפיק גרפים/טבלאות | נתיב ל-`results/` | קבצי PNG/HTML תחת `assets/` |

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
`prompt_tokens`, `max_new_tokens`, `load_time_sec`, `time_to_first_token_sec`,
`tokens_per_sec`, `peak_ram_mb`, `total_wall_time_sec`, `generated_text`,
`timestamp`. משמש כפורמט אחיד לכל שלוש השיטות — כך ש-`ReportService` לא צריך לדעת
משהו על ההבדלים הפנימיים בין השיטות.

## 5. ADRs (Architecture Decision Records)

### ADR-1: בחירת המודל — `microsoft/Phi-3-medium-4k-instruct` (~14B, MIT, לא-gated)

**הקשר:** יש לבחור מודל "גדול אך מותאם למחשב" ללא GPU, עם 76GB RAM ו-CPU חלש
(4 ליבות), כך שההבדל בין Baseline ל-AirLLM יהיה משכנע אך הריצה עדיין תסתיים בזמן
סביר.

**אלטרנטיבות שנשקלו:**
- מודל 7-8B (Llama-3.1-8B/Mistral-7B): בטוח וקל, אך ה"מאבק" של ה-baseline מול
  ה-RAM הנדיב (76GB) פחות דרמטי — ~15GB בלבד מתוך 76GB.
- מודל 30B+ (למשל Qwen2.5-32B): ניגוד דרמטי ביותר (FP16 ~64GB, קרוב לגבול 76GB)
  אך הורדה/ריצה עלולות לקחת שעות על 4 ליבות בלבד — לא מעשי למסגרת זמן של מטלה.
- **Phi-3-medium-4k-instruct (14B, MIT, לא-gated) — נבחר**: ב-FP32 (~56GB) המודל
  צורך את רוב ה-76GB ומשאיר מרווח דק בלבד ל-OS/Python, מה שיוצר תרחיש ריצה איטית
  ולחוצה בזיכרון (מדגים במדויק את הדרישה "מה קורה כשמנסים להריץ מודל גדול על
  המעבד שלכם") מבלי לחצות שעות של זמן ריצה על CPU של 4 ליבות. הרישיון החופשי
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
    def probe_hardware(self) -> HardwareSpec: ...
```
