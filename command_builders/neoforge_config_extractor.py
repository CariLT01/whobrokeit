from typing import TypedDict
from pathlib import Path
import json
import re
import os
import zipfile

# REGEXES
MINECRAFT_CLIENT_REGEX = r"^minecraft-.*-client\.jar$"
MINECRAFT_CLIENT_VERSION_REGEX = r"minecraft-(.+)-client\.jar"
JAVA_NATIVES_MATCH = r"-Djava\.library\.path=.*"
NEOFORGE_INSTALLER_MATCH = r"^neoforge-(.+)-installer\.jar$"


class NeoforgeConfig(TypedDict):
    forge_libraries_directory: str
    forge_minecraft_path: str
    forge_installer_path: str

    neoforge_version: str
    fml_version: str
    mc_version: str
    neoform_version: str

    java_path: str
    class_path: str


class NeoforgeVersions(TypedDict):

    neoform_version: str
    fml_version: str
    mc_version: str
    libraries: list[str]
    installer_path: str
    neoforge_version: str


class NeoforgeConfigExtractor:

    def __init__(self): ...

    @staticmethod
    def get_index(value: str, list: list[str]) -> int:
        try:
            return list.index(value)
        except ValueError:
            return -1

    def find_libraries_parent(self, path: Path) -> Path | None:
        for parent in path.parents:
            if parent.name == "libraries":
                return parent
        return None

    def find_most_common_library_directory(self, class_path: str):

        libraries = class_path.split(";")

        all_libraries_parents: dict[str, int] = {}

        for library in libraries:
            library_path = Path(library)

            libraries_parent = self.find_libraries_parent(library_path)
            if libraries_parent == None:
                print("Falling back to hard-coded 5 level parents. May be inaccurate")

                libraries_parent = library_path.parent.parent.parent.parent.parent
            libraries_str_path = str(libraries_parent)

            current_count = all_libraries_parents.get(str(libraries_str_path))
            if current_count is None:
                print(f"Detected potential libraries path: {libraries_str_path}")
                all_libraries_parents[libraries_str_path] = 1
            else:
                all_libraries_parents[libraries_str_path] = current_count + 1

        # get max
        most_common_libraries_path = max(
            all_libraries_parents, key=lambda k: all_libraries_parents[k]
        )
        print(f"Most common path: {most_common_libraries_path}")
        return most_common_libraries_path

    def search_for_installer(
        self, mod_loader: str, mod_loader_version: str, libraries_path: str
    ) -> str | None:
        # for neoforge
        installer_name = f"{mod_loader}-{mod_loader_version}-installer.jar"

        print(f"Searching for installer: {installer_name}...")

        lib_path = Path(libraries_path)

        for path in lib_path.rglob("*"):
            if path.is_file():
                # print(f"Found: {path.name}, doesn't match: {installer_name}")
                if path.name == installer_name:
                    return str(path)
        return None

    def get_client_jar(self, class_path: str) -> str | None:

        libraries = class_path.split(";")

        for library in libraries:
            base_name = os.path.basename(library)
            matches = re.match(MINECRAFT_CLIENT_REGEX, base_name)
            if matches:
                return library
        return None

    def get_client_version_from_name(self, name: str) -> str | None:
        match = re.search(MINECRAFT_CLIENT_VERSION_REGEX, name)
        if match:
            version = match.group(1)
            return version
        return None

    @staticmethod
    def maven_to_expanded_path(coord: str) -> str:
        parts = coord.split(":")

        group = parts[0].replace(".", "/")
        artifact = parts[1]
        version = parts[2]
        classifier = parts[3] if len(parts) > 3 else None

        base = f"{group}/{artifact}/{version}"

        if classifier:
            filename = f"{artifact}-{version}-{classifier}.jar"
        else:
            filename = f"{artifact}-{version}.jar"

        return f"{base}/{filename}"

    def get_forge_versions(self, installer_path: str) -> NeoforgeVersions | None:
        with zipfile.ZipFile(installer_path) as f:
            with f.open("version.json") as file:
                raw_data = file.read().decode()
                version_data = json.loads(raw_data)

                game_arguments: list[str] = version_data["arguments"]["game"]
                neoform_index = self.get_index("--fml.neoFormVersion", game_arguments)
                fml_version_index = self.get_index("--fml.fmlVersion", game_arguments)
                neoforge_version_index = self.get_index(
                    "--fml.neoForgeVersion", game_arguments
                )

                if neoform_index == -1 or fml_version_index == -1:
                    raise ValueError(
                        f"Could not find appropriate arguments in: {game_arguments}"
                    )

                neoform_version = game_arguments[neoform_index + 1]
                fml_version = game_arguments[fml_version_index + 1]
                game_version = version_data["inheritsFrom"]
                neoforge_version = game_arguments[neoforge_version_index + 1]

                libraries_to_download = version_data["libraries"]
                libs: list[str] = []
                for lib in libraries_to_download:
                    name: str = lib["name"]
                    transformed_name = self.maven_to_expanded_path(name)
                    # print(f"Neoforge found: {transformed_name}")
                    libs.append(transformed_name)

                return {
                    "fml_version": fml_version,
                    "mc_version": game_version,
                    "neoform_version": neoform_version,
                    "libraries": libs,
                    "installer_path": installer_path,
                    "neoforge_version": neoforge_version,
                }

    def test_neoforge_configuration(
        self, libs_path: str, class_path: str, neoforge_config: NeoforgeVersions
    ):

        class_path_libs = class_path.split(";")
        class_path_libs_norm = [os.path.normpath(p) for p in class_path_libs]

        for library in neoforge_config["libraries"]:
            full_path = os.path.normpath(os.path.join(libs_path, library))

            if not full_path in class_path_libs_norm:
                print(f"Path {full_path} not found in libraries, missing dependency")
                return False
        print("All dependencies match classpath")
        return True

    def guess_neoforge_version(
        self, libraries_directory: str, class_path: str, mc_version: str
    ) -> NeoforgeVersions | None:

        neoforged_libs_path = os.path.join(
            libraries_directory, "net", "neoforged", "neoforge"
        )

        for path in Path(neoforged_libs_path).rglob("*"):
            if path.is_file():
                match = re.match(NEOFORGE_INSTALLER_MATCH, path.name)
                if match:
                    neoforge_version = match.group(1)
                    print(f"Attempting neoforge version: {neoforge_version}")
                    neoforge_versions_properties = self.get_forge_versions(str(path))
                    if neoforge_versions_properties is None:
                        print(f"Could not find neoforge version properties on: {path}")
                        continue

                    if neoforge_versions_properties["mc_version"] != mc_version:
                        print(
                            f"Minecraft version does not match: {neoforge_versions_properties["mc_version"]} != {mc_version}"
                        )
                        continue

                    test_config_valid = self.test_neoforge_configuration(
                        libraries_directory, class_path, neoforge_versions_properties
                    )
                    if not test_config_valid:
                        print(f"Dependency test failed on: {path}")
                        continue

                    return neoforge_versions_properties

    def extract_config(self, command_arguments: list[str]) -> NeoforgeConfig:

        cp_label_index = self.get_index("-cp", command_arguments)

        if cp_label_index == -1:
            raise ValueError("Unable to find classpath in detected command!")

        cp_index = cp_label_index + 1

        class_path = command_arguments[cp_index]

        libraries_path = self.find_most_common_library_directory(class_path)
        print(f"Libraries directory detected to be at: {libraries_path}")

        client_jar = self.get_client_jar(class_path)
        if client_jar is None:
            raise ValueError("Unable to find Minecraft client JAR")

        print(f"Minecraft Client Jar located to be at: {client_jar}")

        client_jar_name = os.path.basename(client_jar)
        client_version = self.get_client_version_from_name(client_jar_name)

        if client_version is None:
            raise ValueError("Unable to find Minecraft client version")

        print(f"Minecraft client version detected to be: {client_version}")

        neoforge_version_properties = self.guess_neoforge_version(
            libraries_path, class_path, client_version
        )
        if neoforge_version_properties is None:
            raise ValueError("Unable to find neoforge version/installer properties")

        print(
            f"Found neoforge version: {neoforge_version_properties["neoforge_version"]}"
        )
        print(f"Found installer path: {neoforge_version_properties["installer_path"]}")
        print(
            f"Found neoform version: {neoforge_version_properties["neoform_version"]}"
        )
        print(f"Found FML version: {neoforge_version_properties["fml_version"]}")

        return {
            "fml_version": neoforge_version_properties["fml_version"],
            "forge_installer_path": neoforge_version_properties["installer_path"],
            "forge_libraries_directory": libraries_path,
            "forge_minecraft_path": client_jar,
            "mc_version": client_version,
            "neoforge_version": neoforge_version_properties["neoforge_version"],
            "neoform_version": neoforge_version_properties["neoform_version"],
            "java_path": command_arguments[0],
            "class_path": class_path,
        }
