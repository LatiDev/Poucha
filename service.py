import json
from seleniumbase import Driver

with open("config.json", 'r') as file:
    data = json.load(file)

DRIVER = Driver(uc=True, binary_location=data["chrome_binary"], headless=True,  incognito=True)

def get_from(url: str):
    print(url)

    DRIVER.get(url)
    DRIVER.wait_for_element("main.page__main")

    return DRIVER.page_source