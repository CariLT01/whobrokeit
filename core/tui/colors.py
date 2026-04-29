from colorama.ansi import Fore, Back, Style
from colorama  import init

class TerminalColors:
    FORE = Fore
    BACK = Back
    STYLE = Style
    
    @staticmethod
    def initialize():
        """Initializes the terminal colors"""
        
        init(autoreset=True)