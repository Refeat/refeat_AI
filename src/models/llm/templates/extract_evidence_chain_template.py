SYSTEM="""
I have a document that contains various pieces of information.
I need you to extract specific evidence from this document that directly answers a particular question I have.
Please identify and present the relevant sections or facts from the document that provide a clear answer to my question.

Output format:
```json
{{
    "evidence": list of string \\ The evidence list that directly answers the question.
}}
```
"""
USER="""
Question: {input}
Document:
===
{context}
===
"""