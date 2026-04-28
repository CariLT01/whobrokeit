# load libraries
import os
import json
from core.mod_conflict_detector import ModDetectorConflict
from command_listeners.command_listener_dispatcher import CommandListenerDispatcher
from colorama import init, Fore, Style, Back
init()

class MainApplication:
    def __init__(self):
        self.listener = CommandListenerDispatcher()
    
    def run(self):
        
        while True:
            mods_path = input("Please enter the path to your mods folder > ")
            
            if not os.path.exists(mods_path):
                print(f"The path '{mods_path}' does not appear to exist. Please try again.")
                continue
            
            break
        

        self.listener.dispatch(mods_path)
        


        self.conflict_detector = ModDetectorConflict(
            mods_path=mods_path
        )
        
        isolated = self.conflict_detector.isolate()
        
        with open("suspected_mods.json", "w") as f:
            json.dump(isolated, f, indent=4)
        
        print(f"Suspected mods include: {json.dumps(isolated, indent=4)}")

application = MainApplication()
application.run()