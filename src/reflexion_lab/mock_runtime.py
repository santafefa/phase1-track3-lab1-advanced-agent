from __future__ import annotations
import os
import json
from openai import OpenAI
from .schemas import QAExample, JudgeResult, ReflectionEntry
from .prompts import ACTOR_SYSTEM, EVALUATOR_SYSTEM, REFLECTOR_SYSTEM

# Khởi tạo OpenAI API Client
client = OpenAI(
    api_key=os.environ.get("FPT_API_KEY"),
    base_url=os.environ.get("FPT_BASE_URL", "https://mkp-api.fptcloud.com")
)

# Tên model theo yêu cầu của bạn
MODEL_NAME = os.environ.get("FPT_MODEL", "<ĐIỀN-TÊN-MODEL-ĐÚNG-VÀO-ĐÂY>")

# Giữ lại biến này để agents.py không bị lỗi import
FIRST_ATTEMPT_WRONG = {"hp2": "London", "hp4": "Atlantic Ocean", "hp6": "Red Sea", "hp8": "Andes"}
FAILURE_MODE_BY_QID = {"hp2": "incomplete_multi_hop", "hp4": "wrong_final_answer", "hp6": "entity_drift", "hp8": "entity_drift"}

def actor_answer(example: QAExample, attempt_id: int, agent_type: str, reflection_memory: list[str]) -> tuple[str, int]:
    context_str = "\n".join([f"- {c.title}: {c.text}" for c in example.context])
    
    user_prompt = f"Question: {example.question}\n\nContext:\n{context_str}\n"
    if agent_type == "reflexion" and reflection_memory:
        reflections_str = "\n".join(reflection_memory)
        user_prompt += f"\nReflection Memory (Lessons from previous attempts):\n{reflections_str}\n"

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": ACTOR_SYSTEM},
            {"role": "user", "content": user_prompt}
        ]
    )
    token_count = response.usage.total_tokens if response.usage else 0
    return response.choices[0].message.content.strip(), token_count

def evaluator(example: QAExample, answer: str) -> tuple[JudgeResult, int]:
    context_str = "\n".join([f"- {c.title}: {c.text}" for c in example.context])
    
    user_prompt = (
        f"Question: {example.question}\n"
        f"Context:\n{context_str}\n\n"
        f"Gold Answer: {example.gold_answer}\n"
        f"Predicted Answer: {answer}\n"
    )
    
    # Sử dụng JSON Mode để ép LLM trả về đúng định dạng
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": EVALUATOR_SYSTEM},
            {"role": "user", "content": user_prompt}
        ],
        response_format={"type": "json_object"}
    )
    token_count = response.usage.total_tokens if response.usage else 0
    content = response.choices[0].message.content
    try:
        return JudgeResult(**json.loads(content)), token_count
    except Exception as e:
        return JudgeResult(score=0, reason=f"Parse error: {e}"), token_count

def reflector(example: QAExample, attempt_id: int, judge: JudgeResult) -> tuple[ReflectionEntry, int]:
    context_str = "\n".join([f"- {c.title}: {c.text}" for c in example.context])
    
    user_prompt = (
        f"Question: {example.question}\n"
        f"Context:\n{context_str}\n\n"
        f"Evaluator Feedback: {judge.reason}\n"
    )
    
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": REFLECTOR_SYSTEM},
            {"role": "user", "content": user_prompt}
        ],
        response_format={"type": "json_object"}
    )
    token_count = response.usage.total_tokens if response.usage else 0
    content = response.choices[0].message.content
    try:
        data = json.loads(content)
        return ReflectionEntry(attempt_id=attempt_id, **data), token_count
    except Exception as e:
        return ReflectionEntry(attempt_id=attempt_id, failure_reason=f"Parse error", lesson="N/A", next_strategy="Try again."), token_count
