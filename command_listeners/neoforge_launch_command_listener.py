import psutil
import time
import os
import json
from colorama import init, Fore, Back, Style
init()

from command_builders.neoforge_command_builder import NeoforgeCommandBuilder

seen = set()


class LaunchCommandListener:
    def __init__(self):
        self.seen = set()
        
        self.neoforge_command_builder = NeoforgeCommandBuilder()
    
    def listen_for_game(self, mods_path: str) -> list[str]:
        while True:
            for p in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if "java" in p.info['name'].lower():
                        if p.pid not in seen:
                            print("NEW JAVA PROCESS DETECTED")
                            
                            with open("launch_command_raw.json", "w") as f:
                                json.dump(p.info['cmdline'], f, indent=4)
                            
                            command_arguemnts: list[str] = p.info['cmdline']
                            seen.add(p.pid)
                            
                            try:
                                built_command = self.neoforge_command_builder.build_command(command_arguemnts, mods_path)
                            except Exception as e:
                                print(f"{Fore.RED}Unable to analyze launch: Limited launch metadata detected")
                                print(f"{Style.RESET_ALL}{Fore.YELLOW}This launcher does not expose enough metadata in its launch sequence to reconstruct the launch command needed for launching the game.")
                                print(f"{Style.RESET_ALL}For best experience, please use Prism Launcher.")
                                print(f"\n\ninternal error: {e}")
                                
                                continue
                            
                            print(f"Terminating process: {p.pid}")
                            proc = psutil.Process(p.pid)
                            proc.terminate()
                            
                            return built_command

                except Exception as e:
                    print(f"Process read failed: {e}")
            time.sleep(1)