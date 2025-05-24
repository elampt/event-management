from pydantic import BaseModel
# from pydantic.generics import GenericModel
from typing import Any, Optional, TypeVar, Generic

T = TypeVar('T')

class APIResponse(BaseModel, Generic[T]):
    success: bool
    message: str
    data: Optional[Any] = None