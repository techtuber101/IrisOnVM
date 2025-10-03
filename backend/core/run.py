import os
try:
    import orjson as json_module
    # orjson is 2-3x faster than stdlib json for parsing and serialization
    json_loads = lambda s: json_module.loads(s) if isinstance(s, (bytes, bytearray, memoryview, str)) else s
    json_dumps = lambda obj: json_module.dumps(obj).decode('utf-8')
except ImportError:
    import json as json_module
    json_loads = json_module.loads
    json_dumps = json_module.dumps
import json  # Keep for compatibility
import asyncio
import datetime
from typing import Optional, Dict, List, Any, AsyncGenerator
from dataclasses import dataclass

from core.tools.message_tool import MessageTool
from core.tools.sb_deploy_tool import SandboxDeployTool
from core.tools.sb_expose_tool import SandboxExposeTool
from core.tools.web_search_tool import SandboxWebSearchTool
from dotenv import load_dotenv
from core.utils.config import config
from core.prompts.agent_builder_prompt import get_agent_builder_prompt
from core.agentpress.thread_manager import ThreadManager
from core.agentpress.response_processor import ProcessorConfig
from core.tools.sb_shell_tool import SandboxShellTool
from core.tools.sb_files_tool import SandboxFilesTool
from core.tools.data_providers_tool import DataProvidersTool
from core.tools.expand_msg_tool import ExpandMessageTool
from core.prompts.prompt import get_system_prompt

from core.utils.logger import logger
from core.utils.llm_cache_utils import format_message_with_cache

from core.billing.billing_integration import billing_integration
from core.tools.sb_vision_tool import SandboxVisionTool
from core.tools.sb_image_edit_tool import SandboxImageEditTool
from core.tools.sb_designer_tool import SandboxDesignerTool
from core.tools.sb_presentation_outline_tool import SandboxPresentationOutlineTool
from core.tools.sb_presentation_tool import SandboxPresentationTool

from core.services.langfuse import langfuse
from langfuse.client import StatefulTraceClient

from core.tools.mcp_tool_wrapper import MCPToolWrapper
from core.tools.task_list_tool import TaskListTool
from core.agentpress.tool import SchemaType
from core.tools.sb_sheets_tool import SandboxSheetsTool
# from core.tools.sb_web_dev_tool import SandboxWebDevTool  # DEACTIVATED
from core.ai_models import model_manager
from core.tools.sb_upload_file_tool import SandboxUploadFileTool
from core.tools.sb_docs_tool import SandboxDocsTool

load_dotenv()


@dataclass
class AgentConfig:
    thread_id: str
    project_id: str
    stream: bool
    native_max_auto_continues: int = 25
    max_iterations: int = 100
    model_name: str = "gemini/gemini-2.5-flash"
    enable_thinking: Optional[bool] = False
    reasoning_effort: Optional[str] = 'low'
    enable_context_manager: bool = True
    agent_config: Optional[dict] = None
    trace: Optional[StatefulTraceClient] = None


class ToolManager:
    def __init__(self, thread_manager: ThreadManager, project_id: str, thread_id: str):
        self.thread_manager = thread_manager
        self.project_id = project_id
        self.thread_id = thread_id
    
    def register_all_tools(self, agent_id: Optional[str] = None, disabled_tools: Optional[List[str]] = None):
        """Register all available tools by default, with optional exclusions.
        
        Args:
            agent_id: Optional agent ID for agent builder tools
            disabled_tools: List of tool names to exclude from registration
        """
        disabled_tools = disabled_tools or []
        
        logger.debug(f"Registering tools with disabled list: {disabled_tools}")
        
        # Core tools - always enabled
        self._register_core_tools()
        
        # Sandbox tools
        self._register_sandbox_tools(disabled_tools)
        
        # Data and utility tools
        self._register_utility_tools(disabled_tools)
        
        # Agent builder tools - register if agent_id provided
        if agent_id:
            self._register_agent_builder_tools(agent_id, disabled_tools)
        
        # Browser tool
        self._register_browser_tool(disabled_tools)
        
        logger.debug(f"Tool registration complete. Registered tools: {list(self.thread_manager.tool_registry.tools.keys())}")
    
    def _register_core_tools(self):
        """Register core tools that are always available."""
        self.thread_manager.add_tool(ExpandMessageTool, thread_id=self.thread_id, thread_manager=self.thread_manager)
        self.thread_manager.add_tool(MessageTool)
        self.thread_manager.add_tool(TaskListTool, project_id=self.project_id, thread_manager=self.thread_manager, thread_id=self.thread_id)
    
    def _register_sandbox_tools(self, disabled_tools: List[str]):
        """Register sandbox-related tools."""
        sandbox_tools = [
            ('sb_shell_tool', SandboxShellTool, {'project_id': self.project_id, 'thread_manager': self.thread_manager}),
            ('sb_files_tool', SandboxFilesTool, {'project_id': self.project_id, 'thread_manager': self.thread_manager}),
            ('sb_deploy_tool', SandboxDeployTool, {'project_id': self.project_id, 'thread_manager': self.thread_manager}),
            ('sb_expose_tool', SandboxExposeTool, {'project_id': self.project_id, 'thread_manager': self.thread_manager}),
            ('web_search_tool', SandboxWebSearchTool, {'project_id': self.project_id, 'thread_manager': self.thread_manager}),
            ('sb_vision_tool', SandboxVisionTool, {'project_id': self.project_id, 'thread_id': self.thread_id, 'thread_manager': self.thread_manager}),
            ('sb_image_edit_tool', SandboxImageEditTool, {'project_id': self.project_id, 'thread_id': self.thread_id, 'thread_manager': self.thread_manager}),
            ('sb_design_tool', SandboxDesignerTool, {'project_id': self.project_id, 'thread_id': self.thread_id, 'thread_manager': self.thread_manager}),
            ('sb_presentation_outline_tool', SandboxPresentationOutlineTool, {'project_id': self.project_id, 'thread_manager': self.thread_manager}),
            ('sb_presentation_tool', SandboxPresentationTool, {'project_id': self.project_id, 'thread_manager': self.thread_manager}),

            ('sb_sheets_tool', SandboxSheetsTool, {'project_id': self.project_id, 'thread_manager': self.thread_manager}),
            # ('sb_web_dev_tool', SandboxWebDevTool, {'project_id': self.project_id, 'thread_id': self.thread_id, 'thread_manager': self.thread_manager}),  # DEACTIVATED
            ('sb_upload_file_tool', SandboxUploadFileTool, {'project_id': self.project_id, 'thread_manager': self.thread_manager}),
            ('sb_docs_tool', SandboxDocsTool, {'project_id': self.project_id, 'thread_manager': self.thread_manager}),
        ]
        
        for tool_name, tool_class, kwargs in sandbox_tools:
            if tool_name not in disabled_tools:
                self.thread_manager.add_tool(tool_class, **kwargs)
                logger.debug(f"Registered {tool_name}")
    
    def _register_utility_tools(self, disabled_tools: List[str]):
        """Register utility and data provider tools."""
        if config.RAPID_API_KEY and 'data_providers_tool' not in disabled_tools:
            self.thread_manager.add_tool(DataProvidersTool)
            logger.debug("Registered data_providers_tool")
    
    def _register_agent_builder_tools(self, agent_id: str, disabled_tools: List[str]):
        """Register agent builder tools with lazy imports for better performance."""
        # Lazy import mapping - only import what's needed
        tool_imports = {
            'agent_config_tool': 'core.tools.agent_builder_tools.agent_config_tool.AgentConfigTool',
            'mcp_search_tool': 'core.tools.agent_builder_tools.mcp_search_tool.MCPSearchTool',
            'credential_profile_tool': 'core.tools.agent_builder_tools.credential_profile_tool.CredentialProfileTool',
            'workflow_tool': 'core.tools.agent_builder_tools.workflow_tool.WorkflowTool',
            'trigger_tool': 'core.tools.agent_builder_tools.trigger_tool.TriggerTool',
        }
        
        from core.services.supabase import DBConnection
        db = DBConnection()
        
        logger.debug(f"Registering agent builder tools for agent_id: {agent_id}")
        logger.debug(f"Disabled tools list: {disabled_tools}")
        
        for tool_name, import_path in tool_imports.items():
            if tool_name not in disabled_tools:
                try:
                    # Lazy import - only import if tool is enabled
                    module_path, class_name = import_path.rsplit('.', 1)
                    module = __import__(module_path, fromlist=[class_name])
                    tool_class = getattr(module, class_name)
                    
                    self.thread_manager.add_tool(tool_class, thread_manager=self.thread_manager, db_connection=db, agent_id=agent_id)
                    logger.debug(f"✅ Registered {tool_name}")
                except Exception as e:
                    logger.warning(f"❌ Failed to register {tool_name}: {e}")
            else:
                logger.debug(f"⏭️ Skipping {tool_name} - disabled (not imported)")
    
    def _register_suna_specific_tools(self, disabled_tools: List[str]):
        """Register tools specific to Suna (the default agent)."""
        if 'agent_creation_tool' not in disabled_tools:
            from core.tools.agent_creation_tool import AgentCreationTool
            from core.services.supabase import DBConnection
            
            db = DBConnection()
            
            if hasattr(self, 'account_id') and self.account_id:
                self.thread_manager.add_tool(AgentCreationTool, thread_manager=self.thread_manager, db_connection=db, account_id=self.account_id)
                logger.debug("Registered agent_creation_tool for Suna")
            else:
                logger.warning("Could not register agent_creation_tool: account_id not available")
    
    def _register_browser_tool(self, disabled_tools: List[str]):
        """Register browser tool."""
        if 'browser_tool' not in disabled_tools:
            from core.tools.browser_tool import BrowserTool
            self.thread_manager.add_tool(BrowserTool, project_id=self.project_id, thread_id=self.thread_id, thread_manager=self.thread_manager)
            logger.debug("Registered browser_tool")
    

class MCPManager:
    def __init__(self, thread_manager: ThreadManager, account_id: str):
        self.thread_manager = thread_manager
        self.account_id = account_id
    
    async def register_mcp_tools(self, agent_config: dict) -> Optional[MCPToolWrapper]:
        all_mcps = []
        
        if agent_config.get('configured_mcps'):
            all_mcps.extend(agent_config['configured_mcps'])
        
        if agent_config.get('custom_mcps'):
            for custom_mcp in agent_config['custom_mcps']:
                custom_type = custom_mcp.get('customType', custom_mcp.get('type', 'sse'))
                
                if custom_type == 'pipedream':
                    if 'config' not in custom_mcp:
                        custom_mcp['config'] = {}
                    
                    if not custom_mcp['config'].get('external_user_id'):
                        profile_id = custom_mcp['config'].get('profile_id')
                        if profile_id:
                            try:
                                from pipedream import profile_service
                                from uuid import UUID
                                
                                profile = await profile_service.get_profile(UUID(self.account_id), UUID(profile_id))
                                if profile:
                                    custom_mcp['config']['external_user_id'] = profile.external_user_id
                            except Exception as e:
                                logger.error(f"Error retrieving external_user_id from profile {profile_id}: {e}")
                    
                    if 'headers' in custom_mcp['config'] and 'x-pd-app-slug' in custom_mcp['config']['headers']:
                        custom_mcp['config']['app_slug'] = custom_mcp['config']['headers']['x-pd-app-slug']
                
                elif custom_type == 'composio':
                    qualified_name = custom_mcp.get('qualifiedName')
                    if not qualified_name:
                        qualified_name = f"composio.{custom_mcp['name'].replace(' ', '_').lower()}"
                    
                    mcp_config = {
                        'name': custom_mcp['name'],
                        'qualifiedName': qualified_name,
                        'config': custom_mcp.get('config', {}),
                        'enabledTools': custom_mcp.get('enabledTools', []),
                        'instructions': custom_mcp.get('instructions', ''),
                        'isCustom': True,
                        'customType': 'composio'
                    }
                    all_mcps.append(mcp_config)
                    continue
                
                mcp_config = {
                    'name': custom_mcp['name'],
                    'qualifiedName': f"custom_{custom_type}_{custom_mcp['name'].replace(' ', '_').lower()}",
                    'config': custom_mcp['config'],
                    'enabledTools': custom_mcp.get('enabledTools', []),
                    'instructions': custom_mcp.get('instructions', ''),
                    'isCustom': True,
                    'customType': custom_type
                }
                all_mcps.append(mcp_config)
        
        if not all_mcps:
            return None
        
        mcp_wrapper_instance = MCPToolWrapper(mcp_configs=all_mcps)
        try:
            await mcp_wrapper_instance.initialize_and_register_tools()
            
            updated_schemas = mcp_wrapper_instance.get_schemas()
            for method_name, schema_list in updated_schemas.items():
                for schema in schema_list:
                    self.thread_manager.tool_registry.tools[method_name] = {
                        "instance": mcp_wrapper_instance,
                        "schema": schema
                    }
            
            logger.debug(f"⚡ Registered {len(updated_schemas)} MCP tools (Redis cache enabled)")
            return mcp_wrapper_instance
        except Exception as e:
            logger.error(f"Failed to initialize MCP tools: {e}")
            return None


