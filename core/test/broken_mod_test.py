from core.types.mod_unit import ModUnitInfo

class BrokenModTest:
    
    def __init__(self, broken_mod: ModUnitInfo):
        
        self.broken_mod = broken_mod
    
    def test(self, units: list[ModUnitInfo]):
        try:
            units.index(self.broken_mod)
        except ValueError:
            return True
        else:
            return False