import os
import zipfile
import io
import tomllib
import json
from typing import TypedDict
from enum import StrEnum
from terminal_ui import console
from core.types.mod_unit import ModUnitInfo
from rich.progress import Progress, TextColumn, BarColumn, TaskProgressColumn


def print(*args, **kwargs):
    console.print(*args, **kwargs)


with open("manual_dependencies.json") as f:
    manual_overrides = json.load(f)


class ModRawJarInfo(TypedDict):
    mod_IDs: set[str]
    jar_file: str
    dependencyIDs: set[str]





class DependencyResolver:

    def __init__(self): ...

    def get_dependencies(self, mod_id: str, dependencies: set[str]) -> set[str]:
        # inject overrides FIRST
        injected = set(manual_overrides.get(mod_id, []))

        return dependencies | injected

    def recursively_parse_jar(
        self,
        jar_name: str,
        jar_file: io.BytesIO,
        dependency_list: set[str] = set(),
        mod_list: set[str] = set(),
    ):

        with zipfile.ZipFile(jar_file, "r") as jar:
            try:

                for name in jar.namelist():
                    if (
                        name.startswith("META-INF/jarjar")
                        and not name.endswith("/")
                        and name.endswith(".jar")
                    ):
                        with jar.open(name) as jarInJar:
                            # print(f"Scanning jar in jar file: {name} located inside: {jar_name}")
                            self.recursively_parse_jar(
                                name,
                                io.BytesIO(jarInJar.read()),
                                dependency_list,
                                mod_list,
                            )

                with jar.open("META-INF/neoforge.mods.toml") as f:
                    content = f.read().decode("utf-8")

                    mod_data = tomllib.loads(content)

                    dependencies: dict[str, list[dict]] | None = mod_data.get(
                        "dependencies"
                    )

                    if dependencies is not None:

                        for dependency_mod in dependencies.values():

                            if not isinstance(dependency_mod, list):
                                # print("Unreadable metadata information found")
                                continue

                            for dependency in dependency_mod:
                                dependency_id = dependency["modId"]
                                mandatory_field = dependency.get("mandatory")
                                required = dependency.get("type")

                                if (
                                    required is not None
                                    and required.lower() != "required"
                                ):
                                    continue

                                if dependency_id == "minecraft":
                                    continue

                                if dependency_id == "neoforge":
                                    continue

                                dependency_list.add(dependency_id)
                                # print(f"Dependency {dependency_id} found in {jar_name}")
                    else:
                        pass
                        # print("No dependencies found for mod")

                    mods = mod_data["mods"]

                    for mod_data in mods:
                        mod_id = mod_data["modId"]

                        # print(f"Identifier: {mod_id} found in {jar_name}")
                        mod_list.add(mod_id)

                    # stuff cannot require and be the same thing, so remove deps
                    for mod_id in mod_list:
                        if mod_id in dependency_list:
                            # print(f"Delete dependency: {mod_id} in {jar_name}")
                            dependency_list.remove(mod_id)

                    # print(f"Dependency parser found dependencies: {dependency_list} for mod iDs: {mod_list} in jar: {jar_name}")
            except KeyError as e:
                pass
                # print(f"Failed to find TOML: {e}")

        return dependency_list, mod_list

    def parse_raw_jar(self, jar_file: str):

        dependency_list: list[str] = []
        mod_list: list[str] = []

        with open(jar_file, "rb") as f:
            mod_dep_list, mod_mod_list = self.recursively_parse_jar(
                jar_file, io.BytesIO(f.read()), dependency_list=set(), mod_list=set()
            )
            dependency_list += mod_dep_list
            mod_list += mod_mod_list

        final_data: ModRawJarInfo = {
            "dependencyIDs": set(dependency_list),
            "mod_IDs": set(mod_list),
            "jar_file": os.path.basename(jar_file),
        }

        print(
            f"Dependency resolver found: {len(dependency_list)} dependencies for mods: {mod_list}: {dependency_list}"
        )

        return final_data

    def recursively_resolve_dependencies(
        self,
        to_resolve: str,
        mod_data_dict: dict[str, ModRawJarInfo],
        mod_id_to_jar: dict[str, str],
        visited: set[str] | None = None,
    ) -> set[str]:

        if visited is None:
            visited = set()

        visited.add(to_resolve)

        # resolve jar file
        jar_file = mod_id_to_jar.get(to_resolve)
        if jar_file is None:
            print(
                f"warn: cannot find {to_resolve}, no dependencies resolved in this node"
            )
            return set()

        # resolve dependencies
        mod_data_info = mod_data_dict.get(jar_file)
        if mod_data_info is None:
            print(
                f"warn: cannot find mod data for: {jar_file}, no dependencies resolved in this node"
            )
            return set()

        raw_deps = mod_data_info["dependencyIDs"]
        dependencies = self.get_dependencies(to_resolve, raw_deps)

        all_dependencies_list: set[str] = set()

        for dependency_id in dependencies:

            all_dependencies_list.add(dependency_id)

            if dependency_id not in visited:
                # print(f"Recursively resolving: {dependency_id}")
                inner_deps = self.recursively_resolve_dependencies(
                    dependency_id, mod_data_dict, mod_id_to_jar, visited=visited
                )
                all_dependencies_list.update(inner_deps)

        # print(f"Resolved {len(all_dependencies_list)} dependencies within this node: {all_dependencies_list} for mod: {to_resolve}")

        return all_dependencies_list

    def resolve_dependencies(self, mod_folder: str):

        print(f"Discovering files in: {mod_folder}")

        mod_folder_items = os.listdir(mod_folder)

        jar_to_mod_id_map: dict[str, set[str]] = {}
        mod_id_to_jar_map: dict[str, str] = {}

        jar_to_jar_data_map: dict[str, ModRawJarInfo] = {}

        with Progress(    TextColumn("[cyan]{task.description:<30}"),
    TextColumn("[dim]{task.fields[file]:<40}"),
    BarColumn(),
    TaskProgressColumn(),
    console=console) as progress:
            task = progress.add_task("Resolving dependencies", total=len(mod_folder_items), file="")

            for mod_item in mod_folder_items:

                progress.update(task, file=f"{mod_item}")
                # print(f"Discovered file: {mod_item}")

                abs_path = os.path.join(mod_folder, mod_item)

                jar_data = self.parse_raw_jar(abs_path)
                jar_to_mod_id_map[jar_data["jar_file"]] = jar_data["mod_IDs"]
                for mod_id in jar_data["mod_IDs"]:
                    mod_id_to_jar_map[mod_id] = abs_path

                jar_to_jar_data_map[abs_path] = jar_data
                
                progress.advance(task)

        units: list[ModUnitInfo] = []

        with Progress(    TextColumn("[cyan]{task.description:<30}"),
    TextColumn("[dim]{task.fields[file]:<40}"),
    BarColumn(),
    TaskProgressColumn(),console=console)as progress:
            
            task = progress.add_task("Resolving dependencies", total=len(jar_to_jar_data_map.items()), file="")
            

            for mod_file, mod_data in jar_to_jar_data_map.items():

                progress.update(task, file=f"{mod_file}")

                # add all dependencies into one

                mod_IDs = mod_data["mod_IDs"]

                all_dependencies: set[str] = set()

                for mod_id in mod_IDs:
                    dependency_children = self.recursively_resolve_dependencies(
                        mod_id, jar_to_jar_data_map, mod_id_to_jar_map
                    )

                    for dep in dependency_children:
                        all_dependencies.add(dep)

                # convert all to jar files

                dependencies_jar: set[str] = set()

                for dep in all_dependencies:

                    jar_file = mod_id_to_jar_map.get(dep)
                    if jar_file is None:
                        print(
                            f"warn: dependency resolver cannot find jar file for: {jar_file}"
                        )
                        continue

                    dependencies_jar.add(jar_file)

                dependencies_jar.add(mod_file)

                units.append(
                    {
                        "jars": [os.path.basename(dep) for dep in dependencies_jar],
                        "root_jar": os.path.basename(mod_file),
                        "mod_IDs": list(mod_data["mod_IDs"]),
                    }
                )
                
                progress.advance(task)

                # print(f"Unit contains {len(dependencies_jar)} jar files: {dependencies_jar}")

        for unit in units:
            print(f"Candidate Unit:{unit}")

        print(f"Scanned units total: {len(units)}")

        with open("units.json", "w") as f:
            json.dump(units, f, indent=4)

        return units
