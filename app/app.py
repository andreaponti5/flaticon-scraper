import io
import logging
import zipfile
from typing import Tuple, List, Union

import dash
import dash_bootstrap_components as dbc
import requests
from dash import ALL, html, Output, Input, State, dcc, ctx
from dash.exceptions import PreventUpdate
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


# Initilize the logger
logging.basicConfig(format='[%(asctime)s] [%(levelname)s]: %(message)s', level=logging.INFO)

# Initialize the Dash app
dash_app = dash.Dash(__name__,
                     external_stylesheets=[
                         dbc.icons.BOOTSTRAP,
                         dbc.themes.BOOTSTRAP,
                         "https://fonts.googleapis.com/css2?family=Montserrat:wght@400;700&display=swap",
                         "/assets/style.css"
                     ])
dash_app.title = "Flaticon Scraper"
server = dash_app.server
app = dash_app.server

# Init variables to keep the status
dash_app.current_page = None
dash_app.search_queries = []
dash_app.imgs_scraped = {}
dash_app.selection_state = {}
dash_app.imgs_url_to_dwnl = {}
dash_app.folder_name = "flaticon-scraper.zip"

# Define the search bar
search_bar = dbc.Row([
    dbc.Col([
        html.H1("Flaticon Scraper")
    ],
        width={"size": 2},
        style={"display": "flex", "align-items": "center"},
    ),
    dbc.Col([
        dbc.Input(
            placeholder="Enter your keywords separated by ;",
            size="lg",
            id='search-bar',
            style={"height": "100%"}
        ),
    ],
        width={"size": 6},
        style={"display": "flex", "align-items": "center"},
    ),
    dbc.Col([
        dbc.Button([
            html.I(className='bi bi-search', ),
        ],
            id='search-button',
            type='button',
            size="lg"),
    ],
        width={"size": 1},
        style={"display": "flex", "justify-content": "center"}
    ),
    dbc.Col([
        dbc.Button([
            html.I(className='bi bi-download', ),
        ],
            disabled=True,
            id='download-button',
            type='button',
            size="lg",
            color="danger"
        ),
        dcc.Download(id="download-zip"),
    ],
        width={"size": 1},
        style={"display": "flex", "justify-content": "left"}
    ),
],
    justify="center",
)

# Define the navigation bar
navbar = dbc.Row([
    dbc.Col([
        dbc.Button([
            html.I(className='bi bi-caret-left-fill', ),
        ],
            id='previous-button',
            type='button',
            size="sm",
            color="primary",
            n_clicks=0,
        ),
    ], width={"size": 1}, style={"display": "flex", "justify-content": "left"}),
    dbc.Col([
        html.H2(id="h2-subpage")
    ], width={"size": 4, "offset": 3}, style={"display": "flex", "justify-content": "center", "align-items": "center"}),
    dbc.Col([
        dbc.Button([
            html.I(className='bi bi-caret-right-fill', ),
        ],
            id='next-button',
            type='button',
            size="sm",
            color="primary",
            n_clicks=0,
        ),
    ], width={"size": 1, "offset": 3}, style={"display": "flex", "justify-content": "right"}),
],
    id="row-navbar",
    style={"visibility": "hidden"}
)

# Define the app layout
dash_app.layout = dbc.Container([
    html.Br(),
    search_bar,
    navbar,
    dbc.Row(id="images-row", justify="center"),
], fluid=True, style={"max-width": "90%"})


@dash_app.callback(
    Output("row-navbar", "style"),
    Output("h2-subpage", "children", allow_duplicate=True),
    Input("search-button", "n_clicks"),
    State("search-bar", "value"),
    prevent_initial_call=True,
)
def scrape_imgs(
        n_clicks: int,
        search_query: str,
) -> Tuple[dict, Union[str, None]]:
    """
    Get a list of images urls for each search query.

    :param n_clicks: number of search-button clicks.
    :param search_query: strings to search in Flaticon separeted by ;.
    :return: make the navbar visible and update the navbar titles.
    """
    logging.debug(f"Callback triggered: scrape_imgs {[n_clicks]}")
    if n_clicks > 0:
        style = {
            "visibility": "visible",
            "background": "#0D6EFDFF",
            "padding": "5px",
            "margin": "15px 0px",
            "border-radius": "25px"
        }
        if ";" not in search_query:
            dash_app.search_queries = [search_query.strip()]
        else:
            dash_app.search_queries = [query.strip() for query in search_query.split(";")]
        logging.info(f"Search queries: {dash_app.search_queries}")
        dash_app.imgs_scraped = {query: get_icons_url(query) for query in dash_app.search_queries}
        dash_app.selection_state = {query: [0] * len(dash_app.imgs_scraped[query]) for query in dash_app.search_queries}
        dash_app.imgs_url_to_dwnl = {query: [] for query in dash_app.search_queries}
        dash_app.current_page = 0
        return style, dash_app.search_queries[0]
    raise PreventUpdate


@dash_app.callback(
    Output("images-row", "children", allow_duplicate=True),
    Input("h2-subpage", "children"),
    prevent_initial_call=True,
)
def show_imgs(
        title: str,
) -> List[dbc.Col]:
    """
    Show the images related to the current page search query.

    :param title: the query.
    :return: a list of images wrapped in dbc.Col.
    """
    logging.debug(f"Callback triggered: show_imgs [{title}]")
    if title in dash_app.search_queries:
        return [dbc.Col([
            html.Img(
                src=url,
                id={"type": "image", "index": i},
                className="image",
                n_clicks=0,
            )
        ]) for i, url in enumerate(dash_app.imgs_scraped[title])]
    raise PreventUpdate


