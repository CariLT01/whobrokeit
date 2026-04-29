import subprocess
import os
import threading
import shutil
import json
from pathlib import Path
from core.types.mod_unit import ModUnitInfo
from core.flags import Flags, ProgramMode
from core.test.test_dispatcher import TestDispatcher
from terminal_ui import console
from pynput import keyboard
from rich.progress import Progress, TextColumn, BarColumn, TaskProgressColumn

class LaunchTesterClass:
    
    def __init__(self, mods_path: str):
        self.mods_path = mods_path
        
        self.is_test_mode: bool = False
        self.initialized: bool = False
        
        if Flags.mode == ProgramMode.TESTING:
            print(f"Flag mode is set to: {ProgramMode.TESTING}, activating test protocol")
            self.is_test_mode = True
    
    def pre_init(self, all_units: list[ModUnitInfo]):
        self.units = all_units
        if self.is_test_mode:
            self.tester = TestDispatcher(self.units)
        self.initialized = True
    
    def launch_process(self, command: list[str]):

        return subprocess.Popen(
            command,
            cwd=os.path.abspath(os.path.join(self.mods_path, "..")),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            stdin=subprocess.PIPE,
            text=True,
            bufsize=1,
            encoding="utf-8",
            errors="ignore",
        )

    def launch_and_test(self, command: list[str]):

        print(
            "Launching Minecraft... Press Y to indicate success, N to indicate failure"
        )

        process = self.launch_process(command)

        _ = """
        OLD CODE
        cp_index = command.index('-cp')
        classpath_value = command[cp_index + 1]
        
        process.stdin.write(f"classpath {classpath_value}\n")
        process.stdin.write("mainClass net.minecraft.client.main.Main\n")
        
        params = [
            "launcher standard",
            "accessToken 0",
            "version 1.21.1"
        ]
        
        for param in params:
            process.stdin.write(param + "\n")
            process.stdin.flush()
        
        # Write the 'launch' command to the process's stdin
        try:
            process.stdin.write("launch\n")
            process.stdin.flush()
        except BrokenPipeError:
            # The process might have died before we could write
            print("Process died before launch command could be sent.")
            return False"""

        result: dict[str, bool | None] = {"value": None}

        def pipe_output():
            if process.stdout:
                for line in process.stdout:
                    print(line, end="")  # forward Minecraft output live

        thread = threading.Thread(target=pipe_output, daemon=True)
        thread.start()

        def on_press(key):
            try:
                if key.char.lower() == "y":
                    print("User inputted success")
                    process.terminate()
                    result["value"] = True
                    return False  # stop listener
                elif key.char.lower() == "n":
                    print("User inputted failure")
                    process.terminate()
                    result["value"] = False
                    return False
            except AttributeError:
                pass  # special keys (ignore)

        listener = keyboard.Listener(on_press=on_press)  # type: ignore
        listener.start()

        process.wait()
        if result["value"] is None:
            print("Detected process died")
            listener.stop()
            return False

        return result["value"]



    def _unit_to_files(self, units: list[ModUnitInfo]) -> list[str]:

        files: list[str] = []
        for unit in units:
            print(f"Adding: {unit["jars"]}")
            files += unit["jars"]

        return files

    def test(self, mods: list[ModUnitInfo]) -> bool:
        """
        Given a list of units, it tests them and returns True if PASS or False if FAIL.
        """
        
        if not self.initialized:
            raise RuntimeError("Not initialized")
        
        if self.is_test_mode and self.tester is not None:
            # print("Test mode active, using test dispatcher")
            return self.tester.test(mods)
        
        return self._test_internal(self._unit_to_files(mods))

    def _test_internal(self, mods: list[str]) -> bool:

        # delete all mods in folder and put them back

        with Progress(
            TextColumn("[cyan]{task.description:<30}"),
            TextColumn("[dim]{task.fields[file]:<40}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
        ) as progress:

            mods_files = os.listdir(self.mods_path)

            task1 = progress.add_task(
                description="Moving files", total=len(mods_files), file=""
            )

            for mod_file in mods_files:
                abs_path = os.path.join(self.mods_path, mod_file)
                temp_abs_path = os.path.join("temp", mod_file)
                # print(f"Moving file: {abs_path} -> {temp_abs_path}")
                progress.update(task1, file=f"{temp_abs_path}")
                try:
                    shutil.move(abs_path, temp_abs_path)
                except Exception as e:
                    print(f"Moved failed: {e}")

                progress.advance(task1)

            mods_set = set(mods)

            task2 = progress.add_task(
                description="Moving files", total=len(mods_set), file=""
            )

            mods_dir = Path(self.mods_path)
            temp_dir = Path("temp")

            # move files to instance
            for mod_file in mods_set:
                src = temp_dir / Path(mod_file).name
                dst = mods_dir / Path(mod_file).name

                progress.update(task2, file=f"{src}")
                try:
                    shutil.move(str(src), str(dst))
                except OSError as e:
                    print(f"Move failed: {e}")

                progress.advance(task2)

        # read launch command
        with open("launch_command.json", "r", encoding="utf-8") as f:
            launch_command: list[str] = json.load(f)

        input()

        return self.launch_and_test(launch_command)