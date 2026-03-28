#STD
import os
import io
import re
import typing
import pathlib
import base64

#IN
import domain
import utils

#OUT
import bs4
import requests
import PIL.Image

SCRAPPER_VERSION = 1
WIKI_NAME = "zenless-zone-zero"

ORIGIN = f"https://{WIKI_NAME}.fandom.com"
WIKI = f"{ORIGIN}/wiki"

AGENT_URL = f"{WIKI}/Agent"
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

ASSETS_FOLDER = os.path.join("assets")
ICONS_FOLDER = os.path.join(ASSETS_FOLDER, "icons") 
SPECIALITIES_FOLDER = os.path.join(ASSETS_FOLDER, "specialities")
ATTRIBUTES_FOLDER = os.path.join(ASSETS_FOLDER, "attributes")
ATTACK_TYPES_FOLDER = os.path.join(ASSETS_FOLDER, "attack_types")
LOGOS_FOLDER = os.path.join(ASSETS_FOLDER, "logos")

WEBS_FOLDER = os.path.join("weblogs")
LOGS_FOLDER = os.path.join("logs")
STATIC_FOLDER = os.path.join("static")

CNN_IMG_RE = rf'https:\/\/static\.wikia\.nocookie\.net\/{WIKI_NAME}\/images\/[\d|\w]+\/[\d|\w]+\/'

IMG_RE = r'(\S+.png)'
ICON_RE = r'Agent (.+) Icon.png'
RANK_RE = r'Icon AgentRank ([S|A]).png'

EXTENSION = "png"
EMBBED_IMG_TAG = "data:image/png;base64,"
DEFAULT_GALLERY = "gallery-0"

#TODO : make this auto generate
ATTRIBUTES_ALIAS = {
    "frost" : "ice",
    "auric ink" : "ether",
    "honed edge": "physical"
}

PNG_FILE_FORMAT = "{name}.png"

if not os.path.exists(ASSETS_FOLDER):
    os.mkdir(ASSETS_FOLDER)

if not os.path.exists(WEBS_FOLDER):
    os.mkdir(WEBS_FOLDER)

if not os.path.exists(LOGS_FOLDER):
    os.mkdir(LOGS_FOLDER)

if not os.path.exists(STATIC_FOLDER):
    os.mkdir(STATIC_FOLDER)

_specialities_cache = {}
_attributes_cache = {}
_icons_cache = {}

_agents_cache = []

_request_cache = {}

class RequestException(Exception):
    def __init__(self, *args):
        super().__init__(*args)

class ExtractException(Exception):
    def __init__(self, msg: str, url: str, hash: str):
        super().__init__(msg)
        self.version = SCRAPPER_VERSION
        self.url = url
        self.hash = hash

class ScrapException(Exception):
    def __init__(self, msg: str):
        super().__init__(msg)

def get_image_url(url):
    assert isinstance(url, str), type(url)
    print(url)

    try:
        response = requests.get(url)
        if response.status_code != 200:
            raise RequestException(f"wrong status code {response.status_code} on {url}")
        
        if len(response.content) == 0:
            raise RequestException("response is empty")

        image = PIL.Image.open(io.BytesIO(response.content))
        image.verify()

        return image.copy()
    except Exception as error:
        raise Exception(f"couldnt download image from {url}") from error

def ensure_content(folder, file, content):
    assert isinstance(folder, str), type(folder)
    assert isinstance(file, str), type(file)

    try:
        if not os.path.exists(folder):
            os.mkdir(folder)

        fullpath = os.path.join(folder, file)
        if os.path.exists(fullpath):
            return fullpath

        with open(fullpath, "w", encoding="UTF-16") as warpper:
            warpper.write(content)
        
        return fullpath
    except Exception as error:
        raise Exception(f"couldnt ensure {file} in {folder}")

def _get_from(url):
    assert isinstance(url, str), type(url)
    print(url)

    try:
        if url in _request_cache:
            text, hash_ = _request_cache[url]
            return bs4.BeautifulSoup(text, "html.parser"), hash_
        else:
            response = requests.get(url)
            if response.status_code != 200:
                raise RequestException(f"wrong status code {response.status_code} on {url}")
            
            if len(response.text) == 0:
                raise Exception("reponse is empty")

            soup = bs4.BeautifulSoup(response.text, "html.parser")

            main_content = soup.find("main", class_="page__main")
            if main_content is None:
                raise Exception("couldnt find main content")

            content_hash = hash(main_content.decode_contents())
            ensure_content(WEBS_FOLDER, f"{content_hash}.html", response.text)
            
            _request_cache[url] = (response.text, content_hash)
        
            return soup, content_hash
    except Exception as error:
        raise Exception(f"couldnt get from {url}")

