#!/bin/bash

# Script to run the custom agent on StreamBench datasets
# Make sure you have set up your environment variables:
# export OAI_KEY=<your_openai_api_key>
# export GOOGLE_API_KEY=<your_google_ai_studio_api_key>
# export ANTHROPIC_KEY=<your_anthropic_api_key>

echo "Running Custom Agent on StreamBench..."

# Example 1: Run on DDXPlus dataset
echo "Running on DDXPlus dataset..."
python -m stream_bench.pipelines.run_bench \
    --agent_cfg "configs/agent/custom.yml" \
    --bench_cfg "configs/bench/ddxplus.yml" \
    --entity "your_entity" \
    --use_wandb

# Example 2: Run on DS-1000 dataset
# echo "Running on DS-1000 dataset..."
# python -m stream_bench.pipelines.run_bench \
#     --agent_cfg "configs/agent/custom.yml" \
#     --bench_cfg "configs/bench/ds_1000.yml" \
#     --entity "your_entity" \
#     --use_wandb

# Example 3: Run on Spider dataset (requires SQL data download)
# echo "Running on Spider dataset..."
# python -m stream_bench.pipelines.run_bench \
#     --agent_cfg "configs/agent/custom.yml" \
#     --bench_cfg "configs/bench/spider.yml" \
#     --entity "your_entity" \
#     --use_wandb

echo "Custom agent benchmarking completed!" 