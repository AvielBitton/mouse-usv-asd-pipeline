# -*- coding: utf-8 -*-
import json, html, os

BASE = os.path.dirname(os.path.abspath(__file__))
content = json.load(open(os.path.join(BASE, "content.json")))
thumbs = json.load(open(os.path.join(BASE, "thumb_b64.json")))
timing = json.load(open(os.path.join(BASE, "timing.json")))

slides = content["slides"]          # keyed by str(num)
holistic = content.get("holistic", [])
danger = content.get("danger", [])
glossary = content.get("glossary", [])

def esc(s):
    return html.escape(str(s or "")).replace("\n", "<br>")

# ----- section metadata (Hebrew names + order) -----
SECTIONS = [
    ("פתיחה", "Opening", "01"),
    ("מוטיבציה", "Motivation", "01"),
    ("רקע", "Background", "02"),
    ("הפתרון", "The solution", "03"),
    ("שאלות מחקר", "Research questions", "04"),
    ("דאטהסט", "Dataset", "05"),
    ("שיטות", "Methods", "06"),
    ("מודלים", "Models", "07"),
    ("תוצאות", "Results", "08"),
    ("הנדסה", "Engineering", "09"),
    ("מסקנות", "Conclusions", "10"),
]
SEC_TIME = {}
for n in range(1, 68):
    t = timing[str(n)]
    SEC_TIME.setdefault(t["section"], 0)
    SEC_TIME[t["section"]] += t["sec"]

SEC_KEY_TO_HE = {
    "Opening": "פתיחה", "Motivation": "מוטיבציה", "Background": "רקע", "Solution": "הפתרון",
    "ResearchQ": "שאלות מחקר", "Dataset": "דאטהסט", "Methods": "שיטות", "Models": "מודלים",
    "Results": "תוצאות", "Engineering": "הנדסה", "Conclusions": "מסקנות",
}

def fmt(sec):
    return f"{sec//60}:{sec%60:02d}"

TOTAL = sum(timing[str(n)]["sec"] for n in range(1, 68))
AVIEL = sum(timing[str(n)]["sec"] for n in range(1, 68) if timing[str(n)]["presenter"] == "Aviel")
CHEN = TOTAL - AVIEL

# ----- presentation tips (authored) -----
TIPS = [
    ("קצב הוא הסיכון מס' 1", "יש 67 שקפים ל-~27.5 דקות — זה אומר ~24 שניות לשקף בממוצע. אל תתעכבו על שקפי-בנייה. שקפים שמופיע עליהם רק כותרת ואייקונים (למשל 39, 41, 42) — משפט אחד וקדימה. שמרו את הזמן ל-5 השקפים הקריטיים: 15 (שאלות מחקר), 34 (שני משטרי הפיצול), 37 (פירוק ה-0.829), 49 (טבלת התוצאות), 57 (חשיבות פיצ'רים)."),
    ("מסירה בין המציגים", "יש 3 העברות: אביאל→חן (16→17), חן→אביאל (45→46), אביאל→חן (59→60). תרגלו משפט-מעבר קצר בכל העברה (\"עכשיו חן ייקח אותנו לתוך הדאטא\"). מי שלא מדבר — מסתכל על הקהל, לא על המסך."),
    ("דעו את 6 המספרים בעל-פה", "0.781 / 0.729 (TabPFN dep/ind), 0.733 (baseline dep), 0.869 (HT recall מכוונן על לא-נראים), 0.783 (ROC-AUC ind), ~0.50 (קיר הדיוק). כמעט כל שאלה כמותית נענית באחד מהם."),
    ("כנות מנצחת התגוננות", "הפרויקט הזה חזק דווקא כי הוא ישר: תיקנתם שגיאת דאטא שהורידה baseline, דיווחתם קונפאונד strain, והצגתם קיר-דיוק במקום להסתיר אותו. כשנשאלים על מגבלה — אשרו אותה, הסבירו למה היא לא שוברת את המסקנה, והצביעו על העבודה העתידית."),
    ("המלכודת שחייבים להכיר מראש", "אם הבוחן מסתכל על שקף 57 וישאל על mother_gen — אל תיבהלו. זה קונפאונד חזוי-מהכלאה; האות האקוסטי האמיתי הוא זה שמשתקף ב-subject-independent וב-ROC-AUC. ראו את בלוק \"מלכודות ותשובות מוכנות\"."),
    ("שני קהלים, שתי שפות", "לבוחן ביולוגי — הדגישו את Mthfr/SAM/מתילציה, את פרדיגמת הבידוד, ואת ה-USV כביו-מרקר. לבוחן טכני — הדגישו את subject-independent, TabPFN, ה-CV deflation, וקיר הדיוק. פסקאות המידע בכל שקף מכסות את שניהם."),
    ("מה לומר כשלא יודעים", "\"שאלה מצוינת — לא בדקנו את זה ישירות; מה שכן מדדנו הוא X, ומכאן ההערכה שלי היא Y.\" עדיף מלנחש. לעולם אל תמציאו מספר."),
    ("סגירה", "שקף 65 הוא ה-take-home: אות אמיתי, חסום בכנות, ורפרודוקטיבי. סיימו עליו בביטחון לפני שעוברים לשקף התודות."),
]

