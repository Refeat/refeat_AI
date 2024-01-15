SYSTEM="""
Analyze the user's intent from last user saying, then enrich the user words to reflect their intent.
Make sure to craft your user words to meet all of your user's needs.
Based on user words, generates queries for search.
The queries created should contain both Korean and English.

Output format:
```json
{{
    "user words": string, \\ The user's words that reflect their intent. It must in korean.
    "query list": list of string \\ The generated search queries.
}}
```

Example:
USER: 인공지능 대해 설명해줘
ASSISTANT: ```json
{{
    "user words": "인공지능의 정의, 활용 분야에 대해 알려줘",
    "query list": ["인공지능의 정의", "Definition of artificial intelligence", "인공지능 활용 분야", "Applications of artificial intelligence"]
}}
```
"""
USER="""{input}"""