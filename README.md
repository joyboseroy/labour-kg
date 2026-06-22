# Indian Labour Law Knowledge Graph

A knowledge graph analysis of India's labour law consolidation: 29 Acts compressed into 4 Labour Codes (2019-2020).

**Research question:** Which legal concepts lost or gained structural importance when the old system was consolidated? Are worker-protective concepts structurally weaker in the new system?

**Short answer:** Yes. Industrial dispute, contract labour, strike, unfair labour practice, and conciliation all lost substantial structural centrality. Notification, provident fund, and health and safety compliance gained it. 134 concepts present in the old system are entirely absent from the new one.

---

## Quick findings

### Old system — structural core (top 5 by betweenness centrality)

| Concept | Betweenness |
|---|---|
| wages | 0.138 |
| industrial dispute | 0.125 |
| contract labour | 0.122 |
| employer | 0.088 |
| strike | 0.076 |

### New system — structural core

| Concept | Betweenness |
|---|---|
| wages | 0.100 |
| notification | 0.080 |
| provident fund | 0.076 |
| trade union | 0.076 |
| health and safety | 0.072 |

The old system was organised around adversarial dispute resolution. The new system is organised around administrative compliance and social security contribution management.

---

### Concepts that lost structural importance

| Concept | Old | New | Change | Note |
|---|---|---|---|---|
| industrial dispute | 0.125 | 0.011 | -0.114 | Core organising category of IDA 1947 |
| contract labour | 0.122 | 0.021 | -0.101 | Absorbed into OSH Code |
| strike | 0.076 | 0.011 | -0.065 | Stricter notice requirements in new system |
| retrenchment | 0.068 | 0.016 | -0.052 | More provisions but less structurally connected |
| unfair labour practice | 0.054 | 0.002 | -0.052 | 96% reduction in bridging centrality |
| conciliation | 0.049 | 0.001 | -0.047 | Dispute resolution machinery demoted |
| collective bargaining | 0.035 | 0.010 | -0.025 | Despite more raw mentions |

**The retrenchment finding is methodologically important.** Retrenchment appears in *more* provisions in the new system (14) than the old (12), yet betweenness centrality fell from 0.068 to 0.016. A concept can be invoked more frequently while mattering less structurally. Raw provision count is a poor measure of legislative protection.

---

### Concepts that gained structural importance

| Concept | Old | New | Change |
|---|---|---|---|
| notification | 0.002 | 0.080 | +0.078 |
| provident fund | 0.006 | 0.076 | +0.071 |
| health and safety | 0.020 | 0.072 | +0.052 |
| social security | 0.000 | 0.049 | +0.049 |
| contribution | 0.000 | 0.035 | +0.035 |
| gratuity | 0.000 | 0.026 | +0.026 |

Genuine expansions (health and safety, social security coverage for gig workers) sit alongside purely procedural compliance requirements (notification, contribution). The new system is structurally organised around administering benefits and recording compliance.

---

### Concepts entirely absent from the new system (selected)

134 concepts present in the old system do not appear in the new system at all.

| Concept | Old provisions | Significance |
|---|---|---|
| workman | 3 | Precise legal category replaced by broader "worker" with weaker protections |
| workmen | 3 | Same |
| public utility service | 4 | Special strike restrictions in essential services |
| self-organisation | 1 | Worker right to organise |
| representative union | 1 | Recognised bargaining agent |
| natural justice | 1 | Procedural protection in disciplinary proceedings |
| coercion | 1 | Anti-coercion provision in organising |
| intimidation | 2 | Same |
| conciliation officer | 1 | Specific role in dispute machinery |
| bargaining representative | 1 | Collective bargaining infrastructure |
| social justice | 1 | Explicit objective of old system |

The replacement of "workman" with "worker" and "employee" is not terminological housekeeping. The old system built specific protections around the legally defined category of "workman" under the Industrial Disputes Act. The new definitions are broader but carry different and in key respects weaker protections.

