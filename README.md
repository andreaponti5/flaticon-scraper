# Easily download icons from Flaticon
This repository contains a simple Python Dash web app to scrape the [Flaticon](https://www.flaticon.com/) website and easily download groups of images.

The app is deployed on vercel at the following link: [Flaticon Scraper](https://flaticon-scraper.vercel.app/).

# Flaticon Scraper
The web app allows you to search for a list of queries separated by `;`. For each query a set of icons taken from Flaticon are proposed.
You can select the icons to download by simply clicking on them. Finally you can download all the selected icons in a zip file.
![flaticon_scraper_demo](https://github.com/andreaponti5/flaticon-scraper/assets/59694427/c40c3738-fd5b-4056-8041-95c0c9eb63db)


## Deploy on a local enviroment
You can run the application in a local enviroment by installing all the required library:
```bash
pip install requirements.txt
```

And running:
```bash
python app/app.py
```

It is also possible to run the web app with docker:
```bash
docker compose up
```
