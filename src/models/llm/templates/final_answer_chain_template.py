SYSTEM="""
Given the following question and answer, create a final answer. Final answer must in **korean**.
If there's information that wasn't provided, say why it wasn't addressed (e.g. I couldn't find the information in the given documentation).
Let's think step by step.

Output format:
```json
{{
    "user intent": string, \\ The information the user wants to get from the question, or the intent of the user's question.
    "thought": string, \\ The thought process you used to arrive at the final answer. 
    "final answer": string \\ You should put what you want to return to use here. final answer must in **korean**.
}}
```
"""
USER="""
Question: {input}
Answer: {answer}
"""