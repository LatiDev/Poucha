import pprint
import asyncio
import dataclasses
import io
import base64
import pathlib
import enum
import re
import typing

import presentation
import service
import utils
import fandom
import fandom.table
import fandom.gallery
import fandom.category

import aiohttp
import bs4
import PIL.Image

WIKI_NAME = "zenless-zone-zero"

ORIGIN = f"https://{WIKI_NAME}.fandom.com"
WIKI = f"{ORIGIN}/wiki"

AGENT_URL = f"{WIKI}/Agent"
AGENT_LIST_URL = f"{WIKI}/Agent/List"
SPECIALITES_URL = f"{WIKI}/Specialty"
ATTRIBUTES_URL = f"{WIKI}/Attribute"

PLAYABLES_URL = f"{WIKI}/Category:Playable_Agents"
#ATTRIBUTES_URL = f"{WIKI}/Category:Attributes"
FACTIONS_URL = f"{WIKI}/Category:Factions"
VERSION_URL = f"{WIKI}/Category:Version_Info"
ICONS_URL = f"{WIKI}/Category:Agent_Icons"

EXCLUSIVE_CHANNEL_URL = f"{WIKI}/Exclusive_Channel/History"
CRITICAL_NODE_URL = f"{WIKI}/Shiyu_Defense/Critical_Node/History"
HOME_URL = f"{WIKI}/Zenless_Zone_Zero_Wiki"

EXTENSION = "png"
EMBBED_IMG_TAG = "data:image/png;base64,"

ATTRIBUTES_ALIAS = {
    "frost" : "ice",
    "auric ink" : "ether",
    "honed edge": "physical"
}

@dataclasses.dataclass
class Agent:
    name: typing.Any
    rank: typing.Any
    attribute: typing.Any
    specality: typing.Any
    attack_type: typing.Any
    faction: typing.Any
    release_version: typing.Any

@dataclasses.dataclass
class AgentCell:
    data: str
    txt: str
    rank: str
    font_family: str = "tahoma.ttf"
    font_size: int = 20

@dataclasses.dataclass
class AgentHeader:
    data: str
    width: int = 180
    height: int = 180

def get_specialities():
    html = service.get_from(SPECIALITES_URL)
    return fandom.gallery.pull(html)

def get_attributes():
    html = service.get_from(ATTRIBUTES_URL)
    return fandom.gallery.pull(html)

def get_icons():
    html = service.get_from(ICONS_URL)
    category, agents, outfit, *others = fandom.category.find_all(html)
    return fandom.category.get_from(agents)

def get_agents() -> list:
    html = service.get_from(AGENT_LIST_URL)

    tables = fandom.table.find_all(html)

    if not tables or len(tables) == 0:
        raise NotImplementedError(tables)

    playable, upcoming, *other = tables

    rows = fandom.table.get_rows(playable)

    if not rows or len(rows) == 0:
        raise NotImplementedError(tables)
    
    output = []

    for row in rows:
        columns: list[bs4.Tag] = fandom.table.get_columns(row)
        if not columns or len(columns) == 0:
            raise NotImplementedError(row)

        cicon, cname, crank, cattribute, cspeciality, cattack_type, cfaction, crelease_date = columns

        icon = fandom.scrap_img(cicon.find("img"))
        name = fandom.scrap_hyperlink(cname.find("a"))
        rank = fandom.scrap_img(crank.find("img"))
        attribute = fandom.scrap_hyperlink(cattribute.find("a"))
        speciality = fandom.scrap_hyperlink(cspeciality.find("a"))
        attack_type = fandom.scrap_hyperlink(cattack_type.find("a"))
        faction = fandom.scrap_hyperlink(cfaction.find("a"))
        release = fandom.scrap_hyperlink(crelease_date.find("a"))

        agent = (
            icon,
            rank,
            attribute,
            speciality,
            attack_type,
            faction,
            release
        )

        #print(agent)

        output.append(agent)

    return output

