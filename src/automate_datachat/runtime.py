from .db import QueryExecutor, SchemaIntrospector
from .registry import DataChatRegistry
from .sqlpolicy import SQLPolicy

# Real LLM Integration
try:
    from automate.models import LLMModelConfig
    from automate_llm.provider.interfaces import CompletionRequest
except ImportError:
    LLMModelConfig = None
    CompletionRequest = None

class RealLLMService:
    """
    Manages the LLM Connection and Provider.
    """
    def __init__(self):
        self.provider = None
        self.model_name = "gpt-3.5-turbo"
        self._setup()

    def _setup(self):
        try:
            from automate.models import LLMModelConfig
            from automate_llm.registry import get_provider_class

            # Get default config (uses is_default=True or first available)
            config = LLMModelConfig.get_default()
            if not config:
                self.error = "No LLMModelConfig found. Please create one in Admin."
                return

            self.model_name = config.name
            provider_model = config.provider
            self.provider_slug = provider_model.slug

            # Setup Secrets Resolver
            import os

            from automate_governance.secrets.interfaces import SecretsBackend
            from automate_governance.secrets.refs import SecretRef
            from automate_governance.secrets.resolver import SecretResolver

            class EnvBackend(SecretsBackend):
                 def resolve(self, ref: SecretRef) -> str:
                     # ref.name is the actual env var name (e.g., OPENAI_API_KEY)
                     return os.environ.get(ref.name, "")

            resolver = SecretResolver(backends={"env": EnvBackend()})

            # Dynamic provider instantiation via registry
            provider_cls = get_provider_class(provider_model.slug)

            if provider_cls:
                api_key_source = provider_model.api_key_env_var

                # Check if it's a raw key (starts with sk-) or an env var name
                if api_key_source.startswith("sk-"):
                    # Raw key stored in DB - use a passthrough resolver
                    class RawKeyResolver:
                        def __init__(self, key):
                            self._key = key
                        def resolve_value(self, ref, **kwargs):
                            return self._key
                    resolver = RawKeyResolver(api_key_source)
                    api_key_ref = api_key_source  # Pass anything, resolver ignores it
                else:
                    # It's an env var name - construct proper secretref with namespace
                    # Format: secretref://env/<namespace>/<name>
                    api_key_ref = f"secretref://env/llm/{api_key_source}"

                self.provider = provider_cls(
                    secret_resolver=resolver,
                    api_key_ref=api_key_ref,
                    org_id_ref=None
                )
            elif provider_model.slug == "mock":
                 # Built-in mock for testing
                 class MockProvider:
                    def chat_complete(self, request):
                        from automate_llm.provider.interfaces import CompletionResponse

                        content = ""
                        last_msg = request.messages[-1]["content"]

                        if "You are a Postgres SQL generator" in request.messages[0]["content"]:
                            if "auth_user" in last_msg or "users" in last_msg.lower():
                                content = "SELECT * FROM auth_user LIMIT 5"
                            else:
                                content = "SELECT * FROM auth_user LIMIT 5"
                        else:
                            content = "I found 5 users in the system. They include 'admin', 'test_user', and others."

                        return CompletionResponse(
                            content=content,
                            usage={"total_tokens": 10},
                            model_used="mock-v1",
                            raw_response={}
                        )
                 self.provider = MockProvider()
            else:
                 self.error = f"Provider '{provider_model.slug}' not registered. Run: register_provider('{provider_model.slug}')"
                 self.provider = None
        except Exception as e:
            self.error = str(e)
            self.provider = None

    def generate_sql(self, history_str: str, question: str, schema: str, session_context: dict = None) -> tuple[str, "LLMRequest"]:
        """Generate SQL and return (sql, llm_request_record).
        
        Args:
            history_str: Conversation history
            question: User's question
            schema: Database schema
            session_context: Optional context with user info, timezone, etc.
        """
        import time

        from automate.models import MCPTool, Prompt
        from automate_llm.governance.models import LLMRequest

        if not self.provider:
            return f"SELECT 'Error: {getattr(self, 'error', 'LLM Provider not ready')}'", None

        # Default session context
        if session_context is None:
            session_context = {}

        # Fetch enabled MCP tools
        mcp_tools = []
        try:
            tools = MCPTool.objects.filter(enabled=True, server__enabled=True).select_related('server')[:50]
            for tool in tools:
                mcp_tools.append({
                    "name": tool.name,
                    "description": tool.description or "No description",
                    "input_schema": tool.input_schema or {},
                    "server_slug": tool.server.slug
                })
        except Exception:
            pass  # MCP tools are optional

        # Get prompt from DB or use fallback
        try:
            prompt_obj = Prompt.objects.get(slug="datachat_sql_generator")
            version = prompt_obj.versions.filter(status="approved").order_by("-version").first()
            if version:
                # Render templates with Jinja2
                from jinja2 import Environment
                env = Environment()
                env.filters['tojson'] = lambda x: __import__('json').dumps(x)
                system_template = env.from_string(version.system_template)
                user_template = env.from_string(version.user_template)
                system_prompt = system_template.render(
                    schema=schema,
                    tools=mcp_tools,
                    context=session_context
                )
                full_user_msg = user_template.render(history=history_str, question=question)
            else:
                raise Prompt.DoesNotExist
        except (Prompt.DoesNotExist, Exception):
            # Fallback to hardcoded (no tools)
            system_prompt = f"""You are a Postgres SQL generator.
Schema:
{schema}

Rules:
- Generate ONLY a single SQL query.
- No markdown, no comments.
- Read-only SELECT only.
- Prefer standard SQL.
"""
            full_user_msg = f"""History:
{history_str}

Question: {question}"""

        # Create pending LLM request with input
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": full_user_msg}
        ]
        llm_req = LLMRequest.objects.create(
            provider=self.provider_slug,
            model=self.model_name,
            prompt_slug="datachat_sql_generator",
            purpose="sql_generation",
            status="PENDING",
            input_payload=messages  # Save input for debugging
        )

        start_time = time.time()
        try:
            response = self.provider.chat_complete(
                CompletionRequest(
                    model=self.model_name,
                    messages=messages
                )
            )

            # Update with success and output
            latency = int((time.time() - start_time) * 1000)
            llm_req.status = "SUCCESS"
            llm_req.latency_ms = latency
            llm_req.output_content = response.content  # Save output for debugging
            if hasattr(response, 'usage') and response.usage:
                llm_req.input_tokens = response.usage.get('prompt_tokens') or response.usage.get('total_tokens')
                llm_req.output_tokens = response.usage.get('completion_tokens')
            llm_req.save()

            return response.content, llm_req

        except Exception as e:
            llm_req.status = "FAILED"
            llm_req.error_message = str(e)
            llm_req.latency_ms = int((time.time() - start_time) * 1000)
            llm_req.save()
            raise

