from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from ..services.clickhouse import ch_service

api_key_scheme = HTTPBearer()


def verify_api_key(
    credentials: HTTPAuthorizationCredentials = Depends(api_key_scheme),
) -> str:
    """
    Validate the Bearer API key sent by a daemon.
    Returns the node_id associated with the key, or raises 401.
    """
    node_id = ch_service.verify_api_key(credentials.credentials)
    if not node_id:
        raise HTTPException(status_code=401, detail="Invalid or unknown API key")
    return node_id
