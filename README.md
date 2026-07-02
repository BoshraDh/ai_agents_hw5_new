# Local LLM Bench — Baseline vs. AirLLM vs. Quantization

**קורס:** סוכני AI, תשפ"ו סמסטר ב · **מטלה:** 5 (`ex05-AirLLM`) · **קוד קבוצה:** `uoh-rl07`

כלי benchmark המריץ מודל שפה גדול בשלוש דרכים על מחשב **ללא GPU ייעודי** — טעינה
סטנדרטית מלאה (Baseline), טעינה שכבה-אחר-שכבה (AirLLM), והרצה בקוונטיזציה (Ollama)
— ומפיק מדדים, ניתוח כלכלי (On-Prem מול API), והשוואות מבוססות-נתונים. נבנה כתוכנה
מקצועית לפי `software_submission_guidelines-V3.pdf`: SDK יחיד, `ApiGatekeeper`
מרכזי, בדיקות עם כיסוי 85%+, ללא ערכים מוקשחים, ניהול גרסאות.

> **⚠ חשוב:** לפי דרישת מסמך המטלה (`ex05-AirLLM.pdf.pdf` §8), קובץ זה חייב לשמש
> כדוח הטכני המעמיק הסופי (עם גרפים/טבלאות/צילומי מסך משובצים בו) — לא רק מדריך
> התקנה. **הסטטוס הנוכחי:** שלד פרויקט מלא (מסמכים + קוד + בדיקות) קיים; הרצת
> הניסויים האמיתית **טרם בוצעה** (ר' `docs/TODO.md` Phase 4). לאחר ההרצה, הקובץ
> הזה יורחב לכלול את כל הסעיפים שמפורטים ב"מבנה הדוח הסופי הצפוי" למטה.

## מפרט חומרה שנבדק

> **⚠ תיקון:** המדידה הראשונית (בתחילת הפרויקט) דיווחה RAM ~76GB — **זו הייתה
> טעות תמלול פי 10** מפלט `wmic` מקוטע. המספר הנכון, מאומת דרך
> `Get-CimInstance Win32_OperatingSystem` וגם באופן עקיף דרך כישלון טעינה בפועל
> של מודל 72B, הוא **~7.65GB**. זה משנה משמעותית את סיפור הניסוי (לטובה — ניגוד
> חד יותר בין Baseline לבין AirLLM) — ר' פירוט ב"יומן ניסויים" למטה.

| רכיב | ערך |
|---|---|
| CPU | Intel Core i7-1165G7, 4 cores / 8 threads |
| **RAM** | **~7.65 GB** (8,211,927,040 בייטים) |
| GPU | Intel Iris Xe משולב — **ללא CUDA**, אין GPU ייעודי |
| אחסון | SSD |
| דיסק פנוי | ~115 GB (מתוך ~475GB; ירד לאחר הורדת מודלים) |

**נימוק בחירת המודל** (`microsoft/Phi-3-medium-4k-instruct`, ~14B, MIT, לא-gated):
ר' `docs/PRD.md` §1.2 ו-`docs/PLAN.md` ADR-1 — עם ~7.65GB RAM בלבד, המודל (~14GB
ב-FP16, ~28GB ב-FP32) פשוט לא ייכנס לזיכרון — Baseline צפוי להיכשל בבירור בטעינה,
בעוד AirLLM (שכבה אחת בזיכרון בכל רגע) צפוי להצליח.

## שאלות המחקר שהדוח הסופי יענה עליהן

(המקור: `ex05-AirLLM.pdf.pdf` §4; הרשימה המלאה עם הקשר מלא ב-`docs/PRD.md` §1.1)

1. מהו צוואר הבקבוק האמיתי שמונע הרצה ישירה — זיכרון או כוח חישוב?
2. כיצד AirLLM משנה את הקצאת המשאבים, והקשר לזיכרון וירטואלי/Paging?
3. מה השפעת הקוונטיזציה על זיכרון, מהירות, ואיכות פלט?
4. כיצד Prefill/Decode משתקפים במדדי TTFT מול TPOT?
5. מהו המחיר (Latency/Throughput) עבור היכולת להריץ מודל גדול על חומרה צנועה?
6. מתי כדאי כלכלית לעבוד מקומית, ומתי עדיף API חיצוני?

## מבנה הדוח הסופי הצפוי (יתמלא לאחר Phase 4)

