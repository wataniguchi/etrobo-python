from typing import Any, Callable, List, Tuple

from .connector import connect_simulator


def create_dispatcher(
    devices: List[Tuple[str, Any]],
    handlers: List[Callable[..., None]],
    interval: float = 0.01,
    course: str = 'left',
    debug: bool = False,
) -> Any:
    return Dispatcher(
        devices=devices,
        handlers=handlers,
        interval=interval,
        course=course,
        debug=debug,
    )


class Dispatcher(object):
    def __init__(
        self,
        devices: List[Tuple[str, Any]],
        handlers: List[Callable[..., None]],
        interval: float = 0.01,
        course: str = 'left',
        debug: bool = False,
    ) -> None:
        self.devices = devices
        self.handlers = handlers
        self.interval = interval
        self.course = course
        self.debug = debug

    def dispatch(self) -> None:
        variables = {name: device for name, device in self.devices}

        def hook():
            for handler in self.handlers:
                handler(**variables)

        connect_simulator(
            course=self.course,
            interval=self.interval,
            hook=hook)
