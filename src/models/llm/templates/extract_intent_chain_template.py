SYSTEM="""
Analyze the user's intent from last user saying, then enrich the user's words to reflect their intent.

Output format:
```json
{{
    "user words": string \\ The user's words that reflect their intent. It must in korean.
}}
```

Example:
USER: 인공지능 대해 설명해줘
ASSISTANT: ```json
{{
    "user words": "인공지능의 정의, 활용 분야, 인공지능 작동 방식에 대해 알려줘"
}}
```
"""
USER="""{input}"""