class PromptManager:
    @staticmethod
    async def build_system_prompt(model_name: str, agent_config: Optional[dict], 
                                  thread_id: str, 
                                  mcp_wrapper_instance: Optional[MCPToolWrapper],
                                  client=None, user_first_name: Optional[str] = None) -> dict:
        
        # Generate cache key based on agent config, model, and user
        # NOTE: model_name is the resolved model ID (e.g., "gemini/gemini-2.5-flash")
        # Each model gets its own cache entry with model-specific formatting
        # If fallback occurs (Gemini->GPT-5), the new model will create its own cache
        # This ensures: 1) Model-specific cache formatting, 2) Fast cache hits per model
        agent_id = agent_config.get('agent_id') if agent_config else 'default'
        agent_version_id = agent_config.get('current_version_id') if agent_config else 'none'
        cache_key = f"system_prompt:{agent_id}:{agent_version_id}:{model_name}:{user_first_name or 'anon'}"
        
        # Try to get from cache first (IMPORTANT: Only caches system prompt, NOT conversation messages)
        try:
            from core.services import redis
            cached_prompt = await redis.get(cache_key)
            if cached_prompt:
                # Use faster orjson if available
                cached_data = json_loads(cached_prompt.decode() if isinstance(cached_prompt, bytes) else cached_prompt)
                logger.debug(f"✅ Using cached system prompt for agent {agent_id} (saved DB query)")
                return cached_data
        except Exception as e:
            logger.debug(f"Cache miss or error for system prompt: {e}")
        
        default_system_content = get_system_prompt()
        
        # Add personalized greeting with user's first name if available
        if user_first_name:
            personalization = f"\n\n# PERSONALIZATION\nYou are speaking with {user_first_name}. Feel free to use their name occasionally in your responses to make the interaction more personal and friendly. For example:\n- \"I'll help you with that, {user_first_name}.\"\n- \"{user_first_name}, I've completed the task for you.\"\n- \"Let me get that done for you, {user_first_name}.\"\nUse their name naturally and sparingly - not in every response, but when it feels appropriate to add a personal touch."
            default_system_content = default_system_content + personalization
        
        if "anthropic" not in model_name.lower():
            sample_response_path = os.path.join(os.path.dirname(__file__), 'prompts/samples/1.txt')
            with open(sample_response_path, 'r') as file:
                sample_response = file.read()
            default_system_content = default_system_content + "\n\n <sample_assistant_response>" + sample_response + "</sample_assistant_response>"
        
        # Start with agent's normal system prompt or default
        if agent_config and agent_config.get('system_prompt'):
            system_content = agent_config['system_prompt'].strip()
        else:
            system_content = default_system_content
        
        # Check if agent has builder tools enabled - append the full builder prompt
        if agent_config:
            agentpress_tools = agent_config.get('agentpress_tools', {})
            has_builder_tools = any(
                agentpress_tools.get(tool, False) 
                for tool in ['agent_config_tool', 'mcp_search_tool', 'credential_profile_tool', 'workflow_tool', 'trigger_tool']
            )
            
            if has_builder_tools:
                # Append the full agent builder prompt to the existing system prompt
                builder_prompt = get_agent_builder_prompt()
                system_content += f"\n\n{builder_prompt}"
        
        # Add agent knowledge base context if available (with Redis cache)
        if agent_config and client and 'agent_id' in agent_config:
            try:
                # Try to get knowledge base from cache first
                kb_cache_key = f"kb:{agent_config['agent_id']}"
                kb_cached = await redis.get(kb_cache_key)
                
                if kb_cached:
                    kb_data = kb_cached.decode() if isinstance(kb_cached, bytes) else kb_cached
                    logger.debug(f"✅ Using cached knowledge base for agent {agent_config['agent_id']} (saved DB query)")
                else:
                    logger.debug(f"Retrieving agent knowledge base context for agent {agent_config['agent_id']}")
                    
                    # Use only agent-based knowledge base context
                    kb_result = await client.rpc('get_agent_knowledge_base_context', {
                        'p_agent_id': agent_config['agent_id']
                    }).execute()
                    
                    kb_data = kb_result.data if kb_result.data else ""
                    
                    # Cache knowledge base for 5 minutes (300 seconds)
                    if kb_data:
                        await redis.set(kb_cache_key, kb_data, ex=300)
                        logger.debug(f"📦 Cached knowledge base for agent {agent_config['agent_id']}")
                
                if kb_data and kb_data.strip():
                    logger.debug(f"Found agent knowledge base context, adding to system prompt (length: {len(kb_data)} chars)")
                    
                    # Construct a well-formatted knowledge base section
                    kb_section = f"""

                    === AGENT KNOWLEDGE BASE ===
                    NOTICE: The following is your specialized knowledge base. This information should be considered authoritative for your responses and should take precedence over general knowledge when relevant.

                    {kb_data}

                    === END AGENT KNOWLEDGE BASE ===

                    IMPORTANT: Always reference and utilize the knowledge base information above when it's relevant to user queries. This knowledge is specific to your role and capabilities."""
                    
                    system_content += kb_section
                else:
                    logger.debug("No knowledge base context found for this agent")
                    
            except Exception as e:
                logger.error(f"Error retrieving knowledge base context for agent {agent_config.get('agent_id', 'unknown')}: {e}")
                # Continue without knowledge base context rather than failing
        
        if agent_config and (agent_config.get('configured_mcps') or agent_config.get('custom_mcps')) and mcp_wrapper_instance and mcp_wrapper_instance._initialized:
            mcp_info = "\n\n--- MCP Tools Available ---\n"
            mcp_info += "You have access to external MCP (Model Context Protocol) server tools.\n"
            mcp_info += "MCP tools can be called directly using their native function names in the standard function calling format:\n"
            mcp_info += '<function_calls>\n'
            mcp_info += '<invoke name="{tool_name}">\n'
            mcp_info += '<parameter name="param1">value1</parameter>\n'
            mcp_info += '<parameter name="param2">value2</parameter>\n'
            mcp_info += '</invoke>\n'
            mcp_info += '</function_calls>\n\n'
            
            mcp_info += "Available MCP tools:\n"
            try:
                registered_schemas = mcp_wrapper_instance.get_schemas()
                for method_name, schema_list in registered_schemas.items():
                    for schema in schema_list:
                        if schema.schema_type == SchemaType.OPENAPI:
                            func_info = schema.schema.get('function', {})
                            description = func_info.get('description', 'No description available')
                            mcp_info += f"- **{method_name}**: {description}\n"
                            
                            params = func_info.get('parameters', {})
                            props = params.get('properties', {})
                            if props:
                                mcp_info += f"  Parameters: {', '.join(props.keys())}\n"
                                
            except Exception as e:
                logger.error(f"Error listing MCP tools: {e}")
                mcp_info += "- Error loading MCP tool list\n"
            
            mcp_info += "\n🚨 CRITICAL MCP TOOL RESULT INSTRUCTIONS 🚨\n"
            mcp_info += "When you use ANY MCP (Model Context Protocol) tools:\n"
            mcp_info += "1. ALWAYS read and use the EXACT results returned by the MCP tool\n"
            mcp_info += "2. For search tools: ONLY cite URLs, sources, and information from the actual search results\n"
            mcp_info += "3. For any tool: Base your response entirely on the tool's output - do NOT add external information\n"
            mcp_info += "4. DO NOT fabricate, invent, hallucinate, or make up any sources, URLs, or data\n"
            mcp_info += "5. If you need more information, call the MCP tool again with different parameters\n"
            mcp_info += "6. When writing reports/summaries: Reference ONLY the data from MCP tool results\n"
            mcp_info += "7. If the MCP tool doesn't return enough information, explicitly state this limitation\n"
            mcp_info += "8. Always double-check that every fact, URL, and reference comes from the MCP tool output\n"
            mcp_info += "\nIMPORTANT: MCP tool results are your PRIMARY and ONLY source of truth for external data!\n"
            mcp_info += "NEVER supplement MCP results with your training data or make assumptions beyond what the tools provide.\n"
            
            system_content += mcp_info

        now = datetime.datetime.now(datetime.timezone.utc)
        datetime_info = f"\n\n=== CURRENT DATE/TIME INFORMATION ===\n"
        datetime_info += f"Today's date: {now.strftime('%A, %B %d, %Y')}\n"
        datetime_info += f"Current year: {now.strftime('%Y')}\n"
        datetime_info += f"Current month: {now.strftime('%B')}\n"
        datetime_info += f"Current day: {now.strftime('%A')}\n"
        datetime_info += "Use this information for any time-sensitive tasks, research, or when current date/time context is needed.\n"
        
        system_content += datetime_info

        system_message = {"role": "system", "content": system_content}
        formatted_message = format_message_with_cache(system_message, model_name)
        
        # Cache the final system message for 5 minutes (300 seconds)
        # This includes MCP info and datetime which change less frequently
        try:
            # Use faster orjson for serialization
            await redis.set(cache_key, json_dumps(formatted_message), ex=300)
            logger.debug(f"📦 Cached system prompt for agent {agent_id}")
        except Exception as e:
            logger.debug(f"Failed to cache system prompt: {e}")
        
        return formatted_message


