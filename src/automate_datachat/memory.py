from typing import List, Dict, Any

class ConversationMemory:
    """
    Manages chat history within a Django session.
    Format:
    [
        {"role": "user", "content": "show me users"},
        {"role": "assistant", "content": "Found 5 users...", "sql": "SELECT...", "data": [...] }
    ]
    """
    SESSION_KEY = "automate_datachat_history"
    MAX_TURNS = 10

    def __init__(self, session: Dict):
        self.session = session

    def get_history(self) -> List[Dict[str, Any]]:
        return self.session.get(self.SESSION_KEY, [])

    def add_user_message(self, content: str):
        history = self.get_history()
        history.append({"role": "user", "content": content})
        self._save(history)

    def add_assistant_message(self, content: str, sql: str = None, data: Any = None, chart: Dict = None):
        history = self.get_history()
        msg = {
            "role": "assistant",
            "content": content,
        }
        if sql:
            msg["sql"] = sql
        # We generally don't store full data rows in session due to size, 
        # but for context "what was the last result" we might need a summary or the last SQL.
        # For now, let's NOT store 'data' in session unless it's small.
        # We WILL store 'sql' which serves as the "data pointer" for the LLM context.
        
        if chart:
            msg["chart"] = chart
            
        history.append(msg)
        self._save(history)

    def get_context_window(self, limit: int = 5) -> str:
        """
        Returns a formatted string of the last N turns for the LLM prompt.
        """
        history = self.get_history()[-limit:]
        buffer = []
        for msg in history:
            role = msg["role"].upper()
            content = msg.get("content", "")
            sql = msg.get("sql", "")
            if sql:
                content += f"\n[Executed SQL]: {sql}"
            buffer.append(f"{role}: {content}")
        return "\n".join(buffer)

    def _save(self, history: List[Dict]):
        # Enforce max length
        if len(history) > self.MAX_TURNS * 2: # 2 messages per turn roughly
            history = history[-(self.MAX_TURNS*2):]
        
        self.session[self.SESSION_KEY] = history
        self.session.modified = True

    def clear(self):
        if self.SESSION_KEY in self.session:
            del self.session[self.SESSION_KEY]
            self.session.modified = True
