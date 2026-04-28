from enum import StrEnum
from command_listeners.neoforge_server_command_listener import NeoforgeServerCommandListener
from command_listeners.neoforge_client_command_listener import NeoforgeClientCommandListener

class Environment(StrEnum):
    SERVER = "server"
    CLIENT = "client"


class CommandListenerDispatcher:
    
    def __init__(self):
        pass
    
    def dispatch(self, mods_path: str):
        
        selected_environment: Environment | None = None
        
        while True:
            
            user_input = input("Please select an environment: 'server' or 'client' >").lower().strip()
            
            if user_input == Environment.SERVER:
                selected_environment = Environment.SERVER
                break
            elif user_input == Environment.CLIENT:
                selected_environment = Environment.CLIENT
                break
            else:
                print(f"Unrecognized environment: '{user_input}'. Please try again.")
        
        if selected_environment == Environment.SERVER:
            listener = NeoforgeServerCommandListener()
            listener.listen_for_command(mods_path)
        elif selected_environment == Environment.CLIENT:
            listener = NeoforgeClientCommandListener()
            listener.listen_for_command(mods_path)
        else:
            raise ValueError(f"Unrecognized environment: '{selected_environment}'")
        