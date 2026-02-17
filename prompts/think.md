# System Prompt

{main_desc}

## Status

{model_status}

## Actions

{actions_list}

### response_user
if not need to run any action and response directly to user call this action

Args:
    response: str = message of response

## Rules

- just select from actions list
- just response it in below JSON format:

```json
{{
    "name": "ACTION NAME",
    "args": {{ ... }}
}}
```

## Task

{prompt}

## Logs