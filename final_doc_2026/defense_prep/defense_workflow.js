export const meta = {
  name: 'defense-speaker-notes',
  description: 'Generate Hebrew per-slide speaker notes, info paragraphs, and examiner Q&A for the M.Sc. USV-autism defense (67 slides) + holistic Q&A, traps, glossary',
  phases: [
    { title: 'Slides', detail: 'per-slide-group agents: summary + Hebrew script + info paragraph + Q&A' },
    { title: 'Extras', detail: 'holistic Q&A, danger-question rehearsal, glossary' },
  ],
}

// ---------- shared context (source of truth = project book) ----------
const SHARED = `
פרויקט: "Analysis of Ultrasonic Vocalizations of Mice for Autism Detection" — פרויקט גמר M.Sc. במדעי הנתונים ב-HIT. מציגים: חן אהרון ואביאל ביטון. מנחה: ד"ר דרור לדרמן. חוקרת ראשית / בעלת הדאטא: פרופ' חוה גולן (אוניברסיטת בן-גוריון). הבוחן החיצוני יכול להיות טכני (מדעי הנתונים) או ביולוגי — יש לכסות את שני הקהלים.
המטרה המדעית: לסווג גורי עכברים מדגם-אוטיזם גנטי (Mthfr-HET, המחלקה החיובית) מול בקרה (WT) לפי קולות על-קוליים (USV), ולבחון עד כמה זה מכליל לעכברים חדשים.

עובדות ליבה (מקור אמת = ספר הפרויקט book_text.txt):
- דאטא גולמי: 125,576 הברות, 126 גורים (91 WT / 29 HET / 6 UNK), 35 אמהות (dams), 5 שנות הקלטה (2015, 2018, 2022, 2023, 2024). Baseline לאחר סינון: 106 עכברים, 12,323 רשומות ברמת recording, 408 sessions לטראק הסדרתי. חוסר איזון ~3:1 WT:HT.
- שני משטרי הערכה (הלב המתודולוגי): subject-dependent = פיצול 60/20/20 לפי רשומה, אותו עכבר יכול להופיע בטריין ובטסט (אופטימי; "כמה טוב על עכבר מוכר"). subject-independent = פיצול לפי עכבר עם stratification ובדיקת אי-חפיפה, אף עכבר לא בשתי קבוצות ("כמה טוב על עכבר חדש לגמרי").
- מודלים טבלאיים: XGBoost (baseline שהתקבל בירושה, לא מכוונן), XGBoost-tuned (חדש, חיפוש 200-trial לכל משטר בנפרד), TabPFN-3 (חדש, המודל הטבלאי הכי חזק). מודלים סדרתיים (BiLSTM / 1D-CNN / Transformer) — נחקרו, לא ניצחו את הטבלאיים.
- תוצאות מפתח (pooled): TabPFN הכי טוב — accuracy 0.781 dependent (עד 0.801 לפי cohort) / 0.729 independent (weighted F1 0.743, ROC-AUC 0.783). XGBoost-tuned — HT recall 0.869 על עכברים לא-נראים (הכי טוב לסקרינינג, balanced acc 0.725). XGBoost baseline 0.733 dep / 0.693 ind.
- ה-0.829 הישן: מספר legacy, subject-dependent, לפני תיקון. מתפרק לשני אפקטים נפרדים ולא "באג אחד": (i) תיקון תווית הגנוטיפ + חישוב המשקלים: 0.829→0.733 (אותו משטר dependent); (ii) מעבר למשטר independent על אותו מודל: 0.733→0.693. רצפת "נחש-תמיד-WT" ≈ 0.73 (כי הדיוק הגולמי פשוט עוקב אחרי יחס המחלקות).
- תיקון אינטגריטי-דאטה: 14 עכברים / 2,495 שורות מטא-דאטה תוקנו HET→WT — גורים WT (גנטית) של אמהות HET שקיבלו בטעות את גנוטיפ האם. הכלאה HET×WT נותנת בערך חצי WF, אז זה תיקון גנטית-הכרחי, לא רגרסיה.
- "קיר הדיוק" (HT precision wall): דיוק המחלקה HT ~0.50 בכל מודל, כל כיוונון וכל משטר — תקרה ברמת הייצוג/הפיצ'רים (לא מגבלה של המסווג). כמחצית מההתראות החיוביות הן false alarms. הסיבה הסבירה: היעדר תיאורי-קול עשירים (frequency contour מלא, bandwidth, עומק אפנון תדר FM).
- קונפאונד הזן (strain): strain1 (2022-2024, רקע מעורב BALB/c×C57, 76 עכברים) נפרד היטב אפילו across-subject (~0.90); strain2 (2015/2018, BALB/c טהור, 50 עכברים) קורס. הזן שזור עם שנת הקלטה + רקע גנטי → אי אפשר לקרוא מספרי per-strain כפנוטיפ טהור. מבחן חוצה-cohort (טריין על זן אחד, טסט על השני) = עבודה עתידית.
- מודלים סדרתיים: התוצאה הטובה בפיצול יחיד (0.704 balanced acc) קרסה תחת 5-fold grouped CV ל-0.563±0.063 — "fold ממוזל", לא רווח אמיתי. הסיבה: מיעוט דאטא (רק ~19 sessions HT ל-fold; רק 24 עכברי HT בסה"כ). מסקנה כנה: "לא נתמך בקנה מידה הנוכחי", לא "הסדר לא אינפורמטיבי".

⚠️ נקודת הסיכון מס' 1 בהגנה (שקף 57 — חשיבות פיצ'רים): mother_gen (גנוטיפ האם) שולט בגרף gain importance (~0.585, פי ~20 מהפיצ'ר הבא). הוא חזוי "מעצם ההכלאה": אם WT → רק גורי WT; רק אם HET יכולה להוליד HET. כלומר חלק ניכר מהדיוק הטבלאי מגיע ממטא-דאטה של יוחסין, לא מהקולות עצמם. mother_gen הוא פיצ'ר פעיל במודל; אין ריצת אבלציה של אקוסטיקה-בלבד. הטקסט בספר מדגיש פיצ'רים אקוסטיים (תדרי-גבול + משכים) ולא מזכיר את mother_gen — יש מתח figure-vs-text שהבוחן עלול לתפוס. תשובה כנה ומוכנה: "mother_gen הוא קונפאונד חזוי מעצם ההכלאה; האות האקוסטי האמיתי הוא מה שמשתקף בהערכה subject-independent, ב-ROC-AUC ובקיר הדיוק; אבלציה נטולת-מטא-דאטה היא עבודה עתידית". אין לטעון שהאקוסטיקה לבדה מניבה את הדיוק הראשי.
`.trim()

