import os
import asyncio
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv('token')
HOST = os.getenv('host')
USERNAME = os.getenv('username')
PASSWORD = os.getenv('password')
DATABASE_1_NAME = os.getenv('database_1_name')


from nltk.corpus import cmudict
dictionary = cmudict.dict()

SKYS_SERVER_ID = 609112858214793217

PLURALKIT_ID = 466378653216014359
HUSSIEBOT_ID = 480855402289037312
TODDBOT_ID = 461265486655520788
YAGBOT_ID = 204255221017214977
TUPPERBOX_ID = 431544605209788416

VRISKA_ID = 707112913722277899
SKYS_ID = 259774152867577856
EM_ID = 279738154662232074

SPIDERMOD_ROLE_ID = 784225831979057153
BOT_ROLE_ID = 609121032389001226
SHUPPERBOX_ROLE_ID = 784148456960557076
PK_DOWN_ROLE_ID = 787775841438007316

HBS_CHANNEL_ID = 754527915290525807
FOOD_CHANNEL_ID = 612816400339435520
POSITIVE_VENT_CHANNEL_ID = 613085551117074490
HOMESTUCK_CHANNEL_ID = 780992508619653141

HBS_TEST_CHANNEL_ID = 753349219808444438

VENT_CATEGORY_ID = 609118603417092099

databaseSem = asyncio.Semaphore(1)

stars = ["\U00002B50","\U0001F31F","\U00002728"]
moodreacts = ["\U0001F91D","<:bigmood:713218567977304146>"]
cursedreacts = ["\U0001F6BD"]

starboards = ["starboard","lewdboard","moodboard","cursedboard"]

blobspade = "<:blobspade:760161813312307220>"
spaghetti = "\U0001F35D"
looking = "<:looking:772588405904375819>"
newspaper2 = "\U0001F5DE\U0000FE0F"
left_arrow = "\u2b05"
right_arrow = "\u27a1"
x_emoji = "\u274c"
check_emoji = "\u2705"

color = 0x005682

homestuck_characters = ["John Egbert","Rose Lalonde","Jade Harley","Dave Strider","Jane Crocker","Roxy Lalonde","Dirk Strider","Jake English",
                        "Karkat Vantas","Aradia Megido","Tavros Nitram","Sollux Captor","Nepeta Leijon","Kanaya Maryam",
                        "Terezi Pyrope","Vriska Serket","Equius Zahhak","Gamzee Makara","Eridan Ampora","Feferi Peixes",
                        "Kankri Vantas","Damara Megido","Rufioh Nitram","Mituna Captor","Meulin Leijon","Porrim Maryam",
                        "Latula Pyrope","Aranea Serket","Horuss Zahhak","Kurloz Makara","Cronus Ampora","Meenah Peixes"]
hearts = ["<:Heart_00_Mutant:803731091532808212>","<:Heart_12_Rust:803726732649037866>","<:Heart_12_Bronze:803726787271065600>","<:Heart_10_Gold:803726831378235433>",
          "<:Heart_09_Lime:803726872575737866>","<:Heart_09_Olive:803726913810071592>","<:Heart_07_Jade:803727129191514123>","<:Heart_06_Teal:803727045866553344>",
          "<:Heart_05_Cerulean:803727290102054922>","<:Heart_04_Indigo:803727390835605516>","<:Heart_03_Purple:803727487577096202>","<:Heart_02_Violet:803731014987415612>",
          "<:Heart_01_Fuchsia:803731057002283038>"]

bannedPhrases = ["Good Morning", "Good Mornin", "Good Evening", "Good Evenin", "Fair Enough", "Cool Thanks", "Mornin Fellas", "Evenin Fellas"]
starsList = ['｡', '҉', '☆', '°', ':', '✭', '✧', '.', '✼', '✫', '．', '*', '゜', '。', '+', 'ﾟ', '・', '･', '★']
spaces = [" " for x in range(30)]

