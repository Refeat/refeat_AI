SYSTEM="""
Your task is to generate a enriched user query based on the provided user query and the document summary. 
The enriched user query should be specific and enriched enough to answer the user intent.

## Steps to follow
step 1. Based on the query provided by the user and the document summary, formulate a user intent. Only follow the user's query and don't extract any additional intent.
step 2. Based on user query and user intent from step1, make a enriched user query for answer the user intent.

## Output format
```json
{{
    "User Intent of User Query": string, \\ Only follow the user's query and don't extract any additional intent.
    "User Query": string,
    "Enriched User Query": string \\ Make a specific and enriched user query for answer the user intent.
}}
```
"""
USER="""User Query:{input}
Document Summary: {document}
User Query:{input}"""