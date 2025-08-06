from abc import ABC, abstractmethod

from instructor import OpenAISchema


class BaseTool(OpenAISchema, ABC):
    @abstractmethod
    def run(self, **kwargs):
        pass

    @classmethod
    @property
    def openai_schema(cls):
        schema = super(BaseTool, cls).openai_schema
        return {"type": "function", "function": schema}
