#!/usr/bin/env python3
import logging
import json
import datetime
import os
import sys
import traceback

import mwapi

import user_config
import bot_config

def main_path():
    return os.path.dirname(os.path.abspath(sys.modules['__main__'].__file__)) + "/"

# Init global variables
clear_do = False
cats = []
titles = []
tems = []
f = open(main_path()+"dict.json", "r")
langdict = json.load(f)

# Logging filter
class LessThanFilter(logging.Filter):
    def __init__(self, exclusive_maximum, name=""):
        super(LessThanFilter, self).__init__(name)
        self.max_level = exclusive_maximum

    def filter(self, record):
        return 1 if record.levelno < self.max_level else 0

# Set-up logging
def setup_logging():
    global logger
    # Logging
    logger = logging.getLogger("infolog")
    logger.setLevel(logging.DEBUG)
    # Formatter
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    # Stream
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(formatter)
    ch.addFilter(LessThanFilter(logging.ERROR))
    ch.setLevel(logging.DEBUG)
    logger.addHandler(ch)
    # Error stream
    eh = logging.StreamHandler(sys.stderr)
    eh.setLevel(logging.ERROR)
    eh.setFormatter(formatter)
    logger.addHandler(eh)
    # Info log
    if bot_config.enable_log:
        il = logging.FileHandler(main_path()+"logs/info.log")
        il.setLevel(logging.DEBUG)
        il.addFilter(LessThanFilter(logging.ERROR))
        il.setFormatter(formatter)
        logger.addHandler(il)
    # Error log
    el = logging.FileHandler(main_path()+"logs/crashreport.log")
    el.setLevel(logging.ERROR)
    el.setFormatter(formatter)
    logger.addHandler(el)

# Login
def login():
    global session
    session = mwapi.Session(bot_config.site, user_agent="RemBot/1.0", api_path=bot_config.api)
    session.login(user_config.username, user_config.password)

# Load config from the config page
def load_config(path):
    params = {
        "action": "query",
        "prop": "revisions",
        "titles": path,
        "rvprop": "content"
    }
    query = session.get(params)["query"]["pages"]
    for pageid in query:
        if pageid == "-1":
            return False
        if "revisions" not in query[pageid]:
            return False
        return query[pageid]["revisions"][0]["*"]

    return False

# Param maker
def param_maker(values):
    if type(values) != list:
        return values

    final_str = ""
    for i in range(len(values)):
        final_str += str(values[i])

        if i < len(values) - 1:
            final_str += "|"

    return final_str

# Purge cats
def purge_cats():
    for cat in cats:
        session.post(action="purge", generator="categorymembers", gcmtitle=cat, gcmprop="title", gcmlimit=5000, forcelinkupdate=True)

# Purge templates
def purge_tems():
    for tem in tems:
        session.post(action="purge", generator="embeddedin", geititle=tem, geilimit=5000, forcelinkupdate=True)

# Purge pages
def purge_pages():
    session.post(action="purge", titles=param_maker(titles), forcelinkupdate=True)

def should_purge(timestr):
    now = datetime.datetime.now()
    timestr = timestr.split("/")
    if "*" not in timestr[0] and int(timestr[0]) != now.hour:
        return False

    elif "*" not in timestr[1] and int(timestr[1]) != now.minute:
        return False

    return True

def value2list(value):
    logger.info("listing %s" % value)
    if langdict[bot_config.lang]["cat"].lower() in value.lower():
        cats.append(value)
    elif langdict[bot_config.lang]["tem"].lower() in value.lower():
        tems.append(value)
    else:
        titles.append(value)

# Add titles to lists
def list2list(tlist):
    for value in tlist:
        value2list(value)

# Check should purge
def pages2purge():
    global clear_do
    for value in config:
        if should_purge(value):
            logger.info("found schedule for purge %s" % value)
            list2list(config[value])

    if(do_status):
        for value in do_once:
            clear_do = True
            logger.info("found do once schedule for purge %s" % value)
            value2list(value)

def get_token():
    return session.get(action="query", meta="tokens")["query"]["tokens"]["csrftoken"]

def clear_do_once():
    session.post(action="edit", title=bot_config.do_once, text="[]", summary=do_status+langdict[bot_config.lang]["do_desc"], minor=True, bot=True, token=get_token())

def main():
    try:
        # Global variables
        global config
        global do_once
        global do_status
        # Log
        setup_logging()
        logger.info("logging in...")
        # Login
        login()

        logger.info("downloading refresh list from %s" % bot_config.refresh_list)
        logger.info("downloading do once list from %s" %bot_config.do_once)
        # Load config
        config = load_config(bot_config.refresh_list)
        do_once = load_config(bot_config.do_once)
        # If config not loaded exit
        if not config:
            logger.error("failed to download refresh list")
            return 1

        config = json.loads(config)
        try:
            do_once = json.loads(do_once)
            do_status = "[OK]: "
        except:
            do_status = False
        logger.info("listing pages for purge")
        pages2purge()

        if len(titles) > 0:
            logger.info("purging pages")
            purge_pages()
        if len(cats) > 0:
            logger.info("purging categories")
            purge_cats()
        if len(tems) > 0:
            logger.info("purging templates")
            purge_tems()

        if(clear_do):
            clear_do_once()

        logger.info("done")
    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt")
    except:
        logger.error("error: faced unexcepted error check crash report")
        logger.critical(traceback.format_exc())

if __name__ == "__main__":
    main()
