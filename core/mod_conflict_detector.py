import subprocess
import os
import shutil
import threading
from pathlib import Path
import json
from enum import StrEnum
from typing import TypedDict, Any
from dependency_resolver import DependencyResolver, ModUnitInfo
from terminal_ui import console
from core.algorithms.binary_search_algorithm import BinarySearchIsolation
from core.algorithms.quick_x_plain_algorithm import QuickXPlainIsolation
from pynput import keyboard
from rich.progress import Progress, TextColumn, BarColumn, TaskProgressColumn


def print(*args, **kwargs):
    console.print(*args, **kwargs)


class AlgorithmState(StrEnum):
    NONE = "none"
    INITIAL_PRUNING = "prune"
    MINIMAL_CONFLICT_SET = "mcs"


class SearchState(TypedDict):
    data: Any
    stage: AlgorithmState


class ModDetectorConflict:
    def __init__(self, mods_path: "str"):

        self._cache = {}

        self.loaded_state: Any | None = None
        self.units: list[ModUnitInfo] = []
        self.stage: AlgorithmState = AlgorithmState.NONE
        self.dependency_resolver = DependencyResolver()

        self.qxp_isolator = QuickXPlainIsolation(self.save_state)
        self.bs_isolator = BinarySearchIsolation(self.save_state)

        self.n_lauches = 0

        self.mods_path = mods_path

        # make file
        try:
            os.mkdir("temp")
        except OSError:
            pass

        with Progress(
            TextColumn("[cyan]{task.description:<30}"),
            TextColumn("[dim]{task.fields[file]:<40}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
        ) as progress:
            temp_files = os.listdir("temp")
            task = progress.add_task("Moving files", total=len(temp_files), file="")

            # delete all
            for temp_file in temp_files:

                abs_path = os.path.join("temp", temp_file)

                # print(f"Copying previous file back to mod folder: {temp_file}")

                progress.update(task, file=f"{temp_file}")

                mod_abs_path = os.path.join(mods_path, temp_file)
                shutil.move(abs_path, mod_abs_path)

                progress.advance(task)

            mods_files = os.listdir(mods_path)

            task2 = progress.add_task("Moving files", total=len(mods_files), file="")

            # copy
            for mod_file in mods_files:

                progress.update(task2, file=f"{mod_file}")

                if not mod_file.endswith(".jar"):
                    print(f"Skippping {mod_file}")
                    progress.advance(task2)
                    continue

                abs_path = os.path.join(mods_path, mod_file)
                temp_path = os.path.join("temp", mod_file)
                shutil.move(abs_path, temp_path)

                progress.advance(task2)

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

    def test(self, mods: list[str]) -> bool:

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

    def test_func(self, units: list[ModUnitInfo]) -> bool:
        self.n_lauches += 1
        return self.test(self.unit_to_files(units))

    def unit_to_files(self, units: list[ModUnitInfo]) -> list[str]:

        files: list[str] = []
        for unit in units:
            print(f"Adding: {unit["jars"]}")
            files += unit["jars"]

        return files

    def get_cache_state(self) -> dict[str, bool]:
        return {"|".join(key): value for key, value in self._cache.items()}

    def prune_save_states(self, keep_index: int, file_name: str = "save_states.json"):
        try:
            with open(file_name, "r", encoding="utf-8") as f:
                data = json.load(f)

            if keep_index < 0 or keep_index >= len(data):
                return

            confirm = input(
                f"Delete {len(data) - keep_index - 1} newer states? (y/n): "
            )
            if confirm.lower() != "y":
                return

            data = data[: keep_index + 1]

            with open(file_name, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)

            print(f"Pruned save states to index {keep_index}")

        except Exception as e:
            print(f"Failed to prune save states: {e}")

    def save_state(
        self,
        data: Any,
    ):
        final_data: SearchState = {"data": data, "stage": self.stage}
        
        # read existing save states
        existing_data = []
        try:
            with open("save_states.json", "r") as f:
                existing_data = json.load(f)
        except FileNotFoundError:
            pass
        
        new_data = existing_data + [final_data]
        
        with open("save_states.json", "w") as f:
            json.dump(new_data, f, indent=4)
            
        print("Saved data to save_states.json")
            

    def load_state(self) -> list[SearchState] | None:
        try:
            with open("save_states.json", "r") as f:
                data = json.load(f)
                return data
        except OSError as e:
            print(f"Failed to load save states: {e}")
            return None

    def unit_map_by_root(self, units: list[ModUnitInfo]) -> dict[str, ModUnitInfo]:
        return {u["root_jar"]: u for u in units}

    def reconstruct_units(
        self, saved_roots: list[str], unit_map: dict[str, ModUnitInfo]
    ) -> list[ModUnitInfo]:
        rebuilt = []
        for root in saved_roots:
            unit = unit_map.get(root)
            if unit is not None:
                rebuilt.append(unit)
            else:
                print(f"warn: missing unit for root_jar={root}")
        return rebuilt

    def resume_search(self, load_state: Any | None):

        if self.stage == "none":
            raise ValueError("Search stage cannot be NONE")

        if self.stage == "mcs":
            results = self.qxp_isolator.run(self.units, self.test_func, load_state)
            return results

        if self.stage == "prune":
            first_pass = self.bs_isolator.run(self.units, self.test_func, load_state)
            print(f"Found: {len(first_pass)} after first pruning pass")

            test_units = first_pass

            if self.test_func(first_pass):
                print("Unable to continue. Need to restart from beginning.")
                test_units = self.units
            else:
                print("Able to successfully keep units")
                
            self.stage = AlgorithmState.MINIMAL_CONFLICT_SET

            second_pass = self.qxp_isolator.run(test_units, self.test_func, None)
            return second_pass

        raise ValueError(f"Unknown stage! {self.stage}")

    def isolate(self):

        self.units = self.dependency_resolver.resolve_dependencies(
            os.path.abspath("temp")
        )

        all_save_states = self.load_state()
        if all_save_states is not None:
            print(
                f"Found {len(all_save_states)} save states! Would you like to load one?"
            )

            save_index = -1

            while True:
                user_input = input(
                    f"Enter an index ranging from 1 to {len(all_save_states)}, and 0 to cancel: "
                )
                try:
                    user_input_int = int(user_input)

                    if user_input_int == 0:
                        save_index = -1
                        break

                    if user_input_int < 0:
                        print(f"Index cannot be negative: {user_input_int}")

                    if user_input_int > len(all_save_states):
                        print(f"Input is not in the valid range: {user_input_int}")
                        continue

                    save_index = user_input_int - 1
                    break
                except ValueError:
                    print(
                        f"Please enter a valid number. '{user_input}' is not a number."
                    )

            if save_index != -1:

                self.prune_save_states(save_index)

                current_save_state = all_save_states[save_index]

                print(f"Resuming from: {save_index}")

                self.stage = current_save_state["stage"]
                self.loaded_state = current_save_state["data"]

        if self.stage == "none":
            self.stage = AlgorithmState.INITIAL_PRUNING
        
        if self.loaded_state is None:

            print(
                "Detected first launch, no state. Running sanity check... Press N to skip"
            )
            if self.test_func(self.units):
                return []

        candidates = self.resume_search(self.loaded_state)
        print(f"Found: {len(candidates)} in minimal conflict set")
        print(f"Ran {self.n_lauches} tests (launches)")

        return candidates
