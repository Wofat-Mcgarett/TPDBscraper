import yaml
import sys
from tpdbUtil import getTPDBimage
import ast
import datetime
import argparse
import logging as log
import requests
import os.path
import ruamel.yaml
import shutil
import sqlite3

parser = argparse.ArgumentParser()
parser.add_argument(dest="config_path",
                    help="Run with desired config.yml file",
                    type=str,
                    nargs='?')
parser.add_argument("-o", "--overwrite",
                    action = "store_true",
                    dest="overwrite",
                    help="Replaces poster config that has already been set up in PAC")
parser.add_argument("-oi", "--overwrite-image",
                    action = "store_true",
                    dest="overwrite_image",
                    help="Overwrites the image at download path if already exists")
parser.add_argument("-v", "--verbose",
                    action = "store_true",
                    dest="verbose",
                    help="More detailed logs.")
parser.add_argument("-dl", "--download", "--downloader",
                    dest="download",
                    help="Download the images to the specified file path. Will be named collection.jpg",
                    type=str)
parser.add_argument("-is", "--image-server",
                    action = "store_true",
                    dest="image_server",
                    help="Use this tag if you would like Plex-Auto-Collections to use the image server instead of folder_path")
parser.add_argument("-strict", "--strict-mode",
                    action = "store_true",
                    dest="strict_mode",
                    help="Only grab images matching the exact collection name. ")
parser.add_argument("-pmm", "--plex-meta-manager",
                    action = "store_true",
                    dest="pmm",
                    help="Set url_poster for Plex Meta Manager.")
parser.add_argument("-docker", "--docker_path",
                    dest="docker",
                    help="USE IF USING PROGRAMS ON DOCKER. Sets the image path to the docker path specified.",
                    type=str)
parser.add_argument("-pac", "--plex-auto-collections",
                    action = "store_true",
                    dest="pac",
                    help="use for Plex-Auto-Collections")
parser.add_argument("-movie", "--movie-mode",
                    action = "store_true",
                    dest="movie_mode",
                    help="Use this to download posters for all movies in the radarrDB. Use this with download set to a appropriate directory")
parser.add_argument("-radarr", "--radarr", "--radarr_db",
                    dest="radarr",
                    help="When using movie mode, use this to specify the radarr database to use.",
                    type=str)
parser.add_argument("-root", "--root-folder", "--root",
                    dest="root",
                    help="Use this in movie mode. Set it to the radarr root folder path",
                    type=str)
args = parser.parse_args()
# Start Logger. Only send log.info unless verbose on.
if args.verbose:
    log.basicConfig(format="%(asctime)s  - %(levelname)s: %(message)s", level=log.DEBUG, datefmt='%Y-%m-%d %H:%M:%S')
    log.info("Verbose output.")
else:
    log.basicConfig(format="%(asctime)s - %(levelname)s: %(message)s", level=log.INFO, datefmt='%Y-%m-%d %H:%M:%S')

if args.pac and args.pmm:
    log.info("Cannot use both Plex-Auto-Collection and Plex-Meta-Manager modes. Please specify only one")
    exit()
if not args.pac and not args.pmm and not args.movie_mode:
    log.info("Please spcify which app to use. Plex-Auto-Collections -pac or Plex-Meta-Manager -pmm")
    exit()

if args.movie_mode and not args.radarr:
    log.info("Movie mode needs a radarr database to pull moives from")
    exit()

if args.movie_mode and not args.download:
    log.info("Movie mode needs a download path")
    exit()

if args.movie_mode and not args.root:
    log.info("Please specify the radarr root folder when in movie mode -root")
    exit()

config_path = args.config_path
if config_path is None:
    log.info("No config provided. Please specify config path with /path/to/config.yml")
    exit()

def downloadImage(url, filepath):
    # Dont overwrite file if it already exist, unless overwrite mode is on.
    if os.path.isfile(filepath) and not args.overwrite_image:
        log.info("Image file already exists at path {}, skipping.".format(filepath))
        return 
    else:
        r = requests.get(url)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'wb') as outfile:
            outfile.write(r.content)
            log.info("Downloaded image to {}".format(filepath))
            outfile.close()
            return 
    return 

# Get the poster path. This is what is saved in the config. If we use image server we need to use the one from the config. 
def getPosterMode():
    # If download mode on, poster path will be provided path. Config mode is 'file_poster'
    if args.download and not args.image_server:
        mode = 'file_poster'
        return mode
    # If image server and download mode is on, poster path will be the one specified with -d, mode will be None as we dont need to specify a path when using image server.
    elif args.image_server and args.download:
        return 'image_server'
    # If only image server is on, nothing will be set as they have not specified to downlaod.    
    elif args.image_server:
        return None
    #If all else fails, use the URL and set the mode to 'poster'
    mode = 'poster'
    return mode

        

