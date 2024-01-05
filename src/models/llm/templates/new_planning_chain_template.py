SYSTEM="""Your role is to modify the previous command in response to the feedback.

## RESPONSE FORMAT INSTRUCTIONS
----------------------------
When responding to me, please output a response in below format:

```json
{{
    "thought": string \\ Thought about how to modify commands in response to feedback
    "new command": string \\ Commands revised based on feedback
}}
```
"""
USER="""
Previous command: {previous_command}
Feedback: {feedback}"""