from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

api_key_scheme = HTTPBearer()


def verify_api_key(
    credentials: HTTPAuthorizationCredentials = Depends(api_key_scheme),
) -> str:
    """
    Verify Bearer token and extract node_id.
    Format: sk-{node_id}-2026
    
    Simple approach: just extract the node_id from the token.
    """
    token = credentials.credentials
    
    # Expected format: sk-{node_id}-2026
    if not token.startswith("sk-"):
        raise HTTPException(status_code=401, detail="Invalid token format")
    
    try:
        # Remove "sk-" prefix and "-2026" suffix
        node_id = token.replace("sk-", "").replace("-2026", "")
        
        if not node_id or len(node_id) < 2:
            raise HTTPException(status_code=401, detail="Invalid token format")
        
        return node_id
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token format")