const OUTPUT_RULES = `
כללי כתיבה (חובה):
- הכל בעברית, למעט מונחים טכניים, שמות מודלים, מטריקות, ומספרים — שנשארים באנגלית/ספרות בתוך המשפט העברי (למשל "ה-recall על מחלקת HT הוא 0.869"). אל תתרגם מונחים כמו XGBoost / TabPFN / spectrogram / recall / cross-validation.
- "script_he" = בדיוק מה שהמציג אומר בקול, בעברית מדוברת וזורמת (גוף ראשון), באורך שמתאים למספר השניות שהוקצב (בערך 2.2 מילים לשנייה — כלומר ~שניות×2.2 מילים). לא רשימת נקודות — טקסט שנאמר. שקפי מוטיבציה בגוף ראשון, אישי וקצר.
- "summary_he" = 1-2 משפטים: מה מוצג על השקף ומה מטרתו בנרטיב.
- "info_he" = "פסקת המידע": מערך של פריטים {term, explain_he}, אחד לכל מושג/מונח/נתון/ראשי-תיבות/שם-חוקר/מטריקה שמופיע בשקף ושאפשר להישאל עליו. חובה למצות — כל דבר מדעי או טכני. הסבר קצר, מדויק ופשוט (2-4 משפטים), מותר ורצוי להשתמש בידע חיצוני (למשל להסביר מה זה SAM, MTHFR, STFT, gammatone, ELO, ROC-AUC, Youden). כתוב את ההסבר כך שגם בוחן ביולוגי וגם בוחן טכני יבינו.
- "questions" = מערך שאלות שבוחן בתואר שני במדעי הנתונים עלול לשאול על השקף הזה, עם תשובה מלוטשת מבוססת-ספר. 2-3 לשקף תוכן רגיל; 3-4 לשקף מורכב/רגיש; 0 לשקפי חוצץ (divider) ולשקפי מוטיבציה נטו. השאלות ברמה גבוהה — למה בחרתם X, מה החלופה, מה המגבלה. התשובות כנות ומבוססות על עובדות הליבה.
- אם יש "must_ask" בבריף — חובה לכלול שאלה שמכסה בדיוק את הנקודה הזו.
- דיוק מספרי: כל מספר חייב להיות תואם לספר/למצגת. בדוק מול book_text.txt אם אינך בטוח.
`.trim()

// ---------- per-slide briefs ----------
// each: [num, presenter, sec, section, divider, briefText, mustAsk]
const S = {}
const def = (n, p, sec, section, div, brief, must) => { S[n] = { n, p, sec, section, div: !!div, brief, must: must || null } }

def(1,'Aviel',15,'פתיחה',0,'שקף כותרת: שם הפרויקט, המציגים (חן אהרון, אביאל ביטון), מנחה ד"ר דרור לדרמן, בשיתוף פרופ\' חוה גולן (בן-גוריון), 2026. תמונת עכבר + גל קול.')
def(2,'Aviel',22,'פתיחה',0,'Agenda — 10 חלקים: Motivation, Background, The solution, Research questions, Dataset, Methods, Models, Results, Engineering, Conclusions. מפת דרכים לקהל.')
def(3,'Aviel',29,'מוטיבציה',0,'Motivation — Personal: "לראות בן משפחה צעיר משגשג אחרי טיפול מוקדם ומותאם — זיהוי מוקדם זה אישי." בגוף ראשון, קצר, לא מזהה. תמונת ילדה.')
def(4,'Aviel',22,'מוטיבציה',0,'Motivation — Professional: יישום machine learning על דאטא ביו-רפואי אמיתי, בחיפוש אחר biomarker אובייקטיבי. תמונת שני חוקרים.')
def(5,'Aviel',7,'רקע',1,'חוצץ Section 02 — Background: אוטיזם, פער האבחון, ולמה קולות עכברים.')
def(6,'Aviel',29,'רקע',0,'ASD: "1 מתוך 31" ילדים מאובחנים (CDC 2025). מצב נוירו-התפתחותי מורכב, שני תחומי-ליבה התנהגותיים: קשיים בתקשורת חברתית; דפוסי התנהגות מוגבלים וחזרתיים. פי ~4 שכיח יותר בבנים; שכיחות האבחונים עולה.')
def(7,'Aviel',29,'רקע',0,'The diagnostic gap: אוטיזם מאובחן היום רק בהערכה התנהגותית של מומחה — סובייקטיבי, אין מבחן אובייקטיבי; תצפית מתוקננת כמו ADOS על פני מספר מפגשים. ציר זמן: הפניה+המתנה 6-12+ חודשים, הערכה ADOS שבועות-חודשים, גיל אבחון ממוצע 3-4.')
def(8,'Aviel',22,'רקע',0,'The need for a biomarker: האבחון מגיע שנים אחרי הינקות — בדיוק החלון שבו התערבות מוקדמת קריטית. למה האבחון של היום קצר: תלוי בשיפוט סובייקטיבי, קשה ליישם באמינות בינקות. הפתרון הנדרש: biomarker אובייקטיבי — מדד ביולוגי כמותי, מוקדם, מהיר, בלתי-תלוי.')
def(9,'Aviel',37,'רקע',0,'How would you model autism in a mouse? דיאגרמה: WT מול Mthfr-HET; אנזים MTHFR ב-100% מול ~50% פעילות → SAM → מתילציית DNA. שלוש נקודות: "Not one gene" (מתכון של הרבה גנים וצעדים מטבוליים), "MTHFR mutation" (משאיר את האנזים חלקית-פעיל בלבד), "ASD-like, not autism" (העכברים מראים התנהגות דמויית-אוטיזם בלבד). שקף עתיר-מושגים ביולוגיים.', 'must: הסבר מדויק מה זה MTHFR ומה זה SAM ומה הקשר למתילציה ולהתפתחות המוח; ולמה "דמוי-אוטיזם" ולא אוטיזם.')
def(10,'Aviel',22,'רקע',0,'So why do vocal signals matter? תקשורת קולית = אחת התפוקות ההתנהגותיות הבסיסיות ביותר בטבע, קריאה ישירה של פעילות המוח. שלוש נקודות: תפוקה התנהגותית יסודית; מבנה דמוי-דיבור (timing + frequency modulation משותפים לדיבור אנושי); רגישות לנוירו-התפתחות.')
def(11,'Aviel',29,'רקע',0,'Why a mouse? ארבע סיבות: Genetic homology (85-95% מהגנים המקודדים-חלבון משותפים, ל-MTHFR יש אורתולוג עכברי Mthfr); Isolated variables (משתנה אחד — אותה גנטיקה/מזון/דיור, ההבדל היחיד בין הקבוצות הוא הגן, בלי רעש סביבתי); Fast lifecycle (~20 יום היריון, בגרות בשבועות — חלונות התפתחות שלמים בזמן קצר); Vocal communication (USVs — מעגלים בעלי בסיס אבולוציוני משותף לתקשורת אנושית).')
def(12,'Aviel',7,'הפתרון',1,'חוצץ Section 03 — The solution: קולות על-קוליים של עכברים כ-biomarker אובייקטיבי.')
def(13,'Aviel',29,'הפתרון',0,'The candidate biomarker — mouse USVs: ספקטוגרמה עם 36 קריאות שזוהו אוטומטית (10 שניות, 250 kHz). קריאות 35-125 kHz הנפלטות כשגורים מבודדים; האות המדיד המוקדם ביותר (ההתנהגות התקשורתית הראשונה); ההשערה: biomarker ל-ASD שהוא לא-פולשני, אובייקטיבי, כמותי.')
def(14,'Aviel',7,'שאלות מחקר',1,'חוצץ Section 04 — Research questions.')
def(15,'Aviel',45,'שאלות מחקר',0,'Three research questions: RQ1 Models — איזו משפחת מודלים מסווגת הכי טוב HET מול WT מ-USV (XGBoost / TabPFN / sequence)? RQ2 Features — אילו מאפיינים אקוסטיים מניעים את הסיווג, והאם עולים 2-3 פיצ\'רים עקביים? RQ3 Regime & generalization — איך משפיעים משטר ההערכה (subject-dependent מול -independent) וה-cohort (per-strain מול pooled) על הביצועים, ובעיקר על הכללה לעכברים לא-נראים? + מטרת הנדסה: להפוך את הפרוטוטיפ שהתקבל בירושה (שלא רץ) לפייפליין reproducible מקצה-לקצה עם single source of truth.', 'must: מה ההיגיון מאחורי RQ3 — למה בכלל להבחין בין subject-dependent ל-independent.')
def(16,'Aviel',22,'שאלות מחקר',0,'Project timeline — שוחזר מהיסטוריית ה-commits: 2023-05 פרויקט בירושה (XGBoost יחיד, מאת Daniela Gold, נשאר רדום); 2025-11 המחברים לוקחים אחריות; 2026-03 refactor לפייפליין; 2026-04 נוסף subject-independent + תיקון אינטגריטי (14 עכברים/2,495 שורות) + TabPFN; 2026-05 מודלים סדרתיים + ניתוח strain; 2026-06 threshold tuning; 2026-07 סיכום ותיעוד.')

