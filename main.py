from src.osintVK import OsintVK
from src.color import colored
from pathlib import Path
import sys
import configparser
import vk_api

#### GOAL FOR TOMORROW - 1) Create config section checks

art_name = colored('cyan', """ 

 ▄██████▄     ▄████████  ▄█  ███▄▄▄▄       ███      ▄█    █▄     ▄█   ▄█▄ 
███    ███   ███    ███ ███  ███▀▀▀██▄ ▀█████████▄ ███    ███   ███ ▄███▀ 
███    ███   ███    █▀  ███▌ ███   ███    ▀███▀▀██ ███    ███   ███▐██▀   
███    ███   ███        ███▌ ███   ███     ███   ▀ ███    ███  ▄█████▀    
███    ███ ▀███████████ ███▌ ███   ███     ███     ███    ███ ▀▀█████▄    
███    ███          ███ ███  ███   ███     ███     ███    ███   ███▐██▄   
███    ███    ▄█    ███ ███  ███   ███     ███     ███    ███   ███ ▀███▄ 
 ▀██████▀   ▄████████▀  █▀    ▀█   █▀     ▄████▀    ▀██████▀    ███   ▀█▀ 
                                                                ▀              

                Author - AdrianGuretto. Version - 1.0
                                                                                                                                                                                   
""")

if __name__ == '__main__':
    if Path(Path.cwd(), 'config', 'settings.ini').exists() == False:
        print(colored('red', "[!] Wasn't able to locate 'settings.ini' in 'config' folder. Exiting.."))
        sys.exit(0)
    else:
        conf_path = Path(Path.cwd(), 'config', 'settings.ini')
        parser = configparser.ConfigParser()
        parser.read('config/settings.ini')

    print(art_name)
    try:
        login = parser['GENERAL']['LOGIN']
        pwd = parser['GENERAL']['PASSWORD']
    except Exception as e:
        print(colored('red', f"[!] A config parameter is missing ({e}).\nMake sure 'settings.ini' contains LOGIN, PASSWORD, and OUTPUT_FOLDER fields."))
        sys.exit(0)
    OsintVK(login=login, pwd=pwd, config_path=conf_path)