def get_categories(soup):
    assert isinstance(soup, bs4.BeautifulSoup), type(soup)

    output: list[str] = []

    table = soup.find("div", {"class": "category-page__members"})
    if not table or not isinstance(table, bs4.element.Tag):
        return None

    combat = table.find_all("a", {"class" : "category-page__member-link"})
    if not combat or (combat and len(combat) == 0):
        return None

    for row in combat:
        name: str = row.get("title")
        if not name or not isinstance(name, str):
            return None

        output.append(name.lower())
    
    return output

def scrap_categories_thumbnails(soup):
    assert isinstance(soup, bs4.BeautifulSoup), type(soup)

    output = []

    tables = soup.find_all("ul", {"class": "category-page__members-for-char"})    
    if not tables or (tables and len(tables) == 0):
        return None

    categories, agents, outfits, *others = tables

    thumbnails = agents.find_all("img", {"class" : "category-page__member-thumbnail"})
    if not thumbnails or (thumbnails and len(thumbnails) == 0):
        return None

    values = agents.find_all("a", {"class" : "category-page__member-link"})
    if not values or (values and len(values) == 0):
        return None

    for thumbnail, value in zip(thumbnails[::2], values):
        link: str = thumbnail.get("src")
        if not link or not isinstance(link, str):
            return None
        
        cleaned_link = re.search(IMG_RE, link)
        if not cleaned_link:
            continue

        name: str = value.get("title")
        if not name or not isinstance(name, str):
            return None

        name_cleaned = re.search(r'File:Agent (.+) Icon.png', name)
        if not name_cleaned:
            continue

        name = name_cleaned.group(1).lower()
        link = cleaned_link.group(1)

        output.append((name, link))

    return output

def categories_get_by(url):
    assert isinstance(url, str), type(url)
    
    try:
        soup, content_hash = _get_from(url)

        get = get_categories(soup)
        if not get:
            raise ExtractException(f"couldnt extract categories", url, content_hash)
        
        return get
    except Exception as exception:
        raise ScrapException(f"couldnt extract categories of {url}") from exception

def get_thumbnails(url):
    assert isinstance(url, str), type(url)
    
    try:
        soup, content_hash = _get_from(url)

        get = pull_categories_thumbnails(soup)
        if not get:
            raise ExtractException("couldnt extract thumbnail", url, content_hash)
        
        return get
    except Exception as exception:
        raise ScrapException(f"couldnt extract thumbnail of {url}") from exception

def pull_factions():
    return categories_get_by(FACTIONS_URL)

def pull_playables():
    return categories_get_by(PLAYABLES_URL)

def pull_versions():
    return categories_get_by(VERSION_URL)

def pull_icons():
    return get_thumbnails(ICONS_URL)

def gallery_extract_img_url(root):
    assert isinstance(root, bs4.Tag), type(root)

    a = root.find("img")
    if not a or not isinstance(a, bs4.Tag):
        return None

    b = a.get("src")
    if not b or not isinstance(b, str):
        return None

    c = re.search(IMG_RE, b)
    if not c:
        return None

    d = c.group(1)
    if not d or not isinstance(d, str):
        return None

    return d

def gallery_extract_name(root):
    assert isinstance(root, bs4.Tag), type(root)

    a = root.find("a")
    if not a or not isinstance(a, bs4.Tag):
        return None

    b = a.get("title")
    if not b or not isinstance(b, str):
        return None

    return b

def _find_galleries(soup: bs4.BeautifulSoup) -> bs4.ResultSet:
    return soup.find_all("div", class_="wikia-gallery")

def _find_gallery(elements: list[bs4.Tag], search_for: str = DEFAULT_GALLERY):
    for root in elements:
        id = root.get("id")
        if not id or not isinstance(id, str):
            continue

        if id == search_for:
            return root
    return None

