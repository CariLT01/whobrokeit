from typing import TypedDict

class ModUnitInfo(TypedDict):
    jars: list[str]
    root_jar: str
    mod_IDs: list[str]