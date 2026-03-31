import logging



logger = logging.getLogger(__name__)


class HidataAgent:

    
    def _build_sys_prompt(self) -> str:
        """Build system prompt from working dir files and env context.

        Returns:
            Complete system prompt string
        """
        return f"""You are a helpful assistant. """