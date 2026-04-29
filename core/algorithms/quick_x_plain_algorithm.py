from typing import Callable, TypedDict, cast, Any
from enum import StrEnum
import json

from core.algorithms.isolation_algorithm import IsolationAlgorithm
from core.types.mod_unit import ModUnitInfo


# Enums and types
class IsolationStage(StrEnum):
    SPLIT = "split"
    AFTER_S1 = "after_s1"
    AFTER_S2 = "after_s2"


class StackFrame(TypedDict):
    delta: list[str]
    bg: list[str]
    suspect: list[str]
    stage: IsolationStage
    s1: list[str]
    s2: list[str]
    delta2: list[str]


class SaveState(TypedDict):

    cache: dict[str, bool]
    stack: list[StackFrame]
    results: list[list[str]]


class QuickXPlainIsolation(IsolationAlgorithm):
    """
    Implements the QuickXPlain algorithm
    for quickly finding the minimal failing
    subset of units able to reproduce the
    issue.
    """

    def __init__(self, save_func: Callable[[Any], None]):

        self.all_units: dict[str, ModUnitInfo] = {}
        self.test_func = None
        self.cache: dict[frozenset[str], bool] = {}
        self.stack: list[StackFrame] = []
        self.results: list[list[str]] = []
        self.save_func = save_func

    def _compute_dependency_depth(self, units: list[ModUnitInfo]) -> dict[str, int]:
        # Map root_jar -> unit
        jar_to_unit = {u["root_jar"]: u for u in units}
        # Build graph: dependent -> list of dependency root_jars
        graph = {}
        for u in units:
            dep_roots = []
            for jar in u.get("jars", []):
                if jar in jar_to_unit and jar != u["root_jar"]:
                    dep_roots.append(jar)
            graph[u["root_jar"]] = dep_roots

        # Compute depth (distance to farthest leaf)
        depth = {}
        def dfs(node):
            if node in depth:
                return depth[node]
            deps = graph.get(node, [])
            if not deps:
                depth[node] = 0
                return 0
            max_dep_depth = max((dfs(dep) for dep in deps), default=-1)
            depth[node] = max_dep_depth + 1
            return depth[node]

        for node in graph:
            dfs(node)
        return depth

    def run(
        self,
        units: list[ModUnitInfo],
        test_function: Callable[[list[ModUnitInfo]], bool],
        load_state: Any | None,
    ):

        depth_map = self._compute_dependency_depth(units)
        sorted_units = sorted(units, key=lambda u: (depth_map.get(u["root_jar"], 0), u["root_jar"]))
        self.all_units = {unit["root_jar"]: unit for unit in sorted_units}
        self.test_func = test_function
        self.cache: dict[frozenset[str], bool] = {}
        self.stack: list[StackFrame] = []
        self.results: list[list[str]] = []
        
        print(f"QXP received an initial input size of: {len(units)}")

        results = self.qxp_run(load_state)

        return results

    def _serialize_cache(self):

        cache_data = {json.dumps(sorted(list(k))): v for k, v in self.cache.items()}

        return cache_data

    def _deserialize_cache(self, data: dict[str, bool]) -> dict[frozenset[str], bool]:
        return {frozenset(json.loads(k)): v for k, v in data.items()}

    def save_state(self) -> None:

        state: SaveState = {
            "cache": self._serialize_cache(),
            "stack": self.stack,
            "results": self.results,
        }

        self.save_func(state)

    def load_state(self, data: SaveState | None) -> bool:

        if data is None:
            return False

        self.cache = self._deserialize_cache(data["cache"])
        self.stack = data["stack"]
        self.results = data["results"]

        return True

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

    def qxp_run(self, loaded_state: SaveState | None):

        if not self.load_state(loaded_state):
            all_ids: list[str] = list(self.all_units.keys())

            # Skip preminilary check of checking all units to
            # verify there is a conflict

            initial_frame: StackFrame = {
                "delta": all_ids,
                "bg": [],
                "suspect": all_ids,
                "stage": IsolationStage.SPLIT,
                "delta2": [],
                "s1": [],
                "s2": [],
            }
            self.stack.append(initial_frame)

        while self.stack:
            current: StackFrame = self.stack[-1]
            stage: IsolationStage = current["stage"]

            if current["delta"] and not self._execute_test(current["bg"]):
                self.stack.pop()
                self.results.append([])
                continue

            if self._execute_test(current["bg"] + current["delta"]):
                self.stack.pop()
                self.results.append([])
                continue

            if len(current["suspect"]) == 1:
                self.stack.pop()
                self.results.append(current["suspect"])
                continue

            if stage == IsolationStage.SPLIT:
                k = len(current["suspect"]) // 2
                s1, s2 = current["suspect"][:k], current["suspect"][k:]
                current["s1"], current["s2"] = s1, s2
                current["stage"] = IsolationStage.AFTER_S2

                self.stack.append(
                    {
                        "delta": s2,
                        "bg": current["bg"] + s1,
                        "suspect": s2,
                        "stage": IsolationStage.SPLIT,
                        "delta2": [],
                        "s1": [],
                        "s2": [],
                    }
                )
                continue

            elif stage == IsolationStage.AFTER_S2:
                delta2: list[str] = self.results.pop()
                current["delta2"] = delta2
                current["stage"] = IsolationStage.AFTER_S1
                self.stack.append(
                    {
                        "delta": current["s1"],
                        "bg": current["bg"] + delta2,
                        "suspect": current["s1"],
                        "stage": IsolationStage.SPLIT,
                        "delta2": [],
                        "s1": [],
                        "s2": [],
                    }
                )
                continue

            elif stage == IsolationStage.AFTER_S1:
                delta1: list[str] = self.results.pop()
                self.stack.pop()

                self.results.append(delta1 + current["delta2"])

        return [self.all_units[uid] for uid in self.results[0]]
