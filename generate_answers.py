import os, sys, json, time
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

from src.m2_search import HybridSearch
from src.m3_rerank import CrossEncoderReranker
from config import LLM_MODEL, OPENAI_BASE_URL, HYBRID_TOP_K, ANSWERS_PATH
from openai import OpenAI

def main():
    print("Loading chunks and initializing search...")
    all_chunks = json.load(open("debug_chunks.json", encoding="utf-8"))
    search = HybridSearch()
    print("Indexing BM25...")
    search.bm25.index(all_chunks) # Rebuild BM25 in memory
    print("Initializing reranker...")
    reranker = CrossEncoderReranker()
    
    test_set = json.load(open("test_set_50q.json", encoding="utf-8"))
    client = OpenAI(base_url=OPENAI_BASE_URL if OPENAI_BASE_URL else None)
    
    print("\n[3/3] Generating answers for 50 questions...")
    answers = []
    t_start = time.time()
    for q in test_set:
        query = q["question"]
        
        # Search
        retrieved = search.search(query, top_k=HYBRID_TOP_K)
        final_docs = reranker.rerank(query, retrieved, top_k=3)
        
        context = "\n\n".join([f"[{d.metadata.get('id', '?')}] {d.text}" for d in final_docs])
        prompt = f"""Dựa vào tài liệu sau, hãy trả lời câu hỏi. 
Nếu không có thông tin, hãy nói "Tôi không biết".
Tài liệu:
{context}

Câu hỏi: {query}
"""
        try:
            response = client.chat.completions.create(
                model=LLM_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0
            )
            ans_text = response.choices[0].message.content
        except Exception as e:
            ans_text = f"Lỗi API: {e}"
            
        answers.append({
            "question": query,
            "ground_truth": q.get("ground_truth", ""),
            "answer": ans_text,
            "contexts": [d.text for d in final_docs],
            "metadata": {"type": q.get("type", "unknown")}
        })
        print(f"  OK {len(answers)}/50...", flush=True)

    with open(ANSWERS_PATH, "w", encoding="utf-8") as f:
        json.dump(answers, f, ensure_ascii=False, indent=2)

    print(f"\nOK Saved {len(answers)} answers -> answers_50q.json")

if __name__ == "__main__":
    main()
