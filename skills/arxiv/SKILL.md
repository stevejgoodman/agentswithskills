---
name: arxiv-search
description: Search arXiv for academic papers, preprints, and scientific literature on any topic
---

# arXiv Search Skill

## Overview
Use the `arxiv_search` tool to find academic papers and preprints from arXiv.org across all scientific disciplines including physics, mathematics, computer science, quantitative biology, statistics, and economics.

## When to Use
- The user asks about research papers, preprints, or academic literature
- The user wants to find scientific studies on a specific topic
- The user references "papers", "studies", "research", or "arXiv"
- The user wants citations or authoritative scientific sources
- The query involves cutting-edge or technical scientific topics where peer-reviewed literature is valuable

## Instructions

1. **Formulate a precise query**: Use specific technical terms, author names, or paper titles rather than broad keywords. arXiv search uses full-text matching.

2. **Call `arxiv_search`**: Pass the query string. The tool returns paper titles, authors, publication dates, arXiv IDs, PDF links, and abstracts.

3. **Interpret results**: Each result includes:
   - Title and authors
   - Published date (note: arXiv hosts preprints — not all are peer-reviewed)
   - arXiv ID and direct PDF link
   - Abstract summarizing the paper's content

4. **Synthesize findings**: Summarize the most relevant papers for the user, highlighting key findings from the abstracts. Include the PDF link so the user can read the full paper.

5. **Follow up if needed**: If the first search doesn't yield relevant results, refine the query with more specific terms or alternate phrasings.

## Example Queries
- `"transformer attention mechanism self-attention"` — find foundational transformer papers
- `"diffusion models image generation score matching"` — find diffusion model research
- `"large language model alignment RLHF"` — find papers on LLM alignment
- `"quantum error correction surface codes"` — find quantum computing papers
