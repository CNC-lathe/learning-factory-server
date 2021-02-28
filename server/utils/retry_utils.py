from typing import Any, Callable, Tuple, Union
import time

def retry(
        retry_callable: Callable,
        *args: Any,
        retries: int = 3,
        cooldown: float = 0.5,
        handled_exceptions: Union[Tuple[Exception], Exception] = Exception,
        **kwargs: Any
) -> Any:
    """Retry calling <retry_callable> with *args, **kwargs up to <num_retries> times,
    with <cooldown> seconds in between

    Parameters
    ----------
    retry_callable : Callable
        callable to retry calling with
    *args : Any
        args to pass to callable
    retries : int, optional
        number of times to retry calling callable, by default 3
    cooldown : float, optional
        time to wait between calling callable, in seconds, by default 0.5
    handled_exceptions: Union[Tuple[Exception], Exception], optional
        tuple of exceptions to handle (other exceptions will NOT be caught)
    **kwargs : Any
        keyword args to pass to callable

    Returns
    -------
    Any
        returned object from calling callable
    """
    # loop for <retries> times
    while (retries := retries - 1) >= 0:
        try:
            # call retry_callable with args, kwargs
            return retry_callable(*args, **kwargs)

        # catch exception, if one of handled_exceptions
        except handled_exceptions as err:
            # sleep between retries
            if retries > 0:
                time.sleep(cooldown)

            # throw exception if retries are up
            else:
                raise err
