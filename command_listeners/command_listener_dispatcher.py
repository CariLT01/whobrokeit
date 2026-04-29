from enum import StrEnum
from command_listeners.neoforge_server_command_listener import NeoforgeServerCommandListener
from command_listeners.neoforge_client_command_listener import NeoforgeClientCommandListener
from core.tui.prompt_select import prompt_select
from core.tui.colors import TerminalColors as C
from core.flags import Flags, ProgramMode
from terminal_ui import console


class Environment(StrEnum):
    SERVER = "server"
    CLIENT = "client"


class CommandListenerDispatcher:
    
    def __init__(self):
        pass
    
    def dispatch(self, mods_path: str):
        
        if Flags.mode == ProgramMode.TESTING:
            print("Skipping command listener dispatch; detected testing mode")
            return
        
        C.initialize()
        
        selected_environment: Environment | None = None

        
        print(f"{C.STYLE.BRIGHT}Choose an environment:")
        print(f"{C.STYLE.DIM}Choose between NeoForge Server or NeoForge client.")
        print("--")
        print(f"{C.STYLE.BRIGHT}{C.FORE.LIGHTBLUE_EX}NeoForge Client")
        print(f"{C.STYLE.DIM}Launches Minecraft directly from your launcher -- helps debug issues occuring on the client.")
        print("--")
        print(f"{C.STYLE.BRIGHT}{C.FORE.LIGHTYELLOW_EX}NeoForge Server")
        print(f"{C.STYLE.DIM}Requires passing a path to your launch script (.sh or .bat). Helps with debugging issues only occuring on the server.")
        
        user_input = prompt_select(
            title="Choose an environment",
            options=[
                {
                    "option_name": "client",
                    "option_text": "client"
                },
                {
                    "option_name": "server",
                    "option_text": "server"
                }
            ],
        )
        
        if user_input == Environment.SERVER:
            selected_environment = Environment.SERVER
        elif user_input == Environment.CLIENT:
            selected_environment = Environment.CLIENT
        else:
            raise ValueError(f"Unrecognized environment: '{user_input}'. Please try again.")
        
        if selected_environment == Environment.SERVER:
            listener = NeoforgeServerCommandListener()
            listener.listen_for_command(mods_path)
        elif selected_environment == Environment.CLIENT:
            listener = NeoforgeClientCommandListener()
            listener.listen_for_command(mods_path)
        else:
            raise ValueError(f"Unrecognized environment: '{selected_environment}'")
        