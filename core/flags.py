from enum import StrEnum

class ProgramMode(StrEnum):
    
    PRODUCTION = "production"
    TESTING = "testing"
    

class _FlagsClass:
    
    def __init__(self):
        
        self.mode: ProgramMode = ProgramMode.PRODUCTION
    

Flags = _FlagsClass()