class MessageManager:
    def __init__(self, client, thread_id: str, model_name: str, trace: Optional[StatefulTraceClient], 
                 agent_config: Optional[dict] = None, enable_context_manager: bool = False):
        self.client = client
        self.thread_id = thread_id
        self.model_name = model_name
        self.trace = trace
        self.agent_config = agent_config
        self.enable_context_manager = enable_context_manager
    
    async def build_temporary_message(self) -> Optional[dict]:
        system_message = None
        
        if self.agent_config and 'system_prompt' in self.agent_config:
            system_prompt = self.agent_config['system_prompt']
            if system_prompt:
                system_message = system_prompt
        
        if self.agent_config:
            agentpress_tools = self.agent_config.get('agentpress_tools', {})
            has_builder_tools = any(
                agentpress_tools.get(tool, False) 
                for tool in ['agent_config_tool', 'mcp_search_tool', 'credential_profile_tool', 'workflow_tool', 'trigger_tool']
            )
            
            if has_builder_tools:
                from core.prompts.agent_builder_prompt import AGENT_BUILDER_SYSTEM_PROMPT
                if system_message:
                    system_message += f"\n\n{AGENT_BUILDER_SYSTEM_PROMPT}"
                else:
                    system_message = AGENT_BUILDER_SYSTEM_PROMPT
        
        if system_message:
            return {
                "temporary": True,
                "role": "system",
                "content": system_message
            }
        
        return None


