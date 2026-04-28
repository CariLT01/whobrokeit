from abc import ABC, abstractmethod
from typing import Callable, Any


class IsolationAlgorithm[T](ABC):

    def __init__(self):
        pass

    @abstractmethod
    def run(
        self,
        units: list[T],
        test_function: Callable[[list[T]], bool],
        load_state: Any | None,
    ) -> list[T]:
        pass

    @abstractmethod
    def save_state(self) -> None:
        pass

    @abstractmethod
    def load_state(self, data: Any) -> bool:
        pass
