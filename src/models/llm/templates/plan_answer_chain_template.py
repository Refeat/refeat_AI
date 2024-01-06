SYSTEM="""
Given the following extracted parts of a document and a question, create a final answer. 
Provide a rich answer that maximizes the use of relevant content.

Output format:
```json
{{
    "user intent": string, \\ The information wants to get from the question, or the intent of the question.
    "thought": string, \\ The thought process you used to arrive at the final answer.
    "final answer": string \\ final answer must in **korean**. If you cannot answer the question, apologize for not having enough information. And if there was some relevant information, return it.
}}
```
"""
USER="""
Question: {input}
Document:
------
{context}
------
"""