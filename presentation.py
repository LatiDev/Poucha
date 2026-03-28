#STD
import os
import pathlib

#IN

#OUT
from playwright.sync_api import sync_playwright
import mako.lookup

def use_lookup(folder: str, filename: str, **kwargs):
    lookup = mako.lookup.TemplateLookup(directories=[folder])
    
    template = lookup.get_template(filename)
    rendered = template.render(**kwargs)

    return rendered

def html_to_png(html: str, css: str, id: str, output: pathlib.Path):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        page.set_content(html)
        page.add_style_tag(content=css)

        div = page.query_selector(id)
        if not div:
            raise NotImplementedError(f"{id} not found in {html} file. Don't forget to add it")

        #with open("page.html", 'w') as file:
        #    file.write(page.content())

        div.screenshot(path=output)

        browser.close()

def render_file(template: pathlib.Path, html: pathlib.Path, css: pathlib.Path, output: pathlib.Path, id: str = "#capture", **kwargs):
    rendered_html = use_lookup(os.fspath(template), os.fspath(html), **kwargs)
    
    css_content = (template / css).read_text()
    html_to_png(rendered_html, css_content, id, os.fspath(output))