def(17,'Chen',7,'דאטהסט',1,'חוצץ Section 05 — Dataset.')
def(18,'Chen',29,'דאטהסט',0,'The raw data: אלפי קבצי WAV + קובץ Excel מטא-דאטה לכל שנה. טבלת דוגמה: Mother, Mother genotype, Pup ID, Sex, Offspring genotype (=TARGET), Day (P4-P12), Session, Recording no (.wav). התווית: HT (מודל-אוטיזם) מול WT (בריא). מספרים גדולים: 126 גורים, 408 sessions, 125,576 הברות, 5 שנים.')
def(19,'Chen',22,'דאטהסט',0,'Dataset composition — small multiples: לפי offspring genotype (WT 91, HT 29, UNK 6); לפי שנה (2015:31, 2018:19, 2022:30, 2023:22, 2024:24); לפי strain (BALB/c=strain2: 50, BALB/c+C57=strain1: 76); לפי מין (F 69, M 47, U 10); לפי יום פוסט-לידתי (P4:71, P6:96, P8:42, P10:32, P12:26); הברות לפי שנה.')
def(20,'Chen',29,'דאטהסט',0,'Class balance & longitudinal structure: איזון מחלקות ברמת recording — 9,283 WT / 3,040 HT ≈ 3:1 (75.3%/24.7%). הברות לכל עכבר: median 828, mean 997. עכבר בודד תורם מאות הברות מתואמות (correlated) — מבנה longitudinal.', 'must: למה המבנה ה-longitudinal מחייב פיצול subject-grouped (אחרת דליפת מידע).')
def(21,'Chen',22,'דאטהסט',0,'Strain: a biological confound: BALB/c טהור — 50 עכברים (2015, 2018; מסומן strain2). BALB/c+C57 מעורב — 76 עכברים (2022-2024, הכלאה אמיתית על רקע C57BL/6; מסומן strain1). הזן שונה גם ברקע גנטי וגם בעידן ההקלטה → confounded עם הגנוטיפ. מטופל כ-cohort scope מפורש.', 'must: מדוע strain הוא confound ולא סתם משתנה.')
def(22,'Chen',7,'שיטות',1,'חוצץ Section 06 — Methods: מאודיו על-קולי גולמי לספקטוגרמות מוכנות-למודל.')
def(23,'Chen',29,'שיטות',0,'From recordings to a diagnosis: כל הקלטה עוברת שני שלבים למודים. Stage 1 = Syllable typing (Segment → spectrogram → CNN). Stage 2 = Classification (Tabular: XGBoost/TabPFN; Sequence: BiLSTM/1D-CNN/Transformer) → אבחנה HT/WT. סקירה של הפייפליין.')
def(24,'Chen',29,'שיטות',0,'Finding the calls (Stage 1): energy detector קלאסי (לא רשת) מאתר כל קריאה על-קולית. 90 gammatone filters ב-35-125 kHz; קריטריון tonality (אנרגיה מרוכזת במעט ערוצים) לכל frame של 6ms; מיזוג פערים <20ms; זריקת קריאות <10ms; פלט start/end/duration. דוגמה עם 36 הברות שזוהו.', 'must: למה detector קלאסי ולא רשת נוירונים; ואיך נקבעים גבולות הקריאה.')
def(25,'Chen',29,'שיטות',0,'Typing each call with a CNN (Stage 1): משימת computer-vision. Syllable clip מרופד ל-0.25s וממורכז → Spectrogram image 128×128×3 (high-pass 30 kHz, STFT win 512 / hop 128, resize, נורמליזציה ל-3 ערוצים) → CNN backbone BiT ResNet-50×3 (~211M params, GroupNorm + Weight Standardization, pretrained על ImageNet-21k) → Syllable type (softmax על 10 סוגים; confidence<0.5 → Undefined).', 'must: כיצד מתבצע המעבר מ-detected call לספקטוגרמה (STFT, ריפוד ל-0.25s, resize, 3 ערוצים).')
def(26,'Chen',15,'שיטות',0,'Model card — the syllable-typing CNN: BiT ResNet-50×3; TASK סיווג רב-מחלקתי של סוג הברה; BACKBONE ResNet-v2 bottleneck, blocks (3,4,6,3), width×3; NORMALIZATION GroupNorm + Weight Standardization (חתימת BiT); PRETRAINING ImageNet-21k ואז fine-tune עם ראש Dense(→10); OUTPUT softmax על 10, conf<0.5→Undefined (מחלקה 11 post-hoc); INFERENCE batched. הערה: אין model card מפורסם ל-typer (סט האימון והדיוק לכל מחלקה לא ידועים; חסר weight shard) — מגבלה.')
def(27,'Chen',15,'שיטות',0,'The network, layer by layer: 128×128×3 → backbone ResNet-50×3 (blocks 3,4,6,3, WS-conv + GroupNorm) → global average pool → Dense→10 softmax → argmax → סוג הברה. 10 סוגים + Undefined (max prob<0.5).')
def(28,'Chen',15,'שיטות',0,'A repertoire of 10 call types: ספקטוגרמות אמיתיות. Single vowel (Upward, Downward, Flat, Short, Chevron, Complex); Multiple vowels (Frequency steps, Two syllables); Advanced harmonic (Composite, Harmonic); Undefined (low-confidence). מקובצים ל-4 רמות מורכבות.')
def(29,'Chen',15,'שיטות',0,'Syllable-type distribution: 125,576 הברות, מסווגות ע"י ה-CNN וצבועות לפי קבוצת מורכבות. Frequency steps=44,547 (שולט), Composite=17,816, Two syllables=13,006, Undefined=12,311, Chevron=12,105, Short=6,996, Complex=6,713, Flat=5,246, Harmonic=4,316, Upward=1,798, Downward=722. Undefined (~10%) נזרק בטראק הטבלאי אך נשמר בסדרתי.', 'must: מה נותנת החלוקה לסוגי הברות שונים לעומת רק לזהות שזו הברה — למה חשוב אם זה Short או Frequency steps.')
def(30,'Chen',22,'שיטות',0,'The acoustic signal: WT vs HT: box plots ברמת הברה ל-Start (Hz), End (Hz), Duration, ISI. נבדלים באופן עדין אך עקבי לפי גנוטיפ — ה-cues הרגישים-ל-ASD מ-Shekel et al. (2021): start frequency, bandwidth, duration.', 'must: כמה גדול ההבדל בפועל בין WT ל-HT (עדין, התפלגויות חופפות — וזה קשור ל-precision wall).')

