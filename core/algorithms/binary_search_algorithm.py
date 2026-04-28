import json
from typing import Callable, Any, TypedDict, cast
from core.algorithms.isolation_algorithm import IsolationAlgorithm
from core.types.mod_unit import ModUnitInfo


class SaveState(TypedDict):
    current: list[str]
    candidate: list[str]
    stack: list[list[str]]
    cache: dict[str, bool]


class BinarySearchIsolation(IsolationAlgorithm):

    def __init__(self, save_func: Callable[[Any], None]):
        self.save_func = save_func
        self.cache: dict[frozenset[str], bool] = {}

        self.candidate: list[str] = []
        self.current: list[str] = []
        self.stack: list[list[str]] = []
        self.all_units: dict[str, ModUnitInfo] = {}  # maps ID to unit
        self.test_func: Callable[[list[ModUnitInfo]], bool]

    def run(
        self,
        units: list[ModUnitInfo],
        test_function: Callable[[list[ModUnitInfo]], bool],
        load_state: Any | None,
    ) -> list[ModUnitInfo]:

        self.load_state(load_state)

        self.test_func = test_function
        self.all_units = {unit["root_jar"]: unit for unit in units}

        suspect_units = self._binary_isolate()
        suspect_units_items = [self.all_units[k] for k in suspect_units]
        return suspect_units_items

    def _serialize_cache(self):
        cache_data = {json.dumps(sorted(list(k))): v for k, v in self.cache.items()}
        return cache_data

    def _deserialize_cache(self, data: dict[str, bool]) -> dict[frozenset[str], bool]:
        return {frozenset(json.loads(k)): v for k, v in data.items()}

    def load_state(self, data: SaveState | None) -> bool:
        if data is None:
            return False

        self.cache = self._deserialize_cache(data["cache"])
        self.candidate = data["candidate"]
        self.current = data["current"]

        return True

    def save_state(self) -> None:

        state: SaveState = {
            "cache": self._serialize_cache(),
            "candidate": self.candidate,
            "current": self.current,
            "stack": self.stack,
        }

        self.save_func(state)

    def _execute_test(self, unit_ids: list[str]) -> bool:
        """
        A wrapper for the expensive test_func, in order to perform cache lookup first.
        """

        assert self.test_func is not None

        key: frozenset[str] = frozenset(unit_ids)
        if key in self.cache:
            return cast(bool, self.cache[key])

        units_to_test: list[ModUnitInfo] = [self.all_units[uid] for uid in unit_ids]
        result: bool = self.test_func(units_to_test)

        self.cache[key] = result
        self.save_state()

        return result

    def _binary_isolate(self) -> list[str]:

        if len(self.all_units.keys()) <= 2:
            return list(self.all_units.keys())

        self.stack = [list(self.all_units.keys())]

        while self.stack:

            current_value = self.stack.pop()
            self.current = current_value

            if len(current_value) <= 2:
                return current_value

            mid = len(current_value) // 2
            left = current_value[:mid]
            right = current_value[mid:]

            left_result = self._execute_test(left)
            right_result = self._execute_test(right)

            if not left_result and right_result:
                self.stack.append(left)
                continue

            if left_result and not right_result:
                self.stack.append(right)
                continue

            # Unknown structure, stop search
            return self.current

        return list(self.all_units.keys())
