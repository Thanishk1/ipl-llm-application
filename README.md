# IPL Cricket Analytics — Hybrid Stats + RAG System

An IPL analytics application combining two complementary systems: a **structured
stats engine** over ball-by-ball match data, and a **hand-built RAG pipeline**
over match reports — unified behind a single natural-language query interface.

## What it does

Ask questions like:
- *"What was Kohli's strike rate in the 2025 season?"* → structured stats engine
- *"How did Kohli perform against KKR on opening night?"* → RAG over match reports
- *"RCB vs KKR 2026"* → detects that RCB and KKR played each other twice that
  season, and asks which match you mean (with date + venue) before answering,
  rather than silently mixing facts from both games

## Architecture

**Structured stats path**
Ball-by-ball JSON from [Cricsheet](https://cricsheet.org) is parsed into
`matches`, `deliveries`, `players`, and `squads` parquet tables, queried
directly for batting/bowling stats by season and player.

**RAG path**
ESPNcricinfo match reports are chunked structurally (by subheading), then
subchunked to a 256-token budget with overlap, embedded with
`all-MiniLM-L6-v2`, and retrieved via cosine similarity with metadata
filtering (team, season) and query expansion. Answers are generated with
Gemini, grounded strictly in retrieved chunks.

**Disambiguation**
When a query names two teams that met more than once in a season, the system
detects the ambiguity post-filtering (before ranking) and returns the
candidate matches — by date and venue — instead of silently blending chunks
from different games into one answer.

**Router**
A Flask app (`app.py`) routes queries between the two paths and serves a
simple web UI for both stats lookup and natural-language Q&A.

## Project structure

```
Stats/              structured stats queries over parsed parquet tables
Rag/                retrieval, query parsing, disambiguation, LLM generation
chunking/           report → chunk → subchunk pipeline
player_mapping/     player name / alias resolution
ipl_report_scraper/ ESPNcricinfo report scraping
parsed/             derived parquet tables (matches, deliveries, players, squads)
static/, templates/ Flask frontend
app.py              Flask entry point
```

## Setup

```bash
python -m venv venv
venv\Scripts\Activate.ps1      # Windows
pip install -r requirements.txt

# Add your Gemini API key to Rag/.env:
#   GEMINI_API_KEY=your_key_here

python app.py
```

## Known limitations

- Faithfulness: Gemini correctly grounds answers when context is deliberately
  fabricated, but can hallucinate plausible specifics for well-known players
  when retrieval is incomplete — likely pretraining leakage rather than a
  retrieval bug.
- Report corpus currently covers 2025–2026 seasons; structured stats cover
  2023–2026.
- Multi-match queries (e.g. "compare RCB's two 2026 meetings with MI") aren't
  yet handled as a single query — the disambiguation flow currently resolves
  to one match at a time.

## Roadmap

- [ ] Evaluation harness (recall@5, faithfulness, refusal-correctness) — in progress
- [ ] Hybrid search (BM25 + cosine, fused via RRF) + cross-encoder reranking
- [ ] Lightweight retrieval observability/logging
- [ ] Query rewriting, agentic router with trajectory-level eval

## Data sources

- Ball-by-ball data: [Cricsheet](https://cricsheet.org) (CC BY 4.0)
- Match reports: ESPNcricinfo