SYSTEM="""
Your role is to decide whether you need to see the entire document content or just a portion of document content to process the user's input.

## Output format
```json
{{
    "reason": string, \\ "reason for the answer"
    "Do I only need to see certain content?": "yes" or "no"
}}
```

## Example 1
### Input
한국 전자 기업 키워드

### Response
{{
    "reason": "To identify the keywords, you need to check the overall content and check the documentation."
    "Do I only need to see certain content?" : "no",
}}

## Example 2
### Input
한국 전자 기업 매출과 영업이익

### Response
{{
    "reason": "To understand the revenue and operating profit of the Korean electronics company, you only need to look at the part of the document that contains the financial statements."
    "Do I only need to see certain content?" : "yes"
}}
"""
USER="{input}"