def(31,'Chen',7,'מודלים',1,'חוצץ Section 07 — Models: הפיכת טביעת-האצבע של ההברות לחיזוי WT-מול-HT.')
def(32,'Chen',22,'מודלים',0,'Two families of classifiers: Tabular models (מטריצת recording 12,323×48; XGBoost inherited, XGBoost-tuned חדש, TabPFN-3 חדש) — [Our focus, הסיפור המרכזי]. Sequence models (רצפים per-session 408×≤256; BiLSTM, 1D-CNN, Transformer) — [Explored; לא ניצחו את הטבלאי, סוכמו ולא הועמקו]. פרוטוקול הערכה משותף אחד.')
def(33,'Chen',37,'מודלים',0,'One recording → 48 numbers: כל הקלטה מצטמצמת לוקטור קבוע של 48 עמודות — שמְמַצע החוצה את הסדר הזמני. 10 סוגי הברות × 4 פיצ\'רים (mean start kHz, mean end kHz, relative freq, mean dur ms) = 40; + 6 מטא-דאטה (Avg ISI, Sex, Age, Session, Strain, Mother genotype); TARGET = pup genotype; Mouse index לקיבוץ בלבד (לא פיצ\'ר).', 'must: מה המשמעות של averaging away הסדר הזמני, ולמה mother_gen נמצא בין הפיצ\'רים (רמז לקונפאונד בשקף 57).')
def(34,'Chen',45,'מודלים',0,'Two ways to split the data (EVALUATION): אותם 106 עכברים (WT 82, HT 24) — מה שמשתנה זה מה מפצלים. Subject-dependent: פיצול לפי recording; כל עכבר מזין את שלושת הפיצולים → אותו עכבר בטריין ובטסט → אופטימי (within-subject). Subject-independent: פיצול לפי עכבר, stratified, ללא חפיפה; Train 63 (49WT/14HT), Val 21 (16WT/5HT), Test 22 (17WT/5HT); across-subject (עכבר לא-נראה לגמרי). רק 24 עכברי HT בסה"כ → ~5 נופלים ל-Test → folds בשונות גבוהה.', 'must: מה בדיוק הדליפה (leakage) שמונע הפיצול subject-independent, ולמה 24 עכברי HT יוצרים folds רועשים.')
def(35,'Chen',15,'מודלים',0,'Model card — XGBoost baseline (inherited): gradient-boosted trees; המתכון הישן הלא-מכוונן ששוגר עם הפרויקט; 50 עצים, max_depth 5, learning rate 0.1; scale_pos_weight = n_WT/n_HT ≈ 3.1 (ידני); המודל היחיד ב-handover; נקודת הייחוס.')
def(36,'Chen',29,'מודלים',0,'How gradient boosting decides: 46 features (40 acoustic 10×4 + 6 meta); 50 עצים רדודים, כל אחד מתאים ל-residual של הקודם (depth 5, lr 0.1); Σ→sigmoid → p(HT) בסף 0.5. scale_pos_weight=3.12 מעלה משקל למחלקת HT הנדירה. מספרי הטסט של ה-baseline: 0.733 accuracy, 0.94 HT recall, 0.50 HT precision, 0.749 weighted F1 (subject-dependent).', 'must: למה נבחר עומק עץ כזה (depth 5) ומה זה נותן; ומה תפקיד learning rate.')
def(37,'Chen',45,'מודלים',0,'Baseline (RESULTS): ה-0.829 שדווח בעבר היה subject-dependent, legacy, לפני תיקון. פירוק: 0.829 −0.096 (תיקון תוויות גנוטיפ) → 0.733 (subject-dependent מתוקן) −0.040 (קיבוץ לפי עכבר) → 0.693 (subject-independent). רצפת "נחש-תמיד-WT" ≈ 0.73. שני משטרים = שתי שאלות שונות, לא "טוב-מול-רע".', 'must: כיצד מפרקים את הירידה מ-0.829, ולמה זה לא "המודל שלכם גרוע יותר".')
def(38,'Chen',29,'מודלים',0,'Why tuned beats default: במשטר שסופר — עכברים לא-נראים — הכיוונון הורג את ה-overfit. subject-independent, 22 עכברים held-out: Balanced accuracy 0.675→0.755 (+0.08); HT recall 0.64→0.87 (+0.23). Leaner trees (50/depth5 → 20/depth3); רגולריזציה חזקה יותר (min_child_weight 20, reg_lambda 3.0); נמצא ע"י חיפוש 200-trial random עם cross-validation. Takeaway: אותם פיצ\'רים, אותם עכברים — כיוונון לבדו הפך שינון להכללה.', 'must: מה זה cross-validation ואיך הוא משמש כאן; ולמה מודל רדוד ומוגבל יותר מכליל טוב יותר.')
def(39,'Chen',15,'מודלים',0,'Three tabular classifiers: XGBoost baseline (inherited, un-tuned, scale_pos_weight≈3.1, המודל היחיד ב-handover); XGBoost tuned (new, חיפוש 200-trial randomized עם CV, מתכון נפרד לכל משטר); TabPFN-3 (new, prior-data-fitted transformer, in-context Bayesian inference במעבר forward יחיד, ללא כיוונון; המודל הטבלאי הכי חזק).')
def(40,'Chen',29,'מודלים',0,'What is TabPFN? (1): Classic ML (למשל XGBoost) — הטבלה שלך → אמן מודל חדש (דקות-שעות) → חפש hyper-parameters → חזה. TabPFN — מאומן מראש פעם אחת על מיליוני טבלאות סינתטיות; מזינים שורות מתויגות + query כ-context → מעבר forward יחיד, ללא כיוונון → חזה WT/HT. "language model for spreadsheets" — in-context learning, מביא את הלמידה איתו.', 'must: מה זה prior-data-fitted network ומה זה in-context learning; ובמה זה שונה מהותית מ-XGBoost.')
def(41,'Chen',15,'מודלים',0,'What is TabPFN? (2): דיוק ממוצע על 51 datasets מ-OpenML; TabPFN-3-Thinking מוביל על העצים המוגברים הטובים ביותר ב-~420 ELO. 93% win rate מול classic ML על TabArena; 0.2 שניות לחיזוי מיליון דגימות; 80% מהמקרים מנצחים AutoML.')
def(42,'Chen',15,'מודלים',0,'Model card — TabPFN-3: foundation model לטבלאות (prior-data-fitted network); INFERENCE חיזוי Bayesian in-context במעבר forward יחיד; TUNING אין; DATA USAGE מקפל את ה-validation לתוך האימון — רואה ~80% מהדאטא מול ~60% של XGBoost; INPUT מטריצת 48 עמודות; ROLE המסווג הטבלאי הכי טוב. 1 forward pass, 0 hyper-parameters.')
def(43,'Chen',29,'מודלים',0,'How TabPFN decides — without training: 46×N שורות אימון (ה-context/prompt המתויג) + 1 recording חדש (query) → transformer מאומן-מראש (משקלים קפואים, in-context, ללא gradient descent על הדאטא שלך) → in-context posterior p(HT) בסף 0.5. balance_probabilities=True → תיקון 3:1 מובנה. מספרים: 0.781 accuracy (+0.048), 0.92 HT recall (−0.02), 0.55 HT precision (+0.05), 0.794 weighted F1 (+0.045). הכי טוב בשני המשטרים; בקושי יורד על עכברים לא-נראים: 0.729 independent מול 0.693 של XGBoost.')
def(44,'Chen',29,'מודלים',0,'What if the order of the calls is the signal? המודלים הטבלאיים ממַצעים כל הקלטה, וזורקים סדר וקצב — אז הסתכלנו על session כרצף. session אחד ≈ 10 דקות קריאות בידוד בסדר שהתרחשו. כל קריאה = 14 מספרים (4 acoustic, 8 type embedding, 2 flags), עד 256 צעדים. Tabular track זורק סדר (ממוצעים per-type); Sequence track שומר סדר ("המנגינה, לא רק התווים"). Gal et al. (2023): הדינמיקה הזמנית של הקריאות נושאת אות פנוטיפי. מודלים שנוסו: BiLSTM, 1D-CNN, Transformer.', 'must: למה בכלל בנינו מודל sequence בנוסף לטבלאי — מה ההבדל, ומה ה-embedding של סוג ההברה.')
def(45,'Chen',37,'מודלים',0,'A lucky fold, not a real gain: פיצול אחד נראה מצוין; cross-validation הראה שהסיבה היא קנה-מידה של דאטא, לא ההשערה. Balanced accuracy על עכברים לא-נראים: best single split 0.704 → 5-fold grouped CV 0.563±0.063 (−0.141). למה: data starvation — 125,576 הברות → 408 sessions → ~19 HT per fold; רק 24 עכברי HT בכל הדאטהסט. Chance=0.50; חלק מהמודלים ניבאו HT לכל session. מסקנה כנה: לא נתמך בקנה-מידה הזה (לא ש"הסדר לא אינפורמטיבי"). Verdict: Explored, not chosen.', 'must: איך cross-validation "ניפח החוצה" (deflate) את 0.704, ומה זה fold ממוזל (lucky fold).')

