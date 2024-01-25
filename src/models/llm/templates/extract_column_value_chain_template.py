SYSTEM="""
Make a answer for the User Query using parts of noisy Document.
Generate answers using only solid evidence from the documentation.
If there is no solid evidence, Return "해당 사항 없음".

Output format:
```json
{{
    "Final Answer": list of string
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