# ----- HTML -----
CSS = """
:root{
  --bg:#f7f6f2; --card:#ffffff; --ink:#1c2230; --muted:#5b6472; --line:#e6e3db;
  --aviel:#2563eb; --chen:#0d9488; --navy:#1a1a2e; --accent:#2563eb;
  --script-bg:#eef4ff; --script-line:#2563eb; --info-bg:#fbf9f4; --q-bg:#f4f7f5;
  --warn-bg:#fff4ec; --warn-line:#e8873b;
}
@media (prefers-color-scheme: dark){
  :root{ --bg:#12141a; --card:#1a1d26; --ink:#e8eaf0; --muted:#9aa3b2; --line:#2b303c;
    --script-bg:#16233d; --info-bg:#1d2029; --q-bg:#161f1c; --warn-bg:#2a1f16; --navy:#0f1220; }
}
:root[data-theme="dark"]{ --bg:#12141a; --card:#1a1d26; --ink:#e8eaf0; --muted:#9aa3b2; --line:#2b303c;
  --script-bg:#16233d; --info-bg:#1d2029; --q-bg:#161f1c; --warn-bg:#2a1f16; --navy:#0f1220; }
:root[data-theme="light"]{ --bg:#f7f6f2; --card:#ffffff; --ink:#1c2230; --muted:#5b6472; --line:#e6e3db;
  --script-bg:#eef4ff; --info-bg:#fbf9f4; --q-bg:#f4f7f5; --warn-bg:#fff4ec; --navy:#1a1a2e; }
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
  font-family:"Segoe UI","Assistant","Heebo",Arial,sans-serif;line-height:1.65;}
.wrap{max-width:1040px;margin:0 auto;padding:24px 20px 80px;}
header.top{background:var(--navy);color:#fff;border-radius:16px;padding:26px 28px;margin-bottom:22px;}
header.top h1{margin:0 0 6px;font-size:26px;line-height:1.25;}
header.top .sub{opacity:.85;font-size:15px;}
header.top .meta{margin-top:12px;font-size:14px;opacity:.8;}
.pill{display:inline-block;padding:2px 10px;border-radius:999px;font-size:12.5px;font-weight:600;white-space:nowrap;}
.pill.aviel{background:rgba(37,99,235,.15);color:var(--aviel);border:1px solid rgba(37,99,235,.35);}
.pill.chen{background:rgba(13,148,136,.15);color:var(--chen);border:1px solid rgba(13,148,136,.35);}
.pill.time{background:rgba(120,120,120,.14);color:var(--muted);border:1px solid var(--line);}
.pill.sec{background:rgba(26,26,46,.08);color:var(--muted);border:1px solid var(--line);}
.panel{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:18px 20px;margin:16px 0;}
.panel h2{margin:0 0 12px;font-size:20px;}
.panel h3{margin:18px 0 8px;font-size:16px;color:var(--muted);}
table{border-collapse:collapse;width:100%;font-size:13.5px;}
.tblwrap{overflow-x:auto;}
th,td{border:1px solid var(--line);padding:6px 9px;text-align:right;}
th{background:rgba(26,26,46,.06);font-weight:700;}
td.num,th.num{direction:ltr;text-align:center;font-variant-numeric:tabular-nums;}
.legend{font-size:13px;color:var(--muted);margin-top:6px;}
.tips li{margin-bottom:9px;}
.tips b{color:var(--accent);}
.secband{margin:34px 0 8px;padding:10px 16px;background:var(--navy);color:#fff;border-radius:10px;
  display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;}
.secband .nm{font-size:18px;font-weight:700;}
.secband .en{opacity:.7;font-size:13px;font-weight:400;margin-inline-start:8px;}
.slide{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:0;margin:14px 0;overflow:hidden;}
.slide.aviel{border-inline-start:5px solid var(--aviel);}
.slide.chen{border-inline-start:5px solid var(--chen);}
.slide .head{display:flex;gap:14px;align-items:flex-start;padding:16px 18px 0;flex-wrap:wrap;}
.slide .num{font-size:30px;font-weight:800;color:var(--muted);min-width:42px;line-height:1;}
.slide .htext{flex:1;min-width:220px;}
.slide .htext .en{font-size:17px;font-weight:700;}
.slide .htext .badges{margin-top:7px;display:flex;gap:6px;flex-wrap:wrap;}
.slide img{display:block;width:340px;max-width:42%;height:auto;border:1px solid var(--line);border-radius:8px;}
@media(max-width:720px){.slide img{max-width:100%;width:100%;}}
.slide .body{padding:6px 18px 18px;}
.blk{margin-top:12px;}
.blk .lab{font-size:12.5px;font-weight:700;letter-spacing:.02em;color:var(--muted);
  text-transform:uppercase;margin-bottom:5px;display:flex;align-items:center;gap:6px;}
.summary{color:var(--muted);}
.script{background:var(--script-bg);border-inline-start:4px solid var(--script-line);
  border-radius:8px;padding:12px 14px;font-size:15.5px;}
.info{background:var(--info-bg);border:1px solid var(--line);border-radius:8px;padding:6px 14px;}
.info .it{padding:8px 0;border-bottom:1px dashed var(--line);}
.info .it:last-child{border-bottom:none;}
.info .t{font-weight:700;}
.qa{background:var(--q-bg);border:1px solid var(--line);border-radius:8px;padding:10px 14px;margin-top:8px;}
.qa .q{font-weight:700;}
.qa .a{margin-top:4px;color:var(--ink);}
.qa .a b{color:var(--accent);}
.big-sec{margin-top:44px;}
.big-sec > h2{font-size:23px;border-bottom:3px solid var(--accent);padding-bottom:8px;}
.warn{background:var(--warn-bg);border:1px solid var(--warn-line);border-inline-start:5px solid var(--warn-line);
  border-radius:10px;padding:12px 16px;margin:12px 0;}
.warn .q{font-weight:700;}
.warn .a{margin-top:6px;}
.dline{padding:3px 0;}
.dline b{color:var(--warn-line);}
.gl-group{margin-top:16px;}
.gl-group h3{color:var(--accent);}
.gl{display:grid;grid-template-columns:1fr;gap:0;}
.gl .it{padding:7px 0;border-bottom:1px dashed var(--line);}
.gl .t{font-weight:700;}
.toc{columns:2;font-size:14px;column-gap:26px;}
.toc a{color:var(--accent);text-decoration:none;}
@media(max-width:640px){.toc{columns:1;}}
.themebtn{position:fixed;inset-block-start:12px;inset-inline-start:12px;z-index:50;background:var(--card);
  border:1px solid var(--line);color:var(--ink);border-radius:8px;padding:6px 10px;cursor:pointer;font-size:13px;}
a.jump{color:var(--muted);text-decoration:none;font-size:12px;}
"""