class AgentRunner:
    def __init__(self, config: AgentConfig):
        self.config = config
    
    async def setup(self):
        if not self.config.trace:
            self.config.trace = langfuse.trace(name="run_agent", session_id=self.config.thread_id, metadata={"project_id": self.config.project_id})
        
        self.thread_manager = ThreadManager(
            trace=self.config.trace, 
            agent_config=self.config.agent_config
        )
        
        self.client = await self.thread_manager.db.client
        
        response = await self.client.table('threads').select('account_id').eq('thread_id', self.config.thread_id).execute()
        
        if not response.data or len(response.data) == 0:
            raise ValueError(f"Thread {self.config.thread_id} not found")
        
        self.account_id = response.data[0].get('account_id')
        
        if not self.account_id:
            raise ValueError(f"Thread {self.config.thread_id} has no associated account")
        
        # Get user's first name for personalized responses
        self.user_first_name = await self._get_user_first_name()

        project = await self.client.table('projects').select('*').eq('project_id', self.config.project_id).execute()
        if not project.data or len(project.data) == 0:
            raise ValueError(f"Project {self.config.project_id} not found")

        project_data = project.data[0]
        sandbox_info = project_data.get('sandbox', {})
        if not sandbox_info.get('id'):
            logger.debug(f"No sandbox found for project {self.config.project_id}; will create lazily when needed")
    
    async def setup_tools(self):
        tool_manager = ToolManager(self.thread_manager, self.config.project_id, self.config.thread_id)
        
        agent_id = None
        if self.config.agent_config:
            agent_id = self.config.agent_config.get('agent_id')
        
        disabled_tools = self._get_disabled_tools_from_config()
        
        tool_manager.register_all_tools(agent_id=agent_id, disabled_tools=disabled_tools)
        
        is_suna_agent = (self.config.agent_config and self.config.agent_config.get('is_suna_default', False)) or (self.config.agent_config is None)
        logger.debug(f"Agent config check: agent_config={self.config.agent_config is not None}, is_suna_default={is_suna_agent}")
        
        if is_suna_agent:
            logger.debug("Registering Suna-specific tools...")
            self._register_suna_specific_tools(disabled_tools)
        else:
            logger.debug("Not a Suna agent, skipping Suna-specific tool registration")
    
    def _register_suna_specific_tools(self, disabled_tools: List[str]):
        if 'agent_creation_tool' not in disabled_tools:
            from core.tools.agent_creation_tool import AgentCreationTool
            from core.services.supabase import DBConnection
            
            db = DBConnection()
            
            if hasattr(self, 'account_id') and self.account_id:
                self.thread_manager.add_tool(AgentCreationTool, thread_manager=self.thread_manager, db_connection=db, account_id=self.account_id)
                logger.debug("Registered agent_creation_tool for Suna")
            else:
                logger.warning("Could not register agent_creation_tool: account_id not available")
    
    def _get_disabled_tools_from_config(self) -> List[str]:
        disabled_tools = []
        
        if not self.config.agent_config or 'agentpress_tools' not in self.config.agent_config:
            return disabled_tools
        
        raw_tools = self.config.agent_config['agentpress_tools']
        
        if not isinstance(raw_tools, dict):
            return disabled_tools
        
        if self.config.agent_config.get('is_suna_default', False) and not raw_tools:
            return disabled_tools
        
        def is_tool_enabled(tool_name: str) -> bool:
            try:
                tool_config = raw_tools.get(tool_name, True)
                if isinstance(tool_config, bool):
                    return tool_config
                elif isinstance(tool_config, dict):
                    return tool_config.get('enabled', True)
                else:
                    return True
            except Exception:
                return True
        
        all_tools = [
            'sb_shell_tool', 'sb_files_tool', 'sb_deploy_tool', 'sb_expose_tool',
            'web_search_tool', 'sb_vision_tool', 'sb_presentation_tool', 'sb_image_edit_tool',
            'sb_sheets_tool', 'sb_web_dev_tool', 'data_providers_tool', 'browser_tool',
            'agent_config_tool', 'mcp_search_tool', 'credential_profile_tool', 
            'workflow_tool', 'trigger_tool'
        ]
        
        for tool_name in all_tools:
            if not is_tool_enabled(tool_name):
                disabled_tools.append(tool_name)
        
        if 'sb_presentation_tool' in disabled_tools:
            disabled_tools.extend(['sb_presentation_outline_tool'])
        
        logger.debug(f"Disabled tools from config: {disabled_tools}")
        return disabled_tools
    
    async def setup_mcp_tools(self) -> Optional[MCPToolWrapper]:
        if not self.config.agent_config:
            return None
        
        mcp_manager = MCPManager(self.thread_manager, self.account_id)
        return await mcp_manager.register_mcp_tools(self.config.agent_config)
    
    async def _get_user_first_name(self) -> Optional[str]:
        """Get the user's first name from their profile for personalized responses (with Redis cache)."""
        try:
            # Try cache first
            from core.services import redis
            cache_key = f"user_first_name:{self.account_id}"
            cached_name = await redis.get(cache_key)
            
            if cached_name:
                name = cached_name.decode() if isinstance(cached_name, bytes) else cached_name
                logger.debug(f"✅ Using cached first name for user {self.account_id}")
                return name if name != "None" else None
            
            # Get the primary owner user ID from the account
            account_response = await self.client.table('basejump.accounts').select('primary_owner_user_id').eq('id', self.account_id).execute()
            
            if not account_response.data or len(account_response.data) == 0:
                await redis.set(cache_key, "None", ex=3600)  # Cache "no name" for 1 hour
                return None
                
            user_id = account_response.data[0].get('primary_owner_user_id')
            if not user_id:
                await redis.set(cache_key, "None", ex=3600)
                return None
            
            # Get user metadata from auth.users
            user_response = await self.client.table('auth.users').select('user_metadata, email').eq('id', user_id).execute()
            
            if not user_response.data or len(user_response.data) == 0:
                await redis.set(cache_key, "None", ex=3600)
                return None
                
            user_data = user_response.data[0]
            user_metadata = user_data.get('user_metadata', {})
            email = user_data.get('email', '')
            
            first_name = None
            
            # Extract first name from user_metadata.name or email
            if user_metadata and user_metadata.get('name'):
                # Extract first name from full name
                full_name = user_metadata['name'].strip()
                first_name = full_name.split(' ')[0]
            elif email:
                # Extract name from email prefix
                email_prefix = email.split('@')[0]
                # Remove numbers and special characters, capitalize first letter
                import re
                clean_name = re.sub(r'[0-9._-]', '', email_prefix).lower()
                first_name = clean_name.capitalize() if clean_name else None
            
            # Cache the result for 1 hour
            cache_value = first_name if first_name else "None"
            await redis.set(cache_key, cache_value, ex=3600)
            logger.debug(f"📦 Cached first name for user {self.account_id}")
                
            return first_name
            
        except Exception as e:
            logger.error(f"Failed to get user first name: {e}")
            return None

    def get_max_tokens(self) -> Optional[int]:
        logger.debug(f"get_max_tokens called with: '{self.config.model_name}' (type: {type(self.config.model_name)})")
        if "sonnet" in self.config.model_name.lower():
            return 8192
        elif "gemini" in self.config.model_name.lower():
            return 4096
        elif "gemini-2.5-pro" in self.config.model_name.lower():
            return 64000
        elif "kimi-k2" in self.config.model_name.lower():
            return 8192
        return None
    
    async def run(self) -> AsyncGenerator[Dict[str, Any], None]:
        # Run setup operations in parallel for faster initialization
        logger.debug("🚀 Starting parallel setup operations")
        setup_start = asyncio.get_event_loop().time()
        
        # Setup must complete first (initializes client and account_id)
        await self.setup()
        
        # Now run tools and MCP setup in parallel (both depend on setup being done)
        tools_task = asyncio.create_task(self.setup_tools())
        mcp_task = asyncio.create_task(self.setup_mcp_tools())
        
        # Wait for both to complete
        await tools_task
        mcp_wrapper_instance = await mcp_task
        
        setup_duration = asyncio.get_event_loop().time() - setup_start
        logger.debug(f"✅ Parallel setup completed in {setup_duration:.2f}s")
        
        system_message = await PromptManager.build_system_prompt(
            self.config.model_name, self.config.agent_config, 
            self.config.thread_id, 
            mcp_wrapper_instance, self.client, self.user_first_name
        )
        logger.info(f"📝 System message built once: {len(str(system_message.get('content', '')))} chars")
        logger.debug(f"model_name received: {self.config.model_name}")
        iteration_count = 0
        continue_execution = True

        # TWO-PHASE RESPONSE SYSTEM: Always give instant acknowledgement first, then do actual work
        latest_user_message = await self.client.table('messages').select('*').eq('thread_id', self.config.thread_id).eq('type', 'user').order('created_at', desc=True).limit(1).execute()
        user_message_text = ""
        is_simple_message = False
        needs_instant_ack = True  # Always send instant acknowledgement
        
        if latest_user_message.data and len(latest_user_message.data) > 0:
            data = latest_user_message.data[0]['content']
            if isinstance(data, str):
                data = json.loads(data)
            user_message_text = data.get('content', '')
            
            # Detect simple greetings/conversational messages (only need ack, no tools)
            simple_patterns = ['hi', 'hello', 'hey', 'thanks', 'thank you', 'ok', 'okay', 
                             'cool', 'nice', 'great', 'awesome', 'good', 'sup', 'yo']
            message_lower = user_message_text.lower().strip().rstrip('!.,?')
            
            # Simple message if: short (<15 chars) AND matches pattern OR is very short (<5 chars)
            if (len(message_lower) < 15 and any(pattern in message_lower for pattern in simple_patterns)) or len(message_lower) < 5:
                is_simple_message = True
                logger.info(f"🚀 Simple message detected: '{user_message_text[:20]}...' - single phase response only")
            else:
                logger.info(f"⚡ Complex message detected: '{user_message_text[:50]}...' - two-phase response: instant ack + tools")
            
            if self.config.trace:
                self.config.trace.update(input=data['content'])

        message_manager = MessageManager(self.client, self.config.thread_id, self.config.model_name, self.config.trace, 
                                         agent_config=self.config.agent_config, enable_context_manager=self.config.enable_context_manager)

        # PHASE 1: Send instant acknowledgement for non-simple messages
        if not is_simple_message and needs_instant_ack:
            logger.info("📨 PHASE 1: Sending instant acknowledgement...")
            try:
                # Create a lightweight system prompt for instant ack
                ack_system_prompt = {
                    "role": "system",
                    "content": f"You are Iris, an AI assistant. The user just sent you: '{user_message_text[:100]}...'\n\n"
                               "Respond with a BRIEF (1-2 sentences) acknowledgement that you'll help them. "
                               "Be friendly and confirm what you understand they want. "
                               "Examples: 'I'll help you build that website! Let me start working on it.' or "
                               "'Got it! I'll create that presentation for you right away.'\n\n"
                               "Keep it SHORT - you'll provide the full response with details in a moment."
                }
                
                # Quick LLM call for acknowledgement (no tools, minimal tokens)
                ack_response = await self.thread_manager.run_thread(
                    thread_id=self.config.thread_id,
                    system_prompt=ack_system_prompt,
                    stream=self.config.stream,
                    llm_model=self.config.model_name,
                    llm_temperature=0.7,  # Slightly higher for natural responses
                    llm_max_tokens=150,  # Very short
                    tool_choice="none",  # No tools for instant ack
                    max_xml_tool_calls=0,
                    temporary_message=None,
                    processor_config=ProcessorConfig(
                        xml_tool_calling=False,
                        native_tool_calling=False,
                        execute_tools=False,
                        execute_on_stream=False,
                        tool_execution_strategy="parallel",
                        xml_adding_strategy="user_message"
                    ),
                    native_max_auto_continues=1,
                    include_xml_examples=False,
                    enable_thinking=False,
                    reasoning_effort='low',
                    enable_context_manager=False,  # Skip context management for speed
                    generation=None,
                    cache_metrics=None
                )
                
                # Stream the acknowledgement to user
                if hasattr(ack_response, '__aiter__'):
                    async for chunk in ack_response:
                        yield chunk
                
                logger.info("✅ PHASE 1 complete: Acknowledgement sent")
                
            except Exception as e:
                logger.error(f"Failed to send instant acknowledgement: {e}")
                # Continue to main response anyway
        
        # PHASE 2: Do the actual work with tools (or simple response for greetings)
        while continue_execution and iteration_count < self.config.max_iterations:
            iteration_count += 1

            can_run, message, reservation_id = await billing_integration.check_and_reserve_credits(self.account_id)
            if not can_run:
                error_msg = f"Insufficient credits: {message}"
                yield {
                    "type": "status",
                    "status": "stopped",
                    "message": error_msg
                }
                break

            latest_message = await self.client.table('messages').select('*').eq('thread_id', self.config.thread_id).in_('type', ['assistant', 'tool', 'user']).order('created_at', desc=True).limit(1).execute()
            if latest_message.data and len(latest_message.data) > 0:
                message_type = latest_message.data[0].get('type')
                if message_type == 'assistant':
                    continue_execution = False
                    break

            temporary_message = None
            max_tokens = self.get_max_tokens()
            logger.debug(f"max_tokens: {max_tokens}")
            
            # Log phase 2 start for complex messages
            if not is_simple_message:
                logger.info("🔧 PHASE 2: Starting tool execution and detailed response...")
            
            generation = self.config.trace.generation(name="thread_manager.run_thread") if self.config.trace else None
            try:
                cache_metrics = None
                from core.utils.llm_cache_utils import is_cache_supported, needs_cache_probe
                
                # DISABLED: Cache probe adds 1-2s latency per request
                # Only enable for debugging/monitoring when needed
                ENABLE_CACHE_PROBE = False  # Set to True only when you need cache metrics
                
                if ENABLE_CACHE_PROBE and self.config.stream and needs_cache_probe(self.config.model_name):
                    logger.info(f"🔍 Making cache probe for {self.config.model_name} (doesn't send cache metrics in streaming)...")
                    
                    try:
                        from core.services.llm import make_llm_api_call
                        existing_messages = await self.thread_manager.get_llm_messages(self.config.thread_id)
                        if existing_messages and len(existing_messages) > 0:
                            probe_messages = [system_message] + existing_messages[-4:]  # Last 4 messages
                        else:
                            probe_messages = [system_message]
                        
                        probe_messages.append({
                            "role": "user", 
                            "content": "."
                        })
                        
                        probe_response = await make_llm_api_call(
                            messages=probe_messages,
                            model_name=self.config.model_name,
                            temperature=0,
                            max_tokens=1,
                            stream=False
                        )
                        
                        if hasattr(probe_response, 'usage'):
                            usage = probe_response.usage
                            cache_creation = getattr(usage, 'cache_creation_input_tokens', 0)
                            cache_read = getattr(usage, 'cache_read_input_tokens', 0)
                            total_prompt = getattr(usage, 'prompt_tokens', 0)
                            
                            if cache_read > 0 or cache_creation > 0:
                                cache_percentage = (cache_read / total_prompt * 100) if total_prompt > 0 else 0
                                logger.info(f"✅ CACHE PROBE: {cache_read}/{total_prompt} tokens cached ({cache_percentage:.1f}%), {cache_creation} created")
                                
                                cache_metrics = {
                                    'cache_read_tokens': cache_read,
                                    'cache_creation_tokens': cache_creation,
                                    'cache_percentage': cache_percentage,
                                    'total_prompt_tokens': total_prompt
                                }
                            else:
                                logger.info(f"📊 CACHE PROBE: No cache activity (total prompt: {total_prompt} tokens)")
                                cache_metrics = {
                                    'cache_read_tokens': 0,
                                    'cache_creation_tokens': 0,
                                    'cache_percentage': 0,
                                    'total_prompt_tokens': total_prompt
                                }
                    
                    except Exception as e:
                        logger.warning(f"Cache probe failed (continuing with streaming): {e}")
                
                # Use fast path for simple messages (no tools, instant response)
                if is_simple_message:
                    response = await self.thread_manager.run_thread(
                        thread_id=self.config.thread_id,
                        system_prompt=system_message,
                        stream=self.config.stream,
                        llm_model=self.config.model_name,
                        llm_temperature=0,
                        llm_max_tokens=max_tokens,
                        tool_choice="none",  # No tools for simple messages
                        max_xml_tool_calls=0,  # Disable XML tools
                        temporary_message=temporary_message,
                        processor_config=ProcessorConfig(
                            xml_tool_calling=False,  # Disabled for speed
                            native_tool_calling=False,
                            execute_tools=False,  # No tool execution
                            execute_on_stream=False,
                            tool_execution_strategy="parallel",
                            xml_adding_strategy="user_message"
                        ),
                        native_max_auto_continues=1,  # Single response only
                        include_xml_examples=False,  # Skip examples for speed
                        enable_thinking=False,  # Skip thinking for greetings
                        reasoning_effort='low',
                        enable_context_manager=self.config.enable_context_manager,
                        generation=generation,
                        cache_metrics=cache_metrics
                    )
                else:
                    # Normal path with tools for complex messages
                    response = await self.thread_manager.run_thread(
                        thread_id=self.config.thread_id,
                        system_prompt=system_message,
                        stream=self.config.stream,
                        llm_model=self.config.model_name,
                        llm_temperature=0,
                        llm_max_tokens=max_tokens,
                        tool_choice="auto",
                        max_xml_tool_calls=1,
                        temporary_message=temporary_message,
                        processor_config=ProcessorConfig(
                            xml_tool_calling=True,
                            native_tool_calling=False,
                            execute_tools=True,
                            execute_on_stream=True,
                            tool_execution_strategy="parallel",
                            xml_adding_strategy="user_message"
                        ),
                        native_max_auto_continues=self.config.native_max_auto_continues,
                        include_xml_examples=True,
                        enable_thinking=self.config.enable_thinking,
                        reasoning_effort=self.config.reasoning_effort,
                        enable_context_manager=self.config.enable_context_manager,
                        generation=generation,
                        cache_metrics=cache_metrics
                    )

                if isinstance(response, dict) and "status" in response and response["status"] == "error":
                    yield response
                    break

                last_tool_call = None
                agent_should_terminate = False
                error_detected = False
                full_response = ""

                try:
                    if hasattr(response, '__aiter__') and not isinstance(response, dict):
                        async for chunk in response:
                            if isinstance(chunk, dict) and chunk.get('type') == 'status' and chunk.get('status') == 'error':
                                error_detected = True
                                yield chunk
                                continue
                            
                            if chunk.get('type') == 'status':
                                try:
                                    metadata = chunk.get('metadata', {})
                                    if isinstance(metadata, str):
                                        metadata = json.loads(metadata)
                                    
                                    if metadata.get('agent_should_terminate'):
                                        agent_should_terminate = True
                                        
                                        content = chunk.get('content', {})
                                        if isinstance(content, str):
                                            content = json.loads(content)
                                        
                                        if content.get('function_name'):
                                            last_tool_call = content['function_name']
                                        elif content.get('xml_tag_name'):
                                            last_tool_call = content['xml_tag_name']
                                            
                                except Exception:
                                    pass
                            
                            if chunk.get('type') == 'assistant' and 'content' in chunk:
                                try:
                                    content = chunk.get('content', '{}')
                                    if isinstance(content, str):
                                        assistant_content_json = json.loads(content)
                                    else:
                                        assistant_content_json = content

                                    assistant_text = assistant_content_json.get('content', '')
                                    full_response += assistant_text
                                    if isinstance(assistant_text, str):
                                        if '</ask>' in assistant_text or '</complete>' in assistant_text or '</web-browser-takeover>' in assistant_text:
                                           if '</ask>' in assistant_text:
                                               xml_tool = 'ask'
                                           elif '</complete>' in assistant_text:
                                               xml_tool = 'complete'
                                           elif '</web-browser-takeover>' in assistant_text:
                                               xml_tool = 'web-browser-takeover'

                                           last_tool_call = xml_tool
                                
                                except json.JSONDecodeError:
                                    pass
                                except Exception:
                                    pass

                            yield chunk
                    else:
                        error_detected = True

                    if error_detected:
                        if generation:
                            generation.end(output=full_response, status_message="error_detected", level="ERROR")
                        break
                        
                    if agent_should_terminate or last_tool_call in ['ask', 'complete', 'web-browser-takeover', 'present_presentation']:
                        if generation:
                            generation.end(output=full_response, status_message="agent_stopped")
                        continue_execution = False

                except Exception as e:
                    error_msg = f"Error during response streaming: {str(e)}"
                    if generation:
                        generation.end(output=full_response, status_message=error_msg, level="ERROR")
                    yield {
                        "type": "status",
                        "status": "error",
                        "message": error_msg
                    }
                    break
                    
            except Exception as e:
                error_msg = f"Error running thread: {str(e)}"
                yield {
                    "type": "status",
                    "status": "error",
                    "message": error_msg
                }
                break
            
            if generation:
                generation.end(output=full_response)

        asyncio.create_task(asyncio.to_thread(lambda: langfuse.flush()))


