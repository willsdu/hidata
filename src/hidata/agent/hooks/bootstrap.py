import  logging
from pathlib import Path

logger = logging.getLogger(__name__)


class BootstrapHook:
    def __init__(
        self,
        working_dir: Path,
        language:str="zh",
    ):
        self.working_dir = working_dir
        self.language = language