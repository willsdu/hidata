from hidata.app.runner.runner import AgentRunner
from agentscope_runtime.engine.app.agent_app import AgentApp
from fastapi import FastAPI
from contextlib import asynccontextmanager
import time
from dotenv import load_dotenv
from hidata.app.routers import router as api_router
from pathlib import Path
import os
from fastapi import HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import logging

from hidata.constant import WORKING_DIR
from hidata.utils.logging import add_hidata_file_handler
from hidata.constant import DOCS_ENABLED
from hidata.__version__ import __version__
from hidata.providers.provider_manager import ProviderManager

load_dotenv()

logger = logging.getLogger(__name__)

runner = AgentRunner()

agent_app = AgentApp(
    app_name="Friday",
    app_description="A helpful assistant",
    runner=runner,
)



@asynccontextmanager
async def lifespan(
    app: FastAPI,
):  # pylint: disable=too-many-statements,too-many-branches
    _startup_start_time = time.time()
    # Load .env so server process can read OPENAI_* config.
    load_dotenv(override=False)
    add_hidata_file_handler(WORKING_DIR / "hidata.log")
    await runner.start()

    # --- Model provider manager (non-reloadable, in-memory) ---
    provider_manager = ProviderManager.get_instance()

    app.state.runner = runner
    app.state.provider_manager = provider_manager

    try:
        yield
    finally:
        # Best-effort shutdown. Runner API differs by framework/runtime version,
        # so guard calls to avoid masking the original exception.
        stop = getattr(runner, "stop", None)
        if callable(stop):
            try:
                res = stop()
                if hasattr(res, "__await__"):
                    await res
            except Exception:
                pass
        shutdown = getattr(runner, "shutdown", None)
        if callable(shutdown):
            try:
                res = shutdown()
                if hasattr(res, "__await__"):
                    await res
            except Exception:
                pass



app = FastAPI(
    lifespan=lifespan,
    docs_url="/docs" if DOCS_ENABLED else None,
    redoc_url="/redoc" if DOCS_ENABLED else None,
    openapi_url="/openapi.json" if DOCS_ENABLED else None,
)

@app.get("/api/version")
def get_version():
    """Return the current HiData version."""
    return {"version": __version__}


app.include_router(api_router, prefix="/api")

app.include_router(
    agent_app.router,
    prefix="/api/agent",
    tags=["agent"],
)

# 控制台静态目录解析策略：优先 `env`，其次是打包后的 `copaw` 资源（`console`），最后回退到 `cwd`。
_CONSOLE_STATIC_ENV = "HIDATA_CONSOLE_STATIC_DIR"

def _resolve_console_static_dir() -> Path:
    """解析 Web 控制台静态资源目录。

    优先级顺序：
    1. `COPAW_CONSOLE_STATIC_DIR` 环境变量（显式覆盖）
    2. 已打包发行版中的 `copaw/console` 目录
    3. 本地工作目录的兜底路径（开发/构建产物）
    """
    if os.environ.get(_CONSOLE_STATIC_ENV):
        return os.environ.get(_CONSOLE_STATIC_ENV)
    pkg_dir = Path(__file__).resolve().parent.parent
    candidate_dir=pkg_dir / "console" 
    if candidate_dir.is_dir() and (candidate_dir / "index.html").exists():
        return str(candidate_dir)
    # 兼容/兜底逻辑：下一次发布后预计可移除
    # （因为届时 `vite` 会直接把 console 输出到 `src/copaw/console/` 目录）。 
    cwd = Path(os.getcwd())
    for subdir in ("console/dist", "console_dist"):
        candidate = cwd / subdir
        if candidate.is_dir() and (candidate / "index.html").exists():
            return str(candidate)
    return str(cwd / "console" / "dist")

_CONSOLE_STATIC_DIR = _resolve_console_static_dir()
_CONSOLE_INDEX = (
    Path(_CONSOLE_STATIC_DIR) / "index.html" if _CONSOLE_STATIC_DIR else None
)
logger.info(f"STATIC_DIR: {_CONSOLE_STATIC_DIR}")

@app.get("/")
def read_root():
    if _CONSOLE_INDEX and _CONSOLE_INDEX.exists():
        return FileResponse(_CONSOLE_INDEX)
    return {
          "message": (
            "HiData Web Console is not available. "
            "If you installed HiData from source code, please run "
            "`npm ci && npm run build` in HiData's `console/` "
            "directory, and restart HiData to enable the web console."
        ),
    }

# 挂载控制台静态资源：
# - 单个静态文件（logo/icon）
# - 将 `/assets/*` 挂载为专用静态目录
# - SPA 回退路由（`/{full_path:path}` -> `index.html`）
if os.path.isdir(_CONSOLE_STATIC_DIR):
    _console_path = Path(_CONSOLE_STATIC_DIR)
    
    @app.get("/logo.png")
    def _console_logo():
        f = _console_path / "logo.png"
        if f.is_file():
            return FileResponse(f, media_type="image/png")

        return HTTPException(status_code=404, detail="Not Found")

    @app.get("/copaw-symbol.svg")
    def _console_icon():
        f = _console_path / "copaw-symbol.svg"
        if f.is_file():
            return FileResponse(f, media_type="image/svg+xml")

        raise HTTPException(status_code=404, detail="Not Found")

    _assets_dir = _console_path / "assets"
    if _assets_dir.is_dir():
        app.mount(
            "/assets",
            StaticFiles(directory=str(_assets_dir)),
            name="assets",
        )

    @app.get("/{full_path:path}")
    def _console_spa(full_path: str):
        if _CONSOLE_INDEX and _CONSOLE_INDEX.exists():
            return FileResponse(_CONSOLE_INDEX)

        raise HTTPException(status_code=404, detail="Not Found")