def(46,'Aviel',7,'תוצאות',1,'חוצץ Section 08 — Results.')
def(47,'Aviel',22,'תוצאות',0,'Everything we evaluated: grid — כל מודל, על כל ייצוג, על פני cohort scope (pooled/strain1/strain2) ומשטר פיצול (dep/ind). Tabular (XGBoost, tuned, TabPFN) + Sequence (BiLSTM, 1D-CNN, Transformer). 24 הערכות מדווחות (model×cohort×split). מאחורי הקלעים: חיפוש 200-trial, 8 imbalance levers × 3 ארכיטקטורות sequence, 5-fold grouped CV, 1 CNN typer.')
def(48,'Aviel',29,'תוצאות',0,'Two numbers, honestly reported: TabPFN מגיע לדיוק הגבוה ביותר מבין הטבלאיים ומנצח את ה-baseline בשני המשטרים. Subject-dependent 0.781 (עד 0.801 per cohort). Subject-independent 0.729 (weighted F1 0.743, ROC-AUC 0.783). ל-reference: XGBoost baseline 0.733 dep / 0.693 ind.')
def(49,'Aviel',45,'תוצאות',0,'The tabular models, side by side (טבלה מלאה): לפי משטר. Subject-dependent — XGBoost inherited: Acc 0.733, wF1 0.749, bal.acc 0.795, ROC-AUC 0.876, HT recall 0.940, HT prec 0.496, HT F1 0.649. XGBoost-tuned: 0.772/0.785/0.798/0.885/0.844/0.543/0.661. TabPFN: 0.781/0.794/0.828/0.908/0.918/0.550/0.688. Subject-independent — XGBoost: 0.693/0.706/0.678/0.770/0.637/0.452/0.529. tuned: 0.702/0.719/0.725/0.753/0.869/0.473/0.612. TabPFN: 0.729/0.743/0.662/0.783/0.782/0.499/0.610. TabPFN הכי טוב כללית; tuned-XGBoost נותן את ה-HT recall הכי טוב על לא-נראים. מחלקה חיובית = HT.', 'must: למה balanced accuracy של TabPFN נמוך יחסית ב-independent (0.662) למרות accuracy גבוה — מה זה אומר על WT/HT recall.')
def(50,'Aviel',22,'תוצאות',0,'The generalization gap: dumbbells dependent→independent. XGBoost 0.733→0.693; tuned 0.772→0.702; TabPFN 0.781→0.729. כל מודל יורד מעכברים מוכרים ללא-נראים, אבל TabPFN מעביר (transfers) הכי טוב.')
def(51,'Aviel',29,'תוצאות',0,'Catching the true cases: HT recall: recall = החלק מגורי מודל-ה-ASD האמיתיים שהמודל מסמן. dependent מול independent: XGBoost 0.940→0.637; tuned 0.844→0.869; TabPFN 0.918→0.782. על לא-נראים ה-baseline קורס ל-0.637; הכיוונון משחזר ל-0.869 — הכי טוב מכל מודל.')
def(52,'Aviel',22,'תוצאות',0,'The clinically important number: כלי סקרינינג אסור לו לפספס מקרים אמיתיים → HT recall על עכברים לא-נראים חשוב מכל. 0.869 (tuned XGBoost, ~87% מגורי מודל-ה-ASD); TabPFN מחזיק 0.782. המודל הטוב תלוי במטרה: דיוק כללי → TabPFN; recall של מחלקת מיעוט (סקרינינג) → tuned XGBoost.')
def(53,'Aviel',37,'תוצאות',0,'Where each true class goes (unseen animals): פירוק כל מחלקה אמיתית לנכון-מול-מבולבל. XGBoost: true WT 71% נכון / 29% פוספס, true HT 64%/36%. tuned: WT 64%/36%, HT 87%/13%. TabPFN: WT 71%/29%, HT 78%/22%. הכיוונון חותך פספוסי-HT מ-36% ל-13% — אבל ~30% מהגורים הבריאים עדיין מסומנים HT: זהו קיר הדיוק, מגבלה ברמת הפיצ\'רים.', 'must: למה תמיד ~30% מ-WT דולפים ל-HT (קיר הדיוק) ולא משנה איזה מודל.')
def(54,'Aviel',29,'תוצאות',0,'Ranking quality: ROC and precision–recall: ROC-AUC של TabPFN 0.908 (seen) → 0.783 (unseen); עלות המשטר ≈ −0.12 AUC (פער ההכללה, כמותית). עקומת Precision–Recall למחלקת HT מעל ה-prevalence (0.26) → אות אמיתי, אבל הדיוק מתפורר ב-recall גבוה.', 'must: מה ההבדל בין ROC לבין precision-recall curve ולמה PR רלוונטי יותר כאן (מחלקת מיעוט).')
def(55,'Aviel',29,'תוצאות',0,'What the signal can and can\'t do: שתי תקרות שמעצבות כל מסקנה. (1) The HT precision wall: HT precision מוצמד ~0.50 בכל מודל, כיוונון ופיצול — כמחצית מההתראות שגויות; תקרה ברמת הפיצ\'רים, לא של המסווג. (2) Strain = cohort confound: strain1 across-subject 0.903 בעוד strain2 קורס; הזן confounded עם עידן ההקלטה והרקע הגנטי — מספרי per-strain אינם פנוטיפ טהור.')
def(56,'Aviel',22,'תוצאות',0,'The HT precision wall: dot plot — HT precision בסף 0.5 על פני כל קונפיגורציה טבלאית מתקבץ סביב 0.50 (רצועה אפורה); ה-cohort הקל strain1 בורח כלפי מעלה; קונפיגורציות strain2-independent נופלות מתחת לרצועה (XGBoost ו-tuned קורסים על מחלקת המיעוט — HT recall קרוב לאפס — אז הדיוק שלהם לא משמעותי). תקרה שנקבעת ע"י הפיצ\'רים.')
def(57,'Aviel',45,'תוצאות',0,'Which features drive the call? חשיבות gain של XGBoost, ממוצעת: Mother genotype 0.585 (שולט!), Strain 0.033, Sex 0.028, syll3_dist 0.018, syll6_dist 0.016, Age 0.016, syll1_dist 0.013, syll1_s_freq 0.012, syll3_e_freq 0.011, ... מטא-דאטה שולט; מבין ה-cues האקוסטיים — תדרי-גבול (border frequencies) ומשכים per-type מובילים. הרבה מהאות הוא מטא-דאטה — חלק מהסיבה שקיר הדיוק מחזיק.', 'must: mother_gen שולט בגרף (~0.585) בעוד הטקסט מדגיש פיצ\'רים אקוסטיים — איך אתם מיישבים את זה? האם הדיוק מגיע מהקולות או מיוחסין (breeding confound)? (זו שאלת הסיכון מס\' 1 — ראו בלוק ⚠️).')
def(58,'Aviel',29,'תוצאות',0,'Strain confounds the phenotype: heatmap per-strain לכל המודלים הטבלאיים. strain1 (ה-cohort המעורב, החדש) נפרד; strain2 קורס. הזן שזור עם ה-cohort והרקע הגנטי. strain1-independent ~0.90 אסור לקרוא ככותרת כללית — ייתכן שהמודל קורא cohort membership ולא פנוטיפ.')
def(59,'Aviel',29,'תוצאות',0,'The threshold is a dial we control: קיר הדיוק קבוע — אבל סף ההחלטה שלנו. TabPFN אחד, נקודות תפעול @0.5/Youden/F1/target-recall/balanced. אפשר לדחוף recall→~1.0 על לא-נראים כדי לתפוס כמעט כל מקרה; precision מחזיק ~0.47 (הקיר נשאר) — אז בוחרים recall לסקרינינג. הסף נגזר על ה-validation ומוקפא לפני הטסט; לא משנה AUC.', 'must: מה זה Youden\'s J ולמה על independent הוא "מתנוון" (recall→1, precision מוצמד).')

