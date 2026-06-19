# Lab 16 Benchmark Report

## Metadata
- Dataset: hotpot_100.json
- Mode: mock
- Records: 200
- Agents: react, reflexion

## Summary
| Metric | ReAct | Reflexion | Delta |
|---|---:|---:|---:|
| EM | 0.85 | 0.99 | 0.14 |
| Avg attempts | 1 | 1.19 | 0.19 |
| Avg token estimate | 3504.72 | 4720.35 | 1215.63 |
| Avg latency (ms) | 3775.41 | 6862.35 | 3086.94 |

## Failure modes
```json
{
  "wrong_final_answer": 16
}
```

## Extensions implemented
- structured_evaluator
- reflection_memory
- benchmark_report_json
- mock_mode_for_autograding

## Discussion
Reflexion helps when the first attempt stops after the first hop or drifts to a wrong second-hop entity. The tradeoff is higher attempts, token cost, and latency. In a real report, students should explain when the reflection memory was useful, which failure modes remained, and whether evaluator quality limited gains.