def render_info(items):
    if not items: return ""
    rows = "".join(
        f'<div class="it"><span class="t">{esc(i.get("term"))}</span> — {esc(i.get("explain_he"))}</div>'
        for i in items)
    return f'<div class="blk"><div class="lab">📚 פסקת מידע — מושגים שאפשר להישאל עליהם</div><div class="info">{rows}</div></div>'

def render_qa(items):
    if not items: return ""
    blocks = "".join(
        f'<div class="qa"><div class="q">שאלה: {esc(q.get("q_he"))}</div><div class="a"><b>תשובה:</b> {esc(q.get("a_he"))}</div></div>'
        for q in items)
    return f'<div class="blk"><div class="lab">❓ שאלות אפשריות + תשובות</div>{blocks}</div>'

# ---- results table (slide 49) authored HTML, LTR numbers ----
RESULTS_TABLE = """
<div class="tblwrap"><table>
<tr><th>Model</th><th class="num">Acc</th><th class="num">wF1</th><th class="num">Bal.acc</th><th class="num">ROC-AUC</th><th class="num">HT recall</th><th class="num">HT prec</th><th class="num">HT F1</th></tr>
<tr><td colspan="8" style="background:rgba(37,99,235,.08);font-weight:700">Subject-dependent — עכברים מוכרים</td></tr>
<tr><td>XGBoost · inherited</td><td class="num">0.733</td><td class="num">0.749</td><td class="num">0.795</td><td class="num">0.876</td><td class="num">0.940</td><td class="num">0.496</td><td class="num">0.649</td></tr>
<tr><td>XGBoost-tuned</td><td class="num">0.772</td><td class="num">0.785</td><td class="num">0.798</td><td class="num">0.885</td><td class="num">0.844</td><td class="num">0.543</td><td class="num">0.661</td></tr>
<tr><td><b>TabPFN</b></td><td class="num"><b>0.781</b></td><td class="num"><b>0.794</b></td><td class="num"><b>0.828</b></td><td class="num"><b>0.908</b></td><td class="num">0.918</td><td class="num">0.550</td><td class="num">0.688</td></tr>
<tr><td colspan="8" style="background:rgba(232,135,59,.10);font-weight:700">Subject-independent — עכברים לא-נראים</td></tr>
<tr><td>XGBoost · inherited</td><td class="num">0.693</td><td class="num">0.706</td><td class="num">0.678</td><td class="num">0.770</td><td class="num">0.637</td><td class="num">0.452</td><td class="num">0.529</td></tr>
<tr><td>XGBoost-tuned</td><td class="num">0.702</td><td class="num">0.719</td><td class="num">0.725</td><td class="num">0.753</td><td class="num"><b>0.869</b></td><td class="num">0.473</td><td class="num">0.612</td></tr>
<tr><td><b>TabPFN</b></td><td class="num"><b>0.729</b></td><td class="num"><b>0.743</b></td><td class="num">0.662</td><td class="num"><b>0.783</b></td><td class="num">0.782</td><td class="num">0.499</td><td class="num">0.610</td></tr>
</table></div>
<div class="legend">מחלקה חיובית = HT (מודל-ASD). TabPFN הכי טוב כללית; XGBoost-tuned נותן את ה-HT recall הכי גבוה על עכברים לא-נראים (0.869).</div>
"""

