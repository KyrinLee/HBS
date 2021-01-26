import os
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

VENT_CATEGORY_ID = 609118603417092099

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
x = "\u274c"
check = "\u2705"

colors = [0xa10000,0xa15000,0xa1a100, 0x658200, 0x416600, 0x008141, 0x008282, 0x005682, 0x000056, 0x2b0057, 0x6a006a, 0x77003c,0xff0000]
colors = [0x005682,0x005682,0x005682, 0x005682, 0x005682, 0x005682, 0x005682, 0x005682, 0x005682, 0x005682, 0x005682, 0x005682,0x005682]
homestuck_characters = ["John Egbert","Rose Lalonde","Jade Harley","Dave Strider","Jane Crocker","Roxy Lalonde","Dirk Strider","Jake English",
                        "Karkat Vantas","Aradia Megido","Tavros Nitram","Sollux Captor","Nepeta Leijon","Kanaya Maryam",
                        "Terezi Pyrope","Vriska Serket","Equius Zahhak","Gamzee Makara","Eridan Ampora","Feferi Peixes",
                        "Kankri Vantas","Damara Megido","Rufioh Nitram","Mituna Captor","Meulin Leijon","Porrim Maryam",
                        "Latula Pyrope","Aranea Serket","Horuss Zahhak","Kurloz Makara","Cronus Ampora","Meenah Peixes"]


bannedPhrases = ["Good Morning", "Good Mornin", "Good Evening", "Good Evenin", "Fair Enough", "Cool Thanks", "Mornin Fellas", "Evenin Fellas"]
starsList = ['｡', '҉', '☆', '°', ':', '✭', '✧', '.', '✼', '✫', '．', '*', '゜', '。', '+', 'ﾟ', '・', '･', '★']
spaces = [" " for x in range(30)]


DATABASE_URL = os.environ['DATABASE_URL']
TOKEN = os.environ["token"]


