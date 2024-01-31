SYSTEM="""
Please extract the consise evidences from part of noisy Document that provide helpful evidence to answer the Question.
You should read the document letter by letter, thinking about how each part will related to answer the question, and look for all the evidence without missing any.
Evidence that does not relevant to the question must not be included.
Consise evidences should contain all the information and must form a complete sentence structure with a subject, verb, and object. so that someone who only sees one piece of evidence can understand it.

Output format:
```json
{{
    "consise evidence": list of string \\ The consise evidence list that provide direct relevant information to answer the Question.
}}
```
"""
USER="""
Question: {input}
Document:
===
{context}
===
Question: {input}
"""