---

## Corpus

**Old system (4 Acts, 361 provisions):**
- Industrial Disputes Act 1947 — 191 provisions
- Contract Labour (Regulation and Abolition) Act 1970 — 36 provisions
- Minimum Wages Act 1948 — 55 provisions
- Payment of Wages Act 1936 — 79 provisions

**New system (4 Codes, 588 provisions):**
- Industrial Relations Code 2020 — 130 provisions
- Occupational Safety Health and Working Conditions Code 2020 — 102 provisions
- Code on Wages 2019 — 75 provisions
- Code on Social Security 2020 — 281 provisions

Total after removing amendment footnotes: **840 provisions**

---

## Graph statistics

| System | Concept nodes | Edges |
|---|---|---|
| Old | 325 | 1,548 |
| New | 723 | 4,656 |
| Combined | 857 | 5,678 |

The new system has more concepts but lower individual betweenness scores — a more distributed topology. This is consistent with both greater coverage and fragmentation of previously coherent legal categories.

---

## Pipeline

```
download_acts.py        # fetch 8 Acts/Codes as PDFs, convert to text
      |
parse_provisions.py     # extract sections with numbers, titles, text
      |                 # skips table of contents, handles amendment footnotes
extract_concepts.py     # LLM concept extraction per provision (Groq/Llama-3.3)
      |
build_graph.py          # concept co-occurrence graphs, betweenness centrality
      |
analyse.py              # figures and summary statistics
```

---

## Run it yourself

```bash
pip install requests beautifulsoup4 networkx pandas matplotlib groq

# Get PDFs from prsindia.org or indiacode.nic.in, convert with:
pdftotext -layout "Industrial Disputes Act 1947.pdf" - > data/raw/industrial_disputes_act_1947.txt
# ... repeat for all 8 Acts

python3 scripts/parse_provisions.py
GROQ_API_KEY=your_key python3 scripts/extract_concepts.py   # ~35 mins, appends on interrupt
python3 scripts/build_graph.py
python3 scripts/analyse.py
```

Extraction uses Groq free tier (llama-3.3-70b-versatile). No GPU needed.

---

## Methodology note

Concept extraction by LLM introduces noise. Concepts that appear as distinct strings may be semantically equivalent. The analysis is sensitive to PDF conversion quality. This corpus covers 8 of the 29 Acts in the old system — the four primary industrial relations and wages Acts. Social security and occupational safety Acts from the old system are not in the old system graph, which affects some comparisons with CSS 2020 and OSH 2020.

This is an exploratory analysis, not a peer-reviewed study. The findings are consistent with qualitative legal scholarship on the Labour Codes but should be treated as indicative rather than definitive.

---

## Related work

- [falkor-irac](https://github.com/joyboseroy/falkor-irac) — graph-constrained legal reasoning, Indian judiciary
- [imljd](https://github.com/joyboseroy/imljd) — Indian matrimonial litigation dataset
- [rti-bench](https://github.com/joyboseroy/rti-bench) — Indian RTI Commission decisions dataset
- Labour research paper (Bengaluru Labour Research Initiative) — empirical analysis of Indian IT sector workforce reduction, OSF Preprints

---

## Interpretation

The government's stated rationale was simplification of compliance. The graph analysis shows the new system does achieve structural simplification in one sense: the old system had a more centralised topology with a few highly bridging concepts; the new system is more distributed.

However, the concepts that lost structural importance are not redundant procedural concepts. Industrial dispute, strike, unfair labour practice, and conciliation were the organisational vocabulary of a system designed to manage adversarial labour relations. Their structural demotion represents a substantive change in how the legal system conceptualises the employer-worker relationship.

The shift is from a system that treats labour conflict as normal and provides machinery to resolve it, to a system that treats labour as a factor of production to be administered through compliance and benefits management.

Whether this is simplification or dilution depends on what you think labour law is for.