def openConfig(config_path):
    yaml = ruamel.yaml.YAML()
    #Log the start
    log.info("{} grabbing config...".format(datetime.datetime.now()))
    #try to open the config
    try:
        with open(config_path, "r") as conf:
            shutil.copy(config_path, config_path + ".backup")
            # Load the yaml config
            return ruamel.yaml.load(conf, ruamel.yaml.RoundTripLoader) 
            #Close it now we have it saved as a var
            conf.close() 

    # Grab the collections from the config
    except:
        log.info("Could not open the specified config at {} are you sure the path is correct".format(config_path))
        exit()

def grabCollections(config):
    if config['collections'] is None:
        log.info("No collections found in the provided config {} are you sure this is the right path?".format(config_path))
        exit()
    return config['collections']

def grabURL(collection):
    url = getTPDBimage(collection, args.strict_mode)
    if url is None: 
        log.info("No image found on TPDB matching collection: {}, Skipping.".format(collection)) 
        return None
    return url

def movieModeFilePath(path):
    if args.download and args.root:
        downloadPath = args.download if args.download.endswith("/") else args.download + "/"
        rootPath = args.root if args.root.endswith("/") else args.root + "/"
        
        folderName = path[len(rootPath):]
        return downloadPath + folderName + "/" + "poster.jpg"


def movieMode():
    try:
        radarrDBpath = args.radarr
        radarrDB = sqlite3.connect(radarrDBpath)
        movies = radarrDB.execute("SELECT Title, Path FROM Movies").fetchall()
    except:
        log.info("There was an issue reaching the radarr database")
        exit()
    for title, path in movies:
        poster_path = movieModeFilePath(path)
        if not os.path.isfile(poster_path) and not args.overwrite_image: 
            url = grabURL(title)
            if url is None: continue
            downloadImage(url, poster_path)
        else:
            log.info("Poster path {} already exists. User -oi if you want to overwrite these images".format(poster_path))
            continue

def addPostersToPAC():
    log.info("===================================================================================================")
    log.info("=                       Starting The Poster Databse Scraper                                       =")
    log.info("=                   Author: Jolbol1, https://github.com/jolbol1                                   =")
    log.info("===================================================================================================")
    log.info("Config: {}".format(args.config_path))
    log.info("Download Path: {}".format(args.download))
    log.info("Image Server: {}".format(args.image_server))
    log.info("Overwrite: {}".format(args.overwrite))
    log.info("Strict Mode: {}".format(args.strict_mode))
    log.info("===================================================================================================")

    if args.movie_mode:
        movieMode()
        return
    # Grab the collections in the config. Will exit if none found.
    loaded_config = openConfig(config_path)
    collections = grabCollections(loaded_config)
    # Parse over the individual collections withing.
    mode = getPosterMode()
    for collection in collections:

        #Overwrite existing entries if -o used.
        if args.overwrite:
            if collections[collection].get('file_poster'):
                del collections[collection]['file_poster']
            if collections[collection].get('poster'):
                del collections[collection]['poster']

        if mode is 'file_poster':
            poster_path = args.download + "/" + collection +".jpg"
            if not os.path.isfile(poster_path) and not args.overwrite_image: 
                url = grabURL(collection)
                if url is None: continue
                downloadImage(url, poster_path)
            else:
                log.info("Poster path {} already exists. User -oi if you want to overwrite these images".format(poster_path))
            if args.docker:
                poster_path = args.docker + "/" + collection +".jpg"
            collections[collection][mode] = poster_path
            log.info("{} {} set to {}".format(collection, mode, poster_path))
        elif mode is 'poster':
            url = grabURL(collection)
            if url is None: continue
            if args.pmm:
                collections[collection]['url_poster'] = url
            else:
                collections[collection][mode] = url
            log.info("{} {} set to {}".format(collection, mode, url))
        elif mode is 'image_server':
            url = grabURL(collection)
            if url is None: continue
            poster_path = args.download + "/" + collection +".jpg"
            downloadImage(url, poster_path)
        elif mode is None:
            log.info("You should specify a download path with -d when using image server, otherwise nothing will change.")
            return

    with open(config_path, 'w') as conf:
        ruamel.yaml.dump(loaded_config, conf, ruamel.yaml.RoundTripDumper)      
addPostersToPAC()
