import os
import json
from colorama import Fore, Back, Style, init
from command_listeners.command_listener_interface import CommandListenerInterface

init()

class NeoforgeServerCommandListener(CommandListenerInterface):
    
    def __init__(self):
        pass
    
    @classmethod
    def listen_for_command(cls, mods_path: str):
        
        startup_script_path = ""
        
        while True:
        
            startup_script_path = input("Please enter the path to your startup script > ")

            if not os.path.exists(startup_script_path):
                print(f"{Fore.RED}The path '{startup_script_path}' does not appear to exist. Please enter another path.{Style.RESET_ALL}")
                continue
            
            if not (startup_script_path.endswith(".sh") or startup_script_path.endswith(".bat")):
                print(f"{Fore.RED}The path'{startup_script_path}' does not appear to be a script, it does not appear to end with '.bat' or '.sh'.\nPlease try again.{Style.RESET_ALL}")
                continue
            
            break
        
        with open("launch_command.json", "w", encoding="utf-8") as f:
            json.dump([startup_script_path], f)
        
        print(f"Startup script selected: {startup_script_path}")