def slide_html(n):
    sl = slides.get(str(n))
    t = timing[str(n)]
    pres = t["presenter"]; pres_he = "אביאל" if pres == "Aviel" else "חן"
    cls = "aviel" if pres == "Aviel" else "chen"
    sec_he = SEC_KEY_TO_HE.get(t["section"], t["section"])
    title = sl.get("title") if sl else ""
    img = thumbs.get(str(n), "")
    badges = (f'<span class="pill {cls}">🎤 {pres_he}</span>'
              f'<span class="pill time">⏱ {t["sec"]} שנ׳</span>'
              f'<span class="pill sec">{sec_he}</span>')
    head = (f'<div class="head"><div class="num">{n}</div>'
            f'<div class="htext"><div class="en">{esc(title)}</div>'
            f'<div class="badges">{badges}</div></div>'
            f'<img loading="lazy" src="{img}" alt="slide {n}"></div>')
    parts = []
    if sl and sl.get("summary_he"):
        parts.append(f'<div class="blk"><div class="lab">📝 סיכום השקף</div><div class="summary">{esc(sl["summary_he"])}</div></div>')
    if sl and sl.get("script_he"):
        parts.append(f'<div class="blk"><div class="lab">🗣️ מה להגיד ({pres_he})</div><div class="script">{esc(sl["script_he"])}</div></div>')
    if sl:
        parts.append(render_info(sl.get("info_he", [])))
    if n == 49:
        parts.append(f'<div class="blk"><div class="lab">📊 טבלת התוצאות (לפי הספר)</div>{RESULTS_TABLE}</div>')
    if sl:
        parts.append(render_qa(sl.get("questions", [])))
    body = f'<div class="body">{"".join(parts)}</div>'
    return f'<div class="slide {cls}" id="s{n}">{head}{body}</div>'