who_choices_sky = ["Me.","You.","Andrew Fucking Hussie.","Who do you *think*?","Evan/Em.","Prompto.","Hatsune Miku.","Vriska.",
                   "Milk Boy.","Nox.","David Elizabeth Strider.","It's a secret.","Why do you gotta know?",
                   "That's classified.","I remember, it was many years ago. I was but a young boy...",
                   "I refuse to answer.", "shut up.", "I hate answering your stupid questions.", "Why are you like this?",
                   "Buy me chicken nuggets and I'll tell you.",
                   "We're no strangers to love\nYou know the rules and so do I (do I)\nA full commitment's what I'm thinking of\nYou wouldn't get this from any other guy\nI just wanna tell you how I'm feeling\nGotta make you understand\nNever gonna give you up\nNever gonna let you down\nNever gonna run around and desert you\nNever gonna make you cry\nNever gonna say goodbye\nNever gonna tell a lie and hurt you\nWe've known each other for so long\nYour heart's been aching, but you're too shy to say it (say it)\nInside, we both know what's been going on (going on)\nWe know the game and we're gonna play it\nAnd if you ask me how I'm feeling\nDon't tell me you're too blind to see\nNever gonna give you up\nNever gonna let you down\nNever gonna run around and desert you\nNever gonna make you cry\nNever gonna say goodbye\nNever gonna tell a lie and hurt you\nNever gonna give you up\nNever gonna let you down\nNever gonna run around and desert you\nNever gonna make you cry\nNever gonna say goodbye\nNever gonna tell a lie and hurt you\nWe've known each other for so long\nYour heart's been aching, but you're too shy to say it (to say it)\nInside, we both know what's been going on (going on)\nWe know the game and we're gonna play it\nI just wanna tell you how I'm feeling\nGotta make you understand\nNever gonna give you up\nNever gonna let you down\nNever gonna run around and desert you\nNever gonna make you cry\nNever gonna say goodbye\nNever gonna tell a lie and hurt you\nNever gonna give you up\nNever gonna let you down\nNever gonna run around and desert you\nNever gonna make you cry\nNever gonna say goodbye\nNever gonna tell a lie and hurt you\nNever gonna give you up\nNever gonna let you down\nNever gonna run around and desert you\nNever gonna make you cry\nNever gonna say goodbye\nNever gonna tell a lie and hurt you"]
who_choices = ["Me.","You.","Andrew Fucking Hussie.","Who do you *think*?","Hatsune Miku.","Vriska.","It's a secret.","Why do you gotta know?","That's classified.","I remember, it was many years ago. I was but a young boy...",
                "We're no strangers to love\nYou know the rules and so do I (do I)\nA full commitment's what I'm thinking of\nYou wouldn't get this from any other guy\nI just wanna tell you how I'm feeling\nGotta make you understand\nNever gonna give you up\nNever gonna let you down\nNever gonna run around and desert you\nNever gonna make you cry\nNever gonna say goodbye\nNever gonna tell a lie and hurt you\nWe've known each other for so long\nYour heart's been aching, but you're too shy to say it (say it)\nInside, we both know what's been going on (going on)\nWe know the game and we're gonna play it\nAnd if you ask me how I'm feeling\nDon't tell me you're too blind to see\nNever gonna give you up\nNever gonna let you down\nNever gonna run around and desert you\nNever gonna make you cry\nNever gonna say goodbye\nNever gonna tell a lie and hurt you\nNever gonna give you up\nNever gonna let you down\nNever gonna run around and desert you\nNever gonna make you cry\nNever gonna say goodbye\nNever gonna tell a lie and hurt you\nWe've known each other for so long\nYour heart's been aching, but you're too shy to say it (to say it)\nInside, we both know what's been going on (going on)\nWe know the game and we're gonna play it\nI just wanna tell you how I'm feeling\nGotta make you understand\nNever gonna give you up\nNever gonna let you down\nNever gonna run around and desert you\nNever gonna make you cry\nNever gonna say goodbye\nNever gonna tell a lie and hurt you\nNever gonna give you up\nNever gonna let you down\nNever gonna run around and desert you\nNever gonna make you cry\nNever gonna say goodbye\nNever gonna tell a lie and hurt you\nNever gonna give you up\nNever gonna let you down\nNever gonna run around and desert you\nNever gonna make you cry\nNever gonna say goodbye\nNever gonna tell a lie and hurt you"]


