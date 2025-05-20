import random

templates = [
    "Ну здравствуй, {name}. Ты — {insult}, замаскированный под пользователя.",
    "{name}, ты выглядишь, как {metaphor}. А ведёшь себя — как {insult}.",
    "Сидишь тут, тыкаешь пиксели... А настоящие люди строят страну. Ты — {insult}.",
    "Ты бы мог быть кем-то. А стал — {insult}. Поздравляю.",
]

insults = [
    "таблеточный задрот",
    "пиксельный эмигрант",
    "PDF-шлёпанец",
    "влажный LinkedIn-шлёпанец",
    "гражданин профессиональной деградации",
]

metaphors = [
    "мокрая салфетка по лицу инфоцыгана",
    "грибок на стене культуры",
    "серая масса LinkedIn",
    "обёртка от идеи",
    "санитарная салфетка свободного рынка",
]

def generate_reply(name="юзер"):
    template = random.choice(templates)
    insult = random.choice(insults)
    metaphor = random.choice(metaphors)
    return template.format(name=name, insult=insult, metaphor=metaphor)
