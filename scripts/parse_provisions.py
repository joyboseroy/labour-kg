"""
Parse raw Act text into structured provisions.
Handles Indian legislation formatting including:
- Table of contents at top (skip it, find actual section text)
- Spaced-out section headings from pdftotext layout mode
- Chapter headers mixed with section headers
"""

import re, os, json
import pandas as pd

RAW_DIR  = "data/raw"
OUT_PATH = "data/processed/provisions.jsonl"
os.makedirs("data/processed", exist_ok=True)

ACT_META = {
    "industrial_disputes_act_1947":    {"era": "old", "short": "IDA 1947"},
    "contract_labour_act_1970":        {"era": "old", "short": "CLA 1970"},
    "minimum_wages_act_1948":          {"era": "old", "short": "MWA 1948"},
    "payment_of_wages_act_1936":       {"era": "old", "short": "PWA 1936"},
    "code_on_wages_2019":              {"era": "new", "short": "CW 2019"},
    "industrial_relations_code_2020":  {"era": "new", "short": "IRC 2020"},
    "code_on_social_security_2020":    {"era": "new", "short": "CSS 2020"},
    "osh_code_2020":                   {"era": "new", "short": "OSH 2020"},
}


def clean_text(text: str) -> str:
    """Normalise pdftotext layout output."""
    # Collapse runs of spaces to single space per line
    lines = []
    for line in text.split('\n'):
        line = re.sub(r' {2,}', ' ', line).strip()
        lines.append(line)
    # Remove page numbers (lone numbers on a line)
    lines = [l for l in lines if not re.match(r'^\d{1,4}$', l)]
    return '\n'.join(lines)


def find_body_start(text: str) -> int:
    """
    Skip the table of contents. The body starts after the last
    occurrence of a TOC-style line (section number + dot + title on one line
    with no body text following it).

    Strategy: find where actual section text begins — look for a section
    heading followed by substantive text (not just another section number).
    """
    # Look for lines like "1. Short title..." that are followed by
    # actual paragraph text (not another numbered line)
    toc_end = 0
    lines = text.split('\n')
    in_toc = False
    for i, line in enumerate(lines):
        if re.search(r'ARRANGEMENT OF SECTIONS|TABLE OF CONTENTS', line, re.I):
            in_toc = True
        if in_toc:
            # TOC ends when we hit a line that looks like a section heading
            # followed by body text (paragraph starting with capital, >60 chars)
            if i > 5 and re.match(r'^\d+[\w\-]*\.?\s+\w', line):
                # Check if the next non-empty line is body text
                for j in range(i+1, min(i+5, len(lines))):
                    nextl = lines[j].strip()
                    if nextl and not re.match(r'^\d+[\w\-]*[.\s]', nextl):
                        if len(nextl) > 60:
                            toc_end = sum(len(l)+1 for l in lines[:i])
                            in_toc = False
                            break
    return toc_end


def parse_sections(text: str, act_name: str) -> list:
    meta = ACT_META.get(act_name, {"era": "unknown", "short": act_name})
    text = clean_text(text)

    # Skip table of contents
    body_start = find_body_start(text)
    body = text[body_start:]

    sections = []

    # Primary pattern: "2. Definitions." or "25A. Lay-off."
    # Must be at start of line, section number, dot, title
    SECTION_RE = re.compile(
        r'(?m)^(\d+[A-Z]?(?:-[A-Z])?)\.\s+([A-Z][^\n]{2,120})\n'
    )

    matches = list(SECTION_RE.finditer(body))

    if len(matches) < 3:
        # Fallback: looser pattern
        SECTION_RE2 = re.compile(
            r'(?m)^(\d+[A-Z]?)\s*\.\s*([A-Z][^\n]{2,120})'
        )
        matches = list(SECTION_RE2.finditer(body))

    if len(matches) < 3:
        # Last resort: split on double newlines, pick blocks starting with number
        blocks = re.split(r'\n{2,}', body)
        for block in blocks:
            block = block.strip()
            if not block:
                continue
            m = re.match(r'^(\d+[A-Z]?)[.\s]+(.{5,120})', block)
            if m and len(block) > 100:
                sections.append({
                    "act":      act_name,
                    "era":      meta["era"],
                    "short":    meta["short"],
                    "section":  m.group(1).strip(),
                    "title":    m.group(2).split('\n')[0].strip()[:200],
                    "text":     block[:3000],
                    "concepts": [],
                })
        return sections

    # Extract text between consecutive matches
    for i, m in enumerate(matches):
        start = m.start()
        end   = matches[i+1].start() if i+1 < len(matches) else len(body)
        section_text = body[start:end].strip()

        # Skip if section text is too short (likely still TOC)
        if len(section_text) < 80:
            continue

        sections.append({
            "act":      act_name,
            "era":      meta["era"],
            "short":    meta["short"],
            "section":  m.group(1).strip(),
            "title":    m.group(2).strip()[:200],
            "text":     section_text[:3000],
            "concepts": [],
        })

    return sections


def main():
    all_provisions = []

    for act_name in ACT_META:
        path = os.path.join(RAW_DIR, f"{act_name}.txt")
        if not os.path.exists(path):
            print(f"  MISSING: {act_name}")
            continue

        with open(path, encoding="utf-8") as f:
            text = f.read()

        # Strip metadata header lines added by download script
        text = re.sub(r'^#.*\n', '', text, flags=re.MULTILINE)

        provisions = parse_sections(text, act_name)
        print(f"  {act_name}: {len(provisions)} sections parsed")
        all_provisions.extend(provisions)

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        for p in all_provisions:
            f.write(json.dumps(p) + "\n")

    print(f"\nTotal provisions: {len(all_provisions)}")
    print(f"Saved to {OUT_PATH}")

    df = pd.DataFrame(all_provisions)
    if not df.empty:
        print("\nBreakdown by Act:")
        print(df.groupby(["short","era"])["section"].count().to_string())


if __name__ == "__main__":
    main()
