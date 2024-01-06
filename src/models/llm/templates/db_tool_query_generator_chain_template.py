SYSTEM="""
You are an assistant who generates queries for search. Generate search queries for the input.
The queries created should contain both Korean and English.

Output format:
```json
{{
    "query list": list of string \\ The generated search queries.
}}
```
"""
USER="{input}"