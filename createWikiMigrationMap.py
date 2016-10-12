#!/usr/bin/python
#
# Walk an existing MoinMoin wiki, and create a map of what to do with the pages.
# by default every page action is "move"

import argparse
import urllib                             # copying from web to filesystem
import urllib2                            # HTTP access
import HTMLParser                         #
import os
import os.path
import time                               # I need sleep


ALL_PAGES = "TitleIndex"                  # links to all pages we can see

class MoinPageList (HTMLParser.HTMLParser):
    """
    The HTML page listing all the pages on a MoinMoin Wiki.
    """

    def __init__(self, htmlText):

        HTMLParser.HTMLParser.__init__(self)

        self.inPageList = False           # once true, stays true 
        self.inPageLink  = False          # Only true in <a> tag
        self.htmlText = htmlText
        self.urlOpener = urllib.URLopener()

        return (None)

    def genPageSpreadSheet(self):
        """
        Generate a TSV showing each page
        """
        print("Old Location\tAction\tNew Location\tComments")
        self.feed(self.htmlText)        # process the HTML text; dealing with each page

        return(None)

    def handle_starttag(self, tag, attrs):
        if tag == "h2":
            self.inPageList = True        # page links section has started
        elif tag == "li" and self.inPageList:
            self.inPageLink = True
        elif tag == "a" and self.inPageLink: 
            # build a page URL
            pageName = attrs[0][1]
            newPageName = pageName.replace("%20",'')
            pageUrl = self.baseWikiUrl + pageName
            print(pageUrl + "\tKeep\t" + newPageName + "\t")
            
        return(None)

    def handle_data(self, data):
        #print data
        return(None)

    def handle_endtag(self, tag):
        if tag == "a":
            self.inPageLink = False
        return(None)


class Argghhs(object):
    """
    Process and provide access to command line arguments.
    """

    def __init__(self):
        argParser = argparse.ArgumentParser(
            description='Pull all the pages from the MoinMoin Wiki.  Prints the URL of any copied page.',
            epilog = 'Example:\n    createWikiMigrationMap.py --basewikiurl="https://wiki.galaxyproject.org/"')
        argParser.add_argument(
            "--basewikiurl", required=True,
            help="The base URL of the Moin wiki to copy")
        self.args = argParser.parse_args()

        return(None)

args = Argghhs()
        
                
# Get the HTML for page listing all pages in wiki
pageHtml = urllib2.urlopen(args.args.basewikiurl + ALL_PAGES).read()

moinPageList = MoinPageList(pageHtml)
moinPageList.baseWikiUrl = args.args.basewikiurl
moinPageList.genPageSpreadSheet()







