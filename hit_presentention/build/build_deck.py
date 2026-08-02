#!/usr/bin/env python3
"""Build the self-contained defense deck: inject base64 fonts + figures into
deck_template.html -> ../defense_deck_v2.html, and emit the Hebrew notes handout.

Run:  python3 build/build_deck.py
Then render PDFs:  bash build/render_pdf.sh
"""
import base64, re, os, glob

BASE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.dirname(BASE)                      # hit_presentention/
TEMPLATE = os.path.join(BASE, "deck_template.html")
ASSETS = os.path.join(BASE, "assets")
FONTS = os.path.join(BASE, "fonts")

def b64(path): return base64.b64encode(open(path, "rb").read()).decode()
def font_uri(w): return "data:font/woff2;base64," + b64(os.path.join(FONTS, f"Inter-{w}.woff2"))
def img_uri(key):
    p = os.path.join(ASSETS, key + ".png")
    if not os.path.exists(p):
        c = glob.glob(os.path.join(ASSETS, key + "*.png"))
        if not c: return None
        p = c[0]
    return "data:image/png;base64," + b64(p)

def main():
    html = open(TEMPLATE, encoding="utf-8").read()
    for w in ["Regular", "Medium", "SemiBold", "Bold", "Black"]:
        html = html.replace("{{FONT:%s}}" % w, font_uri(w))
    missing = []
    for k in set(re.findall(r"\{\{IMG:([^}]+)\}\}", html)):
        uri = img_uri(k)
        if uri is None: missing.append(k); continue
        html = html.replace("{{IMG:%s}}" % k, uri)
    if missing: print("!! MISSING IMAGES:", missing)
    leftover = re.findall(r"\{\{[^}]+\}\}", html)
    if leftover: print("!! LEFTOVER TOKENS:", set(leftover))
    out = os.path.join(OUT_DIR, "defense_deck_v2.html")
    open(out, "w", encoding="utf-8").write(html)
    print("wrote", out, round(len(html)/1024/1024, 2), "MB")
    build_notes(html)

def build_notes(html):
    blocks = re.findall(r'<div class="notes"([^>]*)>(.*?)</div>\s*</section>', html, re.S) \
             or re.findall(r'<div class="notes"([^>]*)>(.*?)</div>', html, re.S)
    def attr(a, n):
        m = re.search(r'data-%s="([^"]*)"' % n, a); return m.group(1) if m else ""
    cards = []
    for a, body in blocks:
        ul = re.search(r"<ul>.*?</ul>", body, re.S)
        ul = ul.group(0) if ul else body
        cards.append(f'<section class="ncard"><div class="nhd"><span class="nn">Slide {attr(a,"n")}</span>'
                     f'<span class="nw">{attr(a,"who")} &nbsp;·&nbsp; {attr(a,"time")}</span></div>'
                     f'<h2>{attr(a,"title")}</h2>{ul}</section>')
    doc = ('<!DOCTYPE html><html lang="he" dir="rtl"><head><meta charset="utf-8">'
        '<title>Speaker Notes — USV Defense</title><style>'
        '@page{size:A4;margin:16mm 14mm}*{margin:0;padding:0;box-sizing:border-box}'
        "body{font-family:'Assistant','Rubik','Arial','Noto Sans Hebrew',sans-serif;color:#14181d;background:#fff;line-height:1.5}"
        '.ncard{border:1px solid #dcdcd4;border-radius:10px;padding:16px 18px;margin-bottom:14px;break-inside:avoid}'
        '.nhd{display:flex;justify-content:space-between;align-items:baseline;border-bottom:1px solid #ececE4;padding-bottom:7px;margin-bottom:9px;direction:ltr}'
        '.nn{font-weight:800;color:#0B7C81;font-size:14px}.nw{font-weight:700;color:#E0851B;font-size:13px}'
        'h2{font-size:19px;margin-bottom:9px;color:#152A40}ul{list-style:none;display:flex;flex-direction:column;gap:7px}'
        'li{font-size:15px;padding-right:16px;position:relative}li::before{content:"";position:absolute;right:0;top:8px;width:6px;height:6px;background:#0E9AA0;border-radius:50%}'
        '.hand{color:#E0851B;font-weight:700}.en{direction:ltr;unicode-bidi:isolate;display:inline-block}'
        'h1{font-size:22px;margin-bottom:4px;color:#152A40}.sub{color:#5C656E;margin-bottom:18px;font-size:14px}'
        '</style></head><body><h1>Speaker Notes — Analysis of USVs for Autism Detection</h1>'
        '<div class="sub">מצגת הגנה · Chen Aharon &amp; Aviel Bitton · דף עזר למציג (לא מוקרן)</div>'
        + "\n".join(cards) + "</body></html>")
    outp = os.path.join(OUT_DIR, "defense_notes_handout.html")
    open(outp, "w", encoding="utf-8").write(doc)
    print("wrote", outp, "(", len(cards), "note cards )")

if __name__ == "__main__":
    main()
