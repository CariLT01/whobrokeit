import random
import json
from enum import IntEnum
from core.types.mod_unit import ModUnitInfo
from core.test.broken_mod_test import BrokenModTest
from core.test.conflict_dependency_test import ConflictDependencyTest
from rich.prompt import Prompt

class TestType(IntEnum):
    NONE = 0
    SINGLE = 1
    MULTI = 2

class TestDispatcher:
    
    def __init__(self, units: list[ModUnitInfo]):
        
        self.test_mode: TestType = TestType.NONE
        
        # get choice
        test_mode = Prompt.ask(
            prompt="Choose testing mode",
            choices=["single", "multi"]
        )
        
        if test_mode == "single":
            self.test_mode = TestType.SINGLE
        elif test_mode == "multi":
            self.test_mode = TestType.MULTI
        else:
            raise ValueError(f"Unrecognized test type: {test_mode}")
        
        self.units = units
        
        if self.test_mode == TestType.SINGLE:
            
            # choose random mod
            random_mod = random.choice(self.units)
            
            print(f"Chosen failing unit: {json.dumps(random_mod, indent=4)}")
            
            self.tester = BrokenModTest(random_mod)
        
        elif self.test_mode == TestType.MULTI:
            
            k = int(input("test: k = "))
            random_mods = random.choices(self.units, k=k)
            
            print(f"Chosen minimal failing set: {json.dumps(random_mods, indent=4)}")
            
            self.tester = ConflictDependencyTest(random_mods)
        
        else:
            raise ValueError(f"Unrecognized test type: {self.test_mode}")
        
    def test(self, current_units: list[ModUnitInfo]) -> bool:
        return self.tester.test(current_units)
        
        
        
        