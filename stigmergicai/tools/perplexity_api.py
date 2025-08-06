import os
from typing import Iterable, AnyStr

from openai import OpenAI


class SearchPerplexity:
    def __init__(self, model="llama-3.1-sonar-large-128k-online") -> None:
        api_key = os.getenv("PRPLXTY_API_KEY")
        self.model = model
        self.client = OpenAI(api_key=api_key, base_url="https://api.perplexity.ai")

    def query(self, search_string: str) -> str:
        try:
            result = self._completion(search_string)
            return result
        except Exception as e:
            raise Exception("Broken Api!  %s" % str(e))

    def query_stream(self, search_string: str) -> Iterable[AnyStr]:
        try:
            results = self._completion(search_string, stream=True)
            # print([result for result in results])

            # TODO stream at paragraph level
            output = ""
            for result in results:
                output += result
                if "\n" in result:
                    yield output
                    output = ""

            yield output
        except Exception as e:
            raise Exception("Broken Api!  %s" % str(e))

    def _completion(self, query: str, stream=False):
        messages = [
            {
                "role": "system",
                "content": (
                    "You are an artificial intelligence assistant and you need to "
                    "deliver helpful, up-to-date, and factual responses."
                ),
            },
            {
                "role": "user",
                "content": (query),
            },
        ]

        response = self.client.chat.completions.create(model=self.model, messages=messages, stream=stream)

        return response
