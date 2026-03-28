#STD
import re

#IN
import fandom.core as core

#OUT
import bs4

def _scrap_image(root: bs4.Tag):
    image = core.scrap_img(root)

    #if not re.search(r'agent (.*) icon\.png', image.alt):
    #    raise NotImplementedError(image.alt)

    if not re.search(core.LINK_RE, image.src):
        raise NotImplementedError(image.src)
    
    if not re.search(core.LINK_RE, image.data_src):
        raise NotImplementedError(image.data_src)
    
    return image

def _scrap_hyperlink(root: bs4.Tag):
    hyperlink = core.scrap_hyperlink(root)

    #if not re.search(r'\/wiki\/File:Agent_(.*)_Icon.png', hyperlink.href):
    #    raise NotImplementedError(hyperlink.href)

    if not re.search(core.HYPERLINK_RE, hyperlink.href):
        raise NotImplementedError(hyperlink.href)

    #if not re.search(r'file:agent (.*) icon\.png', hyperlink.title):
    #    raise NotImplementedError(hyperlink.title)

    return hyperlink

def find_all(content) -> list:
    if isinstance(content, str):
        content = bs4.BeautifulSoup(content, "html.parser")

    tables = content.find_all("ul", {"class": "category-page__members-for-char"})    
    if not tables or (tables and len(tables) == 0):
        raise NotImplementedError(content)
    
    return tables

def _tag_get_from(root: bs4.Tag):
    if not isinstance(root, bs4.Tag) or not root.name == "ul":
        raise NotImplementedError(root)
    
    class_ = root.get("class")
    if "category-page__members-for-char" not in class_:
        raise NotImplementedError(class_)

    output = []

    for row in root.find_all("li", {"class": "category-page__member"}):
        thumbnail = row.find("img", {"class" : "category-page__member-thumbnail"})
        value = row.find("a", {"class" : "category-page__member-link"})

        img = _scrap_image(thumbnail) if thumbnail else None
        hyperlink = _scrap_hyperlink(value) if value else None

        if not img and not hyperlink:
            raise NotImplementedError(row)
        
        output.append((hyperlink, img))

    return output

def _html_get_from(html: str):
    soup = bs4.BeautifulSoup(html, "html.parser")
    return _tag_get_from(soup)

def get_from(content):
    if isinstance(content, str):
        return _html_get_from(content)
    elif isinstance(content, bs4.Tag):
        return _tag_get_from(content)
    else:
        raise NotImplementedError(f"function not implemented for type {type(content)}")

def get_all(content):
    if isinstance(content, str):
        content = bs4.BeautifulSoup(content, "html.parser")

    sections = content.find_all("ul", {"class": "category-page__members-for-char"})    
    if not sections or (sections and len(sections) == 0):
        raise NotImplementedError(content)
    
    output = []

    for section in sections:
        for row in section.find_all("li", {"class": "category-page__member"}):
            thumbnail = row.find("img", {"class" : "category-page__member-thumbnail"})
            value = row.find("a", {"class" : "category-page__member-link"})

            img = _scrap_image(thumbnail) if thumbnail else None
            hyperlink = _scrap_hyperlink(value) if value else None

            if not img and not hyperlink:
                raise NotImplementedError(row)
            
            output.append((hyperlink, img))

    return output