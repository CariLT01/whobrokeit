from pathlib import Path
import os
from command_builders.neoforge_config_extractor import NeoforgeConfigExtractor


class NeoforgeCommandBuilder:
    
    def __init__(self):
        
        self.config_extractor = NeoforgeConfigExtractor()
    
    def build_command(self, comamnd_arguments: list[str], mods_path: str) -> list[str]:
        
        mods_path_obj = Path(mods_path)
        
        instance_configuration = self.config_extractor.extract_config(comamnd_arguments)
        
        return [
            instance_configuration["java_path"],
            f"-Dforgewrapper.librariesDir={instance_configuration["forge_libraries_directory"]}",
            f"-Dforgewrapper.minecraft={instance_configuration["forge_minecraft_path"]}",
            f"-Dforgewrapper.installer={instance_configuration["forge_installer_path"]}",
            "-cp",
            instance_configuration["class_path"],
            "io.github.zekerzhayard.forgewrapper.installer.Main",
            "--accessToken",
            "0",
            "--version",
            instance_configuration["mc_version"],
            "--gameDir",
            str(mods_path_obj.parent),
            "--launchTarget",
            "forgeclient",
            "--fml.neoForgeVersion",
            instance_configuration["neoforge_version"],
            "--fml.fmlVersion",
            instance_configuration["fml_version"],
            "--fml.mcVersion",
            instance_configuration["mc_version"],
            "--fml.neoFormVersion",
            instance_configuration["neoform_version"]
        ]