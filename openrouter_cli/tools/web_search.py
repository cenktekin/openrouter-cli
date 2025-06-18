import requests
from typing import Dict, List
from rich.console import Console

console = Console()

class WebSearchTool:
    def __init__(self):
        self.base_url = "https://api.duckduckgo.com/"
        self.headers = {
            "User-Agent": "OpenRouter-Tool/1.0"
        }

    def search(self, query: str, max_results: int = 5) -> Dict:
        """Execute a web search using DuckDuckGo API."""
        try:
            params = {
                "q": query,
                "format": "json",
                "no_html": 1,
                "no_redirect": 1
            }

            response = requests.get(
                self.base_url,
                params=params,
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()

            data = response.json()

            # Format results
            results = []
            if "Abstract" in data and data["Abstract"]:
                results.append({
                    "title": data.get("Heading", "Abstract"),
                    "url": data.get("AbstractURL", ""),
                    "snippet": data["Abstract"]
                })

            if "RelatedTopics" in data:
                for topic in data["RelatedTopics"][:max_results]:
                    if "Text" in topic and "FirstURL" in topic:
                        results.append({
                            "title": topic.get("Text", "").split(" - ")[0],
                            "url": topic["FirstURL"],
                            "snippet": topic["Text"]
                        })

            return {
                "results": results,
                "total_results": len(results),
                "query": query
            }

        except requests.RequestException as e:
            console.print(f"[red]Error during web search: {str(e)}[/red]")
            return {
                "results": [],
                "total_results": 0,
                "error": str(e)
            }
