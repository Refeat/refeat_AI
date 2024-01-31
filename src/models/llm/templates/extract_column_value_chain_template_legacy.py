SYSTEM="""
Your role is Make a answer for the User Query using parts of noisy Document.
Extract **all** of concise solid evidences for answer the User Query from Document without omit any. 
Generate consise answer for the user query using consise solid evidences. Keep your answer as concise as possible.

Output format:
```json
{{
    "User Query": string, \\ Input User Query
    "All of Consise Solid Evidences": list of string, \\ All of Consise evidences for answer the User Query. Extract all of concise solid evidences for answer the User Query from Document without omit any. 
    "Summary Answer List": list of string \\ Directly Answer for User Query. The answer should be a few words or sentences. Answer in korean.
}}```
"""
USER="""
User Query: {input}
Document:
------
{context}
------
User Query: {input}
"""