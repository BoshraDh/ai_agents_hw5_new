# PRD — מנגנון: Model Loader Service (Baseline)

## תיאור מפורט

`ModelLoaderService` מריץ את המודל בדרך הסטנדרטית לגמרי: `transformers.
AutoModelForCausalLM.from_pretrained(model_name, torch_dtype=<precision>)` — טעינת
**כל** משקלות המודל ל-RAM בבת אחת, ואז `model.generate(...)` על CPU. זהו קו הבסיס
("baseline") שנועד להראות במפורש את הבעיה שהמטלה מבקשת להדגים: מה קורה כשמנסים
להריץ מודל גדול על מעבד/זיכרון רגילים, ללא GPU.

### רקע תיאורטי (מההרצאה)

הטעינה המלאה פירושה שכל הפרמטרים (במקרה שלנו ~14B פרמטרים) חייבים להיות בזיכרון בו
זמנית. בשלב ה-Decode כל טוקן דורש מעבר על **כל** המשקלות (GEMV, memory-bound) —
כך שקצב היצירה מוגבל על ידי רוחב הפס של הזיכרון (ולא כוח חישוב), וללא ליבות
Tensor Cores של GPU הביצועים על CPU חלש הם איטיים משמעותית.

## דרישות ספציפיות

- קלט: `model_name: str`, `precision: Literal["fp32","fp16","bf16"]`, `prompt: str`,
  `max_new_tokens: int`.
- פלט: `RunMetrics` הכולל `load_time_sec`, `ttft_sec` (Time To First Token, נמדד
  דרך streaming — ר' `docs/PLAN.md` ADR-4), `tpot_sec` (Time Per Output Token),
  `tokens_per_sec`, `peak_ram_mb`, `total_wall_time_sec`, `estimated_power_wh`,
  `generated_text`.
- מדידת peak RAM מתבצעת דרך `BaseMetricsCollectorMixin` (thread רקע דוגם `psutil`)
  לאורך **כל** שלב הטעינה וההרצה — לא רק בסיום.
- הורדת המשקלות (אם לא קיימים ב-cache מקומי) עוברת דרך `ApiGatekeeper` (לא קריאה
  ישירה ל-`huggingface_hub`).
- טיפול בכשל: אם הטעינה נכשלת (למשל `MemoryError` או OOM-kill של המערכת), השירות
  תופס את החריגה, מתעד אותה כ-`RunMetrics` עם `succeeded=False` ו-הודעת שגיאה —
  זהו בעצמו ממצא לגיטימי ("מה קורה כשמנסים להריץ מודל גדול מדי").

## אילוצים וחלופות שנשקלו

- **FP32 כברירת מחדל ל-baseline** (במקום FP16): נבחר במכוון כדי למקסם את הלחץ על
  76GB ה-RAM (~56GB) וליצור ניגוד ברור מול AirLLM. FP16 זמין כאופציית קונפיגורציה
  לניסוי משני (השוואת precision בנוסף לשיטת טעינה).
- נשקל להגביל אורך generate ל-token בודד בלבד לצורך מהירות; נדחה — נדרשים לפחות
  כמה עשרות טוקנים כדי למדוד tokens/sec יציב (ר' `config/setup.json:
  benchmark.token_lengths`).

## קריטריוני הצלחה ותרחישי בדיקה

- **Happy path**: המודל נטען, generate מסתיים, כל שדות `RunMetrics` מלאים ותקינים
  (`tokens_per_sec > 0`).
- **Edge case — כשל זיכרון**: מדומה בבדיקות יחידה דרך mock שזורק `MemoryError`;
  השירות חייב לתפוס ולהחזיר `RunMetrics(succeeded=False, error=...)` ולא לקרוס.
- **Edge case — precision לא נתמך**: קלט לא חוקי ל-`precision` מעלה `ValueError`
  ברור לפני כל ניסיון טעינה (fail fast).
