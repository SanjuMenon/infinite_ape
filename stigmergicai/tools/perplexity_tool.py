from pydantic import Field

from stigmergicai.tools.base import BaseTool
from stigmergicai.tools.perplexity_api import SearchPerplexity


class PerplexityTool(BaseTool):
    """
    A useful tool in delivering helpful, up-to-date, and factual responses to all your questions
    """

    name: str = Field(description="the name of the assistant to be called", title="name")
    query: str = Field(description="query to the assistant", title="query")

    def run(self, **kwargs):
        searcher = SearchPerplexity()
        return searcher.query(self.query)