def(60,'Chen',7,'הנדסה',1,'חוצץ Section 09 — Engineering contribution: לפי הנחיות HIT, הפיכת פרוטוטיפ מחקרי שהתקבל בירושה למערכת reproducible מקצה-לקצה היא תוצאה בפני עצמה.')
def(61,'Chen',29,'הנדסה',0,'A segmentation app the lab actually uses: GUI בלחיצה אחת שעוטף segmentation + CNN typing — נבנה עבור פרופ\' חוה גולן לאצור USVs בלי command line. היררכיית year→session; אותם אלגוריתמים כמו הפייפליין; מפיק את הקובץ הקנוני; תפס את שגיאת הגנוטיפ. פורסם — USV Segmentation v1.0.2, Zenodo, installer ל-Windows בלחיצה אחת.')
def(62,'Chen',37,'הנדסה',0,'From inherited prototype to a single source of truth: שושלת דאטא מתועדת אחת, versioned מקצה-לקצה. Raw WAV → GUI segmentation → Canonical file (single source of truth) → Manifest + filters → Train matrices → Per-run results. Single source of truth (קובץ קנוני אחד + manifest עם גרסאות מחליף גיליונות מפוזרים); Data-integrity fix (14 עכברים / 2,495 שורות HET→WT + ה-baseline הכן והנמוך יותר); End-to-end reproducible (סביבה נעולה — requirements + Dockerfile, ו-CLI flags למודל/משטר/strain). Open source ב-GitHub; citable ב-Zenodo doi.')
def(63,'Chen',7,'מסקנות',1,'חוצץ Section 10 — Conclusions & future work.')
def(64,'Chen',45,'מסקנות',0,'Answering the research questions: RQ1 Models — Yes: TabPFN מנצח בשני המשטרים (0.781 within / 0.729 across, ROC-AUC 0.783); tuned XGBoost נותן minority recall הכי טוב (0.869 על לא-נראים). RQ2 Features — Partly: תדרי-גבול ומשכים per-syllable-type (עקבי עם Shekel et al.) — אבל HT precision ≈ 0.50 מסמן תקרה ברמת הייצוג. RQ3 Regime — Decisive: המשטר שולט (עד ~0.30 פער ב-HT recall), strain confounded עם cohort, sequence לא עוזר בקנה-מידה הזה. Engineering — Yes: פייפליין reproducible + תיקון שגיאת הגנוטיפ.')
def(65,'Chen',29,'מסקנות',0,'Conclusion: קולות USV של עכברים נושאים אות אמיתי של מודל-ASD — חזק על עכברים מוכרים, ריאלית מעל הסיכוי על חדשים. סקאלה: chance 0.50 → subject-independent (unseen 0.729 acc / 0.783 AUC) → subject-dependent (seen 0.78-0.80) → perfect 1.00. שלושה עוגנים: The signal is real (0.869 HT recall תופס מקרים אמיתיים על לא-נראים); Honestly bounded (תקרת precision ~0.50 ברמת הפיצ\'רים + קונפאונד strain — מדווח לכל משטר, לא מוסתר); Reproducible & auditable (single source of truth, קוד פתוח, כל מספר עקיב).')
def(66,'Chen',29,'מסקנות',0,'Where this goes next (Future work): שלושה צעדים בעלי המנוף הגבוה ביותר. (1) Richer per-call features — הוספת descriptors מלאים של frequency contour (mean/min/max/slope, bandwidth, FM depth) כדי לבדוק אם קיר ה-HT-precision נשבר — הניסוי בעל המנוף הגבוה ביותר. (2) A true cross-cohort test — אימון על זן אחד והערכה על השני, כדי להפריד פנוטיפ ASD מ-cohort membership ולשלוט בהבדל הרקע הגנטי. (3) Per-subject decisions — צבירת חיזויי call/session להצבעה אחת לכל עכבר ודיווח מטריקות ברמת subject — הרזולוציה הקלינית המשמעותית.')
def(67,'Chen',15,'מסקנות',0,'Thank you — Questions & discussion: מנחה ד"ר דרור לדרמן; חוקרת ראשית ובעלת הדאטא פרופ\' חוה גולן (בן-גוריון); הוצג ע"י חן אהרון ואביאל ביטון, M.Sc. Data Science.')

