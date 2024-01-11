SYSTEM="""
What evidence do we need to answer the question given the current evidence?

Output format:
```json
{{
    "evidence": string \\ Fake evidence for answer the question. If question is in Korean, answer in Korean. If question is in English, answer in English.
}}
```

Example:
USER: Question: Which magazine was started first Arthur's Magazine or First for Women? 
Current Evidence: Arthur's Magazine(1844-1846) was an American literary periodical published inPhiladelphia in the 19th century.
ASSISTANT: ```json
{{
    "evidence": "Alf Clausen (born April 16, 1941) is an American composer of film and television scores. He is best known for his work on 'The Simpsons'"
}}
```
"""
USER="""Question: {input}
Current Evidence: {evidence}
"""