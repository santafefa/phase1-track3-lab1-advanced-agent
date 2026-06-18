from __future__ import annotations
from dataclasses import dataclass
import time
from typing import Literal
from .mock_runtime import FAILURE_MODE_BY_QID, actor_answer, evaluator, reflector
from .schemas import AttemptTrace, QAExample, ReflectionEntry, RunRecord

@dataclass
class BaseAgent:
    agent_type: Literal["react", "reflexion"]
    max_attempts: int = 1
    def run(self, example: QAExample) -> RunRecord:
        reflection_memory: list[str] = []
        reflections: list[ReflectionEntry] = []
        traces: list[AttemptTrace] = []
        final_answer = ""
        final_score = 0
        for attempt_id in range(1, self.max_attempts + 1):
            start_time = time.time()
            answer, actor_tokens = actor_answer(example, attempt_id, self.agent_type, reflection_memory)
            actor_latency = int((time.time() - start_time) * 1000)
            start_time = time.time()
            judge, judge_tokens = evaluator(example, answer)
            judge_latency = int((time.time() - start_time) * 1000)
            token_estimate = actor_tokens + judge_tokens
            latency_ms = actor_latency + judge_latency
            trace = AttemptTrace(attempt_id=attempt_id, answer=answer, score=judge.score, reason=judge.reason, token_estimate=token_estimate, latency_ms=latency_ms)
            final_answer = answer
            final_score = judge.score
            if judge.score == 1:
                traces.append(trace)
                break
            
            if self.agent_type == "reflexion" and attempt_id < self.max_attempts:
                start_time = time.time()
                reflection, reflector_tokens = reflector(example, attempt_id, judge)
                reflector_latency = int((time.time() - start_time) * 1000)
                trace.token_estimate += reflector_tokens
                trace.latency_ms += reflector_latency
                trace.reflection = reflection
                reflections.append(reflection)
                reflection_str = f"Attempt #{attempt_id} failed. Reason: {reflection.failure_reason}. Lesson: {reflection.lesson}. Next strategy: {reflection.next_strategy}"
                reflection_memory.append(reflection_str)
            traces.append(trace)
        total_tokens = sum(t.token_estimate for t in traces)
        total_latency = sum(t.latency_ms for t in traces)
        if final_score == 1:
            failure_mode = "none"
        else:
            reason = traces[-1].reason.lower() if traces else ""
            if "drift" in reason or "wrong" in reason or "spurious" in reason:
                failure_mode = "entity_drift"
            elif "hop" in reason or "incomplete" in reason or "missing" in reason:
                failure_mode = "incomplete_multi_hop"
            else:
                failure_mode = "wrong_final_answer"
        return RunRecord(qid=example.qid, question=example.question, gold_answer=example.gold_answer, agent_type=self.agent_type, predicted_answer=final_answer, is_correct=bool(final_score), attempts=len(traces), token_estimate=total_tokens, latency_ms=total_latency, failure_mode=failure_mode, reflections=reflections, traces=traces)

class ReActAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__(agent_type="react", max_attempts=1)

class ReflexionAgent(BaseAgent):
    def __init__(self, max_attempts: int = 3) -> None:
        super().__init__(agent_type="reflexion", max_attempts=max_attempts)
