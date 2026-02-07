"""
Retry Handler
Retry failed operations with exponential backoff
"""

import asyncio
import time
from typing import Callable, TypeVar, Optional
from functools import wraps

T = TypeVar('T')


class RetryHandler:
    """Handle retries with exponential backoff"""
    
    @staticmethod
    async def retry_async(
        func: Callable,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 30.0,
        exponential_base: float = 2.0,
        exceptions: tuple = (Exception,)
    ) -> Optional[T]:
        """
        Retry async function with exponential backoff
        
        Args:
            func: Async function to retry
            max_attempts: Maximum retry attempts
            base_delay: Initial delay in seconds
            max_delay: Maximum delay in seconds
            exponential_base: Exponential backoff multiplier
            exceptions: Tuple of exceptions to catch
            
        Returns:
            Function result or None if all attempts failed
        """
        last_exception = None
        
        for attempt in range(1, max_attempts + 1):
            try:
                return await func()
            except exceptions as e:
                last_exception = e
                
                if attempt == max_attempts:
                    print(f"\n❌ Max retry attempts ({max_attempts}) reached")
                    print(f"   Error: {e}")
                    return None
                
                # Calculate delay with exponential backoff
                delay = min(base_delay * (exponential_base ** (attempt - 1)), max_delay)
                
                print(f"\n⚠️  Attempt {attempt}/{max_attempts} failed: {e}")
                print(f"   Retrying in {delay:.1f}s...")
                
                await asyncio.sleep(delay)
        
        return None
    
    @staticmethod
    def retry_sync(
        func: Callable,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 30.0,
        exponential_base: float = 2.0,
        exceptions: tuple = (Exception,)
    ) -> Optional[T]:
        """
        Retry sync function with exponential backoff
        
        Args:
            func: Sync function to retry
            max_attempts: Maximum retry attempts
            base_delay: Initial delay in seconds
            max_delay: Maximum delay in seconds
            exponential_base: Exponential backoff multiplier
            exceptions: Tuple of exceptions to catch
            
        Returns:
            Function result or None if all attempts failed
        """
        last_exception = None
        
        for attempt in range(1, max_attempts + 1):
            try:
                return func()
            except exceptions as e:
                last_exception = e
                
                if attempt == max_attempts:
                    print(f"\n❌ Max retry attempts ({max_attempts}) reached")
                    print(f"   Error: {e}")
                    return None
                
                # Calculate delay with exponential backoff
                delay = min(base_delay * (exponential_base ** (attempt - 1)), max_delay)
                
                print(f"\n⚠️  Attempt {attempt}/{max_attempts} failed: {e}")
                print(f"   Retrying in {delay:.1f}s...")
                
                time.sleep(delay)
        
        return None


def with_retry(max_attempts: int = 3, base_delay: float = 1.0):
    """
    Decorator for automatic retry with exponential backoff
    
    Usage:
        @with_retry(max_attempts=3)
        async def my_function():
            ...
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            async def _func():
                return await func(*args, **kwargs)
            
            return await RetryHandler.retry_async(
                _func,
                max_attempts=max_attempts,
                base_delay=base_delay
            )
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            def _func():
                return func(*args, **kwargs)
            
            return RetryHandler.retry_sync(
                _func,
                max_attempts=max_attempts,
                base_delay=base_delay
            )
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator
