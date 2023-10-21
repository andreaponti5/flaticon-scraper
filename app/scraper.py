from requests_html import HTMLSession


def get_icons_url(query):
    url = f"https://www.flaticon.com/search?word={query}"
    icons_title, icons_url = [], []
    session = HTMLSession()
    response = session.get(url)
    content = response.html.find("div.icon--holder")
    for icon in content:
        icons_title.append(icon.find("img", first=True).attrs["alt"])
        icons_url.append(icon.find("img", first=True).attrs["data-src"])
    session.close()
    return icons_url
