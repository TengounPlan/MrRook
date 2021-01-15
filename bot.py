# bot.py
import os
import re
import copy
import random
import requests
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
SERVER = os.getenv('DISCORD_SERVER')


bot = commands.Bot(command_prefix='!')
@bot.event
async def on_ready():
    global ah_api 
    global ah_api_p 
    global ah_api_faq
    ah_api = [{}]
    ah_api_p = [{}]
    ah_api_faq= [{}]
    global init_api
    init_api = False
    refresh_ah_api()

def refresh_ah_api():
    global ah_api
    global ah_api_p
    global init_api
    ah_api = sorted([c for c in requests.get('https://es.arkhamdb.com/api/public/cards?encounter=1').json()],
                        key=lambda card: card['name'])

        # only player cards
    ah_api_p = [c for c in ah_api if "spoiler" not in c]
    init_api = True

def sort_cards(self, cards):
        # input should be a list of full card dictionaries to be sorted
        # first sort by title
    cards = sorted(cards, key=lambda card: card['name'])
        # next sort by type
    cards = sorted(cards, key=lambda card: self.type_code_sort[card['type_code']])
    return cards

@bot.command(name='ahhelp', aliases=['arkhamhelp'])
async def ahhelp(ctx):
    m_response = "¿Seguro que quieres saberlo? No hay vuelta atrás:\n"
    m_response += "!ah [nombre] - Busca una carta de jugador.\n"
    m_response += "!ahe [nombre] - Busca una carta de Encuentro.\n"
    m_response += "!ahb [nombre] - Busca la cara trasera de una carta. Incluye las cartas de Encuentro.\n"
    m_response += "!ahX [nombre] - Busca una carta de jugador de nivel X.\n"
    m_response += "!aha [nombre] - Busca entre todas las cartas y sube hasta 5.\n"
    m_response += "Me tendrás que perdonar, pero todavía estoy ordenando mis cosas. Quizá en un futuro haré más cosas."

    await ctx.send(m_response[:2000])


