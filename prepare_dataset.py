import json
import random
from pathlib import Path

def main():
    input_path = Path("data/hotpot_dev_distractor_v1.json")
    output_path = Path("data/hotpot_100.json")

    if not input_path.exists():
        print(f"Không tìm thấy file: {input_path}")
        print("Vui lòng tải bộ dữ liệu 'hotpot_dev_distractor_v1.json' và đặt vào thư mục 'data'.")
        return

    print(f"Đang đọc dữ liệu từ {input_path}...")
    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Chọn ngẫu nhiên 100 câu (hoặc lấy toàn bộ nếu file có ít hơn 100 câu)
    num_samples = min(100, len(data))
    sampled_data = random.sample(data, num_samples)

    formatted_data = []
    for item in sampled_data:
        # Chuyển đổi format của HotpotQA sang format QAExample của bài lab
        context_chunks = []
        for title, sentences in item.get("context", []):
            text = " ".join(sentences)
            context_chunks.append({"title": title, "text": text})

        formatted_item = {
            "qid": item.get("_id", ""),
            "difficulty": item.get("level", "medium"),
            "question": item.get("question", ""),
            "gold_answer": item.get("answer", ""),
            "context": context_chunks
        }
        formatted_data.append(formatted_item)

    # Lưu file kết quả
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(formatted_data, f, indent=2, ensure_ascii=False)

    print(f"Đã lưu thành công {len(formatted_data)} bản ghi vào {output_path}")

if __name__ == "__main__":
    main()