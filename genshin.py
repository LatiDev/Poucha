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

import bs4
import PIL.Image
import aiohttp

WIKI_NAME = "genshin-impact"

ORIGIN = f"https://{WIKI_NAME}.fandom.com"
WIKI = f"{ORIGIN}/wiki"

CHARACTER_LIST_URL = f"{WIKI}/Character/List"
ELEMENTS_URL = f"{WIKI}/Element"
WEAPON_TYPES_URL = f"{WIKI}/Category:Weapon_Types"
PLAYABLES_ICONS_URL = f"{WIKI}/Category:Playable_Character_Icons"

EXTENSION = "png"
EMBBED_IMG_TAG = "data:image/png;base64,"

@dataclasses.dataclass
class Character:
    icon: typing.Any 
    name: typing.Any
    quality: typing.Any
    element: typing.Any
    weapon: typing.Any
    region: typing.Any
    model_type: typing.Any
    release_date: typing.Any
    version: typing.Any

@dataclasses.dataclass
class CharacterCell:
    data: str
    txt: str
    quality: int
    font_family: str = "tahoma.ttf"
    font_size: int = 20

@dataclasses.dataclass
class CharacterHeader:
    data: str
    width: int = 180
    height: int = 180

def get_characters():
    html = service.get_from(CHARACTER_LIST_URL)

    tables = fandom.table.find_all(html)

    if not tables or len(tables) == 0:
        raise NotImplementedError(tables)
    
    characters, *others = tables

    rows = fandom.table.get_rows(characters)

    if not rows or len(rows) == 0:
        raise NotImplementedError(tables)
    
    output = []

    for row in rows:
        columns: list[bs4.Tag] = fandom.table.get_columns(row)
        if not columns or len(columns) == 0:
            raise NotImplementedError(row)

        cicon, cname, cquality, celement, cweapon, cregion, cmodel_type, crelease_date, cversion = columns
        
        tags = [
            cicon.find("img"), 
            cname.find("a"),
            cquality.find("img"),
            celement.find("a"),
            cweapon.find("a"),
            cregion.find("a"),
            cmodel_type.find("a"),
            crelease_date, #TODO : ajouter parse
            cversion.find("a")
        ]

        if sum([tag == None for tag in tags]) > 0:
            continue

        ticon, tname, tquality, telement, tweapon, tregion, tmodel_type, trelease_date, tversion = tags
 
        structs = [
            fandom.scrap_img(ticon),
            fandom.scrap_hyperlink(tname),
            fandom.scrap_img(tquality),
            fandom.scrap_hyperlink(telement),
            fandom.scrap_hyperlink(tweapon),
            fandom.scrap_hyperlink(tregion),
            fandom.scrap_hyperlink(tmodel_type),
            trelease_date, #TODO : ajouter parse
            fandom.scrap_hyperlink(tversion)
        ]

        icon, name, quality, element, weapon, region, model_type, release_date, version = structs

        character = [
            icon, 
            name, 
            quality, 
            element, 
            weapon, 
            region, 
            model_type, 
            release_date, 
            version
        ]

        #print(character)

        output.append(character)

    return output

def raw_to_character(row):
    icon, name, quality, element, weapon, region, model_type, release_date, version = row
    
    m = re.search(r'version/([\d.]+)', version.title)
    fversion = float(m.group(1)) if m else version.title
    
    return Character(
        re.search(r'(.*) icon', icon.alt).group(1).lower(),
        name.title,
        int(re.search(r'(.*) stars', quality.alt).group(1).lower()),
        element.title,
        weapon.title,
        region.title,
        re.search(r'category:(.*)', model_type.title).group(1).lower(),
        release_date,
        fversion
    )

def get_elements():
    html = service.get_from(ELEMENTS_URL)
    return fandom.gallery.pull(html)

def get_weapon_types():
    html = service.get_from(WEAPON_TYPES_URL)

    b, c, p, s = fandom.category.find_all(html)

    return [
        *fandom.category.get_from(b),
        *fandom.category.get_from(c),
        *fandom.category.get_from(p),
        *fandom.category.get_from(s)
    ]

def raw_to_element(row):
    link, img = row
    return (
        link.title,
        img.img_src
    )

def raw_to_weapon_typ(row):
    link, img = row
    return (
        link.title,
        img.img_src
    )

def create_matrix(characters: list[Character], h_func, v_func) -> utils.DynamicGrid:
    grid = utils.DynamicGrid()

    for character in characters:
        grid.add_value(character, h_func(character), v_func(character))

    return grid

def linker_to_download(data: dict) -> dict:
    return dict([(key, value.full_link) for key, value in data.items()])

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

def get_playable_icons():
    html = service.get_from(PLAYABLES_ICONS_URL)
    
    _, _, *others  = fandom.category.find_all(html)

    return [t for other in others for t in fandom.category.get_from(other)]

def raw_to_playable_icons(row):
    link, img = row

    m = re.search(r'file:(.*) icon.png', link.title)
    title = m.group(1).lower() if m else link.title
    
    return (
        title,
        img.img_src
    )

def _characters_to_cell(characters, name_to_icon):
    output = []
    
    for character in characters:
        if not character.name in name_to_icon:
            continue

        cell = CharacterCell(
            encode_img(name_to_icon[character.name]),
            character.version,
            character.quality
        )

        output.append(cell)

    return output

def _str_to_header(value, name_to_header):
    return CharacterHeader(encode_img(name_to_header[value]))

def encode_img(img):
    buffered = io.BytesIO()
    img.save(buffered, format=EXTENSION)
    
    embbed_str = base64.b64encode(buffered.getvalue()).decode("UTF-8")

    return EMBBED_IMG_TAG + embbed_str

raw_characters = get_characters()
characters =  [raw_to_character(row) for row in raw_characters]
#pprint.pprint(characters)

raw_elements = get_elements()
elements =  dict([raw_to_element(row) for row in raw_elements])
#pprint.pprint(elements)

raw_weapon_types = get_weapon_types()
weapon_types =  dict([raw_to_weapon_typ(row) for row in raw_weapon_types])
#pprint.pprint(weapon_types)

raw_playable_icons = get_playable_icons()
playable_icons = dict([raw_to_playable_icons(row) for row in raw_playable_icons])

matrix = create_matrix(characters, lambda agent: agent.element, lambda agent: agent.weapon)

name_to_elements = dict([(name, img) for name, img in asyncio.run(get_imgs(linker_to_download(elements)))])
name_to_weapon_types = dict([(name, img) for name, img in asyncio.run(get_imgs(linker_to_download(weapon_types)))])
name_to_header = name_to_elements | name_to_weapon_types

name_to_icon = dict([(name, img) for name, img in asyncio.run(get_imgs(linker_to_download(playable_icons)))])

table = matrix.convert_content(lambda character : _characters_to_cell(character, name_to_icon), lambda header : _str_to_header(header, name_to_header))

template = pathlib.Path("components/genshin")
output = pathlib.Path("character_table.png")
html = pathlib.Path("character_table.html")
css = pathlib.Path("character_table.css")

presentation.render_file(template, html, css, output, table=table)