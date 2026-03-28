#STD
import dataclasses
import os
import re

#IN

#OUT
import bs4

LINK_RE = r'(https:\/\/static\.wikia\.nocookie\.net\/(.*)\/images\/(\w+)\/(\w+)\/(([^/]+)\.(\w+)))'
HYPERLINK_RE = r'\/wiki\/(.*)'

@dataclasses.dataclass
class ImageSrc:
    full_link: str
    wiki_name: str
    id1: str
    id2: str
    full_filename: str
    filename: str
    file_ext: str

    def __hash__(self):
        return hash(self.full_link)

    def __eq__(self, other):
        return isinstance(other, ImageSrc) and self.full_link == other.full_link

@dataclasses.dataclass
class ImageTag:
    alt: str
    src: str
    data_src: str
    data_image_name: str
    data_image_key: str

    def _get_filename(self, src):
        matchs = re.search(LINK_RE, src)
        if not matchs:
            raise NotImplementedError(src)

        return ImageSrc(*matchs.groups())

    def get_link(self):
        if re.search(LINK_RE, self.src):
            return self.src
        elif re.search(LINK_RE, self.data_src):
            return self.data_src
        
        return None
    
    @property
    def img_src(self):
        link = self.get_link()
        if not link:
            raise NotImplementedError(link)

        return self._get_filename(link)

@dataclasses.dataclass
class HyperlinkTag:
    href: str
    title: str

    def get_to(self):
        matchs = re.search(HYPERLINK_RE, self.href)
        if not matchs:
            raise NotImplementedError(self.href)

        return matchs.group(0)

WEBS_FOLDER = os.path.join("weblogs")
if not os.path.exists(WEBS_FOLDER):
    os.mkdir(WEBS_FOLDER)

def scrap_img(root: bs4.Tag):
    try:
        if not isinstance(root, bs4.Tag) or not root.name == "img":
            raise NotImplementedError(root)

        alt: str = root.get("alt")
        src: str = root.get("src")
        data_src: str = root.get("data-src")
        data_image_name: str = root.get("data-image-name")
        data_image_key: str = root.get("data-image-key")

        return ImageTag(
            alt.lower() if alt else None,
            src,
            data_src,
            data_image_name, 
            data_image_key
        )

    except Exception as error:
        raise NotImplementedError(f"couldnt scrap img") from error

def scrap_hyperlink(root: bs4.Tag):
    try:
        if not isinstance(root, bs4.Tag) or not root.name == "a":
            raise NotImplementedError(root)

        href: str = root.get("href")
        title: str = root.get("title")

        return HyperlinkTag(
            href, 
            title.lower() if title else None
        )

    except Exception as error:
        raise NotImplementedError(f"couldnt scrap hyperlink") from error