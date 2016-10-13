# WikiMigration
Code to migrate from MoinMoin wiki.

Contains several scripts:

## grabWikiPages.py

Pull all the pages from the MoinMoin Wiki. Prints the URL of any copied page.

```
grabMoinWikiPages.py [-h] --basewikiurl BASEWIKIURL --sourceformat
                            SOURCEFORMAT --destdir DESTDIR [--onlynew]

optional arguments:
  -h, --help            show this help message and exit
  --basewikiurl BASEWIKIURL
                        The base URL of the Moin wiki to copy
  --sourceformat SOURCEFORMAT
                        'wiki' or 'html' wiki gets the page source in wiki
                        markup; html gets the full generated HTML for the
                        pages.
  --destdir DESTDIR     Path to directory to copy pages into
  --onlynew             Only get pages you don't already have a copy of

Example: grabMoinWikiPages.py --destdir="MoinPages" --onlynew
--basewikiurl="https://wiki.galaxyproject.org/"
```

## parseMoinToMarkdown.py

Convert a single wiki page (a file) from MoinMoin to Github Flavored Markdown.
Running this with no params does nothing. Running with --debug produces a LOT
of output. Markdown is sent to stdout.

```
parseMoinToMarkdown.py [-h] [--moinpage MOINPAGE] [--mdpage MDPAGE]
                              [--runtests] [--debug]

optional arguments:
  -h, --help           show this help message and exit
  --moinpage MOINPAGE  File containing a single MoinMoin page.
  --mdpage MDPAGE      Where to put the resulting markdown page.
  --runtests           Run Unit Tests.
  --debug              Include debug output

Example: parseMoinToMarkdown.py --moinpage=Admin.moin --mdpage=Admin.md --debug
```

## runMigration.py

Convert all pages in a directory structure from MoinMoin to Markdown.  Does not convert Creole or redirect pages.  
Runs ```parseMoinToMarkdown.py``` to convert each page.

```
runMigration.py [-h] --srcdir SRCDIR --destdir DESTDIR [--onlynew]

optional arguments:
  -h, --help         show this help message and exit
  --srcdir SRCDIR    Path of directory to get Moin pages from
  --destdir DESTDIR  Path of directory to put translated pages into
  --onlynew          Only translate pages you haven't already translated

Example: runMigration.py --srcdir="MoinPages" --destdir="MarkdownPages --onlynew
```