def _scrap_gallery(root: bs4.Tag):
    output = []

    elements = root.find_all("div", class_="wikia-gallery-item")
    for element in elements:
        img_part = element.find("div", class_="thumb")
        if not img_part or not isinstance(img_part, bs4.Tag):
            continue

        txt_part = element.find("div", class_="lightbox-caption")
        if not txt_part or not isinstance(txt_part, bs4.Tag):
            continue

        img_url = gallery_extract_img_url(img_part)
        if not img_url or not isinstance(img_url, str):
            continue

        txt = gallery_extract_name(txt_part)
        if not txt or not isinstance(txt, str):
            continue

        output.append((txt.lower(), img_url))

    return output

def _pull_gallery(url: str, id: str = DEFAULT_GALLERY):
    assert isinstance(url, str), type(url)
    assert isinstance(id, str), type(id)

    try:
        soup, content_hash = _get_from(url)

        galleries = _find_galleries(soup)
        if not galleries or not isinstance(galleries, bs4.ResultSet):
            raise ExtractException(f"couldnt find any galleries of {content_hash} > {url}", url, content_hash)

        element = _find_gallery(galleries, id)
        if not element:
            raise ExtractException(f"couldnt find gallery of {id} | {content_hash} > {url}", url, content_hash)

        output = _scrap_gallery(element)

        return output
    except Exception as exception:
        raise ScrapException(f"couldnt scrap gallery of {url} | {id}") from exception

def pull_attributes():
    return [(name, link_embbed_img(img_url)) for name, img_url in _pull_gallery(ATTRIBUTES_URL)]

def pull_specialities():
    return [(name, link_embbed_img(img_url)) for name, img_url in _pull_gallery(SPECIALITES_URL)]

def pull_categories_thumbnails(soup):
    thumbnails = scrap_categories_thumbnails(soup)
    return [(name, link_embbed_img(img_url)) for name, img_url in thumbnails]

def link_save_as(link: str, dest_filename: str):
    img = get_image_url(link)
    
    safe_filename = f"{dest_filename}.{EXTENSION}" if not dest_filename.endswith(f".{EXTENSION}") else dest_filename
    path = pathlib.Path(os.path.join(ASSETS_FOLDER, safe_filename))
    
    img.save(path)

    return path

def encode_img(img: PIL.Image.Image):
    buffered = io.BytesIO()
    img.save(buffered, format=EXTENSION)
    
    embbed_str = base64.b64encode(buffered.getvalue()).decode("utf-8")

    return EMBBED_IMG_TAG + embbed_str

def link_embbed_img(link: str):
    return encode_img(get_image_url(link))

def __get_from_cache(name, cache: dict, pull_func: typing.Callable):
    if len(cache) == 0:
        cache.update(pull_func())

    return cache.get(name)

def get_icon(name):
    global _icons_cache
    return __get_from_cache(name, _icons_cache, pull_icons)

def get_attribute(name):
    global _attributes_cache
    return __get_from_cache(name, _attributes_cache, pull_attributes)

def get_speciality(name):
    global _specialities_cache
    return __get_from_cache(name, _specialities_cache, pull_specialities)

def get_agent(name):
    global _agents_cache
    return __get_from_cache(name, _agents_cache, lambda : [(agent.name, agent) for agent in pull_agents()])

def get_image_name(name):
    img = None
    
    attribute = get_attribute(name)
    if not img and  attribute:
        img = attribute

    speciality = get_speciality(name)
    if not img and speciality:
        img = speciality

    icon = get_icon(name)
    if not img and icon:
        img = icon

    if not img:
        raise NotImplementedError(name)

    return img

def scrap_tables(id: str) -> list:
    try:
        soup, content_hash = _get_from(AGENT_URL)

        tables = soup.find_all("table", class_=id)
        if len(tables) == 0:
            raise NotImplementedError(f"no tables found on {content_hash}")

        return tables
    except Exception as error:
        raise NotImplementedError(f"couldnt scrap tables on {content_hash}") from error

def scrap_rows(table_root: bs4.Tag) -> list:
    try:
        head, body = table_root.find("thead"), table_root.find("tbody")    
        
        if not head or not body:
            print("table doesnt follow thead, tbody pattern")
            return table_root.find_all("tr")
        
        return body.find_all("tr")
    except Exception as error:
        raise NotImplementedError(f"couldnt scrap rows") from error

def scrap_columns(row_root: bs4.Tag) -> list:
    try:
        return row_root.find_all("td")
    except Exception as error:
        raise NotImplementedError(f"couldnt scrap columns") from error