לפי `ex05-AirLLM.pdf.pdf` §8, לאחר ביצוע הניסויים בפועל, README זה יורחב לכלול:
מפרט חומרה מלא + נימוק בחירת מודל, תיאור הניסוי ושלביו, סיכום ממצאים (Baseline מול
AirLLM וקוונטיזציה) עם טבלאות/גרפים משובצים, סיכום ניתוח הכדאיות הכלכלית עם גרף
נקודת-האיזון, הסבר המקשר בין התוצאות למושגי ההרצאה, את Model Roofline diagram
(ההרחבה המקורית), ומענה מפורש לכל שאלות המחקר לעיל — לצד הוראות ההפעלה שכבר קיימות
למטה.

## יומן ניסויים וממצאים (מתעדכן בזמן אמת לאורך Phase 4)

> הערה על "צילומי מסך": אני (סוכן ה-AI) מריץ פקודות בטרמינל ולא יכול לצלם מסך
> אמיתי. הראיה בפועל היא פלט טרמינל מלא ומדויק, נשמר גם כקובץ JSON תחת `results/`
> וגם מצוטט כאן. אם תרצי צילומי מסך גרפיים ממש להגשה הרשמית, אפשר לצלם בעצמך את
> הפלטים המתועדים כאן.

### ✅ ניסוי 1 — בדיקת עשן: `phi3:mini` דרך Ollama (ex05 §6.1 "Do")

**מטרה:** לוודא שהצנרת (Ollama מותקן ורץ + קריאת API) עובדת קצה-לקצה לפני מעבר
למודל הגדול. **תוצאה: הצלחה מלאה.**

```
$ curl http://localhost:11434/api/generate -d '{"model": "phi3:mini",
  "prompt": "Explain in one short sentence what virtual memory is.", "stream": false}'

תשובת המודל: "Virtual memory is a computer's, in reality, uses hard disk space
              to simulate additional RAM when physical RAM is insufficient."

total_duration:  24.95s  (load_duration: 19.26s)
prompt_eval_count: 20 tokens   →  TTFT (Prefill) ≈ 1.77s
eval_count: 26 tokens          →  TPOT (Decode) ≈ 0.153s/token  (~6.8 tokens/sec)
```

ראיה גולמית: `results/ollama_smoke_test_phi3_mini.json`.

### ✅ ניסוי 2 — מודל גדול מדי: `qwen2.5:72b` דרך Ollama (Baseline נכשל)

**מטרה:** להדגים "מה קורה כשמנסים להריץ מודל גדול מדי" (ex05 §5.2) עם מודל
משמעותית מעבר ליכולת החומרה. **תוצאה: כישלון מיידי ומתועד — לא ריצה איטית, אלא
כישלון טעינה מוחלט.**

```
$ ollama pull qwen2.5:72b     # 47GB, הצליח להוריד (יש מספיק דיסק)
$ curl http://localhost:11434/api/generate -d '{"model": "qwen2.5:72b",
  "prompt": "Explain in one short sentence what virtual memory is.", "stream": false}'

HTTP 500, נכשל אחרי 6.28 שניות בלבד

שגיאה מלאה:
  "llama-server process has terminated: exit status 1:
   ggml_backend_cpu_buffer_type_alloc_buffer: failed to allocate buffer of
   size 19192545280 (~19.2GB)
   alloc_tensor_range: failed to allocate CPU buffer of size 19192545280
   error loading model: unable to allocate CPU buffer"
```

