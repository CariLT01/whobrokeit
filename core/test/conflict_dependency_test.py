from core.types.mod_unit import ModUnitInfo

class ConflictDependencyTest():
    
    def __init__(self, conflicts: list[ModUnitInfo]):
        self.conflicts: set[str] = set([conflict["root_jar"] for conflict in conflicts])
    
    def test(self, units: list[ModUnitInfo]):
        units_jar_set = {unit["root_jar"] for unit in units}

        for conflicting_item in self.conflicts:
            if conflicting_item not in units_jar_set:
                return True  # at least one missing → OK

        return False  # all conflicts found → fail