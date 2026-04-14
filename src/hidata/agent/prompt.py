import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Default fallback prompt
DEFAULT_SYS_PROMPT = """
You are a helpful assistant.
"""

# Backward compatibility alias
SYS_PROMPT = DEFAULT_SYS_PROMPT


class PromptConfig:
    """Configuration for system prompt building."""

    # Default files to load when no config is provided
    # All files are optional - if they don't exist, they'll be skipped
    DEFAULT_FILES = [
        "AGENTS.md",
        "SOUL.md",
        "PROFILE.md",
    ]

class PromptBuilder:
    """Builder for constructing system prompts from markdown files."""

    def __init__(
        self,
        working_dir: Path,
        enabled_files: list[str] | None = None,
    ):
        """Initialize prompt builder.

        Args:
            working_dir: Directory containing markdown configuration files
            enabled_files: List of filenames to load (if None, uses default order)
        """
        self.working_dir = working_dir
        self.enabled_files = enabled_files
        self.prompt_parts = []
        self.loaded_count = 0

    def _load_file(self, filename: str) -> None:
        """Load a single markdown file.

        All files are optional - if they don't exist or can't be read,
        they will be silently skipped.

        Args:
            filename: Name of the file to load
        """
        file_path = self.working_dir / filename

        if not file_path.exists():
            logger.debug("File %s not found, skipping", filename)
            return

        try:
            content = file_path.read_text(encoding="utf-8").strip()

            # Remove YAML frontmatter if present
            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    content = parts[2].strip()

            if content:
                if self.prompt_parts:  # Add separator if not first section
                    self.prompt_parts.append("")
                # Add section header with filename
                self.prompt_parts.append(f"# {filename}")
                self.prompt_parts.append("")
                self.prompt_parts.append(content)
                self.loaded_count += 1
                logger.debug("Loaded %s", filename)
            else:
                logger.debug("Skipped empty file: %s", filename)

        except Exception as e:
            logger.warning(
                "Failed to read file %s: %s, skipping",
                filename,
                e,
            )

    def build(self) -> str:
        """Build the system prompt from markdown files.

        All files are optional. If no files can be loaded, returns the default prompt.

        Returns:
            Constructed system prompt string
        """
        # Determine which files to load
        files_to_load = (
            PromptConfig.DEFAULT_FILES
            if self.enabled_files is None
            else self.enabled_files
        )

        # Load all files (all are optional)
        for filename in files_to_load:
            self._load_file(filename)

        if not self.prompt_parts:
            logger.warning("No content loaded from working directory")
            return DEFAULT_SYS_PROMPT

        # Join all parts with double newlines
        final_prompt = "\n\n".join(self.prompt_parts)

        logger.debug(
            "System prompt built from %d file(s), total length: %d chars",
            self.loaded_count,
            len(final_prompt),
        )

        return final_prompt



def build_system_prompt_from_working_dir() -> str:
    """
    从工作目录读取 Markdown 文件，构建系统提示词。

    本函数通过从 WORKING_DIR（默认 ~/.copaw）加载 Markdown 文件来组装系统提示词。
    这些文件用于定义智能体的行为、人格与操作规范。

    要加载的文件由配置项 agents.system_prompt_files 决定。
    若未配置，则回退到默认文件：
    - AGENTS.md — 详细工作流、规则与指引
    - SOUL.md — 核心身份与行为原则
    - PROFILE.md — 智能体身份与用户画像

    上述文件均为可选。若某文件不存在或无法读取，将跳过该文件。
    若最终没有任何文件可加载，则返回默认提示词。

    返回:
        str: 由 Markdown 文件拼接而成的系统提示词；若无可用文件，则为默认提示词。

    示例:
        若 working_dir 中存在 AGENTS.md、SOUL.md、PROFILE.md，将按序合并为：
        "# AGENTS.md\\n\\n...\\n\\n# SOUL.md\\n\\n...\\n\\n# PROFILE.md\\n\\n..."
    """
    from ..constant import WORKING_DIR
    from ..config import load_config

    # 从配置中读取要启用的文件列表
    config = load_config()
    enabled_files = (
        config.agents.system_prompt_files
        if config.agents.system_prompt_files is not None
        else None
    )

    builder = PromptBuilder(
        working_dir=Path(WORKING_DIR),
        enabled_files=enabled_files,
    )
    return builder.build()