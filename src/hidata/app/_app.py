from hidata.app.runner.runner import AgentRunner
from agentscope_runtime.engine.app.agent_app import AgentApp
from fastapi import FastAPI
from contextlib import asynccontextmanager
import time

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
    startup_start_time = time.time()
    add_hidata_file_handler(WORKING_DIR / "hidata.log")
    await runner.start()

 # --- Model provider manager (non-reloadable, in-memory) ---
    provider_manager = ProviderManager.get_instance()

    app.state.runner = runner
    app.state.provider_manager = provider_manager



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
