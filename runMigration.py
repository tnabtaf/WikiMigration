#!/usr/local/bin/python3
# -*- coding: utf-8 -*-
#
# Migrate from Moin to Markdown.  Takes a Moin directory structure, translates the files
# and then creates a corresponding Markdown structure

import os
import os.path
import argparse
import parseMoinToMarkdown

notImplementedPages = []                  # Pages containing makup that we aren't translating

class Argghhs(object):
    """
    Process and provide access to command line arguments.
    """

    def __init__(self):
        argParser = argparse.ArgumentParser(
            description='Convert all pages from MoinMoin to Markdown.',
            epilog = 'Example:\n    runMigration.py --srcdir="MoinPages" --destdir="MarkdownPages --onlynew')
        argParser.add_argument(
            "--srcdir", required=True,
            help="Path of directory to get Moin pages from")
        argParser.add_argument(
            "--destdir", required=True,
            help="Path of directory to put translated pages into")
        argParser.add_argument(
            "--onlynew", required=False, action="store_true",
            help="Only translate pages you haven't already translated")
        self.args = argParser.parse_args()

        return(None)


def traverse(srcdir, destdir, indent):
    """
    Implement each individual Moin page as it's own directory, with the text of the page in
    index.md in that directory.
    """
    global notImplementedPages, args
    
    for root, dirs, files in os.walk(srcdir):
        for file in files:
            fileDestDir = destdir + '/' + file[:-5]
            fileDestDirNew = False
            if not os.path.exists(fileDestDir):
                os.mkdir(fileDestDir)
                fileDestDirNew = True
            destfile = fileDestDir + '/index.md'
            srcfile = srcdir + '/' + file
            if (not args.args.onlynew) or (not os.path.exists(destfile)):
                print ('.' * indent, 'FILE:', file)
                try:
                    parseMoinToMarkdown.translate(srcfile, destfile)
                except NotImplementedError as e:
                    notImplementedPages.append([srcfile, e.args[0]])
                    if fileDestDirNew: # clean up
                        os.rmdir(fileDestDir)

        for dir in dirs:
            print ('.' * indent, 'DIR: ', dir)
            newdir = destdir + '/' + dir
            if not os.path.exists(newdir):
                os.mkdir(newdir)
            traverse(srcdir + '/' + dir, newdir, indent+1)
        return()
    
args = Argghhs()

# Walk source dir, translating pages as we find them.

traverse(args.args.srcdir, args.args.destdir, 0)

print("Number of Not Implemented pages: " + str(len(notImplementedPages)))
for probs in notImplementedPages:
    print("  Page: " + probs[0])
    print("            Err: " + probs[1] + "\n")


    
