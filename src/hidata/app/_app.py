from hidata.app.runner.runner import AgentRunner
from agentscope_runtime.engine.app.agent_app import AgentApp
from fastapi import FastAPI
from contextlib import asynccontextmanager
import time
from dotenv import load_dotenv

from hidata.constant import WORKING_DIR
from hidata.utils.logging import add_hidata_file_handler
from hidata.constant import DOCS_ENABLED
from hidata.__version__ import __version__
from hidata.providers.provider_manager import ProviderManager

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


app.include_router(
    agent_app.router,
    prefix="/api/agent",
    tags=["agent"],
)
