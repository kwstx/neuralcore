import time
import random
import asyncio
from typing import Callable, Any, Type, Union

def exponential_backoff_with_jitter(
    attempt: int,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    jitter: bool = True
) -> float:
    """
    Calculates the delay for the next retry using exponential backoff with jitter.
    """
    delay = min(max_delay, base_delay * (2 ** attempt))
    if jitter:
        delay = random.uniform(0, delay)
    return delay

async def retry_with_backoff(
    func: Callable[..., Any],
    *args,
    max_retries: int = 5,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    retry_on: Union[Type[Exception], tuple[Type[Exception], ...]] = Exception,
    **kwargs
) -> Any:
    """
    Executes a function with retry logic governed by exponential backoff and jitter.
    """
    for attempt in range(max_retries):
        try:
            return await func(*args, **kwargs)
        except retry_on as e:
            if attempt == max_retries - 1:
                raise e
            
            delay = exponential_backoff_with_jitter(attempt, base_delay, max_delay)
            await asyncio.sleep(delay)
