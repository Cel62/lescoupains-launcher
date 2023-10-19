import json
import urllib.request
from ast import literal_eval
from configparser import ConfigParser, NoSectionError, NoOptionError, ParsingError
from functools import partial
from subprocess import call
from tkinter import PhotoImage, messagebox
from zipfile import ZipFile

import minecraft_launcher_lib
import requests
from PyQt6.QtCore import QUrl
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QLabel, QPushButton, QWidget
from cryptography.fernet import Fernet
from customtkinter import *
import installation


# bug impossible d'ouvrir deux fois de suite une QApplication

def main():
    def widget_connect():
        launch_button.place(x=310, y=315)
        logout_button.place(x=328, y=400)
        login_button.place_forget()
        bouton.place_forget()

    def widget_disconnect():
        launch_button.place_forget()
        logout_button.place_forget()
        login_button.place(x=310, y=330)
        bouton.place(x=305, y=400)
        bouton.deselect()

    def login():
        def handle_url_change(url2):
            global login_data
            if url2.toString().startswith("https://www.microsoft.com"):
                # Get the code from the url
                try:
                    auth_code = minecraft_launcher_lib.microsoft_account.parse_auth_code_url(url2.toString(), state)
                except AssertionError:
                    print("Les états ne correspondent pas !")
                    sys.exit(1)
                except KeyError:
                    print("L'URL n'est pas valide.")
                    sys.exit(1)
                app.quit()

                print("BUG 1")
                try:
                    login_data = minecraft_launcher_lib.microsoft_account.complete_login(client_id, secret, redirect_url, auth_code, code_verifier)
                except minecraft_launcher_lib.exceptions.AzureAppNotPermitted as e:
                    print(e)
                print("BUG 2")
                if v.get() == 1:
                    with open("config.ini", "w") as file2:
                        fernet = Fernet(key)
                        config_ini['LOGIN']['remember'] = "1"
                        config_ini['LOGIN']['login_data'] = str(fernet.encrypt(str(login_data).encode()))
                        config_ini.write(file2)

                widget_connect()
                print('Connecté')

        login_url, state, code_verifier = minecraft_launcher_lib.microsoft_account.get_secure_login_data(client_id, redirect_url)

        class LoginWindow(QMainWindow):
            def __init__(self):
                super().__init__()
                self.setWindowTitle("Microsoft Login")
                self.setGeometry(100, 100, 800, 600)

                layout = QVBoxLayout()

                self.web_view = QWebEngineView()
                layout.addWidget(self.web_view)

                self.label_status = QLabel("Attente pour la connexion...")
                layout.addWidget(self.label_status)

                self.button_cancel = QPushButton("Annuler")
                # noinspection PyUnresolvedReferences
                self.button_cancel.clicked.connect(self.close)
                layout.addWidget(self.button_cancel)

                central_widget = QWidget()
                central_widget.setLayout(layout)
                self.setCentralWidget(central_widget)

                self.web_view.load(QUrl(login_url))

        app = QApplication(sys.argv)
        login_window = LoginWindow()
        # noinspection PyUnresolvedReferences
        login_window.web_view.urlChanged.connect(handle_url_change)
        login_window.show()
        app.exec()

    def logout():
        print("Déconnexion...")
        with open("config.ini", "w") as file3:
            config_ini['LOGIN']['remember'] = "0"
            config_ini.remove_option('LOGIN', 'login_data')
            config_ini.write(file3)
        widget_disconnect()

    def update_forge():
        download_forge = True

        for x in minecraft_launcher_lib.utils.get_installed_versions(installation.launcher_directory):
            if x["id"] == full_name_forge_version:
                download_forge = False
                break

        if download_forge:
            progressbar = CTkProgressBar(window)
            progressbar.set(0)
            progressbar.place(x=10, y=450)
            current_max = 0

            def set_status(status: str):
                print(status)

            def set_progress(progress: int):
                global current_max
                if current_max != 0:
                    progressbar.set(progress / current_max)
                    window.update_idletasks()

            def set_max(new_max: int):
                global current_max
                current_max = new_max

            progression = {
                "setStatus": set_status,
                "setProgress": set_progress,
                "setMax": set_max
            }

            text_update = cancan.create_text(400, 500, text="Mise à jour de forge...\nCeci peut prendre quelques minutes", font=('Impact', 20), fill='#BF2727')
            window.update()

            print("La version de Forge n'est pas installée. Téléchargement en cours.")
            minecraft_launcher_lib.forge.install_forge_version(name_forge_version, minecraft_directory, callback=progression)
            cancan.delete(text_update)
            progressbar.destroy()
            print("Installation terminée.")
        else:
            print("La version de Forge est déjà installée.")

    def update_mods():
        mods_folder = installation.launcher_directory + "/mods"

        # créé le répertoire mods s'il n'existe pas
        if not os.path.exists(mods_folder):
            os.makedirs(mods_folder)
            print("Le dossier des mods a été crée !")

        # check si la version des mods est la même
        versionCheck_path = installation.launcher_directory + "/versionCheck.json"

        with open(versionCheck_path, "w") as f:
            f.write(requests.get("https://raw.githubusercontent.com/DCelcraft/lescoupains-launcher/main/versionLauncher.json").text)

        with open(versionCheck_path, "r") as f:
            data = json.load(f)

        with open("versionLauncher.json", "r") as f:
            data2 = json.load(f)

        def downloadMods():
            print("Téléchargement des mods.")
            text_update = cancan.create_text(400, 350, text="Téléchargement des mods...\nCeci peut prendre une minute", font=('Impact', 20), fill='#BF2727')
            window.update()
            progressbar = CTkProgressBar(window)
            progressbar.set(0)
            progressbar.place(x=10, y=450)

            def reporthook(count, block_size, total_size):
                status = count * block_size * 100 / total_size
                print(status)
                progressbar.set(status / 100)
                window.update_idletasks()

            urllib.request.urlretrieve("https://www.dropbox.com/scl/fi/9msrgnnxxvw6vhn0ul9ye/mods.zip?rlkey=risipdqsd911h90d2plwsxpmw&dl=1", mods_folder + "/mods.zip", reporthook=reporthook)
            print("Le fichier zip des mods a été téléchargé.")

            with ZipFile(mods_folder + "/mods.zip", "r") as archive:
                archive.extractall(mods_folder)

            try:
                os.remove(mods_folder + "/mods.zip")
                print("Les mods ont été dézippées. Suppression de mods.zip effectuée avec succès !")
            except OSError as e:
                print(f"Une erreur s'est produite en essayant de supprimer le fichier mods.zip : {e}")

            cancan.delete(text_update)
            progressbar.destroy()

        if len(os.listdir(mods_folder)) == 0:
            print("Les mods ne sont pas téléchargés. Téléchargement des mods !")
            downloadMods()

        # check si la version des mods est bien la bonne avec GitHub et le launcher
        elif data["mods"] == data2["mods"]:
            print("La version des mods est la bonne. Pas besoin de retélécharger les mods !")

        # sinon on télécharge les mods
        else:
            print("La version des mods n'est pas pas la bonne. Mise à jour des mods !")
            for file in os.listdir(mods_folder):
                os.remove(mods_folder + "/" + file)
                print(f"Suppression du mod {file}")
            downloadMods()

    def start_game(parameter):
        options = {"username": parameter["name"],
                   "uuid": parameter["id"],
                   "token": parameter["access_token"],
                   "launcherName": 'Les Coupains Launcher',
                   "launcherVersion": "0.1",
                   "customResolution": launcher_ini.getboolean('SETTING_MINECRAFT', 'custom_resolution'),
                   "resolutionWidth": launcher_ini.get('SETTING_MINECRAFT', 'width'),
                   "resolutionHeight": launcher_ini.get('SETTING_MINECRAFT', 'height'),
                   "jvmArguments": ["-Xmx2G", "-Xms2G"]
                   }  # "server": None -> don't work

        if launcher_ini.getboolean('SETTING_MINECRAFT', 'show_console'):
            options['executablePath'] = 'java'
        else:
            options['executablePath'] = 'javaw'

        if launcher_ini.getboolean('SETTING_MINECRAFT', 'auto_connect'):
            options['server'] = launcher_ini.get('SETTING_MINECRAFT', 'server')
        xmx = launcher_ini.get('SETTING_MINECRAFT', 'xmx')
        xms = launcher_ini.get('SETTING_MINECRAFT', 'xms')
        options["jvmArguments"] = [f"-Xmx{xmx}M", f"-Xms{xms}M"]
        print(options)

        command = minecraft_launcher_lib.command.get_minecraft_command(full_name_forge_version, minecraft_directory, options)
        call(command)
        sys.exit(0)

    def launch():
        global login_data
        config_ini.read('config.ini')
        remember1 = config_ini.get('LOGIN', 'remember')
        window.withdraw()
        if int(remember1) == 1:
            fernet2 = Fernet(key)
            login_data = literal_eval(fernet2.decrypt(literal_eval(config_ini.get('LOGIN', 'login_data'))).decode())
            start_game(login_data)
        elif int(remember1) == 0:
            start_game(login_data)

    def create_config_file():
        os.remove('config.ini')
        with open('config.ini', 'w') as file5:
            new_config = ConfigParser()
            new_config.read('config.ini')
            new_config.add_section('LOGIN')
            new_config['LOGIN']['remember'] = "0"
            new_config.write(file5)

    def setting():
        def save():
            xmx = xmx_entry.get()
            xms = xms_entry.get()
            width = width_entry.get()
            height = height_entry.get()
            print(f'Xmx : {xmx} ; Xms : {xms} ; Width : {width} ; Height : {height}')
            if radio_var.get() == 0 and (str(width) == '' or str(height) == '') or str(xmx) == '' or str(xms) == '':
                print('You can\'t save')
                messagebox.showerror(title='Error',
                                     message='You can\'t save with an empty value')
            else:
                with open("launcher.ini", "w") as file:
                    print('saving...')

                    if console_variable.get() == 1:
                        launcher_ini['SETTING_MINECRAFT']['show_console'] = 'True'
                    elif console_variable.get() == 0:
                        launcher_ini['SETTING_MINECRAFT']['show_console'] = 'False'

                    if radio_var.get() == 1:
                        launcher_ini['SETTING_MINECRAFT']['custom_resolution'] = 'False'
                    elif radio_var.get() == 0:
                        launcher_ini['SETTING_MINECRAFT']['custom_resolution'] = 'True'
                        launcher_ini['SETTING_MINECRAFT']['width'] = str(width)
                        launcher_ini['SETTING_MINECRAFT']['height'] = str(height)

                    launcher_ini['SETTING_MINECRAFT']['xmx'] = str(xmx)
                    launcher_ini['SETTING_MINECRAFT']['xms'] = str(xms)

                    launcher_ini.write(file)

        def change_state_radiobutton(state):
            if state == 'disable':
                print('custom resolution disable')
                height_entry.delete(0, END)
                width_entry.delete(0, END)
                height_entry.configure(state="disabled")
                width_entry.configure(state="disabled")
                height_var = StringVar()
                width_var = StringVar()
                width_var.set(config_dict.get('width'))
                height_var.set(config_dict.get('height'))
                height_entry.configure(textvariable=height_var)
                width_entry.configure(textvariable=width_var)
            elif state == 'enable':
                print('custom resolution enable')
                height_entry.configure(state="normal")
                height_entry.delete(0, END)
                height_entry.insert(END, config_dict.get('height'))
                width_entry.configure(state="normal")
                width_entry.delete(0, END)
                width_entry.insert(END, config_dict.get('width'))

        def reset():
            if messagebox.askokcancel(title="Reset config",
                                      message='Are you sure you want to reset the launcher settings ?'):
                create_config_file()
                os.remove('launcher.ini')
                with open('launcher.ini', 'w') as file:
                    reset_launcher = ConfigParser()
                    reset_launcher.read('launcher.ini')
                    reset_launcher.add_section('SETTING_FRAME')
                    reset_launcher.add_section('SETTING_MINECRAFT')
                    reset_launcher['SETTING_FRAME']['setting_title'] = "Settings"
                    reset_launcher['SETTING_FRAME']['setting_geometry'] = "600x350"
                    reset_launcher['SETTING_MINECRAFT']['server'] = "kipikcube.tk"
                    reset_launcher['SETTING_MINECRAFT']['show_console'] = "False"
                    reset_launcher['SETTING_MINECRAFT']['custom_resolution'] = "False"
                    reset_launcher['SETTING_MINECRAFT']['width'] = "854"
                    reset_launcher['SETTING_MINECRAFT']['height'] = "480"
                    reset_launcher['SETTING_MINECRAFT']['xmx'] = "2000"
                    reset_launcher['SETTING_MINECRAFT']['xms'] = "500"

                    reset_launcher.write(file)
                messagebox.showwarning(title='Restart Launcher', message='The launcher will close, please relaunch it')
                sys.exit(0)

        setting_title = launcher_ini.get('SETTING_FRAME', 'setting_title')
        setting_geometry = launcher_ini.get('SETTING_FRAME', 'setting_geometry')
        setting_window = CTkToplevel()
        setting_window.geometry(setting_geometry)
        setting_window.title(setting_title)
        setting_window.resizable(width=False, height=False)
        # setting_window.iconbitmap('assets/kipikcube.ico')
        setting_window.grab_set()

        config_dict = launcher_ini['SETTING_MINECRAFT']
        custom = config_dict.getboolean('custom_resolution')
        if custom:
            valeur = 0
        else:
            valeur = 1

        label_resolution = CTkLabel(setting_window, text='Résolution', font=('Impact', 15))
        width_entry = CTkEntry(setting_window, width=50, placeholder_text='854px')
        height_entry = CTkEntry(setting_window, width=50, placeholder_text='480px')
        width_label = CTkLabel(setting_window, text='Largeur :')
        height_label = CTkLabel(setting_window, text='Hauteur :')
        radio_var = IntVar(value=valeur)
        default_resolution = CTkRadioButton(setting_window, text='Résolution par défaut', variable=radio_var,
                                            command=partial(change_state_radiobutton, 'disable'), value=1)
        custom_resolution = CTkRadioButton(setting_window, text='Résolution personnalisée :', variable=radio_var,
                                           command=partial(change_state_radiobutton, 'enable'), value=0)
        if custom:
            change_state_radiobutton('enable')
        else:
            height_entry.configure(state="disabled")
            width_entry.configure(state="disabled")

        save_button = CTkButton(setting_window, text='SAVE', font=('Impact', 20), command=save, fg_color='green')
        label_jvm = CTkLabel(setting_window, text='Argument JVM', font=('Impact', 15))
        mo_label = CTkLabel(setting_window, text='Mo')
        mo_label1 = CTkLabel(setting_window, text='Mo')
        xmx_label = CTkLabel(setting_window, text='Xmx :')
        xms_label = CTkLabel(setting_window, text='Xms :')
        xmx_entry = CTkEntry(setting_window, width=65)
        xmx_entry.insert(END, config_dict.get('xmx'))
        xms_entry = CTkEntry(setting_window, width=65, placeholder_text=config_dict.getint('xms'))
        xms_entry.insert(END, config_dict.get('xms'))
        cancel_button = CTkButton(setting_window, command=setting_window.destroy, text='CANCEL/EXIT',
                                  font=('Impact', 20), fg_color='grey')
        console_variable = IntVar()
        console = CTkCheckBox(setting_window, text='Show console', variable=console_variable)
        console_value = config_dict.getboolean('show_console')
        if console_value:
            console.select()
        elif not console_value:
            console.deselect()

        reset_button = CTkButton(setting_window, text='Reset', width=20, fg_color='grey',
                                 command=reset)

        default_resolution.place(x=50, y=100)
        custom_resolution.place(x=50, y=150)
        label_resolution.place(x=100, y=50)
        width_label.place(x=85, y=200)
        height_label.place(x=85, y=250)
        width_entry.place(x=150, y=200)
        height_entry.place(x=150, y=250)
        save_button.place(x=50, y=300)
        cancel_button.place(x=400, y=300)
        label_jvm.place(x=380, y=50)
        xmx_label.place(x=350, y=100)
        xms_label.place(x=350, y=150)
        xmx_entry.place(x=400, y=100)
        xms_entry.place(x=400, y=150)
        mo_label.place(x=480, y=100)
        mo_label1.place(x=480, y=150)
        console.place(x=350, y=200)
        reset_button.place(x=20, y=10)
        setting_window.mainloop()

    if not os.path.exists('config.ini'):
        print('Aucun fichier n\'a été trouvé pour stocker le code de connexion')
        print('Création du fichier... ("config.ini")')
        with open('config.ini', 'w') as config_file:
            config_file.write('[LOGIN]\nremember = 0')

    key = b'gN12nuGGNSHu0pMFna0kG1jDqYNx1hyFwmW1jDUs494='
    id_ini = ConfigParser()
    launcher_ini = ConfigParser()
    config_ini = ConfigParser()
    # App Azure
    try:
        id_ini.read('id.ini')
        fernet1 = Fernet(key)
        client_id = fernet1.decrypt(literal_eval(id_ini.get('ID', 'client_id'))).decode()
        secret = fernet1.decrypt(literal_eval(id_ini.get('ID', 'secret'))).decode()
        redirect_url = fernet1.decrypt(literal_eval(id_ini.get('ID', 'redirect_url'))).decode()
    except (NoSectionError, NoOptionError, ParsingError) as error:
        print(f'Fichier corrompu \'id.ini\', merci de réinstaller le launcher : {error}')
        messagebox.showwarning(title='Erreur', message='Fichier corrompu \'id.ini\', merci de réinstaller le launcher')

    # Launcher Config DEFAULT
    launcher_ini.read('launcher.ini')
    try:
        config_ini.read('config.ini')
        remember = int(config_ini.get('LOGIN', 'remember'))
    except (NoSectionError, NoOptionError, ValueError, ParsingError) as error:
        print(f'Error, corrupted file \'config.ini\': {error}')
        print('Repairing file...')
        create_config_file()
        remember = 0

    set_appearance_mode("dark")  # Modes: system (default), light, dark
    set_default_color_theme("green")  # Themes: blue (default), dark-blue, green

    window = CTk()
    window.title("Les Coupains Launcher")
    # window.iconbitmap('assets/kipikcube.ico')
    window.geometry("720x480")
    window.resizable(width=False, height=False)
    fond = PhotoImage(file="assets/fond.png")
    cancan = CTkCanvas(master=window, width=720, height=480, highlightthickness=0)
    cancan.create_image(0, 0, anchor=NW, image=fond)
    cancan.place(x=-1, y=-1)

    text_starting = cancan.create_text(380, 100, text="Démarrage du Launcher", font=('Impact', 30))
    window.update()

    v = IntVar()
    bouton = CTkCheckBox(window, variable=v, text="Remember me")

    launch_button = CTkButton(window, text="PLAY", width=100, height=50, font=('Impact', 30), command=launch)
    login_button = CTkButton(window, text="LOGIN", width=100, height=50, font=('Impact', 30), command=login)

    logout_button = CTkButton(window, text="LOGOUT", width=55, height=10, command=logout, fg_color='red',
                              font=('Impact', 15))

    setting_button = CTkButton(window, text='Settings', width=0, height=0, border_spacing=0, fg_color='grey',
                               command=setting)

    # Répertoire de Minecraft
    minecraft_directory = installation.launcher_directory
    # Get Minecraft directory
    print(f"Minecraft directory : {minecraft_directory}")
    name_forge_version = "1.20.1-47.2.1"
    full_name_forge_version = "1.20.1-forge-47.2.1"

    update_forge()
    update_mods()

    setting_button.place(x=650, y=20)

    # applique les bons widgets en fonction de si l'utilisateur est logger sur le launcher ou non
    if remember == 1:
        widget_connect()
    else:
        widget_disconnect()

    cancan.delete(text_starting)

    window.mainloop()


current_max = None

if __name__ == "__main__":
    main()