// ---------- groups ----------
const GROUPS = [
  { key: 'g1', label: 'שקפים 1-4 (פתיחה+מוטיבציה)', nums: [1,2,3,4] },
  { key: 'g2', label: 'שקפים 5-11 (רקע)', nums: [5,6,7,8,9,10,11] },
  { key: 'g3', label: 'שקפים 12-16 (פתרון+שאלות מחקר)', nums: [12,13,14,15,16] },
  { key: 'g4', label: 'שקפים 17-21 (דאטהסט)', nums: [17,18,19,20,21] },
  { key: 'g5', label: 'שקפים 22-30 (שיטות)', nums: [22,23,24,25,26,27,28,29,30] },
  { key: 'g6', label: 'שקפים 31-38 (מודלים א)', nums: [31,32,33,34,35,36,37,38] },
  { key: 'g7', label: 'שקפים 39-45 (מודלים ב: TabPFN+sequence)', nums: [39,40,41,42,43,44,45] },
  { key: 'g8', label: 'שקפים 46-54 (תוצאות א)', nums: [46,47,48,49,50,51,52,53,54] },
  { key: 'g9', label: 'שקפים 55-59 (תוצאות ב)', nums: [55,56,57,58,59] },
  { key: 'g10', label: 'שקפים 60-67 (הנדסה+מסקנות)', nums: [60,61,62,63,64,65,66,67] },
]

const DIR = '/home/aviel/dev/hit/mouse-usv-asd-pipeline/final_doc_2026/defense_prep'

function slideBlock(n) {
  const s = S[n]
  return `--- שקף ${n} | מציג: ${s.p} | זמן מוקצב: ${s.sec} שניות | סקשן: ${s.section}${s.div ? ' | [שקף חוצץ — divider]' : ''}\n` +
    `תיאור: ${s.brief}` + (s.must ? `\nחובה לכלול שאלה שמכסה: ${s.must}` : '')
}

const SCHEMA = {
  type: 'object',
  properties: {
    slides: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          slide: { type: 'integer' },
          title: { type: 'string', description: 'כותרת השקף באנגלית כפי שמופיעה' },
          summary_he: { type: 'string' },
          script_he: { type: 'string', description: 'מה שהמציג אומר בקול, עברית מדוברת, באורך שמתאים לזמן המוקצב' },
          info_he: {
            type: 'array',
            items: { type: 'object', properties: { term: { type: 'string' }, explain_he: { type: 'string' } }, required: ['term','explain_he'] },
          },
          questions: {
            type: 'array',
            items: { type: 'object', properties: { q_he: { type: 'string' }, a_he: { type: 'string' } }, required: ['q_he','a_he'] },
          },
        },
        required: ['slide','title','summary_he','script_he','info_he','questions'],
      },
    },
  },
  required: ['slides'],
}

phase('Slides')
const slideResults = await parallel(GROUPS.map(g => () => {
  const imgs = g.nums.map(n => `${DIR}/slides/slide-${String(n).padStart(2,'0')}.png`).join('\n')
  const prompt = `אתה עוזר-הכנה בכיר להגנת פרויקט גמר M.Sc. במדעי הנתונים. משימתך: להפיק "ספיקר-נוטס" ופסקאות-מידע ושאלות-בוחן בעברית עבור קבוצת שקפים.

${SHARED}

${OUTPUT_RULES}

מקורות שאתה חייב לקרוא לפני הכתיבה כדי לדייק במספרים ובפרטים:
1. תמונות השקפים שלך (קרא כל אחת עם הכלי Read):
${imgs}
2. טקסט הספר (מקור האמת): ${DIR}/book_text.txt
3. טקסט המצגת: ${DIR}/presentation_text.txt

הקבוצה שלך: ${g.label}. הפק פריט לכל אחד מהשקפים הבאים, לפי הסדר. עבור שקף חוצץ (divider): summary_he קצר, script_he משפט מעבר קצר (מתאים לזמן), info_he ריק או מינימלי, questions ריק. עבור שקפי מוטיבציה: questions ריק.

${g.nums.map(slideBlock).join('\n\n')}

החזר JSON תקין לפי הסכימה בלבד. ודא ש-slide הוא מספר השקף הנכון.`
  return agent(prompt, { label: `slides:${g.key}`, phase: 'Slides', schema: SCHEMA, agentType: 'general-purpose' })
    .then(r => ({ key: g.key, slides: (r && r.slides) || [] }))
}))

phase('Extras')
const HOLISTIC_SCHEMA = {
  type: 'object',
  properties: { items: { type: 'array', items: { type: 'object', properties: { q_he: { type: 'string' }, a_he: { type: 'string' }, tag: { type: 'string' } }, required: ['q_he','a_he'] } } },
  required: ['items'],
}
const GLOSSARY_SCHEMA = {
  type: 'object',
  properties: { items: { type: 'array', items: { type: 'object', properties: { term: { type: 'string' }, kind: { type: 'string', description: 'biology | ml | metric | dataset | other' }, def_he: { type: 'string' } }, required: ['term','def_he'] } } },
  required: ['items'],
}

