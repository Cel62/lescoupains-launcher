import os

appdata = os.getenv("APPDATA").replace('\'', '/')
launcher_directory = appdata + "/.lescoupainslauncher"


def createFolder():
    if not os.path.exists(launcher_directory):
        os.makedirs(launcher_directory)
        print(f"Le dossier '{launcher_directory}' a été crée avec succès.")
    else:
        print(f"Le dossier '{launcher_directory}' existe déjà.")

    return launcher_directory


current_max = 0


def set_status(status: str):
    print(status)


def set_progress(progress: int):
    if current_max != 0:
        print(f"{progress}/{current_max}")


def set_max(new_max: int):
    global current_max
    current_max = new_max


callback = {
    "setStatus": set_status,
    "setProgress": set_progress,
    "setMax": set_max
}