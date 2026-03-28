#STD

#IN

#OUT
import bs4

def _tag_find_all(root: bs4.Tag) -> list:
    tables = root.find_all("table", class_="article-table")
    if not tables or len(tables) == 0:
        raise NotImplementedError(f"no tables found in {root}")

    return tables

def _html_find_all(html: str) -> list:
    soup = bs4.BeautifulSoup(html, "html.parser")
    return _tag_find_all(soup)

def find_all(content):
    if isinstance(content, str):
        return _html_find_all(content)
    elif isinstance(content, bs4.Tag):
        return _tag_find_all(content)
    else:
        raise NotImplementedError(f"function cant handle payload of type {type(content)}")

def _tag_get_rows(table: bs4.Tag) -> list:
    head, body = table.find("thead"), table.find("tbody")    
    
    if not head or not body:
        print("table doesnt follow thead, tbody pattern")
        return table.find_all("tr")
    
    return body.find_all("tr")

def _html_get_rows(html: str):
    soup = bs4.BeautifulSoup(html, "html.parser")
    return _tag_get_rows(soup)

def get_rows(content):
    if isinstance(content, str):
        return _html_get_rows(content)
    elif isinstance(content, bs4.Tag):
        return _tag_get_rows(content)
    else:
        raise NotImplementedError(f"function cant handle payload of type {type(content)}")
    
def _tag_get_columns(root: bs4.Tag) -> list:
    return root.find_all("td")

def _html_get_columns(html: str):
    soup = bs4.BeautifulSoup(html, "html.parser")
    return _tag_get_columns(soup)

def get_columns(content) -> list:
    if isinstance(content, str):
        return _html_get_columns(content)
    elif isinstance(content, bs4.Tag):
        return _tag_get_columns(content)
    else:
        raise NotImplementedError(f"function cant handle payload of type {type(content)}")