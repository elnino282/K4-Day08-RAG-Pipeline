# RAG Evaluation Results

## Framework sử dụng

Lightweight local rubric evaluator trong `group_project/evaluation/eval_pipeline.py`.
Evaluator này chạy trực tiếp trên `golden_dataset.json`, đo retrieval context và câu trả lời extractive surrogate để tránh tốn nhiều lượt gọi LLM trong lớp.

## Overall Scores

| Metric | Config A (hybrid + rerank) | Config B (dense-only) | Δ |
|--------|---------------------------:|----------------------:|---:|
| Faithfulness | 1.000 | 1.000 | +0.000 |
| Answer Relevance | 0.485 | 0.453 | +0.032 |
| Context Recall | 0.900 | 0.891 | +0.009 |
| Context Precision | 0.166 | 0.150 | +0.016 |
| **Average** | **0.638** | **0.624** | **+0.014** |

## A/B Comparison Analysis

**Config A:** Hybrid retrieval: semantic search + BM25 lexical search + reranking.

**Config B:** Dense-only baseline: semantic search without BM25 or reranking.

**Kết luận:** Config A có điểm trung bình tốt hơn trên golden set hiện tại. Nếu điểm context recall thấp ở một nhóm câu hỏi, nên kiểm tra lại chunking, metadata source và query terms của nhóm đó.

## Category Breakdown

| Category | Cases | Avg | Recall | Precision |
|---|---:|---:|---:|---:|
| cross-border-shipping | 1 | 0.726 | 0.983 | 0.233 |
| order-tracking | 2 | 0.715 | 0.924 | 0.194 |
| out-of-scope | 2 | 0.554 | 0.861 | 0.143 |
| payment | 4 | 0.647 | 0.917 | 0.129 |
| product-listing | 3 | 0.683 | 0.994 | 0.152 |
| prohibited-products | 2 | 0.500 | 0.596 | 0.149 |
| refund | 3 | 0.650 | 0.970 | 0.198 |
| returns-refunds | 3 | 0.633 | 0.902 | 0.182 |

## Worst Performers (Bottom 3)

| # | Question | Faithfulness | Relevance | Recall | Failure Stage | Root Cause |
|---|----------|-------------:|----------:|-------:|---------------|------------|
| 1 | Tôi có thể đăng bán cá cảnh hoặc hamster trên Shopee không? | 1.000 | 0.150 | 0.191 | context_precision | Retrieved context does not overlap enough with the expected evidence. |
| 2 | Shopee có hoàn tiền trực tiếp vào ví MoMo không? | 1.000 | 0.000 | 0.833 | answer_relevance | Retrieved context does not overlap enough with the expected evidence. |
| 3 | Những trường hợp nào được yêu cầu trả hàng hoặc hoàn tiền? | 1.000 | 0.292 | 0.796 | context_precision | Retrieved context does not overlap enough with the expected evidence. |

## Recommendations

### Cải tiến 1
**Action:** Bổ sung metadata `category`, `customer_role`, `source_url` đầy đủ cho mọi document và ưu tiên filter theo intent.
**Expected impact:** Tăng context precision, nhất là các câu phân biệt buyer/seller.

### Cải tiến 2
**Action:** Thêm query expansion tiếng Việt cho các cụm như hoàn tiền, trả hàng, COD, bằng chứng, sản phẩm cấm.
**Expected impact:** Tăng context recall cho lexical/hybrid search.

### Cải tiến 3
**Action:** Chạy lại evaluation với LLM judge như DeepEval hoặc RAGAS khi có quota API ổn định.
**Expected impact:** Đánh giá faithfulness và answer relevance sát câu trả lời sinh bởi chatbot hơn.

## Dataset Summary

- Total cases: 20
- Answerable cases: 18
- Negative cases: 2
- Roles: {'buyer': 15, 'seller': 5}
- Categories: {'payment': 4, 'refund': 3, 'order-tracking': 2, 'cross-border-shipping': 1, 'returns-refunds': 3, 'product-listing': 3, 'prohibited-products': 2, 'out-of-scope': 2}
