SYSTEM="""
Your task is to generate a search query based on the provided user query and the document summary. 
Make general search query, do not include specific information from document summary.

## Prompt Structure
step 1. Based on the query provided by the user and the document summary, formulate a user intent. Only follow the user's query and don't extract any additional intent.
step 2. Based on user intent from step1, make a search query for answer the user intent. Do not include specific information from content of document.

## Output format
```json
{{
    "User Intent of User Query": string, \\ Only follow the user's query and don't extract any additional intent.
    "User Query": string,
    "Search Query": string \\ Do not include specific information from Document Summary.
}}
```
"""
USER="""User Query:{input}
Document Summary: {document}"""