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

| רכיב | ערך |
|---|---|
| CPU | Intel Core i7-1165G7, 4 cores / 8 threads |
| RAM | ~76 GB |
| GPU | Intel Iris Xe משולב — **ללא CUDA**, אין GPU ייעודי |
| אחסון | SSD (ככל הנראה NVMe; יאומת בפועל דרך `--mode hardware`) |
| דיסק פנוי | ~172 GB |

**נימוק בחירת המודל** (`microsoft/Phi-3-medium-4k-instruct`, ~14B, MIT, לא-gated):
ר' `docs/PRD.md` §1.2 ו-`docs/PLAN.md` ADR-1 — גדול מספיק כדי ליצור לחץ אמיתי על
ה-RAM ב-FP32 (~56GB מתוך 76GB), אך לא גדול מדי מכדי ש-AirLLM יוכל להריץ אותו.

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
