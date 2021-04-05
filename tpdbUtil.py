import mechanicalsoup
import sys
import urllib.parse
import logging as log

def getTPDBimage(collection, strict=False):

    # Connect to duckduckgo
    collection_search = urllib.parse.quote_plus(str(collection))
    browser = mechanicalsoup.StatefulBrowser(user_agent="MechanicalSoup")
    url = "https://theposterdb.com/search?term={}".format(collection_search)
    log.debug("Attempting search at: {}".format(url))
    browser.open(url)
    for link in browser.links():
        if strict:
            if "<strong>{}</strong>".format(collection) in str(link):
                return imageSelect(link.attrs['href'])

        else:
            if collection in str(link):
                return imageSelect(link.attrs['href'])



def imageSelect(collection):
    log.debug("Search found: {}".format(collection))
    browser = mechanicalsoup.StatefulBrowser(user_agent="MechanicalSoup")
    browser.open(collection)
    page = browser.get_current_page()
    all_images = page.findAll('picture')
    log.debug("Found {} images on page".format(len(all_images)))
    image_list = []
    for image in all_images:
        for src in image.find_all('source'):
            if (src['srcset'].endswith(".jpg") and not src['srcset'].startswith("https://image.tmdb.org")):
                image_list.append(src['srcset'])

    if image_list:
        log.debug("Narrowed down to {} images".format(len(image_list)))
        return image_list[0]    
    return None

