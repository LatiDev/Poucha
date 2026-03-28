#STD
import re

#IN
import fandom.core as core

#OUT
import bs4

DEFAULT_GALLERY = "gallery-0"
GALLERY_CLASS = "wikia-gallery"

def _tag_find_all(tag: bs4.Tag):
    return tag.find_all("div", class_=GALLERY_CLASS)

def _html_find_all(html: str):
    soup = bs4.BeautifulSoup(html, "html.parser")
    return _tag_find_all(soup)

def find_all(content) -> list:
    if isinstance(content, str):
        return _html_find_all(content)
    elif isinstance(content, bs4.Tag):
        return _tag_find_all(content)
    else:
        raise NotImplementedError(f"function cant handle payload of type {type(content)}")

def _tag_is_valid(tag: bs4.Tag, id: str=DEFAULT_GALLERY):
    return tag.get("id") == id

def _html_is_valid(html: str, id: str=DEFAULT_GALLERY):
    soup = bs4.BeautifulSoup(html, "html.parser")
    return _tag_is_valid(soup, id)

def is_valid(content, id: str):
    if isinstance(content, str):
        return _html_is_valid(content, id)
    elif isinstance(content, bs4.Tag):
        return _tag_is_valid(content, id)
    else:
        raise NotImplementedError(f"function cant handle payload of type {type(content)}")

def _tag_scrap(tag: bs4.Tag):
    output = []

    cells: list = tag.find_all("div", class_="wikia-gallery-item")
    if not cells or len(cells) == 0:
        raise NotImplementedError(cells)
    
    for element in cells:
        img_section = element.find("div", class_="thumb")
        if not img_section or not isinstance(img_section, bs4.Tag):
            continue

        img_part = img_section.find("img", class_="thumbimage")
        if not img_part or not isinstance(img_part, bs4.Tag):
            continue

        img = scrap_img(img_part)
        if not img or not isinstance(img, core.ImageTag):
            continue


        txt_section = element.find("div", class_="lightbox-caption")
        if not txt_section or not isinstance(txt_section, bs4.Tag):
            continue

        txt = txt_section.find("a")
        if not txt or not isinstance(txt, bs4.Tag):
            continue

        hyperlink = core.scrap_hyperlink(txt)
        if not hyperlink or not isinstance(hyperlink, core.HyperlinkTag):
            continue
        
        output.append((hyperlink, img))

    return output

def _html_scrap(html: str):
    soup = bs4.BeautifulSoup(html, "html.parser")
    return _tag_scrap(soup)

def scrap(content):
    if isinstance(content, str):
        return _html_scrap(content)
    elif isinstance(content, bs4.Tag):
        return _tag_scrap(content)
    else:
        raise NotImplementedError(f"function cant handle payload of type {type(content)}")

def find(elements: list, search: str):
    if not isinstance(elements, list) or len(elements) == 0:
        raise NotImplementedError(elements)

    for root in elements:
        if is_valid(root, search):
            return root

    return None

def _tag_scrap_img(tag: bs4.Tag):
    img = core.scrap_img(tag)

    if not re.search(core.LINK_RE, img.src):
        raise NotImplementedError(img.src)

    return img

def _html_scrap_img(html: str):
    soup = bs4.BeautifulSoup(html)
    return _tag_scrap_img(soup)

def scrap_img(content):
    if isinstance(content, str):
        return _html_scrap_img(content)
    elif isinstance(content, bs4.Tag):
        return _tag_scrap_img(content)
    else:
        raise NotImplementedError(f"function cant handle payload of type {type(content)}")

def pull(html: str, id: str=DEFAULT_GALLERY):
    try:
        galleries = find_all(html)
        if not galleries or not isinstance(galleries, bs4.ResultSet):
            raise NotImplementedError(f"couldnt find any galleries")

        element = find(galleries, id)
        if not element:
            raise NotImplementedError(f"couldnt find gallery of {id}")

        output = scrap(element)

        return output
    except Exception as exception:
        raise NotImplementedError(f"couldnt scrap gallery") from exception