@bot.command(name='ah', aliases=['arkham', 'arkhamhorror', 'ahe', 'ahb', 'ah0', 'ah1', 'ah2', 'ah3', 'ah4', 'ah5', 'aha', 'ahfaq', 'ahefaq', 'ahfaq1', 'ahfaq2', 'ahfaq3', 'ahfaq4', 'ahfaq5'])
async def ah(ctx, string):
        subexists = False
        m_query = ' '.join(ctx.message.content.split()[1:]).lower()
        img = 'imagesrc'
        faq = False
        faq_response = None

        # Auto-link some images instead of other users' names
        query_redirects = {
            }
        if m_query.find("~") >= 0:
            m_query,m_subquery = m_query.split("~",1)
            subexists = True
        m_response = ""
        if m_query in query_redirects.keys():
            m_response = query_redirects[m_query]
        elif not m_query:
            # post help text if no query
            m_response = "!ah [nombre] - Busca una carta de jugador\n"
            m_response += "!ahe [nombre] - Busca una carta de Encuentro\n"
            m_response += "!ahb [nombre] - Busca la cara trasera de una carta\n"
            m_response += "!ahX [nombre] - Busca una carta de jugador de nivel X\n"
            m_response += "!aha [nombre] - Busca entre todas las cartas y postea hasta 5\n"
            m_response += "!ahfaq [nombre] - Busca entre todas las cartas y postea las FAQ\n"
            m_response += "Todos los comandos !ah permiten también una búsqueda en formato [nombre]~[subtítulo], para cartas donde 2 o más opciones existen\n"
            m_response += "!ahfaq, !ahefaq, y !ahfaqX mostrarán las FAQ de la carta en cuestión\n"
        else:
            # Otherwise find and handle card names
            if not init_api:
                refresh_ah_api()

            if ctx.invoked_with.__contains__("ahe"):
                # search encounter cards
                m_cards = [c for c in ah_api if c['name'].lower().__contains__(m_query) and "spoiler" in c]
                if not m_cards:
                    # search back side names of agendas/ acts
                    m_cards = [c for c in ah_api if
                               "back_name" in c and c["back_name"].lower().__contains__(m_query)]
                    img = 'backimagesrc'
            elif ctx.invoked_with[-1] in ["0", "1", "2", "3", "4", "5"]:
                # search for player cards with specific level
                n = int(ctx.invoked_with[-1])
                m_cards = [c for c in ah_api_p if c['name'].lower().__contains__(m_query) and c['xp'] == n]
            elif ctx.invoked_with == "ahb":
                # search card back sides
                m_cards = [c for c in ah_api if
                           (c['name'].lower().__contains__(m_query) and 'backimagesrc' in c) or (
                           "back_name" in c and c["back_name"].lower().__contains__(m_query))]
                img = 'backimagesrc'
            elif ctx.invoked_with == "aha":
                # search all cards
                m_cards = [c for c in ah_api if c['name'].lower().__contains__(m_query)]
            else:
                # search player cards
                m_cards = [c for c in ah_api_p if c['name'].lower().__contains__(m_query)]

            if subexists:
                m_check = [c for c in m_cards if (c.__contains__('subname') and c['subname'].lower().__contains__(m_subquery))]
                if m_check:
                    m_cards = m_check
            for c in m_cards:
                if m_query == c['name'].lower():
                    # if exact name match, post only the one card
                    m_cards = [c]
                    break
            if len(m_cards) == 1:
                try:
                    m_response += "http://arkhamdb.com" + m_cards[0][img]
                    if ctx.invoked_with.__contains__("faq"):
                        #Print it
                        holder = requests.get('http://arkhamdb.com/api/public/faq/' + m_cards[0]["code"]).json()
                        if not holder:
                            m_response = "No FAQ exists for this card. Perhaps, in another reality, it did?"
                        else:
                            m_response = holder[0]['text'];
                            m_response = re.sub("<span class=", "", m_response)
                            m_response = re.sub("icon-","",m_response)
                            m_response = re.sub("></span>", "", m_response)
                            m_response = re.sub("<[^>]*>", "", m_response)
                            #_response = re.sub("[\]].*?[\)]", "", m_response)
                            m_response = re.sub("[\[\]]", "", m_response)
                            m_response = re.sub("/card", "https://arkhamdb.com/card", m_response)
                            #m_response = re.sub("[\<].*?[\-]","", m_response)
                            #m_response = re.sub("[\>].*?[\>]", "", m_response)
                            #m_response = re.sub("[\]].*?[\]]", "", m_response)
                            faq_response = m_response.splitlines()
                            faq_response = filter(None, faq_response)


                            


                except KeyError as e:
                    if e.args[0] == "imagesrc":
                        # if no image on ArkhamDB
                        m_response = "'{}' no tiene imagen en ArkhamDB:\n".format(m_cards[0]['name'])
                        m_response += "https://es.arkhamdb.com/card/" + m_cards[0]["code"]
            elif len(m_cards) == 0:
                m_response += "Disculpa, no encuentro ninguna carta con esos parámetros:\n"
                m_response += "http://es.arkhamdb.com/find/?q=" + m_query.replace(" ", "+")
            else:
                if ctx.invoked_with == "aha":
                    # post up to 5 images with !aha command
                    for i, card in enumerate(m_cards[:5]):
                        m_response += "http://es.arkhamdb.com{0}\n".format(card[img])
                    if len(m_cards) > 5:
                        m_response += "[{0}/{1}]".format(5, len(m_cards))
                else:
                    # else just post a link
                    m_response = "'{}' cartas encontradas:\n".format(len(m_cards))
                    m_response += "https://es.arkhamdb.com/find?q=" + m_query.replace(" ", "+")
        if (ctx.invoked_with.__contains__("faq") and faq_response != None) :
            for strin in faq_response:
                await ctx.send(strin[:2000])
        else:
            await ctx.send(m_response[:2000])

bot.run(TOKEN)