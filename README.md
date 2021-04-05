# TPDBscraper
An unofficial poster scraper for collections and movies. Can be used with Plex-Auto-Collections or Plex-Meta-Manager

# TPDBscraper
Will automatically grab the most popular poster from TPDB for your "Plex-Auto-Collections" config

## Usage
To run, `python3 pacTPDB.py /path/to/plex-auto-collections/config.yml`

By default this will use URL's for the posters

By default this script will not replace any poster config you have already set up in Plex-Auto-Collections, add `-o` to force it to overwrite, e.g: `python3 pacTPDB.py -c /path/to/plex-auto-collections/config.yml -o`

All options:
```
positional arguments:
  config_path           Run with desired config.yml file

optional arguments:
  -h, --help            show this help message and exit
  -o, --overwrite       Replaces poster config that has already been set up in
                        PAC
  -oi, --overwrite-image
                        Overwrites the image at download path if already
                        exists
  -v, --verbose         More detailed logs.
  -dl DOWNLOAD, --download DOWNLOAD, --downloader DOWNLOAD
                        Download the images to the specified file path. Will
                        be named collection.jpg
  -is, --image-server   Use this tag if you would like Plex-Auto-Collections
                        to use the image server instead of folder_path
  -strict, --strict-mode
                        Only grab images matching the exact collection name.

```
Runnig the script with only -is will do nothing. You must specify where to download the images to with -dl aswell. REMEMBER: If using docker for Plex-Auto-Collections this should not be the image server path on the docker, it should be the path on your machine.
