import os
from pathlib import Path

class EnvVarLoader:
    """读取并解析环境变量的工具类（带类型转换、默认值与边界保护）。"""

    @staticmethod
    def get_bool(env_var: str, default: bool = False) -> bool:
        """读取布尔型环境变量（支持 true/1/yes 等常见真值）。"""
        val = os.environ.get(env_var, str(default)).lower()
        return val in ("true", "1", "yes")

    @staticmethod
    def get_float(
        env_var: str,
        default: float = 0.0,
        min_value: float | None = None,
        max_value: float | None = None,
        allow_inf: bool = False,
    ) -> float:
        """读取浮点型环境变量（可选上下界裁剪；可禁用无穷值）。"""
        try:
            value = float(os.environ.get(env_var, str(default)))
            if min_value is not None and value < min_value:
                return min_value
            if max_value is not None and value > max_value:
                return max_value
            if not allow_inf and (
                value == float("inf") or value == float("-inf")
            ):
                return default
            return value
        except (TypeError, ValueError):
            return default

    @staticmethod
    def get_int(
        env_var: str,
        default: int = 0,
        min_value: int | None = None,
        max_value: int | None = None,
    ) -> int:
        """读取整型环境变量（可选上下界裁剪）。"""
        try:
            value = int(os.environ.get(env_var, str(default)))
            if min_value is not None and value < min_value:
                return min_value
            if max_value is not None and value > max_value:
                return max_value
            return value
        except (TypeError, ValueError):
            return default

    @staticmethod
    def get_str(env_var: str, default: str = "") -> str:
        """读取字符串环境变量（空缺时回退到默认值）。"""
        return os.environ.get(env_var, default)



# 工作目录：默认写入到用户目录下的 ~/.hidata，可用 HIDATA_WORKING_DIR 覆盖
WORKING_DIR = (
    Path(EnvVarLoader.get_str("HIDATA_WORKING_DIR", "~/.hidata"))
    .expanduser()
    .resolve()
)

SECRET_DIR = (
    Path(
        EnvVarLoader.get_str(
            "COPAW_SECRET_DIR",
            f"{WORKING_DIR}.secret",
        ),
    )
    .expanduser()
    .resolve()
)


# Skills 目录约定
# 已启用的 skills（agent 会从这里加载）
ACTIVE_SKILLS_DIR = WORKING_DIR / "active_skills"