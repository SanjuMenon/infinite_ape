import random

import numpy as np
from agency_swarm import Agency

from benchmarks.stream_bench.stream_bench.agents.base import Agent
from benchmarks.stream_bench.stream_bench.agents.utils import get_llm, setup_logger
from stigmergicai.models.agent import Agent as StigmergicAgent
from stigmergicai.tools.perplexity_tool import PerplexityTool


class StigmergicAiBenchmarkRunner(Agent):
    def __init__(self, config: dict) -> None:
        self.seed = config["seed"]
        random.seed(self.seed)
        np.random.seed(self.seed)
        self.method = config["agent_name"]
        self.warmup_steps = config["warmup_steps"]
        # super().__init__(config)
        self.config = config
        self.llms = [get_llm(llm["series"], llm["model_name"]) for llm in config["llms"]]
        self.exp_name = config["exp_name"] if "exp_name" in config else self.get_name()
        self.log_path = f'log/{config["bench_name"]}/{config["split"]}/{self.exp_name}'
        self.logger = setup_logger(name="jsonlines_logger", log_file=f"{self.log_path}.jsonl")
        self.llm_names = [llm["model_name"] for llm in config["llms"]]
        self.LOG_KEYS += [llm["model_name"] for llm in config["llms"]]
        self.log_info = {KEY: 0 for KEY in self.LOG_KEYS}  # log information of the current data point
        self.accum_log_info = {
            KEY: 0 for KEY in self.LOG_KEYS
        }  # accum_log_info: accumulation of self.log_info through time steps

        agent = StigmergicAgent(
            name="My P-Agent",
            description="This is a description of my agent.",
            instructions="Use perplexity tool to help you when you answer a question. Respond in JSON string format, with the answer as the key.",
            tools=[PerplexityTool],
            temperature=0.3,
            max_prompt_tokens=25000,
        )

        self.agency = Agency([agent], temperature=0)

    def __call__(self, question: str, **kwargs) -> str:
        return self.agency.get_completion(question)

    def update(self, has_feedback: bool, **feedbacks) -> bool:
        return False

    def get_name(self) -> str:
        llm_names = [llm["model_name"] for llm in self.config["llms"]]
        return "__".join(
            [
                self.config["agent_name"],
                "_".join(llm_names),
                self.config["rag"]["embedding_model"].split("/")[-1],  # remove '/' to avoid incorrect path
                self.config["rag"]["order"],
                str(self.config["rag"]["top_k"]),
                f"warmup-{self.warmup_steps}",
                f"seed-{self.seed}",
            ]
        )