class ChatOrchestrator:
    def __init__(self, request=None):
        self.executor = QueryExecutor()
        self.llm_service = RealLLMService()
        self.request = request
        self.db_session = None

        # Initialize DB Session for message persistence
        if request and request.user.is_authenticated:
            from .models import DataChatSession
            self.db_session, _ = DataChatSession.objects.get_or_create(user=request.user)
        elif request:
            from .models import DataChatSession
            session_key = request.session.session_key or ""
            if session_key:
                self.db_session, _ = DataChatSession.objects.get_or_create(session_key=session_key)

        # Initialize Memory for session-based context (deprecated, will use DB)
        from .memory import ConversationMemory
        if request:
            self.memory = ConversationMemory(request.session)
        else:
            self.memory = None

        from .intelligence import ResultSummarizer, VisualizationEngine
        self.viz_engine = VisualizationEngine

        if self.llm_service.provider:
            self.summarizer = ResultSummarizer(self.llm_service.provider, self.llm_service.model_name)
        else:
            self.summarizer = None

    def _get_client_ip(self) -> str:
        """Get client IP address from request, handling proxies."""
        if not self.request:
            return "Unknown"

        # Check for proxy headers
        x_forwarded_for = self.request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0].strip()

        return self.request.META.get("REMOTE_ADDR", "Unknown")

    def chat(self, user_question: str):
        # 1. Context and History
        schema_str = SchemaIntrospector.get_llm_context()
        history_str = self.memory.get_context_window() if self.memory else ""

        if self.memory:
            self.memory.add_user_message(user_question)

        # Build session context for the LLM (non-sensitive info only)

        from django.utils import timezone

        session_context = {
            "current_datetime": timezone.now().strftime("%Y-%m-%d %H:%M:%S %Z"),
            "timezone": str(timezone.get_current_timezone()),
            "date": timezone.now().strftime("%Y-%m-%d"),
            "time": timezone.now().strftime("%H:%M:%S"),
        }

        if self.request:
            # Add user info (non-sensitive only)
            if self.request.user.is_authenticated:
                session_context["username"] = self.request.user.username
                session_context["user_id"] = self.request.user.id
                session_context["is_staff"] = self.request.user.is_staff
            else:
                session_context["username"] = "Anonymous"

            # Add safe request info
            session_context["ip_address"] = self._get_client_ip()
            session_context["user_agent"] = self.request.META.get("HTTP_USER_AGENT", "Unknown")[:100]

        # 2. Policy Setup
        exposed_tables = DataChatRegistry.get_exposed_tables().keys()
        if not exposed_tables:
             msg = "No tables exposed. Please register models in DataChatRegistry."
             if self.memory: self.memory.add_assistant_message(msg)
             return {"answer": msg, "sql": ""}

        policy = SQLPolicy(allowed_tables=exposed_tables)

        # 3. Generate SQL (returns tuple with LLMRequest for audit)
        raw_response, sql_llm_request = self.llm_service.generate_sql(history_str, user_question, schema_str, session_context)
        raw_response = raw_response.replace('```sql', '').replace('```', '').strip()

        # 4. Detect response type: SQL, TOOL_CALL, or conversational
        is_sql = raw_response.upper().startswith(('SELECT', 'WITH'))
        is_tool_call = raw_response.startswith('TOOL_CALL:')

        # Handle MCP tool calls
        if is_tool_call:
            return self._execute_tool_call(raw_response, user_question, sql_llm_request)

        if not is_sql:
            # This is a conversational response, not SQL
            final_answer = raw_response

            # Save to DB
            if self.db_session:
                from .models import DataChatMessage
                DataChatMessage.objects.create(
                    session=self.db_session,
                    role="user",
                    content=user_question
                )
                DataChatMessage.objects.create(
                    session=self.db_session,
                    role="assistant",
                    content=final_answer,
                    llm_request=sql_llm_request
                )

            if self.memory:
                self.memory.add_assistant_message(final_answer, "", [])

            return {
                "answer": final_answer,
                "sql": "",
                "data": [],
                "chart": None,
                "error": None
            }

        sql_to_execute = raw_response
        query_error = None
        results = []

        # 5. Validate & Execute
        try:
            sql_to_execute = policy.validate_and_optimize(raw_response)
            results = self.executor.run_query(sql_to_execute, policy)
        except Exception as e:
            query_error = str(e)

        # 5. Summarize & Visualize
        chart_config = None
        if not query_error:
            chart_config = self.viz_engine.detect_chart(results)

        final_answer = ""
        if self.summarizer:
            final_answer = self.summarizer.summarize(user_question, sql_to_execute, results, query_error)
        else:
            final_answer = str(query_error) if query_error else f"Found {len(results)} rows. (LLM Summarizer unavailable)"

        # 6. Save to DB (persistent) and Memory (session context)
        if self.db_session:
            from .models import DataChatMessage

            # Save user message
            DataChatMessage.objects.create(
                session=self.db_session,
                role="user",
                content=user_question
            )

            # Save assistant response with audit link
            DataChatMessage.objects.create(
                session=self.db_session,
                role="assistant",
                content=final_answer,
                sql=sql_to_execute,
                data_json=results,
                chart_json=chart_config,
                error=query_error or "",
                llm_request=sql_llm_request
            )

        # Keep session memory for context window (backward compatibility)
        if self.memory:
            self.memory.add_assistant_message(final_answer, sql_to_execute, results, chart=chart_config)

        return {
            "answer": final_answer,
            "sql": sql_to_execute,
            "data": results,
            "chart": chart_config,
            "error": query_error
        }

    def _execute_tool_call(self, raw_response: str, user_question: str, llm_request) -> dict:
        """
        Execute an MCP tool call and return the result.
        
        Args:
            raw_response: The raw LLM response starting with "TOOL_CALL: {...}"
            user_question: Original user question
            llm_request: The LLMRequest record for audit
            
        Returns:
            dict with answer, data, and tool_call info
        """
        import json

        from automate.models import MCPTool
        from automate_llm.mcp_client import MCPClient, MCPClientError

        try:
            # Parse TOOL_CALL JSON
            tool_call_str = raw_response.replace("TOOL_CALL:", "").strip()
            tool_call = json.loads(tool_call_str)
            tool_name = tool_call.get("tool", "")
            tool_args = tool_call.get("args", {})

            # Find the tool and its server
            tool = MCPTool.objects.select_related("server").filter(
                name=tool_name,
                enabled=True,
                server__enabled=True
            ).first()

            if not tool:
                error_msg = f"Tool '{tool_name}' not found or not enabled."
                return self._save_and_return(user_question, error_msg, llm_request, tool_call=tool_call_str)

            # Execute the tool
            client = MCPClient(tool.server)
            result = client.execute_tool(tool_name, tool_args)

            # Update tool usage stats
            from django.utils import timezone
            tool.call_count += 1
            tool.last_called = timezone.now()
            tool.save(update_fields=["call_count", "last_called"])

            # Format result for user
            if isinstance(result, dict):
                if result.get("success", True):
                    data = result.get("data", result)
                    answer = f"**{tool_name}** returned:\n```json\n{json.dumps(data, indent=2)}\n```"
                else:
                    answer = f"Tool error: {result.get('error', 'Unknown error')}"
            else:
                answer = f"**{tool_name}** returned: {result}"

            return self._save_and_return(user_question, answer, llm_request, tool_call=tool_call_str, tool_result=result)

        except json.JSONDecodeError as e:
            error_msg = f"Invalid tool call format: {e}"
            return self._save_and_return(user_question, error_msg, llm_request, error=str(e))
        except MCPClientError as e:
            error_msg = f"Tool execution failed: {e}"
            return self._save_and_return(user_question, error_msg, llm_request, error=str(e))
        except Exception as e:
            error_msg = f"Error executing tool: {e}"
            return self._save_and_return(user_question, error_msg, llm_request, error=str(e))

    def _save_and_return(self, user_question: str, answer: str, llm_request,
                         tool_call: str = None, tool_result: dict = None, error: str = None) -> dict:
        """Helper to save messages and return response dict."""
        if self.db_session:
            from .models import DataChatMessage

            DataChatMessage.objects.create(
                session=self.db_session,
                role="user",
                content=user_question
            )
            DataChatMessage.objects.create(
                session=self.db_session,
                role="assistant",
                content=answer,
                llm_request=llm_request
            )

        if self.memory:
            self.memory.add_assistant_message(answer, "", [])

        return {
            "answer": answer,
            "sql": "",
            "data": tool_result if tool_result else [],
            "chart": None,
            "error": error,
            "tool_call": tool_call
        }

