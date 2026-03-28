import service
import fandom.category
import pprint
import re
import utils

WIKI_NAME = "honkai-star-rail"

ORIGIN = f"https://{WIKI_NAME}.fandom.com"
WIKI = f"{ORIGIN}/wiki"

CHARACTER_LIST_URL = f"{WIKI}/Character/List"
CHARACTER_ICON_URL = f"{WIKI}/Category:Character_Icons"

PATHS_URL = f"{WIKI}/Category:Paths"
TYPES_URL = f"{WIKI}/Category:Types"

def get_paths():
    html = service.get_from(PATHS_URL)
    return [(hyperlink, img) for hyperlink, img in fandom.category.get_all(html) if img]

def get_types():
    html = service.get_from(TYPES_URL)
    return [(hyperlink, img) for hyperlink, img in fandom.category.get_all(html) if img]

def get_character_icons():
    html = service.get_from(CHARACTER_ICON_URL)
    return [(hyperlink, img) for hyperlink, img in fandom.category.get_all(html) if img]

def raw_to_path(row):
    link, img = row
    return (link.title, img.img_src)

def raw_to_type(row):
    link, img = row
    return (link.title, img.img_src)   

def raw_to_character_icon(row):
    link, img = row

    m = re.search(r'file:character (.*) icon.png', link.title)
    title = m.group(1).lower() if m else link.title
    
    return (title, img.img_src)

def create_matrix(characters: list[Character], h_func, v_func) -> utils.DynamicGrid:
    grid = utils.DynamicGrid()

    for character in characters:
        grid.add_value(character, h_func(character), v_func(character))

    return grid

raw_paths = get_paths()
paths = dict([raw_to_path(row) for row in raw_paths])

raw_types = get_types()
types = dict([raw_to_type(row) for row in raw_types])

raw_character_icons = get_character_icons()
character_icons = dict([raw_to_character_icon(row) for row in raw_character_icons])