import os
import json
import requests
from time import sleep
from colorama import Fore, init
import webbrowser
import math

USER_FOLDER = './users'
API_URL = 'https://api-xji1.onrender.com'

init(autoreset=True)

if not os.path.exists(USER_FOLDER):
    os.makedirs(USER_FOLDER)

def color_text(text, phase=0):
    center = 128
    width = 127
    frequency = 2 * math.pi / len(text)
    colored_text = ''
    for i in range(len(text)):
        red = int((math.sin(frequency * i + 2 + phase) * width) + center)
        green = int((math.sin(frequency * i + 0 + phase) * width) + center)
        blue = int((math.sin(frequency * i + 4 + phase) * width) + center)
        color = f"\033[38;2;{red};{green};{blue}m"
        colored_text += color + text[i]
    return colored_text + Fore.RESET

HEADER_TEXT = color_text('''
                   _                    
 /\   /\___ _ __ | |_ _   _ _ __ __ _ 
 \ \ / / _ \ '_ \| __| | | | '__/ _` |
  \ V /  __/ | | | |_| |_| | | | (_| |
   \_/ \___|_| |_|\__|\__,_|_|  \__,_|
''', 0)

def print_header(username=None):
    clear_screen()
    print(HEADER_TEXT)
    if username:
        print(Fore.CYAN + f'Welcome Back to Ventura, {username}!')
    else:
        print(Fore.CYAN + 'Welcome to Ventura!')

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def load_profile():
    profile_files = [f for f in os.listdir(USER_FOLDER) if f.endswith('.json')]
    if profile_files:
        profile_path = os.path.join(USER_FOLDER, profile_files[0])
        with open(profile_path, 'r') as f:
            return json.load(f)
    return None

def change_cosmetic(display_name, account_id, token):
    skin_name = "Ventura"
    try:
        user_data_path = os.path.join(USER_FOLDER, f"{display_name}.json")
        with open(user_data_path, 'r') as file:
            profile_data = json.load(file)

        response = requests.get(f'https://fortnite-api.com/v2/cosmetics/br/search?name={skin_name}')
        skin_data = response.json().get('data')

        if not skin_data:
            print(Fore.RED + f'Skin "{skin_name}" not found. Exiting.')
            return

        skin_id = skin_data['id']
        party_url = f'https://party-service-prod.ol.epicgames.com/party/api/v1/Fortnite/user/{profile_data["AccountID"]}'
        party_response = requests.get(party_url, headers={'Authorization': f'Bearer {profile_data["Token"]}'})

        if party_response.status_code != 200:
            print(Fore.RED + 'You must be online. Exiting.')
            return

        party_data = party_response.json().get('current')
        
        if not party_data:
            print(Fore.RED + 'You must be online! Exiting.')
            return

        party_id = party_data[0]['id']
        member = next((m for m in party_data[0]['members'] if m['account_id'] == profile_data['AccountID']), None)

        if not member:
            print(Fore.RED + 'Member not found. Exiting.')
            return

        current_revision = member['revision']
        update_object = {
            "Default:AthenaCosmeticLoadout_j": json.dumps({
                "AthenaCosmeticLoadout": {
                    "characterPrimaryAssetId": f"AthenaCharacter:{skin_id}",
                    "characterEKey": "",
                    "backpackDef": "",
                    "backpackEKey": "",
                    "pickaxeDef": "",
                    "pickaxeEKey": "",
                    "contrailDef": "",
                    "contrailEKey": "",
                    "scratchpad": [],
                    "cosmeticStats": []
                }
            })
        }

        print(Fore.CYAN + 'Running...')
        while True:
            patch_response = requests.patch(
                f'https://party-service-prod.ol.epicgames.com/party/api/v1/Fortnite/parties/{party_id}/members/{profile_data["AccountID"]}/meta',
                json={
                    "delete": [],
                    "revision": current_revision,
                    "update": update_object
                },
                headers={'Authorization': f'Bearer {profile_data["Token"]}'}
            )

            if patch_response.status_code == 204:
                print(Fore.GREEN + f'Successfully changed to skin: {skin_name}!')
                break
            else:
                print(Fore.RED + f'Failed to change skin. Status Code: {patch_response.status_code}, Response: {patch_response.text}')
            sleep(0.5)

    except Exception as e:
        print(Fore.RED + f'Error changing skin: {e}')

def login(auth_code=None):
    profile = load_profile()
    if profile:
        print_header(profile["Username"])
        print(Fore.CYAN + 'Using saved login details...')
        change_cosmetic(profile["Username"], profile["AccountID"], profile["Token"])
        return

    webbrowser.open('https://www.epicgames.com/id/api/redirect?clientId=3f69e56c7649492c8cc29f1af08a8a12&responseType=code')

    while True:
        auth_code = input(Fore.GREEN + 'Authorization Code: ').strip()
        if auth_code:
            break

    try:
        print(Fore.CYAN + 'Logging In....')
        url = f'{API_URL}/oauth?authorization_code={auth_code}'
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        if 'access_token' not in data:
            print(Fore.RED + 'Invalid response from server.')
            sleep(3)
            login()
            return

        profile_data = {
            "Token": data['access_token'],
            "Username": data['display_name'],
            "AccountID": data['account_id'],
            "DeviceID": data['device_id'],
            "Secret": data['secret'],
            "Icon": data['icon']
        }

        profile_path = os.path.join(USER_FOLDER, f"{profile_data['Username']}.json")
        with open(profile_path, 'w') as f:
            json.dump(profile_data, f, indent=2)

        print(Fore.GREEN + f'Logged in as: {profile_data["Username"]}!')
        sleep(3)
        main_menu(profile_data["Username"], profile_data["AccountID"], profile_data["Token"])

    except requests.exceptions.RequestException as e:
        print(Fore.RED + f'Error during login: {e}')
        sleep(3)
        login()

def main_menu(display_name, account_id, token):
    print_header(display_name)

if __name__ == "__main__":
    print_header()
    login()
