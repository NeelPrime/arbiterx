# ArbiterX Benchmark Suite

## Methodology

This benchmark proves **≥90% token reduction** by comparing two approaches to providing
codebase context to an LLM:

### Naive Baseline
- For a given query, identify all files whose names or content match query keywords
- Sum up the **full content** of those files in tokens
- This simulates what a tool like Claude Code does when it reads files for context

### ArbiterX (Symbol Map)
- Build the codebase map once
- For the same query, retrieve only **relevant symbol signatures + docstrings**
- Sum up the map response in tokens
- This is what an LLM would actually need to understand the code

### Metrics

| Metric | Formula |
|--------|---------|
| Token Reduction | `(1 - arbiterx_tokens / naive_tokens) × 100` |
| Context Precision | `relevant_symbols / total_symbols_returned` |
| Build Time | Time to build the initial map |
| Query Time | Time to query the map |

## Running

```bash
# Benchmark against the arbiterx repo itself
python benchmarks/run_benchmark.py --repo .

# Benchmark against any repo
python benchmarks/run_benchmark.py --repo /path/to/repo

# Save results
python benchmarks/run_benchmark.py --repo . --output benchmarks/results/latest.md
```

## Expected Results

On a typical ~10k-50k LOC repo:
- **Token reduction: 90-98%** (signatures are ~5% of full file content)
- **Build time: <5s** for repos under 50k LOC
- **Query time: <50ms** per lookup
