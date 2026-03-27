# Preprocessing Validation and QA Report

## Objective Coverage

- Parsed Markdown and CSV files from repository data source.
- Extracted title, section title, and cleaned content.
- Applied text normalization and character cleanup.
- Chunked documents with token window target 384 and hard limit 512.
- Assigned role-based metadata tags per department.

## Summary Metrics

- Parsed sections: 204
- Total chunks: 43
- Avg tokens per chunk: 368.60
- Min tokens per chunk: 142
- Max tokens per chunk: 508

## Validation Checks

- Chunks above token max (512): 0
- Chunks below token min (300): 5
- Chunks with missing metadata: 0
- Departments represented: engineering, finance, general, hr, marketing

## Parsed Section Counts by Department

- engineering: 81
- finance: 21
- general: 56
- hr: 1
- marketing: 45

## Outcome

Preprocessing output is valid for downstream RBAC embedding/indexing pipelines.
