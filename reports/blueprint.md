# CI/CD Blueprint: RAG Eval + Guardrail Stack

**Sinh viên:** NguyenDucManh-2A202600945 
**Ngày:** 30/06/2026

---

## Guard Stack Architecture

```
User Input
    │
    ▼ (~476ms P95)
[Presidio PII Scan]
    │ block if: VN_CCCD / VN_PHONE / EMAIL detected
    │ action:   return 400 + "PII detected in query"
    ▼ (~125ms P95)
[NeMo Input Rail]
    │ block if: off-topic / jailbreak / prompt injection
    │ action:   return 503 + refuse message
    ▼
[RAG Pipeline (Day 18)]
    │ M1 Chunk → M2 Search → M3 Rerank → GPT-4o-mini
    ▼
[NeMo Output Rail]
    │ flag if:  PII in response / sensitive content
    │ action:   replace with safe response
    ▼
User Response
```

---

## Latency Budget

*(Kết quả Task 12 — measure_p95_latency())*

| Layer | P50 (ms) | P95 (ms) | P99 (ms) | Budget |
|---|---|---|---|---|
| Presidio PII | 253.15 | 475.75 | 475.75 | <10ms |
| NeMo Input Rail | 104.76 | 125.12 | 125.12 | <300ms |
| RAG Pipeline | N/A | N/A | N/A | <2000ms |
| NeMo Output Rail | N/A | N/A | N/A | <300ms |
| **Total Guard** | 353.71 | **583.99** | 583.99 | **<500ms** |

**Budget OK?** [ ] Yes / [x] No  
**Comment:** Độ trễ đã cải thiện đáng kể khi đo nhiều lần (loại bỏ cold start), Presidio tốn ~476ms và NeMo tốn ~125ms (tổng P95 ~584ms). Dù vậy vẫn vượt qua Budget (<500ms). Cần tối ưu thêm các model nhận diện thực thể của Presidio (thay vì spacy model lớn) để giảm latency xuống dưới mức yêu cầu.

---

## CI/CD Gates (phải pass trước khi merge to main)

```yaml
# .github/workflows/rag_eval.yml
- name: RAGAS Quality Gate
  run: python src/phase_a_ragas.py
  env:
    MIN_FAITHFULNESS: 0.75
    MIN_AVG_SCORE: 0.65

- name: Guardrail Gate
  run: pytest tests/test_phase_c.py -k "test_adversarial_suite_pass_rate"
  # phải ≥ 15/20 (75%)

- name: Latency Gate
  run: python -c "from src.phase_c_guard import measure_p95_latency; ..."
  # P95 total < 500ms
```

---

## Monitoring Dashboard (production)

| Metric | Alert Threshold | Action |
|---|---|---|
| RAGAS faithfulness (daily sample) | < 0.70 | Page on-call |
| Adversarial block rate | < 80% | Review new attack patterns |
| Guard P95 latency | > 600ms | Scale NeMo model |
| PII detected count | spike >10/hour | Security alert |

---

## Kết quả thực tế từ Lab

| | Kết quả |
|---|---|
| RAGAS avg_score (50q) | 0.8268 |
| Worst metric | faithfulness |
| Dominant failure distribution | factual |
| Cohen's κ | 0.000 |
| Adversarial pass rate | 16 / 20 |
| Guard P95 latency | 583.99 ms |

---

## Nhận xét & Cải tiến

> Hệ thống cho kết quả chất lượng tốt trên 50 câu hỏi (trung bình 0.8268), đặc biệt chính xác trong bối cảnh truy xuất. Tuy nhiên, metric "faithfulness" đang bị suy yếu nhất (đặc biệt ở các câu multi-hop). Hệ thống Guardrails có khả năng block khá ổn (80%) nhưng P95 latency (tổng ~584ms) vẫn nhỉnh hơn một chút so với mức mong đợi (<500ms). Khi đưa lên production, nên (1) tối ưu lại các mô hình nhận diện thực thể của Presidio cho nhẹ hơn, (2) dùng LLM nhỏ cục bộ hoặc API chuyên dụng với độ trễ thấp hơn để chạy Input/Output Rails.
