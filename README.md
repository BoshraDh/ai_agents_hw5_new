# Local LLM Bench — Baseline vs. AirLLM vs. Quantization

**קורס:** סוכני AI, תשפ"ו סמסטר ב · **מטלה:** 5 · **קוד קבוצה:** `uoh-rl07`

כלי benchmark המריץ מודל שפה גדול בשלוש דרכים על מחשב **ללא GPU ייעודי** — טעינה
סטנדרטית מלאה (Baseline), טעינה שכבה-אחר-שכבה (AirLLM), והרצה בקוונטיזציה (Ollama)
— ומפיק מדדים והשוואות מבוססי-נתונים. נבנה כתוכנה מקצועית מלאה לפי
`software_submission_guidelines-V3.pdf`: SDK יחיד, `ApiGatekeeper` מרכזי, בדיקות עם
כיסוי 85%+, ללא ערכים מוקשחים, ניהול גרסאות.

> **סטטוס נוכחי:** שלד פרויקט מלא (מסמכים + קוד + בדיקות) קיים. הרצת הניסויים
> האמיתית (הורדת מודל, מדידה בפועל, גרפים, דוח) **טרם בוצעה** — ר' `docs/TODO.md`
> Phase 4.

## מפרט חומרה שנבדק

| רכיב | ערך |
|---|---|
| CPU | Intel Core i7-1165G7, 4 cores / 8 threads |
| RAM | ~76 GB |
| GPU | Intel Iris Xe משולב — **ללא CUDA** |
| דיסק פנוי | ~172 GB |

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
```

## מדריך תצורה

- `config/setup.json` — שם המודל, precision, אורכי פלט לבדיקה, רשימת פרומפטים,
  רמות קוונטיזציה, נתיבי results/assets.
- `config/rate_limits.json` — הגבלות קצב לכל שירות חיצוני (Hugging Face, Ollama).
- `.env` — `HF_TOKEN` (לא נדרש עבור המודל שנבחר, שאינו gated).

**להחלפת מודל**: שנו `benchmark.model_name` ב-`config/setup.json` בלבד — אין צורך
לגעת בקוד (ר' `docs/PLAN.md` ADR-1 לחלופות מומלצות אם המודל שנבחר יתברר ככבד מדי).

## מבנה הפרויקט

```
src/local_llm_bench/   קוד המקור (sdk/, services/, shared/)
tests/                 בדיקות יחידה + אינטגרציה (עם mocks; tests/integration/test_real_smoke.py
                        רץ ניסויים אמיתיים ומסומן slow — לא רץ כברירת מחדל)
docs/                  PRD, PLAN, TODO + PRD ייעודי לכל מנגנון
config/                קבצי קונפיגורציה (ללא ערכים מוקשחים בקוד)
notebooks/              notebook לניתוח תוצאות
data/, results/, assets/  קלט/פלט ניסויים (ריקים כרגע)
```

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
