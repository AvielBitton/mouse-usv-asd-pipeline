#!/usr/bin/env bash
# Render the deck + Hebrew notes handout to PDF (verified: Chrome 143, exact 16:9).
set -e
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUT="$(dirname "$HERE")"
CHROME="${CHROME:-google-chrome}"

# 1) rebuild the self-contained HTML from template + assets
python3 "$HERE/build_deck.py"

# 2) deck -> 16:9 PDF (one slide per page; @page{size:1280px 720px} makes it exact)
"$CHROME" --headless=new --disable-gpu --no-sandbox --no-pdf-header-footer \
  --virtual-time-budget=6000 \
  --print-to-pdf="$OUT/defense_deck.pdf" "file://$OUT/defense_deck_v2.html"

# 3) Hebrew speaker-notes handout -> A4 PDF
"$CHROME" --headless=new --disable-gpu --no-sandbox --virtual-time-budget=5000 \
  --print-to-pdf="$OUT/defense_notes_handout.pdf" "file://$OUT/defense_notes_handout.html"

echo "Done: defense_deck.pdf  +  defense_notes_handout.pdf"
