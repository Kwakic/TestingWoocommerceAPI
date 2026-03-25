from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class RequestContext:
    method: str
    url: str
    headers: Optional[Dict[str, str]] = None
    params: Optional[Dict[str, Any]] = None
    json: Optional[Dict[str, Any]] = None
