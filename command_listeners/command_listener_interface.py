from abc import ABC, abstractmethod

class CommandListenerInterface:
    
    def __init__(self):
        pass
    
    @classmethod
    @abstractmethod
    def listen_for_command(cls, mods_path: str):
        pass
    
    