# Vector Database & Semantic Search Benchmarking Report

**Generated:** 2026-03-27 15:11:11

## 1. System Configuration

### Embedding Model
- **Requested model:** sentence-transformers/all-MiniLM-L6-v2
- **Active backend:** tfidf
- **Dimensions:** 384

### Vector Database
- **System:** Chroma
- **Storage:** Persistent local storage
- **Distance metric:** Cosine similarity

### Data Statistics
- **Total chunks indexed:** 311
- **Total content volume:** 122,034 characters
- **Average chunk size:** 392 characters
- **Departments:** 5
- **Source documents:** 10

## 2. Embedding Generation Performance

- **Total time:** 0.04 seconds
- **Average time per chunk:** 0.12ms
- **Throughput:** 8092.3 chunks/second

## 3. Indexing Performance

- **Chunks indexed:** 311
- **Total indexing time:** 0.18 seconds

## 4. Query Performance Benchmarks

### Benchmark Query Results

```
                           query                   user_roles department_filter  results_found  query_time_ms  top_similarity
     financial quarterly results                         None               NaN              5           3.36          0.3163
        engineering architecture ['engineering', 'tech_lead']               NaN              5           0.00          0.5416
      employee handbook policies                       ['hr']           general              0          12.12          0.0000
marketing strategy and campaigns                         None         marketing              5           4.22          0.3026
    quarterly performance review    ['finance', 'leadership']               NaN              5           0.00          0.2151
         technical documentation              ['engineering']               NaN              5           6.47          0.5280
                company benefits                         None                hr              5           2.03          0.0000
      market analysis and trends       ['marketing', 'sales']         marketing              5           4.17          0.8061
                 product roadmap   ['engineering', 'product']               NaN              4           0.00          0.4335
           financial forecasting    ['finance', 'leadership']               NaN              5           5.64          0.2893
```

### Performance Summary

| Metric | Value |
|--------|-------|
| Average Query Time | 3.80ms |
| Min Query Time | 0.00ms |
| Max Query Time | 12.12ms |
| Median Query Time | 3.76ms |

### Search Quality Metrics

| Metric | Value |
|--------|-------|
| Queries with Results | 9/10 |
| Average Results per Query | 4.4 |
| Average Top Similarity | 0.3432 |

## 5. Notes

- If backend is `tfidf`, install Microsoft Visual C++ Redistributable to enable ONNX/Torch runtimes on Windows.
- Once runtime dependencies are fixed, rerun the notebook to use all-MiniLM embeddings.
