# OSINTvk
OSINT tool for a popular Russian social media: [VKontakte](https://vk.com/). The application enables users to gather OPENLY AVAILABLE data with a great speed and efficiency. The project is made for ***educational*** purposes only. Nor the author or contributors carry any responsibility for the use of this tool.

## ⚒️ App Commands
OSINTvk application offers a wide range of commands to get an openly available information about a set target:
```
<CMD>              : Pull up the command list

GENERAL INFO
<targetinfo>       : Retrieve general information about the target.
<getprofpic>       : Get target's profile pic.

WALL INFO
<getposts>         : Get all target's wallposts(text).
<getpostimgs>      : Get all target's wallposts with images attached in a separate folder.
<getpostreacts>    : Retrieve info about users who commented or liked target's posts.

PHOTO INFO
<getalbums>        : Return a list of target's albums.
<getalbimgs>       : Return a list of photos in a specific album. Args: ALBUM_ID or ALBUM_TYPE ('saved', 'profile', 'wall')

FRIENDS INFO
<getfriends>       : Retrieve a list of target's friends.
<gettargetmutual>  : Return a list of target's and check against another user. Args: USER_ID

GROUP INFO
<getgroups>        : Get a list of target's groups.
<getgroupmembers>  : Get a list of group members (irregardless the target).
<checkgroupmember> : Check whether the tartget is a member of a group. Args: GROUP_ID

GEO INFO
<getgeopins>       : Retrieve information about target's geo tags. IN DEVELOPMENT...

FULL INFO
<fullosint>        : Get all the information about the target in a separate folder.
```
## ⚙️ Installation and Usage
1. Download ZIP/Clone/Fork the repository:

    ```git clone ```
2. Go to the cloned directory:

    ```cd OSINTvk```
3. Create a virtual environment for the application:

    ```python3 -m venv osintvkenv```
4. Active and navigate to the virtual environment:
    * For Linux-based OS: 
    ```source osintvkenv/bin/activate```
    * For Windows OS: 
    ```.\osintvkenv\Scripts\activate.ps1```
5. Updgrade pip and install the required packages from .txt file:

    ```
    pip3 install pip install --upgrade pip
    pip3 install -r requirements.txt
    ```
5. Navigate to ```config``` folder and open ```settings.ini```. Specify your desired output folder path, login, and password.
6. Run ```main.py``` file, you will be prompted to enter target's userID or nickname.

## 🔗 External library 
[VK API](https://dev.vk.com/api/overview)
