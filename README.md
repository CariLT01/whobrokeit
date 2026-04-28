
# NeoForge Mods Bisect Tool

A tool that allows you to find who to blame.

**This tool uses a combination of algorithms to find which mod(s) are causing issues.** It is able to save you hours of hard work manually performing binary search and guessing which mod is causing the crash. This procedure is even harder when you realize that mods often have many dependencies, and tracking each of them is hard. *And* manual bisection becomes *EVEN HARDER* when only a combination of mods recreates the problem!

This small tool will automatically run tests to pinpoint the exact mod or combination of mods that you can blame.

> [!WARNING]
> **This tool is in a very experimental stage! It currently ONLY SUPPORTS NEOFORGE.**

## How to use

(installation instructions coming *soon*)

> [!WARNING]
> Issues can arise with certain launchers. For stability, please use Prism Launcher.

1. Run `main.py`
2. When asked, enter the path to your `mods` directory.
3. It will then ask you to select `client` or `server`. If you're trying to pinpoint a mod on the client, enter client. Otherwise, enter server.
4. If you selected client, launch your game normally via the launcher (recommended: Prism Launcher).
5. Press ENTER to confirm each launch. Press **Y or N** to indicate success (Y) or failure (N). The game will be killed immediately when you press any of those keys. Please do not close the game manually: any exit code emitted by the process will be considered failure if none of the two keys were pressed.
6. You may pause (stop the program) and resume at any time, and you may rollback to a previous state if you made a mistake by relaunching the tool. 
7. Once the tests are done, the tool will tell you which mods are conflicting with each other and causing issues. Assuming no human errors were made, this result should be pretty accurate. Removing one of the mods listed should resolve the issue you are experiencing.

## How it works

**Pinpointing the mod(s)**

This tool uses binary search, in conjunction with delta debugging. Binary search is used to prune many mods at once, saving a lot of time since delta debugging is usually much slower.

In cases where a single mod is causing the problem, Binary Search will be the only algorithm used.

In cases where it's a mod conflict, binary search is performed first, and delta debugging is performed after once binary search cannot keep pruning mods.

**Resolving Dependencies**

This tool resolves dependencies through the mods' metadata. It also resolves the JARs inside the mods (Jar in jar dependencies). They are resolved automatically without user input

We test using what we call "units", these are atomically testable units that bundle all the required dependencies of one mod (the entire dependency tree).

Unfortunately, this is not 100% reliable. Some mods omit dependencies or declare them incorrectly, causing `ClassNotFound` errors when running Minecraft. You can fix these cases by specifying the additional dependencies required by a mod in `manual_dependencies.json`.

**User Input**

This tool uses keybinds instead of a dialog. That actually saves a lot of time. The process is automatically killed once any of the two keys are pressed. Any exit code is considered failure, if the success keybind was not pressed by the user.

**Launching the game**

Turns out NeoForge (and Forge) are suprisingly hard to launch, unlike Fabric or Quilt. They require arguments like --fml.neoformVersion and etc. which are hard to capture.

In summary, to launch Minecraft, we capture the launch command from a real launcher like Prism, and we grab the classpath. However, Prism launches a wrapper first and not the game directly, meaning we have to reconstruct the direct launch command using the information we have.

**Comparison to other tools**

- Most tools use a dialog for user input. This one uses keybinds, significantly speeding up the bisection process.
- Some tools only allow pinpointing one broken mod. This tool allows you to identify N-way conflicts, without sacrificing any speed when it's a one-broken mod case.
- This is a tool that runs externally, allowing it to be used even when the game itself refuses to launch.
- The only bisection tool that runs on Neoforge.
- This tool has been tested internally with real issues from large modpacks (200-300 mods), and has proven to be highly effective and accurate at pinpointing mods, saving lots of time (hours to days).

> [!WARNING]
> This is a VERY experimental tool! It may crash or otherwise produce incorrect results in some cases. However, if the program works correctly and no human errors were made at classifying failure vs. success, it should be pretty accurate :D