**ניתוח (עונה על שאלת מחקר #1):** צוואר הבקבוק כאן הוא **זיכרון (RAM), לא כוח
חישוב** — הכישלון קרה תוך 6.28 שניות, לפני שהחל כל חישוב Prefill/Decode ממשי.
המערכת ניסתה להקצות מאגר יחיד של ~19.2GB, בעוד סך כל ה-RAM הזמין הוא ~7.65GB —
כישלון הקצאה מיידי וודאי, לא תלוי-עומס. זו בדיוק הדרך שבה מזהים "בפועל, לא
בהשערות" (ex05 §3) שההגבלה היא memory-bound: השגיאה עצמה מדווחת את גודל ההקצאה
שנכשלה, לא timeout או האטה הדרגתית.

ראיה גולמית: `results/ollama_qwen72b_fail_evidence.json`.

### ✅ ניסוי 3 — Phi-3-medium (14B) דרך AirLLM — **ההדגמה המרכזית של המטלה**

**מטרה:** להראות שאותה מגבלת ~7.65GB RAM שגרמה לכישלון בניסוי 2 **לא** מונעת
הרצה של מודל גדול — כאשר משתמשים ב-AirLLM. **תוצאה: הצלחה מלאה.**

**תקלה שנמצאה ותוקנה בדרך:** הניסיון הראשון נכשל עם `"Torch not compiled with
CUDA enabled"` — התברר ש-`airllm.AutoModel.from_pretrained` ברירת המחדל שלו
`device="cuda:0"`, וזה לא קיים אצלנו. תוקן ב-`airllm_service.py`
(`device="cpu"` מועבר במפורש כעת). ראיה: `results/airllm_phi3_medium_first_attempt_cuda_error.json`.

לאחר התיקון:

```json
{
  "model": "microsoft/Phi-3-medium-4k-instruct (14B)",
  "succeeded": true,
  "peak_ram_mb": 903.2,
  "ttft_sec": 79.361,
  "tpot_sec": 43.07,
  "tokens_per_sec": 0.023,
  "total_wall_time_sec": 1375.145,
  "generated_text": "Virtual memory is a memory management technique that
                      provides an \"idealized abstraction of the storage
                      resources that are..."
}
```

**טבלת השוואה — Baseline מול AirLLM:**

| מדד | Baseline (qwen2.5:72b, Ollama) | AirLLM (Phi-3-medium, 14B) |
|---|---|---|
| הצליח? | ❌ לא | ✅ כן |
| זמן עד כישלון/הצלחה | 6.28s (כישלון) | ~23 דקות (הצלחה) |
| Peak RAM | — (נכשל לפני הקצאה) | **903 MB** |
| שגיאה | "unable to allocate CPU buffer" (~19.2GB) | אין |

**ניתוח (עונה על שאלות מחקר #1, #2, #5):** זהו בדיוק ה-trade-off שההרצאה מתארת —
AirLLM מוותר על מהירות (0.023 טוקנים/שנייה בלבד — כמעט 44 שניות לכל טוקן בודד ב-
Decode) בתמורה לזיכרון זעום (903MB, פחות מ-1/30 מגודל המודל בדיסק). מנגנון
העבודה: כל שכבה מהמודל (מתוך 40) נטענת מהדיסק, מופעלת על הקלט, ואז משוחררת מיד
לפני טעינת השכבה הבאה — בדיוק כמו Paging במערכות הפעלה. TTFT (79.4s) גבוה כי
שלב ה-Prefill חייב לזרום דרך כל 40 השכבות פעם אחת; TPOT (43.1s/טוקן) גבוה כי
**כל טוקן חדש ב-Decode דורש זרימה מחודשת של כל 40 השכבות מהדיסק** — אין שום
"שמירה בזיכרון" בין טוקנים, ולכן קצב היצירה מוגבל לגמרי על ידי מהירות ה-I/O
מהדיסק (memory/IO-bound באופן מובהק, לא compute-bound).

ראיות גולמיות: `results/airllm_phi3_medium_success.json`,
`results/airllm_phi3_medium_first_attempt_cuda_error.json`.

### ✅ ניסוי 4 — קוונטיזציה: `phi3:medium` (Q4_0) דרך Ollama

**מטרה:** להריץ את אותו מודל ראשי (Phi-3-medium) בקוונטיזציה סטנדרטית של Ollama
(Q4_0, 7.9GB במקום ~28GB במקור) ולהשוות לשלוש השיטות. **תוצאה: הצלחה.**

**שתי תקלות אמיתיות נמצאו ותוקנו בדרך** (מעבר לתקלת ה-CUDA בניסוי 3):
1. שם התג של Ollama לא ניתן לגזירה משם המודל ב-Hugging Face
   (`phi-3-medium-4k-instruct` ≠ `phi3:medium`) — תוקן דרך הוספת `ollama_tag`
   מפורש ל-`config/setup.json`.
2. `subprocess.run(["ollama", "pull", ...])` נכשל עם
   `"[WinError 2] The system cannot find the file specified"` כי `ollama` לא היה
   ב-PATH של תהליך הפייתון — תוקן במעבר ל-`POST /api/pull` (HTTP, כמו שאר
   הקריאות ל-Ollama, ללא תלות ב-PATH בכלל).
3. **תקלת מדידה חמורה יותר**: המדידה הראשונה של peak RAM דיווחה "36MB" —
   שגוי לחלוטין! Ollama מריץ את המודל בתהליך OS **נפרד** (`llama-server.exe`),
   ולא בתוך תהליך הפייתון שלנו. תוקן ב-`shared/metrics.py`
   (`BaseMetricsCollectorMixin` מקבל כעת `process_name_filter` ודוגם תהליך
   חיצוני לפי שם, במקום את עצמו) — אומת ידנית מול Task Manager (`llama-server.exe`
   הגיע ל-3.76GB בזמן הריצה) לפני שהמדידה האוטומטית תוקנה ואושרה.

```json
{
  "model": "phi3:medium (Q4_0, 7.9GB)",
  "succeeded": true,
  "peak_ram_mb": 3984.6,
  "ttft_sec": 29.121,
  "tpot_sec": 18.728,
  "tokens_per_sec": 0.052,
  "total_wall_time_sec": 585.938,
  "generated_text": "Virtual memory allows a computer to compensate for
                      limited physical memory by temporarily transferring
                      data from RAM to disk storage, creating an illusion
                      of a..."
}
```

**טבלת השוואה מלאה — שלוש השיטות, אותו מודל בסיסי (Phi-3-medium/משפחתו):**

| מדד | Baseline (qwen2.5:72b, "גדול מדי") | AirLLM (Phi-3-medium, FP-ish) | קוונטיזציה (phi3:medium, Q4_0) |
|---|---|---|---|
| הצליח? | ❌ לא | ✅ כן | ✅ כן |
| גודל מודל בדיסק | 47 GB | ~28 GB | **7.9 GB** |
| Peak RAM | — (נכשל) | **903 MB** | 3,985 MB |
| TTFT | — | 79.4s | 29.1s |
| TPOT | — | 43.1s/token | 18.7s/token |
| תפוקה | — | 0.023 tok/s | 0.052 tok/s |
| זמן כולל | 6.3s (כישלון) | ~23 דקות | ~9.8 דקות |

**ניתוח (עונה על שאלת מחקר #3):** הקוונטיזציה מקטינה את המודל פי ~3.5 בדיסק
(28GB→7.9GB) ומאיצה את הריצה כמעט פי 2 מול AirLLM (TPOT 18.7s מול 43.1s), אך
**עדיין לא מתקרבת ל"מהירה"** — Ollama עדיין חייב לטעון את כל משקלות המודל
הקוונטזי (7.9GB) לזיכרון בבת אחת (peak RAM גבוה משמעותית מ-AirLLM: 3,985MB
מול 903MB), כי בניגוד ל-AirLLM היא **לא** משתמשת בטעינה שכבה-אחר-שכבה — רק
מקטינה את מספר הביטים לכל משקל. זה בדיוק ה"קו האדום" של הדיוק ש-ex05 שואל
עליו: Q4_0 עדיין הפיק תשובה קוהרנטית ונכונה לחלוטין (איכות פלט נשמרה), אך
המחיר של קוונטיזציה לבדה (בלי AirLLM) הוא עדיין peak RAM של כ-4GB — הרבה
יותר מ-7.65GB ה-RAM שיש לנו בפועל אם היינו רוצים גם עוד תהליכים רצים
במקביל, אך עדיין בתוך התקציב.

ראיה גולמית: `results/quantized_phi3_medium_q4_0.json`.

## הוראות התקנה

דרישות: Python 3.10+, [`uv`](https://docs.astral.sh/uv/) מותקן, ו-(לניסוי הקוונטיזציה)
[Ollama](https://ollama.com) מותקן ורץ מקומית.

```bash
git clone https://github.com/BoshraDh/ai_agents_hw5_new.git
cd ai_agents_hw5_new
uv sync --extra dev
cp .env-example .env   # מלאו HF_TOKEN רק אם עוברים למודל gated
```

## הוראות הפעלה

```bash
# זיהוי מפרט החומרה
uv run python -m local_llm_bench.main --mode hardware

# הרצת Baseline בודדת
uv run python -m local_llm_bench.main --mode baseline --prompt "..." --max-new-tokens 64

# הרצת AirLLM בודדת
uv run python -m local_llm_bench.main --mode airllm --prompt "..." --max-new-tokens 64

# הרצת קוונטיזציה בודדת (דורש ollama serve פעיל)
uv run python -m local_llm_bench.main --mode quantized --quant-level Q4_K_M

# הרצת כל מטריצת הניסויים (כל השיטות × כל הפרומפטים × כל אורכי הפלט)
uv run python -m local_llm_bench.main --mode full-suite

# הפקת גרפים/טבלה מתוך results/ קיים
uv run python -m local_llm_bench.main --mode report --results-path results

# ניתוח כלכלי (On-Prem מול API) — חובה לפי ex05 §5.5
uv run python -m local_llm_bench.main --mode economic --avg-run-seconds 5.0

# Model Roofline diagram (ההרחבה המקורית, ex05 §7)
uv run python -m local_llm_bench.main --mode roofline --results-path results --model-params-billion 14
```

## מדריך תצורה

- `config/setup.json` — שם המודל, precision, אורכי פלט לבדיקה, רשימת פרומפטים,
  רמות קוונטיזציה, נתיבי results/assets, `assumed_tdp_watts` (הערכת חשמל),
  `airllm.layer_shards_saving_path` (נתיב שמירת שכבות AirLLM — יש להצביע לכונן
  עם מקום פנוי, ר' `docs/PLAN.md` ADR-5), `roofline` (הנחות תקרת ביצועים משוערות).
- `config/rate_limits.json` — הגבלות קצב לכל שירות חיצוני (Hugging Face, Ollama).
- `config/economic_assumptions.json` — **כל** ההנחות לניתוח הכלכלי (מחירי API,
  עלות חומרה/CAPEX, תעריף חשמל/OPEX, נפחי שימוש לבדיקה) — יש לערוך לפני הרצת
  `--mode economic` כדי שהניתוח ישקף מחירים אמיתיים (ר' `docs/PRD_economic_analysis.md`).
- `.env` — `HF_TOKEN` (לא נדרש עבור המודל שנבחר, שאינו gated).

**להחלפת מודל**: שנו `benchmark.model_name` ב-`config/setup.json` בלבד — אין צורך
לגעת בקוד (ר' `docs/PLAN.md` ADR-1 לחלופות מומלצות אם המודל שנבחר יתברר ככבד מדי).

## מבנה הפרויקט

```
src/local_llm_bench/   קוד המקור (sdk/, services/, shared/)
tests/                 בדיקות יחידה + אינטגרציה (עם mocks; tests/integration/test_real_smoke.py
                        רץ ניסויים אמיתיים ומסומן slow — לא רץ כברירת מחדל)
docs/                  PRD, PLAN, TODO + PRD ייעודי לכל מנגנון (כולל economic_analysis)
config/                קבצי קונפיגורציה (ללא ערכים מוקשחים בקוד)
notebooks/              notebook לניתוח תוצאות
data/, results/, assets/  קלט/פלט ניסויים (ריקים כרגע; assets/ ≈ figures/ ב-ex05)
```

מיפוי מול המבנה המומלץ ב-`ex05-AirLLM.pdf.pdf` §9 (`src/, experiments/, results/,
reports/, figures/`) מתועד ב-`docs/PRD.md` §7.

## הרצת הבדיקות

```bash
uv run pytest                       # בדיקות מהירות בלבד (עם mocks), כיסוי 85%+
uv run pytest --run-slow            # כולל בדיקות אינטגרציה אמיתיות (הורדות כבדות)
uv run ruff check .                 # linting
```

## תרומת קוד

קבצי קוד ≤150 שורות, ללא כפילות (עקרון OOP — mixins/base classes), כל קריאה חיצונית
עוברת דרך `ApiGatekeeper`, כל תצורה דרך `config/` — לא בקוד. ר' `docs/PLAN.md`.

## רישיון וייחוס

קוד הפרויקט למטרות לימודיות (מטלה אקדמית). מודל ברירת המחדל
(`microsoft/Phi-3-medium-4k-instruct`) תחת רישיון MIT מבית Microsoft. חבילת
[AirLLM](https://github.com/lyogavin/airllm) ו-[Ollama](https://ollama.com) בשימוש
בהתאם לרישיונות הפתוחים שלהן.

## יומן פרומפטים

ר' `prompt_log.md` לתיעוד השימוש בסוכן AI (Claude Code) בבניית הפרויקט.