# ----- assemble sections with bands -----
slides_html = []
cur = None
# map section key order by first appearance
order = []
for n in range(1, 68):
    k = timing[str(n)]["section"]
    if k not in order: order.append(k)
seen = set()
for n in range(1, 68):
    k = timing[str(n)]["section"]
    if k not in seen:
        seen.add(k)
        he = SEC_KEY_TO_HE.get(k, k)
        sect = SEC_TIME.get(k, 0)
        slides_html.append(
            f'<div class="secband" id="sec-{k}"><span class="nm">{he}</span>'
            f'<span class="pill time">⏱ {fmt(sect)}</span></div>')
    slides_html.append(slide_html(n))

# ----- timing table (by section) -----
timing_rows = ""
for k in order:
    he = SEC_KEY_TO_HE.get(k, k)
    nums = [n for n in range(1,68) if timing[str(n)]["section"]==k]
    rng = f"{nums[0]}–{nums[-1]}"
    who = "אביאל" if timing[str(nums[0])]["presenter"]=="Aviel" else "חן"
    timing_rows += f'<tr><td>{he}</td><td class="num">{rng}</td><td>{who}</td><td class="num">{fmt(SEC_TIME[k])}</td></tr>'
timing_table = (f'<div class="tblwrap"><table><tr><th>סקשן</th><th class="num">שקפים</th><th>מציג</th><th class="num">זמן</th></tr>'
                f'{timing_rows}<tr style="font-weight:700"><td>סה״כ</td><td class="num">1–67</td>'
                f'<td>אביאל {fmt(AVIEL)} · חן {fmt(CHEN)}</td><td class="num">{fmt(TOTAL)}</td></tr></table></div>')

# ----- holistic -----
holistic_html = "".join(
    f'<div class="qa"><div class="q">{esc(h.get("q_he"))}'
    + (f' <span class="pill sec">{esc(h.get("tag"))}</span>' if h.get("tag") else "")
    + f'</div><div class="a"><b>תשובה:</b> {esc(h.get("a_he"))}</div></div>'
    for h in holistic)

# ----- danger -----
def danger_item(d):
    a = (d.get("a_he","") or "").strip()
    tag = f' <span class="pill sec">{esc(d.get("tag"))}</span>' if d.get("tag") else ""
    parts = [p.strip() for p in a.split("|") if p.strip()]
    if len(parts) > 1:
        rows = []
        for p in parts:
            if ":" in p:
                lab, rest = p.split(":", 1)
                rows.append(f'<div class="dline"><b>{esc(lab.strip())}:</b> {esc(rest.strip())}</div>')
            else:
                rows.append(f'<div class="dline">{esc(p)}</div>')
        body = "".join(rows)
    else:
        body = f'<div class="dline">{esc(a)}</div>'
    return f'<div class="warn"><div class="q">⚠️ {esc(d.get("q_he"))}{tag}</div><div class="a">{body}</div></div>'
danger_html = "".join(danger_item(d) for d in danger)

# ----- glossary grouped -----
KINDS = [("biology","ביולוגיה"),("ml","למידת מכונה / מודלים"),("metric","מטריקות והערכה"),("dataset","דאטהסט"),("other","נוסף")]
gl_html = ""
for key,he in KINDS:
    items = [g for g in glossary if (g.get("kind") or "other").lower().startswith(key[:3]) or (g.get("kind") or "")==key]
    # fallback exact match
    items = [g for g in glossary if (g.get("kind") or "other").lower()==key]
    if not items: continue
    rows = "".join(f'<div class="it"><span class="t">{esc(g.get("term"))}</span> — {esc(g.get("def_he"))}</div>' for g in items)
    gl_html += f'<div class="gl-group"><h3>{he}</h3><div class="gl">{rows}</div></div>'
# any uncategorized
used = {g.get("term") for key,_ in KINDS for g in glossary if (g.get("kind") or "other").lower()==key}
rest = [g for g in glossary if g.get("term") not in used]
if rest:
    rows = "".join(f'<div class="it"><span class="t">{esc(g.get("term"))}</span> — {esc(g.get("def_he"))}</div>' for g in rest)
    gl_html += f'<div class="gl-group"><h3>נוסף</h3><div class="gl">{rows}</div></div>'

