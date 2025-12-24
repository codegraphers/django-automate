# Tutorial: LLM Chaining

**Goal**: Build a workflow that summarizes a support ticket and drafts a response.

## 1. Prerequisites
*   OpenAI API Key (or Anthropic/Gemini).
*   Configured Provider Profile.

## 2. Steps

### Step 1: Define the Prompt Template
In Admin > LLM > Prompts, create a new prompt `ticket_summarizer`:
```jinja2
Summarize this customer issue in 3 bullet points:
{{ description }}
```

### Step 2: Build the Workflow
```json
{
    "steps": [
        {
            "id": "summarize",
            "action": "llm.chat",
            "config": {
                "prompt": "ticket_summarizer",
                "inputs": {
                    "description": "{{ event.payload.body }}"
                }
            }
        },
        {
            "id": "draft_reply",
            "action": "llm.chat",
            "config": {
                "messages": [
                    {"role": "system", "content": "You are a helpful support agent."},
                    {"role": "user", "content": "Draft a reply based on this summary: {{ steps.summarize.output.text }}"}
                ]
            }
        }
    ]
}
```

## 3. Expected Output
The `draft_reply` step output will contain the generated text.