@dash_app.callback(
    Output("h2-subpage", "children", allow_duplicate=True),
    Input("next-button", "n_clicks"),
    Input("previous-button", "n_clicks"),
    prevent_initial_call=True,
)
def change_page(
        next_n_clicks: int,
        previous_n_clicks: int,
) -> str:
    """
    Go to the next or previous page.

    :param next_n_clicks: number of next-button clicks.
    :param previous_n_clicks: number of previous-button clicks.
    :return: update the navbar title (this will trigger also the images update).
    """
    logging.debug(f"Callback triggered: change_page [{next_n_clicks}, {previous_n_clicks}]")
    button_id = ctx.triggered_id
    if button_id is not None:
        if (next_n_clicks > 0) and (button_id == "next-button"):
            dash_app.current_page = dash_app.current_page + 1
            logging.info(f"Going to next page")
        elif (previous_n_clicks > 0) and (button_id == "previous-button"):
            dash_app.current_page = dash_app.current_page - 1
            logging.info(f"Going to previous page")
        else:
            raise PreventUpdate
        if dash_app.current_page < 0:
            dash_app.current_page = len(dash_app.search_queries) - 1
        elif dash_app.current_page >= len(dash_app.search_queries):
            dash_app.current_page = 0
        return dash_app.search_queries[dash_app.current_page]
    raise PreventUpdate


@dash_app.callback(
    Output("images-row", "children", allow_duplicate=True),
    Output("download-button", "disabled"),
    Input({"type": "image", "index": ALL}, "n_clicks"),
    State("images-row", "children"),
    prevent_initial_call=True,
)
def select_img(
        click_data: List[int],
        current_children: dict,
) -> Tuple[dict, bool]:
    """
    Add or remove an image to the list of images to download.

    :param click_data: number of clicks for each image.
    :param current_children: list of images currently visualized.
    :return: the list of images currently visualized, highlighting the selected ones.
        If at least an image is selected the download-button is enabled.
    """
    logging.debug("Callback triggered: select_img")
    disable_button = True
    if not click_data:
        return current_children, disable_button
    current_page = dash_app.search_queries[dash_app.current_page]
    clicked_img = ctx.triggered_id.index
    if click_data[clicked_img] != 0:
        dash_app.selection_state[current_page][clicked_img] = dash_app.selection_state[current_page][clicked_img] + 1
    click_data = dash_app.selection_state[current_page]
    idx_to_update = [i for i, click in enumerate(click_data) if click is not None]
    if len(idx_to_update) == 0:
        return current_children, disable_button
    for idx in idx_to_update:
        current_img_url = current_children[idx]["props"]["children"][0]["props"]["src"]
        if click_data[idx] % 2 == 1:
            current_children[idx]["props"]["children"][0]["props"]["className"] = "image clicked"
            if current_img_url not in dash_app.imgs_url_to_dwnl[current_page]:
                dash_app.imgs_url_to_dwnl[current_page].append(current_img_url)
                logging.info(f"Add image to download list [{current_img_url}]")
        else:
            current_children[idx]["props"]["children"][0]["props"]["className"] = "image"
            if current_img_url in dash_app.imgs_url_to_dwnl[current_page]:
                dash_app.imgs_url_to_dwnl[current_page].remove(current_img_url)
                logging.info(f"Remove image from download list [{current_img_url}]")
    if len(sum(dash_app.imgs_url_to_dwnl.values(), [])) > 0:
        disable_button = False
    logging.info(f"Updated download list: {dash_app.imgs_url_to_dwnl}")
    return current_children, disable_button


@dash_app.callback(
    Output("download-zip", "data"),
    Input("download-button", "n_clicks"),
    prevent_initial_call=True,
)
def download_imgs(
        n_clicks: int,
) -> dict[str, Union[str, bool]]:
    """
    Download the list of selected images from Flaticon into a zip file.

    :param n_clicks: number of download-button clicks.
    :return: dict of file content (base64 encoded) and metadata used by the Download component.
    """
    logging.debug(f"Callback triggered: download_imgs [{n_clicks}]")
    if n_clicks and len(sum(dash_app.imgs_url_to_dwnl.values(), [])) > 0:
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zipf:
            for key in dash_app.imgs_url_to_dwnl:
                logging.info(f"Downloading images [{key}]: {dash_app.imgs_url_to_dwnl[key]}")
                use_idx = True if len(dash_app.imgs_url_to_dwnl[key]) > 1 else False
                for i, image_url in enumerate(dash_app.imgs_url_to_dwnl[key]):
                    response = requests.get(image_url)
                    if response.status_code == 200:
                        image_data = response.content
                        if use_idx:
                            zipf.writestr(f"{key}_{i + 1}.png", image_data)
                        else:
                            zipf.writestr(f"{key}.png", image_data)
        zip_buffer.seek(0)
        return dcc.send_bytes(src=zip_buffer.getvalue(), filename=dash_app.folder_name)


if __name__ == '__main__':
    dash_app.run_server(
        debug=False,
        dev_tools_hot_reload=False,
    )
