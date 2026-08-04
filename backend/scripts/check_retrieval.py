from app.rag.retriever import retrieve_policy_context

queries = [
    "DLP data classification must be set to 'Restricted'",
    "DLP Agent Status",
    "data classification",
]
for q in queries:
    print('---')
    print('Query:', q)
    res = retrieve_policy_context(q, collection_key='master_policies', top_k=5)
    print('Found', len(res), 'items')
    for r in res:
        print('-', r['source'], ':', r['text'][:200].replace('\n',' '))
