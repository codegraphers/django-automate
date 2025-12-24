from typing import List, Dict, Any, Optional
import json

class VisualizationEngine:
    @staticmethod
    def detect_chart(data: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Analyzes the result set and proposes a Chart.js configuration if suitable.
        Simple heuristics:
        1. If 2 columns: 1 string/date (Label), 1 number (Value) -> Bar/Line
        2. If small dataset (< 20 rows) with above structure -> Pie/Donut?
        """
        if not data:
            return None
        
        keys = list(data[0].keys())
        if len(keys) != 2:
            return None
        
        # Determine types
        col1, col2 = keys[0], keys[1]
        
        # Check first row values
        val1 = data[0][col1]
        val2 = data[0][col2]
        
        is_num1 = isinstance(val1, (int, float))
        is_num2 = isinstance(val2, (int, float))
        
        label_col = None
        data_col = None
        
        if is_num1 and not is_num2:
            data_col = col1
            label_col = col2
        elif is_num2 and not is_num1:
            data_col = col2
            label_col = col1
        
        if label_col and data_col:
            # Construct Chart.js Config
            labels = [row[label_col] for row in data]
            values = [row[data_col] for row in data]
            
            return {
                "type": "bar",
                "data": {
                    "labels": labels,
                    "datasets": [{
                        "label": data_col,
                        "data": values,
                        "backgroundColor": "rgba(54, 162, 235, 0.5)",
                        "borderColor": "rgba(54, 162, 235, 1)",
                        "borderWidth": 1
                    }]
                },
                "options": {
                    "responsive": True,
                    "maintainAspectRatio": False
                }
            }
        
        return None

class ResultSummarizer:
    def __init__(self, provider, model_name: str):
        self.provider = provider
        self.model_name = model_name

    def summarize(self, question: str, sql: str, data: List[Dict], error: str = None) -> str:
        """
        Uses the LLM to generate a natural language summary of the results.
        """
        from automate_llm.provider.interfaces import CompletionRequest

        if error:
            prompt = f"""User Question: {question}
System Error: {error}
Task: Explain this error to the user in a friendly, non-technical way. Suggest what they might fix."""
        else:
            # Truncate data for prompt context
            data_sample = data[:10]
            data_str = json.dumps(data_sample, default=str)
            
            prompt = f"""User Question: {question}
Executed SQL: {sql}
Data Results (first {len(data_sample)} rows):
{data_str}

Task: Answer the user's question based strictly on these results. 
- If the result is a count/aggregation, state it clearly.
- If it's a list, summarize what was found.
- Be concise and professional.
- Do NOT mention "SQL" or "rows" unless necessary to explain limit truncations.
- If the data is empty, say "I found no records matching your criteria."
"""

        try:
            response = self.provider.chat_complete(
                CompletionRequest(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": "You are a data analyst assistant."},
                        {"role": "user", "content": prompt}
                    ]
                )
            )
            return response.content
        except Exception:
            # Fallback if summarization fails
            return "Here are the results I found." if not error else f"Error: {error}"
