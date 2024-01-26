SYSTEM="""
I have a document that contains various pieces of information.
I need you to extract specific evidences from this document that relevant to a particular question.
Please identify and present the relevant sections or facts from the document that provide a clear answer to my question.

Output format:
```json
{{
    "evidence": list of string \\ The evidence sentence list that relevant to the question.
}}
```
"""
USER="""
Question: {input}
Document:
===
{context}
===
Question: {input}
"""