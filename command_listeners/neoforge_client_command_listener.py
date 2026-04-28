import json
from colorama import init, Fore, Style, Back
from command_listeners.command_listener_interface import CommandListenerInterface
from command_listeners.neoforge_launch_command_listener import LaunchCommandListener

class NeoforgeClientCommandListener(CommandListenerInterface):
    
    def __init__(self):
        super()
    
    @classmethod
    def listen_for_command(cls, mods_path: str):
        super().listen_for_command(mods_path)
        
        listener = LaunchCommandListener()
        
        print("Waiting for normal game launch...")
        print("Please launch your game normally.")
        print(f"{Fore.BLACK}{Back.YELLOW}Some launchers do not expose full runtime arguments required to reconstruct the NeoForge launch configuration.{Style.RESET_ALL}\n{Fore.CYAN}For best experience, please use Prism Launcher.{Style.RESET_ALL}")
        print("(Note: your game will be terminated as soon as you launch it)")
        command_arguments = listener.listen_for_game(mods_path)
        
        with open("launch_command.json", "w", encoding="utf-8") as f:
            json.dump(command_arguments, f)
        
    
    