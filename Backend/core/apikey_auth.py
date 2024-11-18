# Imports in auth.py file

from .config import settings

from fastapi.security.api_key import APIKeyHeader
from fastapi import Security, HTTPException, Depends
from starlette.status import HTTP_403_FORBIDDEN

api_key_header = APIKeyHeader(name="x-api-key", auto_error=False)

async def APIKeyAuth(api_key_header: str = Security(api_key_header)):
    """
    Authenticate the API provided with the header of the request. 
    """
    if api_key_header == settings.api_key:
        return api_key_header   
    else:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN, detail="Could not validate API KEY, Please provide a valid api key "
        )
