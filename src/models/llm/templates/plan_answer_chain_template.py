SYSTEM="""
Given the following extracted parts of a document and a question, create a final answer. 
Provide a rich answer that maximizes the use of relevant content. If the answer is not in the document, don't try to make up an answer.

Output format:
```json
{{
    "final answer": string \\ final answer must in **korean** and markdown format.
}}
```
"""
USER="""
Question: {input}
Document:
------
{context}
------
Question: {input}
"""