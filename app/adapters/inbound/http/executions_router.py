from fastapi import APIRouter, Depends, Request

router = APIRouter(prefix="/executions", tags=["executions"])


def _repo(request: Request):
    return request.app.state.container.execution_repo


@router.get("/flow")
async def get_session_flow(session_id: str, repo=Depends(_repo)):
    """
    Returns all executions for a session in order, annotated with
    the incoming edge (that led to the node) and the outgoing edge
    (that will lead to the next node).
    """
    return await repo.get_session_flow(session_id)
