SYSTEM="""
Given the following extracted parts of a document and a question, create a final answer. 
Provide a rich answer that maximizes the use of relevant content.

Output format:
```json
{{
    "user intent": string, \\ The information wants to get from the question, or the intent of the question.
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