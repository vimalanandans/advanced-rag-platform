import os
from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from rag_workbench.contracts import RequestContext
from rag_workbench.evaluation import evaluate, load_cases
from rag_workbench.graph import GraphValidationError, pipeline_from_yaml
from rag_workbench.observability import trace_store_from_environment
from rag_workbench.runtime import demo_runtime

app = FastAPI(title="RAG Engineering Workbench", version="0.1.0")
allowed_origins = [origin.strip() for origin in os.environ.get("RAG_WORKBENCH_CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",") if origin.strip()]
app.add_middleware(CORSMiddleware, allow_origins=allowed_origins, allow_credentials=False, allow_methods=["GET", "POST", "OPTIONS"], allow_headers=["Content-Type", "X-Tenant-Id", "X-User-Id", "X-Local-Admin-Token"])
runtime = demo_runtime(trace_store=trace_store_from_environment())
PIPELINE_PATH = Path(__file__).parent.parent / "configs" / "pipelines" / ("local-real.yaml" if os.environ.get("RAG_WORKBENCH_PROFILE") == "local-real" else "baseline.yaml")


class RunRequest(BaseModel):
    question: str


def request_context(
    x_tenant_id: str = Header(...), x_user_id: str = Header(...),
    x_local_admin_token: str = Header(...),
) -> RequestContext:
    expected = os.environ.get("RAG_WORKBENCH_LOCAL_ADMIN_TOKEN", "local-development-token")
    if x_local_admin_token != expected:
        raise HTTPException(status_code=401, detail="invalid local-admin token")
    if x_user_id != "local-admin":
        raise HTTPException(status_code=403, detail="only the configured local administrator is permitted")
    return RequestContext(tenant_id=x_tenant_id, user_id=x_user_id)


AuthenticatedRequest = Annotated[RequestContext, Depends(request_context)]


def _plan():
    return runtime.compile(pipeline_from_yaml(PIPELINE_PATH.read_text()))


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "mode": "local-first"}


@app.get("/components")
def components():
    return runtime.registry.list()


@app.post("/pipelines/validate")
def validate_pipeline(_context: AuthenticatedRequest):
    try:
        plan = _plan()
        return {"valid": True, "fingerprint": plan.fingerprint, "execution_order": plan.order}
    except GraphValidationError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@app.post("/runs")
def run_pipeline(request: RunRequest, context: AuthenticatedRequest):
    return runtime.run(_plan(), request.question, context)


@app.get("/runs")
def list_runs(context: AuthenticatedRequest):
    return [run for run in runtime.trace_store.list() if run.tenant_id == context.tenant_id and run.user_id == context.user_id]


@app.get("/runs/{run_id}")
def get_run(run_id: str, context: AuthenticatedRequest):
    try:
        run = runtime.trace_store.get(run_id)
        if run.tenant_id != context.tenant_id or run.user_id != context.user_id:
            raise HTTPException(status_code=404, detail="run not found")
        return run
    except KeyError as error:
        raise HTTPException(status_code=404, detail="run not found") from error


@app.post("/evaluations/baseline")
def evaluate_baseline(context: AuthenticatedRequest):
    golden = Path(__file__).parent.parent / "data" / "golden" / "baseline.json"
    plan = _plan()
    if plan.pipeline.tenant_id != context.tenant_id:
        raise HTTPException(status_code=404, detail="pipeline not found")
    return evaluate(runtime, plan, load_cases(golden))
