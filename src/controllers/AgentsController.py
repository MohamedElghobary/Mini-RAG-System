from .BaseController import BaseController

import logging
from cohere import Client
from typing import Dict, List
import ast
import requests
import httpx


from helpers.config import Settings

logger = logging.getLogger('uvicorn.error')


settings = Settings()
cohere_client = Client(settings.COHERE_API_KEY)

class AgentsController(BaseController):

    def extract_search_queries_from_text(text: str, no_queries: int = 3) -> List[str]:
        prompt = f"""
    You are a Search Query Extraction Agent. Your task is to analyze a document and extract the most relevant, specific, and useful search queries someone might use to find information related to this document.

    Instructions:
        - Focus on meaningful, real-world search queries based on the document's content.
        - Combine related keywords into compact search-like phrases.
        - Avoid generic or overly broad terms (e.g., "data", "technology").
        - The queries should be in the language of the document.
        - Return only {no_queries} concise, search-optimized phrases.


Number of queries: At most {no_queries}

Document:
{text[:3000]}  # truncate to avoid hitting token limits

Return the result as a Python list like this:
["how convolutional neural networks work", "deep learning for image classification", ...]
    """

        response = cohere_client.generate(
            model="command-r-plus",
            prompt=prompt,
            max_tokens=200,
            temperature=0.4
        )

        try:
            raw = response.generations[0].text.strip()
            raw = raw.replace("،", ",")  # handle Arabic commas or similar
            queries = ast.literal_eval(raw) if raw.startswith("[") else [q.strip() for q in raw.split(",")]
            return [q for q in queries if isinstance(q, str)]

        except Exception as e:
            print("Search query extraction failed:", e)
            return []
        



    async def perform_web_search_for_queries(self, queries: List[str]) -> Dict[str, List[dict]]:
        search_results = {}

        headers = {"Authorization": f"Bearer {settings.TAVILY_API_KEY}"}
        url = "https://api.tavily.com/search"

        async with httpx.AsyncClient(timeout=10.0) as client:
            for query in queries:
                try:
                    logger.info(f"Searching online for: {query}")
                    resp = await client.post(url, headers=headers, json={"query": query, "max_results": 3})

                    if resp.status_code == 200:
                        data = resp.json()
                        search_results[query] = data.get("results", [])
                    else:
                        logger.warning(f"Tavily returned {resp.status_code} for query: {query}")
                        search_results[query] = []

                except httpx.RequestError as exc:
                    logger.error(f"HTTP error for query {query}: {exc}")
                    search_results[query] = []

        return search_results
