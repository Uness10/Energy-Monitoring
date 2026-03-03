from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from ..services.clickhouse import ch_service

api_key_scheme = HTTPBearer()


def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(api_key_scheme)) -> str:
    """
    Validates the API key from the Authorization header.
    Returns the node_id associated with the key.
    """
    api_key = credentials.credentials
    # Look up which node owns this API key
    nodes = ch_service.client.query(
        "SELECT node_id FROM nodes WHERE api_key = {key:String}",
        parameters={"key": api_key},
    )
    if not nodes.result_rows:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return nodes.result_rows[0][0]
