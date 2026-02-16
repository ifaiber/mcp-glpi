"""
Decoradores para GLPI Wrapper.
"""

import time
from functools import wraps
from typing import Callable, TypeVar
import logging

import requests
from ..exceptions import GLPIRequestError

T = TypeVar('T')
logger = logging.getLogger(__name__)


def retry_on_failure(max_retries: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """Decorator para reintentar operaciones fallidas.
    
    Parameters
    ----------
    max_retries : int, default 3
        Número máximo de reintentos
    delay : float, default 1.0
        Tiempo de espera inicial entre reintentos
    backoff : float, default 2.0
        Factor de multiplicación para el delay en cada intento
        
    Returns
    -------
    Callable
        El decorator configurado
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except (requests.RequestException, GLPIRequestError) as e:
                    last_exception = e
                    if attempt == max_retries - 1:
                        break
                    sleep_time = delay * (backoff ** attempt)
                    logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {sleep_time:.1f}s")
                    time.sleep(sleep_time)
            raise last_exception
        return wrapper
    return decorator