def scrap_img(img_root: bs4.Tag, name_re: str):
    try:
        alt: str = img_root.get("alt")
        src: str = img_root.get("data-src")
        ez_filename: str = img_root.get("data-image-name")
        filename: str = img_root.get("data-image-key")

        if not re.search(CNN_IMG_RE, src):
            raise NotImplementedError(f"img src {src} doesnt match pattern")

        re_name = re.search(name_re, ez_filename)
        if not re_name:
            raise NotImplementedError(f"img name {ez_filename} doesnt match pattern")

        return re_name.group(1).lower(), alt.lower(), src.lower(), filename.lower()
    except Exception as error:
        raise NotImplementedError(f"couldnt scrap img") from error

def scrap_hyperlink(hyperlink_root: bs4.Tag):
    try:
        href: str = hyperlink_root.get("href")
        title: str = hyperlink_root.get("title")

        return href.lower(), title.lower()
    except Exception as error:
        raise NotImplementedError(f"couldnt scrap hyperlink") from error

def zzz_rank_alt(alt: str):
    if not alt in ["agentrank s", "agentrank a"]:
        return None

    return "s" if alt == "agentrank s" else "b"

def zzz_release_version(version: str):
    r = re.search(r"\d+\.\d+", version)
    if not r:
        return None

    return float(r.group().lower())

def pull_agents():
    output: list[domain.Agent] = []

    try:
        soup, content_hash = _get_from(AGENT_URL)

        tables = scrap_tables("article-table sortable")
        if not tables or (tables and len(tables) < 2):
            raise ExtractException("couldnt extract table", AGENT_URL, content_hash)

        playable_table, upcoming_table, *other = tables
        if not playable_table or not upcoming_table:
            raise ExtractException("couldnt extract playables table and upcoming table", AGENT_URL, content_hash)

        playable_rows, upcoming_rows = scrap_rows(playable_table), scrap_rows(upcoming_table)
        if (not playable_rows or (playable_rows and len(playable_rows) == 0)) or (not upcoming_rows or (upcoming_rows and len(upcoming_rows) == 0)):
            raise ExtractException("couldnt extract playables rows and upcoming rows", AGENT_URL, content_hash)

        playables_list, upcomings_list = playable_rows[1:], upcoming_rows[1:]
        for row in playables_list:
            columns: list[bs4.Tag] = scrap_columns(row)

            if not columns or (columns and len(columns) < 8):
                raise ExtractException("couldnt extract column of row", AGENT_URL, content_hash)

            cicon, cname, crank, cattribute, cspecality, cattack_type, cfaction, crelease_date, *other = columns

            icon_name, icon_alt, icon_src, icon_filename = scrap_img(cicon.find("img"), ICON_RE)
            rank_name, rank_alt, rank_src, rank_filename = scrap_img(crank.find("img"), RANK_RE)

            _, attribute_title = scrap_hyperlink(cattribute.find("a"))
            _, specality_title = scrap_hyperlink(cspecality.find("a"))
            _, attack_type_title  = scrap_hyperlink(cattack_type.find("a"))
            _, faction_title = scrap_hyperlink(cfaction.find("a"))
            _, release_version_title = scrap_hyperlink(crelease_date.find("a"))

            rank = zzz_rank_alt(rank_alt)
            release_version = zzz_release_version(release_version_title)

            if attribute_title is None or specality_title is None or release_version is None or rank is None:
                print(f"Skipping agent: {icon_name}")
                continue

            if attribute_title in ATTRIBUTES_ALIAS:
                attribute_title = ATTRIBUTES_ALIAS[attribute_title]

            agent = domain.Agent(
                icon_name, 
                rank, 
                attribute_title, 
                specality_title, 
                attack_type_title, 
                faction_title, 
                release_version
            )

            print(agent)

            output.append(agent)
        
        return output
    except Exception as exception:
        raise ScrapException("couldnt scrap agents") from exception

def get_agents():
    if not _agents_cache:
        _agents_cache.extend(pull_agents())
    return _agents_cache

def create_matrix(agents: list[domain.Agent],  h_func: typing.Callable, v_func: typing.Callable):
    matrix = utils.DynamicGrid[domain.Agent, str]()

    for agent in agents:
        print(agent)
        matrix.add_value(agent, h_func(agent), v_func(agent))

    return matrix