import logging

from typing import Literal, Optional
from agentscope.memory import InMemoryMemory
from agentscope.tool import Toolkit
from agentscope.agent import ReActAgent

from hidata.model_factory import create_model_and_formatter

from hidata.agent.prompt import build_system_prompt_from_working_dir

from ..config.util import load_config

from .skills_manager import (
    get_working_skills_dir,
    list_available_skills,
) 

from .tools import (
    browser_use,
    desktop_screenshot,
    edit_file,
    execute_shell_command,
    get_current_time,
    get_token_usage,
    read_file,
    send_file_to_user,
    write_file,
    create_memory_search_tool,  
)

logger = logging.getLogger(__name__)

# Valid namesake strategies for tool registration
NamesakeStrategy = Literal["override", "skip", "raise", "rename"]


class HidataAgent(ReActAgent):
    def __init__(
        self,
        env_context: Optional[str] = None,
        namesake_strategy: NamesakeStrategy ="skip",
        max_iters: int = 50
        ):
        self._env_context = env_context
        self._namesake_strategy = namesake_strategy

        # Initialize toolkit with built-in tools
        toolkit = self._create_toolkit(namesake_strategy=namesake_strategy)

        # register skills
        self._register_skills(toolkit)

        model, formatter = create_model_and_formatter()

        # build system prompt
        sys_prompt = self._build_sys_prompt()

        super().__init__(
            name="HidataAgent",
            model=model,
            system_prompt=sys_prompt,
            toolkit=toolkit,
            memory= InMemoryMemory(),
            formatter=formatter,
            max_iters=max_iters,
        )
    
    def _build_sys_prompt(self) -> str:
        """Build system prompt from working dir files and env context.

        Returns:
            Complete system prompt string
        """
        sys_prompt =  build_system_prompt_from_working_dir()
        if self._env_context is not None:
            sys_prompt = self._env_context + "\n\n" + sys_prompt
        return sys_prompt
    

    def _create_toolkit(self, namesake_strategy: NamesakeStrategy) -> Toolkit:
        """Create and populate toolkit with built-in tools.

        Args:
            namesake_strategy: Strategy to handle namesake tool functions.
                Options: "override", "skip", "raise", "rename"
                (default: "skip")

        Returns:
            Configured toolkit instance
        """
        toolkit = Toolkit()

        config=load_config()
        enabled_tools = {}
        if hasattr(config, "tools") and hasattr(config.tools, "builtin_tools"):
            enabled_tools = {
                name: tool_config.enabled
                for name, tool_config in config.tools.buiildin_tools.items()
            }
        
        # Map of tool functions
        tool_functions = {
            "execute_shell_command": execute_shell_command,
            "read_file": read_file,
            "write_file": write_file,
            "edit_file": edit_file,
            "browser_use": browser_use,
            "desktop_screenshot": desktop_screenshot,
            "send_file_to_user": send_file_to_user,
            "get_current_time": get_current_time,
            "get_token_usage": get_token_usage,
        }

        # Register tools
        for tool_name,tool_func in tool_functions.items():
            if enabled_tools.get(tool_name, True):
                toolkit.register_tool_function(
                    tool_func,
                    namesake_strategy=namesake_strategy,
                )
                logger.debug("Registered tool: %s", tool_name)
            else:
                logger.debug("Skipped tool: %s", tool_name)

        return toolkit



    def _register_skills(self, toolkit: Toolkit) -> None:
        """
        Register skills from working dir files and env context.
        
        Returns:
            None
        """
        working_skills_dir= get_working_skills_dir()
        available_skills = list_available_skills()

        for skill_name in available_skills:
            skill_dir = working_skills_dir / skill_name
            if skill_dir.exists():
                try:
                    toolkit.register_agent_skill(str(skill_dir))
                    logger.debug("Registered skill: %s", skill_name)
                except Exception as e:
                    logger.warning(f"Failed to register skill {skill_name}: {e}")
                    continue