async def run_agent(
    thread_id: str,
    project_id: str,
    stream: bool,
    thread_manager: Optional[ThreadManager] = None,
    native_max_auto_continues: int = 25,
    max_iterations: int = 100,
    model_name: str = "gemini/gemini-2.5-flash",
    enable_thinking: Optional[bool] = False,
    reasoning_effort: Optional[str] = 'low',
    enable_context_manager: bool = True,
    agent_config: Optional[dict] = None,    
    trace: Optional[StatefulTraceClient] = None
):
    effective_model = model_manager.resolve_model_id(model_name) if model_name else "gemini/gemini-2.5-flash"
    if effective_model != model_name:
        logger.debug(f"Resolved agent model '{model_name}' -> '{effective_model}'")
    else:
        logger.debug(f"Using requested agent model: {effective_model}")
    
    config = AgentConfig(
        thread_id=thread_id,
        project_id=project_id,
        stream=stream,
        native_max_auto_continues=native_max_auto_continues,
        max_iterations=max_iterations,
        model_name=effective_model,
        enable_thinking=enable_thinking,
        reasoning_effort=reasoning_effort,
        enable_context_manager=enable_context_manager,
        agent_config=agent_config,
        trace=trace
    )
    
    runner = AgentRunner(config)
    async for chunk in runner.run():
        yield chunk
