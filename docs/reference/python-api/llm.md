# LLM API

Located in `django_automate.llm`.

## `llm_call(prompt, inputs, profile)`
The main entry point for AI generations.
*   **Args**:
    *   `prompt`: String key or Prompt object.
    *   `inputs`: Dict of variables for the prompt template.
    *   `profile`: String name of ConnectionProfile.
*   **Returns**: `LLMRun` object containing `.output.text` and usage stats.
*   **Side Effects**: Creates `LLMRun` record, deducts budget buckets.

## `run_eval(dataset, prompt_version)`
Runs an evaluation suite.
*   **Args**:
    *   `dataset`: List of test cases (input/expected_output).
    *   `prompt_version`: The specific prompt to test.
*   **Returns**: `EvalRun` with aggregate scores (e.g., Accuracy: 85%).