tips_html = "".join(f'<li><b>{esc(tt)}</b> — {esc(body)}</li>' for tt,body in TIPS)

# ----- toc -----
toc = "".join(f'<a href="#sec-{k}">{SEC_KEY_TO_HE.get(k,k)}</a><br>' for k in order)
toc += ('<a href="#holistic">שאלות הוליסטיות</a><br>'
        '<a href="#danger">מלכודות ותשובות מוכנות</a><br>'
        '<a href="#glossary">גיליון מונחים</a>')

HTML = f"""<!doctype html>
<html dir="rtl" lang="he">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>ספיקר-נוטס להגנת פרויקט גמר — USV / Autism</title>
<style>{CSS}</style>
</head>
<body>
<button class="themebtn" onclick="var r=document.documentElement;var d=r.getAttribute('data-theme')==='dark';r.setAttribute('data-theme',d?'light':'dark');">🌓 מצב תצוגה</button>
<div class="wrap">
<header class="top">
  <h1>ספיקר-נוטס והכנה להגנה — ניתוח קולות על-קוליים של עכברים לזיהוי אוטיזם</h1>
  <div class="sub">Analysis of Ultrasonic Vocalizations of Mice for Autism Detection · פרויקט גמר M.Sc. במדעי הנתונים · HIT</div>
  <div class="meta">מציגים: חן אהרון · אביאל ביטון &nbsp;|&nbsp; מנחה: ד"ר דרור לדרמן &nbsp;|&nbsp; חוקרת ראשית ובעלת הדאטא: פרופ' חוה גולן (בן-גוריון) &nbsp;|&nbsp; 67 שקפים · {fmt(TOTAL)} דק' · אביאל {fmt(AVIEL)} / חן {fmt(CHEN)}</div>
</header>

<div class="panel">
  <h2>איך משתמשים במסמך הזה</h2>
  <p>לכל שקף (1–67): <b>סיכום</b> קצר, <b>מה להגיד</b> (הטקסט המדובר בעברית, מותאם לזמן המוקצב), <b>פסקת מידע</b> (כל מושג שאפשר להישאל עליו), ו<b>שאלות אפשריות + תשובות</b>. בסוף: שאלות הוליסטיות, "מלכודות" עם תשובות מוכנות, וגיליון מונחים. פס צבע בצד כל שקף מציין את המציג (כחול = אביאל, טורקיז = חן).</p>
  <div class="toc">{toc}</div>
</div>

<div class="panel">
  <h2>⏱ טבלת תזמון כוללת</h2>
  <p style="color:var(--muted);margin-top:0">יעד: 25–30 דק'. התכנון כאן = <b>{fmt(TOTAL)}</b> (עם באפר קטן למעברים ולשאלות תוך-כדי). זכרו: 67 שקפים = קצב מהיר, ~24 שנ' לשקף תוכן.</p>
  {timing_table}
</div>

<div class="panel tips">
  <h2>🎯 טיפים להצגה</h2>
  <ul>{tips_html}</ul>
</div>

{"".join(slides_html)}

<div class="big-sec" id="holistic">
  <h2>שאלות הוליסטיות ברמת הפרויקט</h2>
  <p style="color:var(--muted)">שאלות שחוצות שקפים — על ההיגיון, ההשוואות והמגבלות של הפרויקט כולו.</p>
  {holistic_html}
</div>

<div class="big-sec" id="danger">
  <h2>⚠️ מלכודות ותשובות מוכנות</h2>
  <p style="color:var(--muted)">השאלות המסוכנות ביותר, עם תשובה מלאה, משפט-בטיחות מיידי, ומה להימנע מלומר.</p>
  {danger_html}
</div>

<div class="big-sec" id="glossary">
  <h2>📖 גיליון מונחים</h2>
  <p style="color:var(--muted)">רענון מהיר לכל ראשי-התיבות והמונחים שבמצגת ובספר.</p>
  {gl_html}
</div>

</div>
</body>
</html>"""

out = os.path.join(BASE, "defense_speaker_notes.html")
open(out, "w", encoding="utf-8").write(HTML)
print("wrote", out, round(len(HTML)/1e6,2), "MB")
print("slides present:", len(slides), "missing:", content.get("missing"))
print("holistic:", len(holistic), "danger:", len(danger), "glossary:", len(glossary))
