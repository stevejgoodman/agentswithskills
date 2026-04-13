"""arXiv search tool for the arxiv skill."""

import arxiv
from langchain_core.tools import InjectedToolArg, tool
from typing_extensions import Annotated


@tool(parse_docstring=True)
def arxiv_search(
    query: str,
    max_results: Annotated[int, InjectedToolArg] = 5,
) -> str:
    """Search arXiv for academic papers on a given topic.

    Use this tool when the user is asking about research papers, academic literature,
    scientific findings, or wants to find preprints on a specific subject.

    Args:
        query: Search query to find relevant papers (e.g. "attention is all you need transformers")
        max_results: Maximum number of papers to return (default: 5)

    Returns:
        Formatted list of matching papers with titles, authors, abstracts, and links
    """
    client = arxiv.Client()
    search = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.Relevance,
    )

    results = list(client.results(search))
    if not results:
        return f"No arXiv papers found for query: '{query}'"

    paper_texts = []
    for paper in results:
        authors = ", ".join(a.name for a in paper.authors[:5])
        if len(paper.authors) > 5:
            authors += f" et al. ({len(paper.authors)} total)"
        paper_texts.append(
            f"## {paper.title}\n"
            f"**Authors:** {authors}\n"
            f"**Published:** {paper.published.strftime('%Y-%m-%d')}\n"
            f"**arXiv ID:** {paper.entry_id}\n"
            f"**PDF:** {paper.pdf_url}\n\n"
            f"**Abstract:** {paper.summary}\n\n---"
        )

    return f"Found {len(results)} paper(s) on arXiv for '{query}':\n\n" + "\n\n".join(paper_texts)
