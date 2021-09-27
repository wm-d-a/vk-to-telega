# vk-to-telega
vk-to-telega is a bot for broadcasting messages from the social network VKontakte to Telegram Messenger. Bot Based on [PyTelegramBotAPI](https://github.com/eternnoir/pyTelegramBotAPI) libraries, [vk_api](https://github.com/python273/vk_api) for Python Programming Language.

# PREPARATION FOR LAUNCH

You need to register your bot from [@BotFather](https://t.me/botfather#:~:text=BotFather%20is%20the%20one%20bot,BotFather%20right%20away.) to get a token. Next, you need to get Access Token to work vk api (https://vkhost.github.io/).

# HOW TO RUN IT
To start the bot you need to have: [Python](https://www.python.org/), [pyTelegramBotAPI](https://pypi.org/project/pyTelegramBotAPI/) library, [vk_api](https://pypi.org/project/vk-api/) library, pickle library

After receiving the tokens, it is necessary to clone this repository (using the GIT or download the archive). Tokens should be recorded in config.py to the corresponding variables.

Before the start, you need to run init.py to initialize log.txt and users.pickle files.

To start run telega.py

# HOW TO RUN IT (FOR TERMUX)
Enter these commands to install and start the bot:

 1. `pkg upgrade`
 2. `pkg install python`
 3. `pip install pyTelegramBotAPI`
 4. `pip install vk_api`
 5. `pkg install git`
 6. `git clone https://github.com/wm-d-a/vk-to-telega`
 7. `cd vk-to-telega`
 8. `python3 init.py`
 9. `echo tele-token="'YOUR TELEGRAM TOKEN'" >> config.py`
 10. `echo vk_token="'YOR VK TOKEN'" >> config.py`
 11. `python3 telega.py` 
