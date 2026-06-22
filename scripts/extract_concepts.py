"""
Extract legal concepts from each provision using Groq LLM.

For each provision, asks the LLM to identify:
  - concepts defined or invoked
  - relations to other provisions (cross-references)
  - worker-protective vs employer-protective orientation

Uses llama-3.3-70b-versatile via Groq (fast, free tier).

Run: GROQ_API_KEY=xxx python3 scripts/extract_concepts.py
Output: data/processed/provisions_with_concepts.jsonl
"""

import os
import json
import time
from groq import Groq

IN_PATH  = "data/processed/provisions.jsonl"
OUT_PATH = "data/processed/provisions_with_concepts.jsonl"

# Core labour law concepts to track across old and new system
CONCEPT_VOCABULARY = [
    # Worker rights
    "retrenchment", "lay-off", "closure", "strike", "lockout",
    "collective bargaining", "trade union", "standing orders",
    "unfair labour practice", "wrongful termination",
    # Wages and compensation
    "minimum wage", "wages", "equal remuneration", "overtime",
    "bonus", "gratuity", "provident fund", "payment of wages",
    # Working conditions
    "working hours", "rest intervals", "leave", "holidays",
    "health and safety", "occupational hazard", "inspector",
    # Employment categories
    "contract labour", "fixed term employment", "apprentice",
    "migrant worker", "worker", "employee", "employer", "establishment",
    # Procedural
    "conciliation", "arbitration", "adjudication", "tribunal",
    "notice period", "enquiry", "appeal", "penalty",
    # Social security
    "ESI", "ESIC", "provident fund", "pension", "maternity benefit",
    "gratuity", "insurance", "disability benefit",
]


SYSTEM_PROMPT = """You are a legal concept extraction system for Indian labour law.
Given a provision from an Indian labour Act or Code, extract:
1. Legal concepts from the provision (use the vocabulary list as a guide but add others you find)
2. Cross-references to other sections if any (e.g. "as defined in Section 2")
3. Whether the provision primarily protects workers, employers, or is procedural

Return ONLY valid JSON, no preamble, no markdown:
{
  "concepts": ["concept1", "concept2"],
  "cross_refs": ["Section X", "Section Y"],
  "orientation": "worker_protective" | "employer_protective" | "procedural" | "definitional"
}"""


def extract_concepts(client: Groq, provision: dict) -> dict:
    prompt = f"""Act: {provision['short']} ({provision['era']} system)
Section {provision['section']}: {provision['title']}

Text:
{provision['text'][:1500]}

Concept vocabulary to consider: {', '.join(CONCEPT_VOCABULARY[:30])}

Extract concepts, cross-references, and orientation."""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": prompt},
            ],
            max_tokens=400,
            temperature=0.1,
        )
        raw = response.choices[0].message.content.strip()
        # Strip markdown fences if present
        raw = raw.replace("```json", "").replace("```", "").strip()
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"concepts": [], "cross_refs": [], "orientation": "unknown"}
    except Exception as e:
        print(f"    LLM error: {e}")
        return {"concepts": [], "cross_refs": [], "orientation": "unknown"}


def main():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("Set GROQ_API_KEY environment variable.")
        return

    client = Groq(api_key=api_key)

    # Load provisions
    provisions = []
    with open(IN_PATH, encoding="utf-8") as f:
        for line in f:
            provisions.append(json.loads(line.strip()))

    print(f"Loaded {len(provisions)} provisions.")

    # Check what's already done
    done_ids = set()
    if os.path.exists(OUT_PATH):
        with open(OUT_PATH, encoding="utf-8") as f:
            for line in f:
                p = json.loads(line.strip())
                done_ids.add(f"{p['act']}_{p['section']}")
        print(f"Already processed: {len(done_ids)}")

    with open(OUT_PATH, "a", encoding="utf-8") as out:
        for i, p in enumerate(provisions):
            pid = f"{p['act']}_{p['section']}"
            if pid in done_ids:
                continue

            print(f"  [{i+1}/{len(provisions)}] {p['short']} s.{p['section']}: {p['title'][:50]}...")

            result = extract_concepts(client, p)
            p["concepts"]     = result.get("concepts", [])
            p["cross_refs"]   = result.get("cross_refs", [])
            p["orientation"]  = result.get("orientation", "unknown")

            out.write(json.dumps(p) + "\n")
            out.flush()

            # Rate limit: ~30 req/min on free tier
            time.sleep(2)

    print(f"\nDone. Output: {OUT_PATH}")


if __name__ == "__main__":
    main()