const extras = await parallel([
  () => agent(`אתה בוחן חיצוני קפדן בהגנת M.Sc. במדעי הנתונים (יכול להיות טכני או ביולוגי). נסח 14-18 שאלות הוליסטיות ברמת-הפרויקט (לא ספציפיות לשקף בודד) עם תשובות מלוטשות ומבוססות-ספר, בעברית.

${SHARED}

קרא גם: ${DIR}/book_text.txt

כסה בין השאר: (1) למה מודל sequence בנוסף לטבלאי ומה ההבדל ביניהם; (2) למה TabPFN ולא רק XGBoost; (3) האם זה שמיש קלינית / האם זה תקף לבני אדם; (4) איך אתם יודעים שהמודל לומד את הפנוטיפ ולא cohort/יוחסין; (5) למה לא החלטה per-mouse; (6) מגבלת גודל הדאטא ומובהקות סטטיסטית / רוחב רווחי-סמך; (7) מה באמת חדש מול הפרויקט שהתקבל בירושה ומול Lederman/PANNs הקודם; (8) למה subject-independent הוא הדרך הנכונה למדוד; (9) מה הייתם עושים אחרת / הצעד הבא הכי חשוב; (10) איך היה מטופל class imbalance; (11) האם ה-CNN typer מהימן בלי model card; (12) מה תפקידו של דרור לדרמן מול חוה גולן. תייג כל שאלה ב-tag קצר (למשל "מתודולוגיה", "ביולוגיה", "תקפות", "הנדסה"). החזר JSON לפי הסכימה.`, { label: 'holistic-qa', phase: 'Extras', schema: HOLISTIC_SCHEMA, agentType: 'general-purpose' }).then(r => ({ kind: 'holistic', items: (r && r.items) || [] })),

  () => agent(`אתה מאמן-הגנה. הפק "רשימת מלכודות" — 8-10 השאלות המסוכנות/מביכות ביותר שהבוחן עלול לשאול, שבהן קל להיכשל, עם: (a) התשובה המלאה והכנה, (b) "משפט-בטיחות" קצר של שורה אחת שאפשר לומר מיד, (c) מה אסור לומר. בעברית.

${SHARED}

קרא גם: ${DIR}/book_text.txt

המלכודות חייבות לכלול לפחות: (1) mother_gen שולט בחשיבות הפיצ'רים בעוד הטקסט מדבר על אקוסטיקה (הסיכון מס' 1); (2) ה-0.829 מול 0.733 — "אז המודל שלכם גרוע יותר?"; (3) strain1 0.903 — "אז יש לכם מודל מצוין!" (קונפאונד); (4) קיר הדיוק ~0.50 — "חצי מההתראות שגויות, זה חסר תועלת?"; (5) המודלים הסדרתיים נכשלו — "אז בזבזתם זמן?"; (6) רק 24 עכברי HT — מובהקות; (7) ה-CNN typer בלי model card ובלי ולידציה מול ground-truth; (8) "מה בעצם עשיתם שהוא חדש?" (מול הירושה והפרויקט הקודם); (9) האם זה רלוונטי לאבחון אוטיזם אמיתי בבני אדם. תייג כל פריט ב-tag. השתמש בשדה a_he לתשובה המלאה, q_he לשאלה; שים את משפט-הבטיחות ואת "אסור לומר" בתוך a_he בפורמט: "תשובה: ... | משפט-בטיחות: ... | להימנע מ: ...". החזר JSON לפי הסכימה (items עם q_he,a_he,tag).`, { label: 'danger-qa', phase: 'Extras', schema: HOLISTIC_SCHEMA, agentType: 'general-purpose' }).then(r => ({ kind: 'danger', items: (r && r.items) || [] })),

  () => agent(`אתה עורך מדעי. הפק גיליון מונחים (glossary) ממצה בעברית לכל ראשי-התיבות והמונחים המדעיים/טכניים שמופיעים במצגת ובספר, כך שהמציגים יוכלו לרענן לפני ההגנה. הגדרה של 1-2 משפטים לכל מונח, מדויקת ונגישה.

${SHARED}

קרא גם: ${DIR}/book_text.txt (יש בו List of Abbreviations) ו-${DIR}/presentation_text.txt

כלול לפחות: ASD, USV, WT, HET/HT, UNK, Mthfr, MTHFR, SAM, one-carbon/folate metabolism, methylation, haploinsufficiency, heterozygous, wild-type, ortholog, ADOS, biomarker, BALB/c, C57BL/6, strain, dam, pup, postnatal day P4-P12, isolation call, spectrogram, STFT, gammatone filterbank, ERB, high-pass, ISI, inter-syllable interval, boundary/border frequency, frequency modulation, bandwidth, CNN, BiT, ResNet, ImageNet-21k, GroupNorm, Weight Standardization, softmax, transfer learning, fine-tuning, argmax, XGBoost, gradient boosting, residual, scale_pos_weight, learning rate, max_depth, regularization, min_child_weight, reg_lambda, hyperparameter search, TabPFN, prior-data-fitted network, in-context learning, foundation model, Bayesian inference, ELO, TabArena, AutoML, OpenML, BiLSTM, LSTM, 1D-CNN, Transformer, self-attention, CLS token, embedding, padding/truncation, sequence, subject-dependent, subject-independent, data leakage, grouped split, stratification, cross-validation, k-fold, fold, deflation, accuracy, balanced accuracy, weighted F1, precision, recall, sensitivity, specificity, F1, ROC, ROC-AUC, precision-recall curve, PR-AUC, prevalence, Youden's J, decision threshold, operating point, confusion matrix, class imbalance, confound, feature importance, gain importance, single source of truth, manifest, Docker, reproducibility, Zenodo, Shekel 2021, Gal 2023, Saeb 2017, MADUV, PANNs. סמן kind לכל מונח (biology/ml/metric/dataset/other). החזר JSON לפי הסכימה.`, { label: 'glossary', phase: 'Extras', schema: GLOSSARY_SCHEMA, agentType: 'general-purpose' }).then(r => ({ kind: 'glossary', items: (r && r.items) || [] })),
])

// ---------- assemble return ----------
const bySlide = {}
for (const g of slideResults) if (g) for (const sl of g.slides) bySlide[sl.slide] = sl
const holistic = extras.find(e => e && e.kind === 'holistic') || { items: [] }
const danger = extras.find(e => e && e.kind === 'danger') || { items: [] }
const glossary = extras.find(e => e && e.kind === 'glossary') || { items: [] }

log(`slides generated: ${Object.keys(bySlide).length}/67 · holistic Q: ${holistic.items.length} · danger Q: ${danger.items.length} · glossary: ${glossary.items.length}`)

return {
  slides: bySlide,
  holistic: holistic.items,
  danger: danger.items,
  glossary: glossary.items,
  missing: Array.from({length:67},(_,i)=>i+1).filter(n=>!bySlide[n]),
}
