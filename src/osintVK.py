import configparser
from pathlib import Path
import traceback
import sys
import datetime
import os
import requests
import shutil

# External libraries
import vk_api 

# Local imports
from src.color import colored

## NOTES:
# Write code for transforming an profile picture into the ASCII characters.


sex_table = {0: 'N/S', 1: 'Female', 2: 'Male'}
vk_platforms = {1: 'WebMobile/Unidentified app', 2: 'iPhone', 3: 'iPad', 4: 'Android', 5: 'WindowsPhone', 6: 'Official Windows App', 7: 'Full Web version/Unidentified App'}
class OsintVK:
    is_json = False
    target_info_text = None
    target_post_text = None

    def __init__(self, login: str, pwd: str, config_path=None) -> None:
        """Author: AdrianGuretto

        Args:
            * login(str): User's login from VK.
            * pwd(str): User's password for the login.
            * config_path(path): A path to the 'settings.ini' file.
        """
        self.login, self.pwd = login, pwd

        conf_parser = configparser.ConfigParser()
        conf_parser.read(config_path)
        self.OUTPUT_FOLDER = Path(Path.home(), conf_parser['GENERAL']['OUTPUT_FOLDER'])
        if Path(self.OUTPUT_FOLDER).exists() == False:
            os.mkdir(self.OUTPUT_FOLDER)

        session = self._account_login(login, pwd, 51674211)
        self.target_acquire()
    
    @staticmethod
    def post_attachment_parse(post):
        """This method takes in a post object and then parses its attachments based on their types.
        
        Args:
            * post(dict): A VK post object
        
        Returns:
            * pi(LiteralString): Parsed attachment object in the post object
        """
        pi = ""
        pi += f"    PostAttachments:"
        attachment_count = 1
        for attachment in post['attachments']:
            attachment_type = attachment['type']
            pi += f"\n        {attachment_count}. AttachmentType: {attachment_type}\n"

            if attachment_type == 'photo':
                pi += f"           OwnerID: {str(attachment['photo']['owner_id'])}\n"
                for size in attachment['photo']['sizes']:
                    if size.get('type') == 'x':
                        photo_url = size.get('url')
                    else:
                        continue
                pi += f"           PhotoLink: {photo_url}\n"

                if attachment['photo']['text'] != '':
                    pi += f"           PhotoDescription: {attachment['photo']['text']}\n"
        
            
            if attachment_type == 'posted_photo': # Legacy attachment type
                pi += f"           OwnerID: {str(attachment['posted_photo']['owner_id'])}\n"
                pi += f"           PhotoLink: {attachment['posted_photo']['photo_604']}\n"
            
            if attachment_type == 'audio':
                pi += f"           Artist: {attachment['audio']['artist']}\n"
                pi += f"           Title: {attachment['audio']['title']}\n"
            
            if attachment_type == 'video':
                pi += f"           OwnerID: {str(attachment['video']['id'])}\n"
                pi += f"           VideoLink: https://vk.com/video{str(attachment['video']['owner_id'])}_{str(attachment['video']['id'])}\n"
                pi += f"           VideoTitle: {attachment['video']['title']}\n"
                pi += f"           VideoDuration: {attachment['video']['duration']}\n"
                pi += f"           VideoViews: {str(attachment['video']['views'])}\n"
                pi += f"           VideoUplDate: {datetime.datetime.fromtimestamp(attachment['video']['date']).strftime('%Y-%m-%d %H:%M:%S')}\n"
            
            if attachment_type == 'doc':
                doc_types = {1: 'Text', 2: 'Archive', 3: 'GIF', 4: 'Image', 5: 'Audio', 6: 'Video', 7: 'DigitalBook', 8: 'Unknown'}
                pi += f"           OwnerID: {str(attachment['doc']['owner_id'])}\n"
                pi += f"           DocTitle: {attachment['doc']['title']}\n"
                pi += f"           DocType: {doc_types[attachment['doc']['type']]}\n"
                pi += f"           DocExtension: {attachment['doc']['ext']}\n"
                pi += f"           DocDate: {datetime.datetime.fromtimestamp(attachment['doc']['date']).strftime('%Y-%m-%d %H:%M:%S')}\n"
                pi += f"           DocDownloadUrl (UNSAFE): {attachment['doc']['url']}\n"
            
            if attachment_type == 'link':
                pi += f"           LinkTitle: {attachment['link']['title']}\n"
                pi += f"           LinkUrl (UNSAFE): {attachment['link']['url']}\n"
                pi += f"           LinkDescription: {attachment['link']['description']}\n"
            attachment_count += 1
        return pi

    @staticmethod          
    def friends_analysis(friend_obj):
        """Analyses the friend list of the selected target. Processes the following friend list's attributes: 1) The most widespread country and city; 2) The most prevalent sex; 3) Average age.
        
        Args:
            * friend_list(obj,dict): Friends object returned from friends.get() method.
        
        Return:
            * processed_data(str): A string with the analysed data included.
        """
        countries = []
        cities = []
        genders = []
        ages = []
        report = "\n[USER STATS]\n"

        if len(friend_obj['items']) == 0:
            print(colored('red', '[!] Unable to examine the data because it is empty.'))
        else:
            try:
                for item in friend_obj['items']:
                    if 'country' in item.keys() and item['country'] != "":
                        countries.append(item['country']['title'])
                    if 'city' in item.keys() and item['city'] != "":
                        cities.append(item['city']['title'])
                    if 'sex' in item.keys() and item['sex'] != 0:
                        genders.append(sex_table[item['sex']])
                    if 'bdate' in item.keys() and item['bdate'] != "" and len(item['bdate'].split('.')) == 3:
                        ages.append(datetime.date.today().year - int(item['bdate'].split('.')[2]))

                #countries examining
                countries2 = countries.copy()
                most_pop_country1 = max(countries, key=countries.count, default=0)
                most_pop_country1_percentage = (countries.count(most_pop_country1) / len(countries)) * 100
                while most_pop_country1 in countries: countries.remove(most_pop_country1)
                most_pop_country2 = max(countries, key=countries.count, default=0)
                most_pop_country2_percentage = (countries2.count(most_pop_country2) / len(countries2)) * 100

                #cities examining
                cities2 = cities.copy()
                most_pop_city1 = max(cities, key=cities.count, default=0)
                most_pop_city1_percentage = (cities.count(most_pop_city1) / len(cities)) * 100
                while most_pop_city1 in cities: cities.remove(most_pop_city1)
                most_pop_city2 = max(cities, key=cities.count, default=0)
                most_pop_city2_percentage = (cities2.count(most_pop_city2) / len(cities2)) * 100

                #genders examining
                most_common_sex = max(genders, key=genders.count, default=0)
                sex_percentage = (genders.count(most_common_sex) / len(genders)) * 100

                #age examining
                avg_age = sum(ages) / len(ages)
                

                report += f"1stMostCommonCOUNTRY: {most_pop_country1} ({str(round(most_pop_country1_percentage, ndigits=2))} %) | 2ndMostCommonCountry: {most_pop_country2} ({str(round(most_pop_country2_percentage, ndigits=2))} %)\n"
                report += f"1stMostCommonCITY: {most_pop_city1} ({str(round(most_pop_city1_percentage, ndigits=2))} %) | 2ndMostCommonCITY: {most_pop_city2} ({str(round(most_pop_city2_percentage, ndigits=2))} %)\n"
                report += f"MostCommonSex: {most_common_sex} ({str(round(sex_percentage))} %)\n"
                report += f"AverageAge: {str(round(avg_age, ndigits=1))}\n"
                        
            except:
                print(colored('red', f"[!] An error has occurred while examining the friends data ({traceback.format_exc()})"))
        return report

    def _account_login(self, login, password, app_id):
        """Establishes connection to a stated user's account
        
        Args:
            * login(str): user's login
            * password(str): user'
        
        Returns:
            * response(bool): True when auth is successful, False when unsuccessful.
        """
        try: 
            print(f'\n[$] Trying to sign into ' + colored('green', f"<{login}>") + ' ...')
            session = vk_api.VkApi(login=login, password=password, auth_handler=self._2FA, captcha_handler=self._captchaHandler)
            session.auth(token_only=True)
        except vk_api.exceptions.BadPassword:
            print(colored('red', "[!] Failed to authenticate (wrong username or password)."))
            sys.exit(2)
        self.vk_method = session.get_api()

        print(colored('green', f'\n[$] Successfully logged into <{login}>!'))
    
    def target_acquire(self):
        """Asks for target user's ID or screen name, verifies that the target exists, 
        checks for all applicable to the target actions depending on privacy status of the page, prints relevant info about target's page.
        """
        while True:
            self.target = input("\n[*] Enter your target's ID or screen name (maxwell123) or 'q' to exit: ")
            if self.target == 'Q' or self.target == 'q':
                sys.exit(0)
            if self.target.isdigit():
                self.target = 'id' + self.target

            name_info = self.vk_method.utils.resolveScreenName(screen_name=self.target)
            if name_info == []:
                print(colored('pink', f'[*] User <{self.target}> does not exists.'))
                continue
            if name_info['type'] == 'user':  ## For now, it only works for users, not groups
                self.target = name_info['object_id']
                while True:
                    try:
                        target_info = self.targetinfo(initial_check=1)
                        availablity = self.check_available_actions(target_info)

                        if availablity == 'private':
                            print("[TARGET INFO]")
                            pit = "\nAvailable Information:\n\n" # Private Information Text
                            pit += f"UserID: {target_info[0]['id']}\n"
                            pit += f"ScreenName: {target_info[0]['screen_name']}\n"
                            if target_info[0]['verified'] == 1:
                                verified = True
                            else:
                                verified = False
                            pit += f"Verified: {str(verified)}\n"

                            pit += f"FirstName: {target_info[0]['first_name']}\n"
                            pit += f"LastName: {target_info[0]['last_name']}\n"

                            pit += f"Sex: {sex_table[target_info[0]['sex']]}\n"

                            if 'bdate' in target_info[0].keys() and target_info[0]['bdate'] != '':
                                pit += f"Birthday: {target_info[0]['bdate']}\n"
                            
                            if 'country' in target_info[0].keys() and target_info[0]['country'] != '':
                                pit += f"Country: {target_info[0]['country']}\n"
                            
                            if 'city' in target_info[0].keys() and target_info[0]['city'] != '':
                                pit += f"City: {target_info[0]['city']}\n"
                            
                            last_seen_device:str = vk_platforms[target_info[0]['last_seen']['platform']]
                            last_seen_time:str = datetime.datetime.fromtimestamp(target_info[0]['last_seen']['time']).strftime('%Y-%m-%d %H:%M:%S')
                            pit += f"LastSeen: {last_seen_time} from {last_seen_device}\n"

                            pit += f"ProfilePic: {target_info[0]['photo_max_orig']}\n"

                            if 'status' in target_info[0].keys() and target_info[0]['status']:
                                pit += f"Status: {target_info[0]['status']}\n\n"
                            
                            if 'counters' in target_info[0].keys() and target_info['counters'] != {}:
                                if 'friends' in target_info[0]['counters'].keys():
                                   pit += f"Friends: {str(target_info[0]['counters']['friends'])}\n"
                                if 'pages' in target_info[0]['counters'].keys():
                                    pit += f"InterestingPages: {str(target_info[0]['counters']['pages'])}\n"
                                if 'posts' in target_info[0]['counters'].keys():
                                    pit += f"Posts: {str(target_info[0]['counters']['posts'])}\n\n"
                            if target_info[0]['can_write_private_message'] == 1:
                                can_chat_with = True
                            else:
                                can_chat_with = False
                            pit += f"CanSendMessages: {str(can_chat_with)}\n"
                            
                            print(pit)
                            self.target = ""
                            break
                            
                        if availablity == 'blocked':
                            print("[TARGET INFO]")
                            bit = "\nAvailable Information:\n\n" # Private Information Text
                            bit += f"UserID: {target_info[0]['id']}\n"
                            bit += f"ScreenName: {target_info[0]['screen_name']}\n"

                            bit += f"FirstName: {target_info[0]['first_name']}\n"
                            bit += f"LastName: {target_info[0]['last_name']}\n"

                            bit += f"Sex: {sex_table[target_info[0]['sex']]}\n"

                            if 'bdate' in target_info[0].keys() and target_info[0]['bdate'] != '':
                                bit += f"Birthday: {target_info[0]['bdate']}\n"
                            
                            if 'country' in target_info[0].keys() and target_info[0]['country'] != '':
                                bit += f"Country: {target_info[0]['country']}\n"
                            
                            if 'city' in target_info[0].keys() and target_info[0]['city'] != '':
                                bit += f"City: {target_info[0]['city']}\n"
                            
                            last_seen_device:str = vk_platforms[target_info[0]['last_seen']['platform']]
                            last_seen_time:str = datetime.datetime.fromtimestamp(target_info[0]['last_seen']['time']).strftime('%Y-%m-%d %H:%M:%S')
                            bit += f"LastSeen: {last_seen_time} from {last_seen_device}\n"

                            bit += f"ProfilePic: {target_info[0]['photo_max_orig']}\n"

                            if 'status' in target_info[0].keys() and target_info[0]['status']:
                                bit += f"Status: {target_info[0]['status']}\n\n"
                            
                            if 'counters' in target_info[0].keys() and target_info['counters'] != {}:
                                if 'friends' in target_info[0]['counters'].keys():
                                   bit += f"Friends: {str(target_info[0]['counters']['friends'])}\n"
                                if 'pages' in target_info[0]['counters'].keys():
                                    bit += f"InterestingPages: {str(target_info[0]['counters']['pages'])}\n"
                                if 'posts' in target_info[0]['counters'].keys():
                                    bit += f"Posts: {str(target_info[0]['counters']['posts'])}\n\n"
                            if target_info[0]['can_write_private_message'] == 1:
                                can_chat_with = True
                            else:
                                can_chat_with = False
                            bit += f"CanSendMessages: {str(can_chat_with)}\n"
                            
                            print(bit)
                            self.target = ""
                            break
                        
                        if availablity == True:
                            try:
                                self.target_subfolder_path = Path(self.OUTPUT_FOLDER, f"{str(self.target)}_{self.target_info_text[0]['first_name']}{self.target_info_text[0]['last_name']}")
                                os.mkdir(self.target_subfolder_path)
                            except FileExistsError:
                                pass
                            self.command_capture()
                            break
                    except:
                        print(colored('red', f'[!] An error has occurred while processing the request ({traceback.format_exc()})\n Try again.'))
            else:
                print(colored('yellow', '[i] This is ID of a group. Enter ID of a targetted USER.'))


    def check_available_actions(self, target_info):
        """Checks for privacy setting of the target
        
        Args:
            * target_info(list): An object received from self.vk_method.users.get(...)
        
        Returns:
            * 'private': When the target's profile is closed by privacy settings
            * 'blocked': When your account has been blacklisted by the target.
        """
        print('[i] Initializing availability check...')
        if 'deactivated' in target_info[0].keys():
            deactivated = target_info[0]['deactivated']
            if deactivated == 'deleted':
                print(colored('pink', '[i] This account has been deleted.'))
            if deactivated == 'banned':
                print(colored('pink', '[i] This account has been banned.'))

        elif target_info[0]['can_access_closed'] == False:
            print(colored('cyan', f"[i] Profile {target_info[0]['id']} is private. You cannot access it fully."))
            return 'private'
        
        elif target_info[0]['blacklisted'] == 1:
            print(colored('cyan', f"[i] User {target_info[0]['id']} has blacklisted you. You cannot access it fully."))
            return 'blocked'
        else:
            return True
     

    def commands_list(self):
        """List of available commands.""" 
        print('------------------------------------------------\n')
        print("Available Commands List for the targeted user: ")
        print("Usage: <command> <args>")
        print("If you wish to target another user, type 'EXIT'.")
        print("!!! To save command output in into JSON-like format, type 'JSON' to turn it on or off. !!!")
        print("You may also save output to the output folder by prepending 'F' to a command. Example: 'F targetinfo'")
        print("NOTE: all standalone output files are saved accordingly: 'targetid_command.extension'. When using commands with multiple output, a folder (target_command) is created, and all the files will stored there.")
        print("<CMD>              : Pull up the command list")
        print("\nGENERAL INFO")
        print("<targetinfo>       : Retrieve general information about the target.")
        print("<getprofpic>       : Get target's profile pic.")
        print("\nWALL INFO")
        print("<getposts>         : Get all target's wallposts(text).")
        print("<getpostimgs>      : Get all target's wallposts with images attached in a separate folder.")
        print("<getpostreacts>    : Retrieve info about users who commented or liked target's posts.")
        print("\nPHOTO INFO")
        print("<getalbums>        : Return a list of target's albums.")
        print("<getalbimgs>       : Return a list of photos in a specific album. Args: ALBUM_ID or ALBUM_TYPE ('saved', 'profile', 'wall')")
        print("\nFRIENDS INFO")
        print("<getfriends>       : Retrieve a list of target's friends.")
        print("<gettargetmutual>  : Return a list of target's and check against another user. Args: USER_ID")
        print("\nGROUP INFO")
        print("<getgroups>        : Get a list of target's groups.")
        print("<getgroupmembers>  : Get a list of group members (irregardless the target).")
        print("<checkgroupmember> : Check whether the tartget is a member of a group. Args: GROUP_ID")
        print("\nGEO INFO")
        print("<getgeopins>       : Retrieve information about target's geo tags. IN DEVELOPMENT...")
        print('\nFULL INFO')
        print("<fullosint>        : Get all the information about the target in a separate folder.\n")

    def command_capture(self):
        """Takes in an executable command from a user, dispatches it to the right function."""
        self.commands_list()
        commands = {'targetinfo':self.targetinfo, 'getprofpic':self.getprofpic, 'getposts':self.getposts, 'getpostimgs':self.getpostsimgs, 'getalbums':self.getalbums, 'getfriends':self.getfriends, 'getgroups':self.getgroups, 'getgeopins':self.getgeopins, 'fullosint':self.fullosint, 'getalbimgs':self.getalbimgs, 'getpostreacts':self.getpostsreacts, 'gettargetmutual':self.gettargetmutual, 'checkgroupmember':self.checkgroupmember, 'getgroupmembers':self.getgroupmembers}

        while True:
            command = input(colored('grey','[^] Execute a command: \n')).split(' ')
            try:
                if 'EXIT' in command:
                    break

                if 'JSON' in command:
                    if self.is_json == False:
                        self.is_json = True
                        print(colored('yellow', '[*] JSON output is on.'))
                    if self.is_json == True:
                        self.is_json = False
                        print(colored('yellow', '[*] JSON output is off.'))
                
                elif 'CMD' in command:
                    self.commands_list()
                
                elif any(commands.keys()) in command:
                    continue

                elif command[0] != 'F' and command[0] in commands:
                    if len(command) > 2:
                        print(colored('pink', f'[*] Too many arguments for a command {command[0]}.'))
                    elif len(command) == 1:
                        output = commands[command[0]]()
                        print(output)
                    elif len(command) == 2:
                        output = commands[command[0]](arg=command[1])
                        print(output)
                
                elif command[0] == 'F' and command[1] in commands:
                    # F cmd arg
                    if len(command) > 3:
                        print(colored('pink', f'[*] Too many arguments for a command {command[0]}.'))
                    elif len(command) == 2:
                        output = commands[command[1]](data_output=True)
                        print(output)
                    elif len(command) == 3:
                        output = commands[command[1]](arg=command[2], data_output=True)
                        print(output)
                else:
                    print(colored('pink', f"[!] Unknown or mistyped command."))

            except IndexError as e:
                print(colored('pink', f"[!] Unknown or mistyped command '{command[0]}'. ({traceback.format_exc()})"))
            
    ### Callable commands

    def targetinfo(self, data_output=False, initial_check=0):
        """Retrieves info about a target

        Args:
            * detailed(bool): By default, False; if True, the function will return detailed info about a target.

        Returns:
            * target_info(list, json): General info about the target in the JSON format.
            * target_info_detailed(str): General info about the target in the parsed format.
        """ 
        target_info = self.vk_method.users.get(user_ids=self.target, fields=['deactivated', 'verified', 'blacklisted', 'uid', 'screen_name', 'first_name', 'last_name', 'sex', 'bdate', 'city', 'country', 'home_town', 'photo_max_orig', 'has_mobile', 'contacts', 'site', 'education', 'universities', 'schools', 'status', 'last_seen', 'followers_count', 'counters', 'relatives', 'relation', 'personal', 'connections', 'activities', 'interests', 'music', 'movies', 'tv', 'books', 'games', 'about', 'quotes', 'can_see_all_posts', 'can_see_audio', 'can_write_private_message', 'timezone'], )
        self.target_info_text = target_info
        if initial_check == 1:
            return target_info
        if self.is_json == True:
            return target_info
        
        if self.is_json == False:
            tid = "" # target info detailed
            tid += f"\n\n[TECH INFO]\n"
            tid += f"UserID: {str(target_info[0]['id'])}\n"
            tid += f"ScreenName: {target_info[0]['screen_name']}\n"

            if target_info[0]['verified'] == 1:
                verified = True
            else:
                verified = False
            tid += f"Verified: {str(verified)}\n"

            last_seen_device:str = vk_platforms[target_info[0]['last_seen']['platform']]
            last_seen_time:str = datetime.datetime.fromtimestamp(target_info[0]['last_seen']['time']).strftime('%Y-%m-%d %H:%M:%S')
            tid += f"LastSeen: {last_seen_time} from {last_seen_device}\n"

            if target_info[0]['can_write_private_message'] == 1:
                can_chat_with = True
            else:
                can_chat_with = False
            tid += f"CanSendMessages: {str(can_chat_with)}\n\n"

            # -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
            tid += "[GENERAL INFO]\n"
            tid += f"FirstName: {target_info[0]['first_name']}\n"
            tid += f"LastName: {target_info[0]['last_name']}\n"

            if target_info[0]['sex'] == 1:
                sex = 'Female'
            elif target_info[0]['sex'] == 2:
                sex = 'Male'
            tid += f"Sex: {sex}\n"

            if 'bdate' in target_info[0].keys() and target_info[0]['bdate'] != '':
                tid += f"Birthday: {target_info[0]['bdate']}\n"
            
            tid += f"ProfilePic: {target_info[0]['photo_max_orig']}\n"

            if target_info[0]['status'] != '':
                tid += f"Status: {target_info[0]['status']}\n"

            if 'country' in target_info[0].keys():
                tid += f"CurrentCountry: {target_info[0]['country']['title']}\n"
            
            if 'city' in target_info[0].keys():
                tid += f"CurrentCity: {target_info[0]['city']['title']}\n"
            
            if 'home_town' in target_info[0].keys() and target_info[0]['home_town'] != '':
                tid += f"Hometown: {target_info[0]['home_town']}\n"
            
            if 'site' in target_info[0].keys() and target_info[0]['site'] != '':
                tid += f"Site: {target_info[0]['site']}\n"
            
            if 'mobile_phone' in target_info[0].keys() and target_info[0]['mobile_phone'] != '':
                tid += f"MobilePhone: {target_info[0]['mobile_phone']}\n"
            
            if 'mobile_phone' in target_info[0].keys() and target_info[0]['home_phone'] != '':
                tid += f"HomePhone: {target_info[0]['home_phone']}\n"
            
            if 'relatives' in target_info[0].keys() and target_info[0]['relatives'] != []:
                rel_num = 1
                tid += 'Relative(s):\n'
                for relative in target_info[0]['relatives']:
                    rel_type = relative['type']
                    if 'id' in relative.keys():
                        try:
                            rel_info = self.vk_method.users.get(user_ids=relative['id'], fields=['first_name', 'last_name'])[0]
                            tid += f"   {rel_num}) Name: {rel_info['first_name']} {rel_info['last_name']}, Relation: {rel_type}, UID: {str(relative['id'])}\n"
                        except:
                            print(colored('red', f"[!] Unable to retrieve data for the relative ID {str(relative['id'])}."))
                            continue
                    elif 'id' in relative.keys() and 'name' in relative.keys():
                        tid += f"   {rel_num}) Name: {relative['name']}, Relation: {rel_type}, UID: {str(relative['id'])}\n"
                    else:
                        tid += f"   {rel_num}) Name: {relative['name']}, Relation: {rel_type}\n"
                    rel_num += 1
            
            if 'relation' in target_info[0].keys() and target_info[0]['relation'] != [] and target_info[0]['relation'] != 0:
                relation = {1: 'Single', 2: 'In a Relationship', 3: 'Engaged', 4: 'Married', 5: 'It Is Complicated', 6: 'Actively Searching', 7: 'In Love'}
                tid += f"RelationStatus: {relation[target_info[0]['relation']]}\n"
                if 'relation_partner' in target_info[0].keys():
                    tid += f"RelationPartner: {target_info[0]['relation_partner']['first_name']} {target_info[0]['relation_partner']['last_name']}, UID: {str(target_info[0]['relation_partner']['id'])}\n"
            
            if 'interests' in target_info[0].keys() and target_info[0]['interests'] != '':
                tid += f"Interests: {target_info[0]['interests']}\n"
            
            if 'books' in target_info[0].keys() and target_info[0]['books'] != '':
                tid += f"FavBooks: {target_info[0]['books']}\n"
            
            if 'tv' in target_info[0].keys() and target_info[0]['tv'] != '':
                tid += f"FavTVShow: {target_info[0]['tv']}\n"

            if 'quotes' in target_info[0].keys() and target_info[0]['quotes'] != '':
                tid += f"Quotes: {target_info[0]['quotes']}\n"

            if 'about' in target_info[0].keys() and target_info[0]['about'] != '':
                tid += f"About: {target_info[0]['about']}\n"

            if 'games' in target_info[0].keys() and target_info[0]['games'] != '':
                tid += f"FavGames: {target_info[0]['games']}\n"

            if 'movies' in target_info[0].keys() and target_info[0]['movies'] != '':
                tid += f"FavMovies: {target_info[0]['movies']}\n"

            if 'activities' in target_info[0].keys() and target_info[0]['activities'] != '':
                tid += f"Activities: {target_info[0]['activities']}\n"

            if 'music' in target_info[0].keys() and target_info[0]['music'] != '':
                tid += f"FavMusic: {target_info[0]['music']}\n"
            
            if 'personal' in target_info[0].keys() and target_info[0]['personal'] != '':
                personal = target_info[0]['personal']
                political_views = {1: 'Communist', 2: 'Socialist', 3: 'Moderate', 4: 'Liberal', 5: 'Conservative', 6: 'Monarchist', 7: 'Ultraconservative', 8: 'Apathetic', 9: 'Libertian'}
                important_in_people = {1: 'intellect and creativity', 2: 'kindness and honesty', 3: 'health and beauty', 4: 'wealth and power', 5: 'courage and persistance', 6: 'humor and love for life'}
                personal_priority = {1: ' family and children', 2: 'career and money', 3: 'entertainment and leisure', 4: 'science and research', 5: 'improving the world', 6: 'personal development', 7: 'beauty and art', 8: 'fame and influence'}
                smoking_view = {1: 'very negative', 2: 'negative', 3: 'neutral', 4: 'compromisable', 5: 'positive'}
                alcohol_view = {1: 'very negative', 2: 'negative', 3: 'neutral', 4: 'compromisable', 5: 'positive'}
                if 'political' in personal.keys() and personal['political'] != '':
                    tid += f"PolicalViews: {political_views[personal['political']]}\n"
                if 'langs' in personal.keys() and personal['langs'] != '':
                    tid += f"Languages: "
                    for lang in personal['langs']:
                        tid += f"{lang}, "
                    tid += '.\n'
                if 'religion' in personal.keys() and personal['religion'] != '':
                    tid += f"Religion: {personal['religion']}\n"
                if 'inspired_by' in personal.keys() and personal['inspired_by'] != '':
                    tid += f"InspiredBy: {personal['inspired_by']}\n"
                if 'people_main' in personal.keys() and personal['people_main'] != 0:
                    tid += f"ImportantInOthers: {important_in_people[personal['people_main']]}\n"
                if 'life_main' in personal.keys() and personal['life_main'] != 0:
                    tid += f"PersonalPriority: {personal_priority[personal['life_main']]}\n"
                if 'smoking' in personal.keys() and personal['smoking'] != 0:
                    tid += f"ViewsOnSmoking: {smoking_view[personal['smoking']]}\n"
                if 'alcohol' in personal.keys() and personal['alcohol'] != 0:
                    tid += f"ViewsOnAlcohol: {alcohol_view[personal['alcohol']]}\n"
            
            tid += f"FriendCount: {str(target_info[0]['counters']['friends'])}\nFollowerCount: {str(target_info[0]['counters']['followers'])}\nOnlineFriends: {str(target_info[0]['counters']['online_friends'])}\nVideoCount: {str(target_info[0]['counters']['videos'])}\nAudioCount: {str(target_info[0]['counters']['audios'])}\n"
            if 'groups' in target_info[0]['counters']:
                tid += f"GroupCount: {str(target_info[0]['counters']['groups'])}\n"

            
            # -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
            tid += "\n[EDUCATION]\n"


            if 'university' in target_info[0].keys() and target_info[0]['university'] != 0:
                curr_university_id = str(target_info[0]['university'])
                curr_university_name = target_info[0]['university_name']
                tid += f"CurrentUniversity: {curr_university_name}\nUniversityID: {curr_university_id}\n"

                if 'faculty' in target_info[0].keys() and target_info[0]['faculty'] != 0:
                    curr_faculty_id:int = target_info[0]['faculty']
                    curr_faculty_name = target_info[0]['faculty_name']
                    tid += f"CurrentFaculty: {curr_faculty_name}\nFacultyID: {curr_faculty_id}\n"

                if 'graduation' in target_info[0].keys() and target_info[0]['graduation'] != 0:
                    tid += f"CurrentGraduationYear: {str(target_info[0]['graduation'])}\n"
            
            if 'schools' in target_info[0].keys() and target_info[0]['schools'] != []:
                school_num = 1
                tid += f"AttendedSchool(s):\n"
                for school in target_info[0]['schools']:
                    school_id:int = school['id']
                    school_country = self.vk_method.database.getCountriesById(country_ids=school['country'])[0]['title']
                    school_city = self.vk_method.database.getCitiesById(city_ids=school['city'])[0]['title']
                    school_name:str = school['name']
                    tid += f"   {school_num}) SchoolName: {school_name}, SchoolID: {school_id}, SchoolCountry: {school_country}, SchoolCity: {school_city}"
                    if 'year_from' in school.keys():
                        tid += f", YearFrom: {str(school['year_from'])}"
                    if 'year_to' in school.keys():
                        tid += f", YearTo: {str(school['year_to'])}"
                    if 'year_graduated' in school.keys():
                        tid += f", YearGraduated: {str(school['year_graduated'])}"
                    if 'class' in school.keys():
                        tid += F", ClassLetter: {school['class']}"
                    if 'speciality' in school.keys():
                        tid += f", Speciality: {school['speciality']}"
                    tid += "\n"
                    school_num += 1
                
            if 'universities' in target_info[0].keys() and target_info[0]['universities'] != []: ### WORK ON THIS
                uni_num = 1
                tid += f"AttendedUniversities:\n"
                for uni in target_info[0]['universities']:
                    uni_id = uni['id']
                    if uni['country'] != 0:
                        uni_country = self.vk_method.database.getCountriesById(country_ids=uni['country'])[0]['title']
                    else:
                        uni_country = "N/S"
                    if uni['city'] != 0:
                        uni_city = self.vk_method.database.getCitiesById(city_ids=uni['city'])[0]['title']
                    else:
                        uni_city = "N/S"
                    uni_name = uni['name']
                    tid += f"   {uni_num}) UniversityName: {uni_name}, UniversityID: {str(uni_id)}, UniversityCountry: {uni_country}, UniversityCity: {uni_city}"
                    if 'faculty' in uni.keys():
                        tid += f", Faculty: {uni['faculty_name']}, FacultyID: {str(uni['faculty'])}"
                    if 'chair' in uni.keys():
                        tid += f", Chair: {uni['chair_name']}, ChairID: {str(uni['chair'])}"
                    if 'graduation' in uni.keys():
                        tid += f", GraduationYear: {str(uni['graduation'])}" 
                    uni_num += 1
                tid += '\n\n'
            
            if tid.endswith('[EDUCATION]\n'):
                tid += 'None'
            
            if data_output == False:
                return tid
            if data_output == True:
                print(tid)
                with open(Path(self.target_subfolder_path, f"{self.target}_targetinfo.txt"), 'w') as f:
                    f.write(tid)
                return colored('cyan', f"[i] Saved the result to the output folder :)")
                
    
    def getprofpic(self, data_output=False):
        """Returns a link to target's profile picture

        Returns:
            pic_url(str, url): A link to the avatar.
        """
        pic_url = self.target_info_text[0]['photo_max_orig']
        if data_output == True:
            pic = requests.get(self.target_info_text[0]['photo_max_orig']).content
            with open(Path(self.target_subfolder_path, f"{self.target}_getprofpic.jpg"), 'wb') as f:
                f.write(pic)
            return colored('cyan', f"[i] Saved the result to the output folder :)")
        else:
            return pic_url

    def getposts(self, data_output=False):
        """Returns a number of target's posts, links to them, links to posts' images, and their description.
        
        Returns:
            * posts(list): A list with target's posts objects. The following fields are returned: {post_id - ,  
        """
        pi = "" # Posts Info
        posts = self.vk_method.wall.get(owner_id=self.target, filter='owner') # owner_id=self.target, 
        
        pi += f"\n[POST INFO FOR UID {str(self.target)}]\n"
        pi += f"TotalPosts: {str(posts['count'])}\n"
        pi += f"\n[POSTS]"
        post_count:str = 1
        for post in posts['items']:
            if 'is_pinned' in post:
                pi += f"[PINNED POST]\n"
            pi += f"\n{post_count}) PostID: {post['id']}\n"
            pi += f"    PostLink: https://vk.com/wall{self.target}_{post['id']}\n"
            pi += f"    PostDate: {datetime.datetime.fromtimestamp(post['date']).strftime('%Y-%m-%d %H:%M:%S')}\n"
            pi += f"    PostLikes: {post['likes']['count']}\n"
            pi += f"    PostComments: {post['comments']['count']}\n"
            pi += f"    PostReposts: {post['reposts']['count']}\n"
            if post['text'] != '':
                pi += f"    PostText: {post['text']}\n"
            
            if 'copy_history' in post.keys():
                pi += "    PostType: Repost\n"

                if str(post['copy_history'][0]['owner_id']).startswith('-'):
                    pi += f"    RepostedFrom: Group; GroupID: {post['copy_history'][0]['owner_id']}\n\n"

                else:
                    pi += f"    RepostedFrom: User; UserID: {post['copy_history'][0]['owner_id']}\n"

                pi += f"    RPostDate: {datetime.datetime.fromtimestamp(post['copy_history'][0]['date']).strftime('%Y-%m-%d %H:%M:%S')}\n"
                pi += f"    RPostLink: https://vk.com/wall{str(post['copy_history'][0]['owner_id'])}_{str(post['copy_history'][0]['id'])}\n"
                if 'signer_id' in post['copy_history'][0]:
                    pi += f"    RPostAuthorID: {str(post['copy_history'][0]['signer_id'])}\n"
                
                if post['copy_history'][0]['text'] != '':
                    pi += f"    RPostText: {post['copy_history'][0]['text']}\n\n"
                
                if 'attachments' in post['copy_history'][0].keys():
                    pi += self.post_attachment_parse(post=post['copy_history'][0])
                
                post_count += 1
            
            elif post['from_id'] != post['owner_id']:
                post_author = self.vk_method.users.get(user_ids=post['from_id'], fields=['first_name', 'last_name'])
                pi += f"      PostType: By {str(post['from_id'])} | {post_author[0]['first_name']} {post_author[0]['last_name']}"
                
            
            else:
                pi += "      PostType: User Post\n"

                if 'attachments' in post.keys():
                    pi += self.post_attachment_parse(post=post)
            post_count += 1
        
        if data_output == False:
            if self.is_json == True:
                return posts
            else:
                return pi
        elif data_output == True:
            if self.is_json == True:
                with open(Path(self.target_subfolder_path, f"{self.target}_getposts.txt"), 'w') as f:
                    f.write(posts)
                print(posts)
                return colored('cyan', f"[i] Saved the result to the output folder :)")
            else:
                with open(Path(self.target_subfolder_path, f"{self.target}_getposts.txt"), 'w') as f:
                    f.write(pi)
                print(pi)
                return colored('cyan', f"[i] Saved the result to the output folder :)")


    def getpostsimgs(self, arg:int=None, data_output=False):
        """Obtains postID and creates a separate folder,—in the specified OUTPUT_FOLDER—whithin which stems post photos on corresponding subfolders. Or creates a folder and puts there all photos from the target's profile.
        Feature with multiple posts parsing is in development.

        Args:
            * post_id(int): the ID of the needed for photo-parse post.
    
        """
        posts = self.vk_method.wall.get(owner_id=self.target, filter='owner')
        post_ids = [str(post['id']) for post in posts['items']]
        
        if arg == None:
            return colored('pink', '[*] Missing argument: postID.')
        
        elif str(arg) in post_ids:

            for post in posts['items']:
                if post['id'] == int(arg):
                    post_path = Path(self.target_subfolder_path, f'{str(self.target)}_getpostimgs', f"post_{str(post['id'])}")
                    try:
                        os.makedirs(post_path)
                    except FileExistsError:
                        shutil.rmtree(post_path)
                        os.makedirs(post_path)

                    if 'copy_history' in post.keys():
                        if 'attachments' in post['copy_history'][0]:
                            for attachment in post['copy_history'][0]['attachments']:
                                if attachment['type'] == 'photo':
                                    for size in attachment['photo']['sizes']:
                                        if size['type'] == 'x':
                                            url = size['url']

                                            if data_output == True:
                                                img = requests.get(url).content
                                                img_path = Path(post_path, f"{str(attachment['photo']['id'])}.jpg")
                                                with open(img_path, 'wb') as f:
                                                    f.write(img)
                                                print(colored('grey', f"[i] Created path: {img_path}"))
                                            else:
                                                return url

                                else:
                                    continue
                            return colored('cyan', '[*] Saved result to the output folder :)')
                        else:
                            return colored('pink', f'[*] No attachments for postID {str(arg)}.')

                    else: #if post is NOT reposted
                        if 'attachments' in post.keys():
                            for attachment in post['attachments']:
                                if attachment['type'] == 'photo':
                                    for size in attachment['photo']['sizes']:
                                        if size['type'] == 'x':
                                            url = size['url']

                                            if data_output == True:
                                                img = requests.get(url).content
                                                img_path = Path(post_path, f"{str(attachment['photo']['id'])}.jpg")
                                                with open(img_path, 'wb') as f:
                                                    f.write(img)
                                                print(colored('grey', f"[i] Created path: {img_path}"))
                                            else:
                                                return url
                                else:
                                    continue
                            return colored('cyan', '[*] Saved result to the output folder :)')

                        else:
                            return colored('pink', f'[*] No attachments for postID {str(arg)}.')

        else:
            return colored('pink', f"[?] PostID {str(arg)} was not found.")


    def getpostsreacts(self, arg:int=None, data_output=False):
        """Obtains profiles of people as well as their comments and likes on the target's profile post.

        Args:
            * arg(int): ID of the post to retrieve the data from.
            * data_output(bool): By default, False; specifies whether to save data in the output folder.
        
        Returns:
            * cdi(str): if JSON=False; comment Detailed Information on the desired post.
            * post_comments(obj, str): if JSON=True; comment raw object.
        """
        if arg == None:
            return colored('pink', "[*] 'getpostsreacts' command required arg: postID.")
        cdi = "" # Comment Detailed Information
        pli = ""
        try:
            post_comments = self.vk_method.wall.getComments(owner_id=self.target, post_id=arg, need_likes=1, sort='asc', extended=1)
            commentators = {}
            comment_count = 1
            cdi += f"\n[COMMENTS FOR POSTID {str(arg)}]\n"
            cdi += f"CommentsNumber: {str(post_comments['count'])}\n"
            cdi += f"TopComments:\n"
            for user in post_comments['profiles']:
                commentators[user['id']] = f"{user['first_name']} {user['last_name']}"
            for comment in post_comments['items']:
                cdi += f"   {str(comment_count)}) CommentID: {str(comment['id'])}\n"
                cdi += f"      Date: {datetime.datetime.fromtimestamp(comment['date']).strftime('%Y-%m-%d %H-%M-%S')}\n"

                if comment['from_id'] in commentators.keys():
                    cdi += f"      Owner: {commentators[comment['from_id']]} | {str(comment['from_id'])}\n"
                else:
                    cdi += f"      UID: {str(comment['from_id'])}\n"

                cdi += f"      Text: {comment['text']}\n"
                cdi += f"      Likes: {str(comment['likes']['count'])}\n"
                cdi += f"      ThreadedComment: {str(comment['thread']['count'])}\n"
                comment_count += 1

        except vk_api.exceptions.ApiError as e:
            return colored('red', f"[!] An error has occurred while retrieving the data for comments({e}).")
        except:
            return colored("red", f"[!] An error has occurred when processing a request ({traceback.format_exc()})")

        try:
            post_likes = self.vk_method.likes.getList(type='post', owner_id=self.target, item_id=arg, extended=1)
            pli = f"\n[LIKES FOR POSTID {str(arg)}]\n" # Post Likes Info
            pli += f"LikesCount: {post_likes['count']}\n"
            pli += f"People: \n"
            people_count = 1
            for user in post_likes['items']:
                pli += f"   {str(people_count)}) {str(user['id'])} | {user['first_name']} {user['last_name']}"
                if 'is_closed' in user.keys():
                    pli += f" | Closed: {str(user['is_closed'])}\n"
                else:
                    pli += '\n'
                people_count += 1

        except Exception as e:
            return colored('red', f"[!] An error has occurred while retrieving the data for likes({traceback.format_exc()}).")
        
        if cdi != "" or pli != "":

            if self.is_json == True:
                if data_output == True:
                    print(post_comments + '\n' + post_likes)
                    with open(Path(self.target_subfolder_path, f"{self.target}_getpostsreacts")) as f:
                        f.write(post_comments + '\n' + post_likes)
                    return colored('cyan', '[i] The result has been saved to the output folder :)')
                else:
                    return post_comments + '\n' + post_likes

            else:
                if data_output == True:
                    print(cdi + pli)
                    with open(Path(self.target_subfolder_path, f"{self.target}_getpostsreacts")) as f:
                        f.write(cdi + '\n' + pli)
                    return colored('cyan', '[i] The result has been saved to the output folder :)')
                else:
                    return cdi + '\n' + pli
        else:
            return colored('pink', "[*] No data has been retrived. Perhaps, the target has restricted access to post reactions :(")


    def getalbums(self, data_output=False):
        """Obtains a list of target's albums.
        
        Returns:
            * albums(str): Editted list of target's photo albums.
        """
        album_list = self.vk_method.photos.getAlbums(owner_id=self.target)
        if album_list['count'] != 0:
            albums = f"\n[ALBUMS OF UID {self.target}]\n"
            albums += f"AlbumCount: {str(album_list['count'])}\n"
            albums += f"Albums:\n"
            alb_count = 1
            for album in album_list['items']:
                albums += f"    {str(alb_count)}) AlbumID: {album['id']} | Title: {album['title']} | OwnerID: {str(album['owner_id'])}\n"
                albums += f"        ItemsInside: {str(album['size'])}\n"
                albums += f"        DateCreated: {datetime.datetime.fromtimestamp(album['created']).strftime('%Y-%m-%d %H:%M:%S')} | LastUpdate: {datetime.datetime.fromtimestamp(album['updated']).strftime('%Y-%m-%d %H:%M:%S')}\n"
                alb_count += 1
            if data_output == True:
                print(albums)
                with open(Path(self.target_subfolder_path, f'{self.target}_getalbums.txt'), 'w') as f:
                    f.write(albums)
                return colored('cyan', f"[i] Saved the result to the output folder :)")
            else:
                return albums
        else:
            return colored('pink', '[!] The target does not have any albums.')
        

    def getalbimgs(self, arg, data_output=False):
        """Gets a list of images contained in the stated album. By default, each user has three albums: saved (often set as private), wall, profile
        
        Args:
            * arg(str/int): Name or ID of an album.
        
        Returns:
            * album_imgs(str)/albinfo(str): Raw Python album info/Formatted album info.
        """
        try:
            album_imgs = self.vk_method.photos.get(owner_id=self.target, album_id=arg, extended=1)
            albinfo = f"\n[DESCRIPTION FOR ALBUM {str(arg)}]\n"
            img_links = {}    
            if album_imgs['count'] != 0 and len(album_imgs['items']) != 0:
                albinfo += f"PhotoCount: {str(album_imgs['count'])}\n"
                item_count = 1
                for item in album_imgs['items']:
                    albinfo += f"   {str(item_count)}) PhotoID: {str(item['id'])} | DateAdded: {datetime.datetime.fromtimestamp(item['date']).strftime('%Y-%m-%d %H:%M:%S')}\n"

                    for size in item['sizes']:
                        if size['type'] == 'x':
                            photo_link = size['url']
                            img_links[str(item['id'])] = photo_link

                    albinfo += f"      PhotoLink: {photo_link}\n"
                    albinfo += f"      OwnerID: {str(item['owner_id'])}\n"
                    if 'text' in item.keys() and item['text'] != '':
                        albinfo += f"      Text: {item['text']}\n"
                    albinfo += f"      LikesCount: {str(item['likes']['count'])} | CommentCount: {str(item['comments']['count'])}\n\n"
                    item_count += 1

            else:
                return colored('pink', '[*] The specified album is empty.')

                
            if data_output == True:
                os.mkdir(Path(self.target_subfolder_path, f"{str(self.target)}_{str(arg)}_getalbimgs"))

                with open(Path(self.target_subfolder_path, f"{str(self.target)}_{str(arg)}_getalbimgs", f"{str(self.target)}_{str(arg)}_getalbimgs.txt"), 'w') as f:
                    if self.is_json == True:
                        f.write(album_imgs)
                    else:
                        f.write(albinfo)
                        
                
                for image in img_links:
                    img = requests.get(img_links[image]).content
                    img_path = Path(self.target_subfolder_path, f"{str(self.target)}_{str(arg)}_getalbimgs", image + '.jpg')
                    with open(img_path, 'wb') as f:
                        f.write(img)
                    print(colored('grey', f"[^] Created path: {img_path}"))
                return colored('cyan', f"[i] Saved the result to the output folder :)")
            else:
                if self.is_json == True:
                    return album_imgs
                else:
                    return albinfo

        except vk_api.exceptions.ApiError as e:
            return colored('red', f"[!] An error has occurred while obtaining {str(arg)} album info ({e}).")
    
    def getfriends(self, data_output=False):
        """Retrieves all friends from the selected target.
        
        Returns:
            * frdsinfo(str): Formatted list of target's friends.
        """
        friends_list = self.vk_method.friends.get(user_id=self.target, fields=['first_name', 'last_name', 'sex', 'city', 'country', 'bdate'])
        frdsinfo = f"\n[FRIENDS INFO FOR UID {str(self.target)}]\n"
        frdsinfo += f"FriendCount: {str(friends_list['count'])}\n"
        frdsinfo += f"Friends:\n"

        if 'items' in friends_list.keys() and len(friends_list['items']) != 0:
            friend_count = 1
            for friend in friends_list['items']:
                frdsinfo += f"  {str(friend_count)}) UID: {friend['id']} | Name: {friend['first_name']} {friend['last_name']}"
                if 'is_closed' in friend.keys():
                    frdsinfo += f" | Private: {str(friend['is_closed'])}"
                if 'bdate' in friend.keys() and friend['bdate'] != '':
                    frdsinfo += f" | Bdate: {friend['bdate']}"
                if 'sex' in friend.keys():
                    frdsinfo += f" | Sex: {sex_table[friend['sex']]}"
                if 'country' in friend.keys():
                    frdsinfo += f" | Country: {friend['country']['title']}({str(friend['country']['id'])})"
                if 'city' in friend.keys():
                    frdsinfo += f" | City: {friend['city']['title']}({str(friend['city']['id'])})"
                frdsinfo += '\n'
                friend_count += 1
            analysis_repost = self.friends_analysis(friends_list)
            frdsinfo += analysis_repost

        else:
            frdsinfo += f"  Not Available."
        
        if data_output == True:
            if self.is_json == False:
                print(frdsinfo + '\n')
                with open(Path(self.target_subfolder_path, f"{str(self.target)}_getfriends.txt"), 'w') as f:
                    f.write(frdsinfo)
                print(colored('cyan', f"[i] Saved the result to the output folder :)"))
            else:
                print(friends_list)
                with open(Path(self.target_subfolder_path, f"{str(self.target)}_getfriends.txt"), 'w') as f:
                    f.write(friends_list)
                print(colored('cyan', f"[i] Saved the result to the output folder :)"))
        else:
            if self.is_json == False:
                return frdsinfo
            else:
                return friends_list


    def gettargetmutual(self, arg:str, data_output=False):
        """Get mutual friends between the target and another user
        
        Args:
            * arg(int/str): ID/ScreenName of another user to countermatch with the target.
        
        Return:
            * mutual_friends(str): A string containing mutual friends of the target and the specified user.
        """
        if type(arg) is int:
            pass
        elif type(arg) is str:
            try:
                arg = self.vk_method.utils.resolveScreenName(screen_name=arg)
                if arg['type'] == 'group' or arg['type'] == 'application':
                    return colored('pink', f"[*] Wrong type of the object ({arg['type']}).")
            except:
                return colored('pink', f"[*] User <{str(arg)}> does not exist.")
        else:
            return colored('pink', f'[*] Wrong type of userID (takes either String or Ineger)')
        
        try:
            mutual_friends_list = self.vk_method.friends.getMutual(source_uid=self.target, target_uid=arg['object_id'])
            if len(mutual_friends_list) == 0:
                return colored('pink', "[*] No mutual friends.")
            mut_frds_text = f"\n[MUTUAL FRIENDS TARGET({str(self.target)}) / UID({str(arg['object_id'])})]\n\n"
            id_count = 1
            user_info = self.vk_method.users.get(user_ids=mutual_friends_list, fields=['first_name', 'last_name', 'sex', 'city', 'country', 'bdate'])
            for friend in user_info:
                mut_frds_text += f"{str(id_count)}) UID: {str(friend['id'])} | Name: {friend['first_name']} {friend['last_name']}"
                if 'is_closed' in friend.keys():
                    mut_frds_text += f" | Private: {str(friend['is_closed'])}"
                if 'bdate' in friend.keys() and friend['bdate'] != '':
                    mut_frds_text += f" | Bdate: {friend['bdate']}"
                if 'sex' in friend.keys():
                    mut_frds_text += f" | Sex: {sex_table[friend['sex']]}"
                if 'country' in friend.keys():
                    mut_frds_text += f" | Country: {friend['country']['title']}({str(friend['country']['id'])})"
                if 'city' in friend.keys():
                    mut_frds_text += f" | City: {friend['city']['title']}({str(friend['city']['id'])})"
                mut_frds_text += '\n'
                id_count += 1
            user_info_for_analysis = {'items':user_info}
            mut_frds_text += self.friends_analysis(user_info_for_analysis)
        except Exception as e:
            return colored('red', f"[!] An error has occurred while getting mutual friends ({e}).")
        
        if self.is_json == False:
            if data_output == True:
                print(mut_frds_text)
                with open(Path(self.target_subfolder_path, f'{str(self.target)}_{str(arg)}_gettargetmutual.txt'), 'w') as f:
                    f.write(mut_frds_text)
                print(colored('cyan', f"[i] Saved the result to the output folder :)"))
            else:
                return mut_frds_text
        else:
            if data_output == True:
                with open(Path(self.target_subfolder_path, f'{str(self.target)}_{str(arg)}_gettargetmutual.txt'), 'w') as f:
                    f.write(mutual_friends_list)
                print(colored('cyan', f"[i] Saved the result to the output folder :)"))
            else:
                return mutual_friends_list
            

    def getgroups(self, data_output=False):
        """Get list of groups, which the target is a part of.
        
        Returns:
            group_info(str): Detailed list of the community members.
        """
        groups_list = self.vk_method.groups.get(user_id=self.target, extended=1, fields=['city', 'country', 'description', 'members_count', 'status', 'contacts'])
        group_info = f"\n[GROUP INFO FOR UID {str(self.target)}]\n"
        
        if groups_list['count'] != 0:
            group_info += f"GroupCount: {str(groups_list['count'])}\n"
            group_info += f"Groups:\n"
            group_count = 1
            for group in groups_list['items']:
                group_info += f"\n\n-----------------------------------------\n"
                group_info += f"{str(group_count)}) GID: {str(group['id'])} | GroupName: {group['name']}"
                if 'screen_name' in group.keys() and group['screen_name'] != '':
                    group_info += f" | ScreenName: {group['screen_name']}"
                group_info += '\n'
                
                if 'description' in group.keys() and group['description'] != '':
                    group_info += f"GroupDescription: {group['description']}\n"
                
                if 'members_count' in group.keys() and group['members_count'] != 0:
                    group_info += f"MembersCount: {str(group['members_count'])}\n"

                if 'status' in group.keys() and group['status'] != '':
                    group_info += f"Status: {group['status']}\n"
                
                if 'contacts' in group.keys() and group['contacts'] != []:
                    group_info += f"Contacts:\n"
                    contact_count = 1

                    for contact in group['contacts']:
                        group_info += f"    {str(contact_count)})"
                        if 'user_id' in contact and contact['user_id'] != 0:
                            group_info += f" UID: {str(contact['user_id'])}"
                        if 'desc' in contact and contact['desc'] != '':
                            group_info += f" | Desc: {contact['desc']}"
                        if 'phone' in contact and contact['phone'] != '':
                            group_info += f" | Phone: {contact['phone']}"
                        if 'email' in contact and contact['email'] != '':
                            group_info += f" | Email: {contact['email']}"
                        contact_count += 1

                        group_info += '\n'
            
                if 'country' in group.keys() and group['country'] != '':
                    group_info += f"Country: {group['country']['title']} ({str(group['country']['id'])})\n"
                if 'city' in group.keys() and group ['city'] != '':
                    group_info += f"City: {group['city']['title']} ({str(group['city']['id'])})\n"
                group_count += 1
                
        else:
            return colored('pink', f"[*] No groups have been found.")

        
        if self.is_json == False:
            if data_output == True:
                print(group_info)
                with open(Path(self.target_subfolder_path, f'{str(self.target)}_gettargetmutual.txt'), 'w') as f:
                    f.write(group_info)
                print(colored('cyan', f"[i] Saved the result to the output folder :)"))
            else:
                return group_info
        else:
            if data_output == True:
                with open(Path(self.target_subfolder_path, f'{str(self.target)}_gettargetmutual.txt'), 'w') as f:
                    f.write(groups_list)
                print(colored('cyan', f"[i] Saved the result to the output folder :)"))
            else:
                return groups_list
        
    def getgroupmembers(self, arg=None, data_output=False):
        """Retrieves members list of a selected community.
        
        Args:
            * arg(int/str): ID or screen name of a group to obtain the members list from.
        
        Returns:
            * members_info(str): Formatted list of group members.
        """
        if type(arg) is int:
            pass
        if type(arg) is str:
            arg = self.vk_method.utils.resolveScreenName(screen_name=arg)
            if len(arg) != 0 and arg['type'] == 'group':
                arg = arg['object_id']
            else:
                return colored('pink', '[!] Wrong type for the argument (argID has to belong to a group).')
        if arg == None:
            return colored('pink', "[*] Need to provide 'arg' argument of ID or screen name of a group.")

        try:
            members_list = self.vk_method.groups.getMembers(group_id=arg, fields=['first_name', 'last_name', 'sex', 'city', 'country', 'bdate'])
            members_info = f"\n\n[MEMBERS INFO FOR GID {str(arg)}]\n"
            member_count = 1
            for member in members_list['items']:
                members_info += f"{str(member_count)}) UID: {str(member['id'])} | Name: {member['first_name']} {member['last_name']}"
                if 'is_closed' in member.keys():
                    members_info += f" | Private: {str(member['is_closed'])}"
                if 'bdate' in member.keys() and member['bdate'] != '':
                    members_info += f" | Bdate: {member['bdate']}"
                if 'sex' in member.keys():
                    members_info += f" | Sex: {sex_table[member['sex']]}"
                if 'country' in member.keys():
                    members_info += f" | Country: {member['country']['title']}({str(member['country']['id'])})"
                if 'city' in member.keys():
                    members_info += f" | City: {member['city']['title']}({str(member['city']['id'])})"
                members_info += '\n'
                member_count += 1
            members_info += self.friends_analysis(members_list)

            if self.is_json == False:
                if data_output == True:
                    with open(Path(self.OUTPUT_FOLDER, f'GID{str(arg)}_getgroupmembers.txt'), 'w') as f:
                        f.write(members_info)
                    print(colored('cyan', f"[i] Saved the result to the output folder :)"))
                else:
                    return members_info
            else:
                if data_output == True:
                    with open(Path(self.OUTPUT_FOLDER, f"GID{self.OUTPUT_FOLDER}_getgroupmembers.txt"), 'w') as f:
                        f.write(members_list)
                    print(colored('cyan', f"[i] Saved the result to the output folder :)"))
                else:
                    return members_list

        except:
            return colored('red', f"[!] An error has occurred while retrieving group members ({traceback.format_exc()}).")

    def checkgroupmember(self, arg, data_output=False):
        """Checks whether the target is a member of a specified community
        
        Args:
            * arg(int/str): ID of a group to check target's membership status.
        
        Returns:
            * 'True'/'False'
        """
        if type(arg) is int:
            pass
        if type(arg) is str:
            arg = self.vk_method.utils.resolveScreenName(screen_name=arg)
            if arg['type'] == 'group':
                arg = arg['object_id']
            else:
                return colored('pink', '[!] Wrong type for the argument (argID has to belong to a group).')

        try:
            is_member = self.vk_method.groups.isMember(group_id=arg, user_id=self.target)
            if is_member == 1:
                return "True"
            elif is_member == 0:
                return "False"
            else:
                return colored('pink', f'[?] Unknown response: {is_member}')
        except:
            return colored('red', f"[!] An error has occurred while checking target's group membership ({traceback.format_exc()}).")
    

    def getgeopins(self, data_output=False):
        # Search info about the newer version of the method. Legacy method: places.getCheckins

        return colored('yellow', f"[*] 'getgeopins' command is still in development.")

    def fullosint(self):
        """Full VK OSINT generation. Such attributes will be provided: general info(targetinfo), profile pic(getprofpic), posts(getposts), album list (getalbums), photos from wall(getalbimgs('wall')), photos from profile(getalbimgs('profile')), saved photos—if available(getalbimgs('saved')), friends list(getfriends), groups list(getgroups)"""
        while True:
            safeguard = input(colored('yellow', '[?] This is going to take up significant amount of time and Internet traffic. Are you sure you want to continue?(y/n): '))
            if safeguard.lower() == 'y':
                break
            if safeguard.lower() == 'n':
                return None
            else:
                continue
        try:
            self.targetinfo(data_output=True)
            self.getprofpic(data_output=True)
            self.getposts(data_output=True)
            self.getalbums(data_output=True)
            self.getalbimgs('wall', data_output=True)
            self.getalbimgs('profile', data_output=True)
            self.getalbimgs('saved', data_output=True)
            self.getfriends(data_output=True)
            self.getgroups(data_output=True)
        except:
            return colored('red', f"[!] An error has occurred while generating the fullosint report ({traceback.format_exc()}).")

                

    def _2FA(self):
        """Function needed for 2-Factor-Authentication
        
        Returns:
            * key(str): 2FA code
            * remember_device(bool): Remembering option
        """

        key = input('Enter authentication code: ') # Code from the 2FA app
        remember_device = input("Remember this device?('yes' or no'): ").lower()
        if remember_device == 'yes':
            remember_device = True
        else:
            remember_device = False
        return key, remember_device

    def _captchaHandler(self, captcha):
        """Whenever a CAPTCHA is required, this function is called.
        
        Args:
            * captcha(obj): Captcha object; for more info https://vk.com/dev/captcha_error
        
        Returns:
            * captcha.try_again(key)(func): A function required for sending captcha code after the CAPTCHA error has occurred.
        """
        key = input(f"[$] Enter a CAPTCHA code from {colored('green', captcha.get_url().strip())}: ")
        return captcha.try_again(key)