def create_matrix(agents: list[Agent], h_func, v_func) -> utils.DynamicGrid:
    grid = utils.DynamicGrid()

    for agent in agents:
        grid.add_value(agent, h_func(agent), v_func(agent))

    return grid

def encode_img(img):
    buffered = io.BytesIO()
    img.save(buffered, format=EXTENSION)
    
    embbed_str = base64.b64encode(buffered.getvalue()).decode("UTF-8")

    return EMBBED_IMG_TAG + embbed_str

def _agent_to_cell(agent: Agent, name_to_icon: dict) -> AgentCell:
    return AgentCell(
        encode_img(name_to_icon[agent.name]),
        agent.release_version,
        agent.rank
    )

def _agents_to_cell(agents, name_to_icon):
    return sorted([_agent_to_cell(agent, name_to_icon) for agent in agents], key=lambda cell : cell.txt, reverse=True)

def _str_to_header(value, name_to_header) -> AgentHeader:
    return AgentHeader(encode_img(name_to_header[value]))

async def download_img(url: str, session: aiohttp.ClientSession, semaphore: asyncio.Semaphore):
    try:
        async with semaphore:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                content = await resp.read()
                return PIL.Image.open(io.BytesIO(content))

    except Exception as error:
        raise NotImplementedError(error)

async def download_key(key: str, url: str, session: aiohttp.ClientSession, semaphore: asyncio.Semaphore):
    return key, await download_img(url, session, semaphore)

async def get_imgs(data: dict[str, str]):
    semaphore = asyncio.Semaphore(4)
    connector = aiohttp.TCPConnector(limit=2)

    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = [download_key(name, link, session, semaphore) for name, link in data.items()]
        results = await asyncio.gather(*tasks, return_exceptions=False)

    return results

def raw_to_agent(row):
    icon, rank, attribute, speciality, attack_type, faction, release = row
    return Agent(
        icon.alt,
        "s" if rank.alt == "agentrank s" else "a",
        ATTRIBUTES_ALIAS[attribute.title] if attribute.title in ATTRIBUTES_ALIAS else attribute.title,
        speciality.title,
        attack_type.title,
        faction.title,
        float(release.title[-3:])
    )

def raw_to_speciality(row):
    link, img = row
    return (
        link.title,
        img.img_src
    )

def raw_to_attributes(row):
    link, img = row
    return (
        link.title,
        img.img_src
    )

def raw_to_icon(row):
    link, img = row
    return (
        re.search(r'file:agent (.*) icon\.png', link.title).group(1).lower(),
        img.img_src
    )

def linker_to_download(data: dict) -> dict:
    return dict([(key, value.full_link) for key, value in data.items()])


def main():
    raw_agents = get_agents()
    agents = [raw_to_agent(row) for row in raw_agents]

    raw_specalities = get_specialities()
    specialities = dict([raw_to_speciality(row) for row in raw_specalities])

    raw_attributes = get_attributes()
    attributes = dict([raw_to_attributes(row) for row in raw_attributes])

    raw_icons = get_icons()
    icons = dict([raw_to_icon(row) for row in raw_icons])

    matrix = create_matrix(agents, lambda agent: agent.specality, lambda agent: agent.attribute)

    name_to_specialities = dict([(name, img) for name, img in asyncio.run(get_imgs(linker_to_download(specialities)))])
    name_to_attributes = dict([(name, img) for name, img in asyncio.run(get_imgs(linker_to_download(attributes)))])
    name_to_header = name_to_specialities | name_to_attributes

    name_to_icon = dict([(name, img) for name, img in asyncio.run(get_imgs(linker_to_download(icons)))])

    table = matrix.convert_content(lambda agent : _agents_to_cell(agent, name_to_icon), lambda header : _str_to_header(header, name_to_header))

    template = pathlib.Path("components/zenless")
    output = pathlib.Path("agent_table.png")
    html = pathlib.Path("agent_table.html")
    css = pathlib.Path("agent_table.css")

    presentation.render_file(template, html, css, output, table=table)

if __name__ == "__main__":
    main()