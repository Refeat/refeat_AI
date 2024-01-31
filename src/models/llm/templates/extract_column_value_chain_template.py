SYSTEM="""
Make a answer for the User Query using parts of noisy Document.
Generate concise answers using only solid evidence from the Document.
If there is no solid evidence, Return "해당 사항 없음".
Use as much information as possible to answer the user's question.

Output format:
```json
{{
    "Summary Answer List": list of string \\ answer in few words or sentences
}}
```
"""
USER="""
User Query: {input}
Document:
------
{context}
------
User Query: {input}
"""