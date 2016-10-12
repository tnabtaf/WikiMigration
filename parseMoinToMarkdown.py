#!/usr/local/bin/python3
# -*- coding: utf-8 -*-
#
# Translate a moinmoin page to Markdown.
# Markdown is Github Flavored Markdown with a large smattering of HTML throughout
#
# Anything not implemented in the translation generates 
# a PLACEHOLDER_thingnotimplemented text item
#
# Requires PyPeg2 to be installed.


import argparse
from pypeg2 import *                           # parser library.
import re
import os



# ################
# Basic Text
# ################

class TrailingWhitespace(List):
    grammar = contiguous(re.compile(r"[ \t\f\v]*\n", re.MULTILINE))

    def compose(self, parser, attr_of):
        return ("\n")


class Punctuation(List):
    """
    Characters that aren't included in plaintext or other tokens

    Matches a single character.
    Prevent matching with table cell ending.
    """
    grammar = contiguous(
        # attr("punctuation", re.compile(r"([^\w\s\|])|(\|(?=[^\|]|$))")))
        attr("punctuation", re.compile(r"([^\w\s\|\<])|(\|(?=[^\|]|$))|(\<(?=[^\<]|$))")))

    def compose(self, parser, attr_of):
        """
        Override compose method to generate Markdown.
        """
        return(self.punctuation)

    def composeHtml(self):
        """
        For now use same as Markdown.
        """
        return(compose(self))

        
    @classmethod
    def test(cls):
        """
        Test different instances of what this should and should not recognize
        """
        # What should work
        parse(".", cls)
        parse("/", cls)
        parse("?", cls)
        parse("|", cls)

        # What should not work
        testFail("||", cls)
        testFail(" OK[", cls)
        testFail(" ", cls)
        testFail("<<", cls)
        testFail("Uh-huh, this text does'nt mean anything. [[", cls)
        testFail("}}", cls)


class LeadingSpaces(List):
    """
    Sometimes the number of spaces at the front of a line matter.

    PyPeg, however, just pitches them, so we preprocess the code and encode
    the number of leading spaces.  This captures that encoding
    """
    grammar = contiguous(
        "@INDENT-",
        attr("depth", re.compile(r"\d+")),
        "@")

    
    def compose(self, parser, attr_of):
        """
        Moin treats leading space like an indent command.

        Markdown does not support indenting, unless it's code.
        What to do?  I don't know.  Can't insert an indent macro here, as
        there is no tag to look for to know when it's done.

        Most of the time, this won't be called, as the parent entities
        keep track of the indents.
        TODO
        """
        return(" " * int(self.depth))          # punt.

    @classmethod
    def trackIndent(cls, item, depthStack, baseDepth):
        """
        Update the depthStack for the current indented Element.

        item: subelement of elment.  Must have a depth attribute
        depthStack: stack of ever increasing depths in current element
        baseDepth: used with code blocks to insert leading spaces; 0 if not in
                   a code block

        Returns the new indentlevel.
        """
        itemDepth = int(item.depth.depth) + baseDepth
        if itemDepth > depthStack[-1]:
            depthStack.append(itemDepth)
        elif itemDepth < depthStack[-1]:
            depthStack.pop()
            while len(depthStack) > 0 and itemDepth < depthStack[-1]:
                depthStack.pop()
            if len(depthStack) == 0 or depthStack[-1] < itemDepth:
                depthStack.append(itemDepth)
        return(len(depthStack) - 1)       # current indent level


class InlineComment(List):
    """
    Moin inline comments either
      Start with /* and run to the end of the line
      Start with /* and end with */ on the same line

    Markdown does not support comments, but YAML does:
      Comments begin with the number sign ( # ), can start anywhere on a line,
      and continue until the end of the line

    TODO: Investigate putting inline comments in the YAML parts of the files.
    """
    grammar = contiguous(
        "/*",
        attr("comment", re.compile(r".*?(?=\*/|\n)")),
        ["*/", restline])   

    def compose(self, parser, attr_of):
        """
        GFM does not appear to support comments.

        Which is unfortuanate as most of these comments are there for a reason.
        See above TODO.
        """
        return("")

    def composeHtml(self):
        """
        For now use same as Markdown.
        """
        return(compose(self))


                
    @classmethod
    def test(cls):
        """
        Test different instances of what this should and should not recognize
        """
        # What should work
        parse("/*\n", cls)
        parse("/* This is a comment */", cls)

        # What should not work
        testFail("*/ Oops comment start backwards */", cls)

class Comment(List):
    """
    Moin comments start with ## in the first two columns.

    Given that PyPeg strips leading whitespace, I'm not sure how to tell when
    lines start with ##.
    """
    grammar = contiguous(
        "##",
        optional(re.compile(r" *"),
            optional(attr("comment", re.compile(r".+")))),
        TrailingWhitespace)
    

    def compose(self, parser, attr_of):
        """
        GFM does not appear to support comments.

        Most were generated by MoinMoin automatically, and arent that helpful
        anyway.
        """
        return("")

    def composeHtml(self):
        """
        For now use same as Markdown.
        """
        return(compose(self))


    @classmethod
    def test(cls):
        """
        Test different instances of what this should and should not recognize
        """
        # What should work
        parse("##\n", cls)
        parse("## \n", cls)
        parse("## I sing the body ...\n", cls)
        parse("## page was renamed from Admin/Disk Quotas\n", cls)

        # What should not work
        testFail("# Not a comment", cls)
        testFail("#format\n", cls)

        

# ============
# plain text
# ============

class PlainText(List):
    """
    Text with no special characters or punctuation in it.
    """
    grammar = contiguous(
        attr("text", re.compile(r"[\w \t\f\v]+")))

    
    def compose(self, parser, attr_of):
        """
        Override compose method to generate Markdown.
        """
        return(self.text)
        
    def composeHtml(self):
        """
        For now use same as Markdown.
        """
        return(compose(self))

    def justTheString(self):
        """
        Return just the string.  This is only needed because QuotedString has this method.
        """
        return(self.text)

        
    @classmethod
    def test(cls):
        """
        Test different instances of what this should and should not recognize
        """
        # What should work
        parse(" Testing with no special terminator", cls)
        parse(" OK DOKE ", cls)

        # What should not work
        testFail(" OK DOKE[[", cls)
        testFail(" OK DOKE]]", cls)
        testFail(" OK DOKE. <<", cls)
        testFail("Uh-huh, this text does'nt mean anything. [[", cls)
        testFail(" OK DOKE}}", cls)
        testFail(" OK DOKE\n NOT! ", cls)

class QuotedString(List):
    """
    String embedded in quotes, single or double.

    Match includes the string.  Does not do the right thing with bolds or
    italics, so they must be matched before this.

    Only called when we expect to have a quoted string (like in a Macro).
    Using this in the general case wreaks havoc because of apostrophes.
    """
    grammar = contiguous(
        attr("quotedText",
             re.compile(r"""(?P<quote>['"])(?P<quotedText>.+?)(?P=quote)""")))


    def compose(self, parser, attr_of):
        """
        Override compose method to generate Markdown.
        """
        return(self.quotedText)

    def justTheString(self):
        """
        Return just the string, without the quotes.
        """
        return(self.quotedText[1:-1])

        
    @classmethod
    def test(cls):
        """
        Test different instances of what this should and should not recognize
        """
        parse("'Jump'", cls)
        parse('''"I Can't do this no more!"''', cls)
        parse(r'"= LAPTOP WITH BROWSER ="', cls)

class SuperScriptText(List):
    """
    Superscript ^notation^

    Expectation is that this will not span across lines.

    Note, there are no subscripts in Galaxy wiki.
    """
    grammar = contiguous(
        attr("superText",
             re.compile(r"""\^(?P<supText>.+?)\^""")))


    def compose(self, parser, attr_of):
        """
        Markdown does not support superscript.
        """
        return("<sup>" + self.superText[1:-1] + "</sup>")      # trim the ^


    def composeHtml(self):
        return(compose(self))             # same.
        
    @classmethod
    def test(cls):
        """
        Test different instances of what this should and should not recognize
        """
        parse("^Jump^", cls)
        parse('''^I Can't do this no more!^''', cls)
        

class StrikeThroughText(List):
    """
    This was --(bad)--.

    Expectation is that this will not span across lines.
    """
    grammar = contiguous(
        attr("strikeThroughText",
             re.compile(r"""--\(.+?\)--""")))


    def compose(self, parser, attr_of):
        """
        Markdown supports it!
        """
        return("~~" + self.strikeThroughText[3:-3] + "~~")    # trim the --( )--


    def composeHtml(self):
        return("<s>" + self.strikeThroughText[3:-3] + "</s>") # trim the --( )--
        
    @classmethod
    def test(cls):
        """
        Test different instances of what this should and should not recognize
        """
        parse("--(Jump)--", cls)
        parse('''--( I Can't do this no more! )--''', cls)

                
class Underline(List):
    """
    __ 2 underscores start and end underlines in moinmoin
    """
    grammar = contiguous("__")
    inUnderline = False

    def compose(self, parser, attr_of):
        """
        Markdown does not support underline.  
        """
        return(self.composeHtml())

    def composeHtml(self):
        Underline.inUnderline = not Underline.inUnderline
        if Underline.inUnderline:
            return("<u>")                 # TODO: figure out what to do here.
        else:
            return("</u>")

        
    @classmethod
    def test(cls):
        """
        Test different instances of what this should and should not recognize
        """
        parse("__", cls)
        parse("__", cls)                  # Turn off inUnderline
        


class Bold(List):
    """
    3 single quotes start and end bold in moinmoin
    """
    grammar = contiguous("'''")
    inBold = False

    def compose(self, parser, attr_of):
        """
        Override compose method to generate Markdown.
        """
        return("**")

    def composeHtml(self):
        Bold.inBold = not Bold.inBold
        if Bold.inBold:
            return("<strong>")
        else:
            return("</strong>")

        
    @classmethod
    def test(cls):
        """
        Test different instances of what this should and should not recognize
        """
        parse("'''", cls)
        parse("'''", cls)


class Italic(List):
    """
    Two single quotes start and stop italics.

    This must be processed after Bold.
    """
    grammar = contiguous("''")
    inItalic = False

    def compose(self, parser, attr_of):
        """
        Override compose method to generate Markdown.
        """
        return("*")


    def composeHtml(self):
        Italic.inItalic = not Italic.inItalic
        if Italic.inItalic:
            return("<em>")
        else:
            return("</em>")


                
    @classmethod
    def test(cls):
        """
        Test different instances of what this should and should not recognize
        """
        parse("''", cls)
        parse("''", cls)



class FontSizeChangeStart(List):
    """
    ~+ increases the font size, ~- decreases it

    Note: When viewing this in Github, the font doesn't actually change size,
    even though the HTML is correct.
    """
    grammar = contiguous("~", attr("direction", re.compile("\+|\-")))

    def compose(self, parser, attr_of):
        if self.direction == "+":
            newSize = "larger"
        else:
            newSize = "smaller"
        return('<span style="font-size: ' + newSize + ';">')
        
    def composeHtml(self):
        return(compose(self))
        
    @classmethod
    def test(cls):
        """
        Test different instances of what this should and should not recognize
        """
        parse("~+", cls)
        parse("~-", cls)


class FontSizeChangeEnd(List):
    """
    +~ / -~ finishes a change in font size
    """
    grammar = contiguous(re.compile("\+|\-"), "~")

    def compose(self, parser, attr_of):
        return('</span>')
        
    def composeHtml(self):
        return(compose(self))
        
    @classmethod
    def test(cls):
        """
        Test different instances of what this should and should not recognize
        """
        parse("+~", cls)
        parse("-~", cls)

        
class Monospace(List):
    """
    Monospace is used to detect inline text that should be monospace.

    Can occur anywhwere that plain text can, and in Moin, markup inside monospace
    is rendered as plain text.
    """
    grammar = contiguous(
        re.compile(r"{{{|\`"),
        attr("monoText", re.compile(r".*?(?=}}}|\`)")),
        re.compile(r"}}}|\`"))
        
    def compose(self, parser, attr_of):
        return("`" + self.monoText + "`")


    def composeHtml(self):
        return("<code>" + self.monoText + "</code>")

                
    @classmethod
    def test(cls):
        """
        Test different instances of what this should and should not recognize
        """
        parse("{{{this is it!}}}", cls)
        parse("`this is it!`", cls)

        

class CodeBlockStart(List):
    """
    {{{ starts a code block.

    Can also specify language.
    {{{#!highlight ini
    {{{#!csv
    """
    inCodeBlock = False
    grammar = contiguous(
        "{{{",
        optional("#!",
                 optional("highlight", re.compile(r" +")),
                 attr("format", re.compile(r"[^\s]+"))))

    def compose(self, parser, attr_of):
        """
        Override compose method to generate Markdown.
        """
        CodeBlockStart.inCodeBlock = True
        out = "```"
        if hasattr(self, "format"):
            out += self.format
        return(out)


    def composeHtml(self):
        CodeBlockStart.inCodeBlock = True
        out = '<span class="codespan">'
        # IGNORING FORMAT; nothing we can do.
        return(out)
        
    @classmethod
    def test(cls):
        """
        Test different instances of what this should and should not recognize
        """
        parse("{{{", cls)
        parse("{{{#!csv", cls)
        parse("{{{#!highlight ini", cls)


class CodeBlockEnd(List):
    """
    }}} ends a code block.
    """
    grammar = contiguous("}}}")

    def compose(self, parser, attr_of):
        """
        Override compose method to generate Markdown.
        """
        CodeBlockStart.inCodeBlock = False
        return("```\n")
        
    def composeHtml(self):
        CodeBlockStart.inCodeBlock = False
        out = '<\span>'
        return(out)

        
    @classmethod
    def test(cls):
        """
        Test different instances of what this should and should not recognize
        """
        parse("}}}", cls)

        


# -------------
# PagePath - defined here instead of in Links b/c of dependencies
# -------------

class InternalPagePath(List):
    """
    path to an internal page.  Can be absolute or relative.

    Absolute paths don't have any prefix:

      Learn
      Learn/Screencasts

    Relative paths do.

      /ChildPage
      ../SiblingPage

    Internal pages can match on fewer characters than external pages
    in the page part of the path.  The anchor part can contain much more.
    Used when we know we have a page name.

    Allowable characters for general URLs are
      ALPHA / DIGIT / "-" / "." / "_" / "~" 
      ":" / "/" / "?" / "#" / "[" / "]" / "@"  - can't handle [] internally
      "!" / "$" / "&" / "'" / "(" / ")"        - can't handle () ...
      / "*" / "+" / "," / ";" / "="            - can't handle ,  ...
      spaces
      % 
    in any combination
    See http://stackoverflow.com/questions/1856785/characters-allowed-in-a-url
    """
    #grammar = contiguous(re.compile(r"[\w\-\.~:/?#@!\$&'\*+;= %]+"))
    grammar = contiguous(
        optional(attr("pagePart", re.compile(r"[\w\-\.~:/?@!\$&'\*+;= %]+"))),
        optional("#",
                 attr("anchorPart", re.compile(r".+?(?=]]|\||$)"))))

    def compose(self, parser, attr_of):
        out = ""
        # Handle PagePath first
        if hasattr(self, "pagePart"):
            # invert from Moin to GFM.
            if self.isSubPageLink():
                out += self.pagePart[1:]      # strip leading /
            elif self.isPageRelativeLink():
                out += self.pagePart          # keep leading ../
            elif self.isRootRelativeLink():
                out += "/" + self.pagePart
            # out += ".md"             # Required when viewing it inside GitHub

        # Now the anchors; GitHub and Moin handle anchor links differently
        # See https://gist.github.com/asabaylus/3071099
        if hasattr(self, "anchorPart"):
            anchor = self.anchorPart.lower()
            anchor = re.sub('[^\w \-]', '', anchor)   # keep only alphanumerics, spaces, hyphens
            anchor = re.sub(' ', '-', anchor)
            out += "#" + anchor
        return(out)
    

    def isSubPageLink(self):
        """
        Return true if this path is to a subpage.  Subpage links start with / 
        """
        if hasattr(self, "pagePart"):
            return(self.pagePart[0] == "/")
        return(False)
        
    def isPageRelativeLink(self):
        """
        Return true if this link uses a relative path to another wiki page.
        Relative links start with ../
        """
        if hasattr(self, "pagePart"):
            return(self.pagePart[0:3] == "../")
        return(False)
        
    def isRootRelativeLink(self):
        """
        Return true if this link uses a path that is relative to the wiki root.
        Root relative links start with a wiki page name
        """
        if hasattr(self, "pagePart") and not self.isSubPageLink() and not self.isPageRelativeLink():
            return(True)
        return(False)

    @classmethod
    def test(cls):
        """
        Test different instances of what this should and should not recognize
        """
        parse("FrontPage/Use Galaxy", cls)
        parse("FrontPage/Use Galaxy#This Part of the page", cls)
        parse("/Includes", cls)
        parse("../Includes/Something", cls)
        parse("#Internal to this page", cls)
        parse("Teach/Trainers#LUMC, ErasmusMC, DTL Learning Programme", cls)


class ExternalPagePath(str):
    """
    path to an external page.  

    Allowable characters are
      ALPHA / DIGIT / "-" / "." / "_" / "~" 
      ":" / "/" / "?" / "#" / "[" / "]" / "@"  - can't handle []
      "!" / "$" / "&" / "'" / "(" / ")"        
      / "*" / "+" / "," / ";" / "="
      spaces
      % 
    in any combination
    See http://stackoverflow.com/questions/1856785/characters-allowed-in-a-url
    """
    grammar = contiguous(re.compile(r"""[\w\-\.~:/?#@!\$&'\(\)\*+, ;= %"]+"""))

    
    @classmethod
    def test(cls):
        """
        Test different instances of what this should and should not recognize
        """
        parse("FrontPage/Use Galaxy", cls)
        parse("FrontPage/Use Galaxy#This Part of the page", cls)
        parse("/Includes", cls)
        parse("developers.google.com/+/features/sign-in", cls)



        
# ################
# MACROS
# ################

class NamedMacroParameter(List):
    grammar = contiguous(
        r",", maybe_some(whitespace), name(), maybe_some(whitespace), "=",
        maybe_some(whitespace), QuotedString)

    @classmethod
    def test(cls):
        """
        Test different instances of what this should and should not recognize
        """
        parse(", fish='jump'", cls)
        parse(', fish="jump high"', cls)
        parse(', from="= LAPTOP WITH BROWSER ="', cls)


class EmptyMacroParameter(List):
    grammar = contiguous(r",")

    @classmethod
    def test(cls):
        """
        Test different instances of what this should and should not recognize
        """
        parse(",", cls)
        parse(", ", cls)

               
class IncludeMacroParameter(List):
    """
    Include params after the page path can be
      empty
      from="some text"
      to="some text"
    and lots of other things we don't use.
    See https://moinmo.in/HelpOnMacros/Include
    """
    grammar = contiguous([NamedMacroParameter, EmptyMacroParameter, whitespace])

    @classmethod
    def test(cls):
        """
        Test different instances of what this should and should not recognize
        """
        NamedMacroParameter.test()
        EmptyMacroParameter.test()
        parse(", fish='jump'", cls)
        parse(", ", cls)


class IncludeMacro(List):
    """
    Include Macros can have one or more params.
      <<Include(FrontPage/Use Galaxy)>>
      <<Include(/Includes, , from="= LAPTOP WITH =\n", to="\nEND_INCLUDE")>>
    The opening and closing << >> will have been stripped before parsing.
    """
    grammar = contiguous(
        "Include(",
        maybe_some(whitespace),
        attr("pagePath", InternalPagePath),
        maybe_some(whitespace),
        attr("params", maybe_some(IncludeMacroParameter)),
        ")")

    def compose(self, parser, attr_of):
        """
        Override compose method to generate Markdown.
        """
        if self.params:
            return("PLACEHOLDER_INCLUDE(" + compose(self.pagePath) + compose(self.params) + ")")
        else:
            return("PLACEHOLDER_INCLUDE(" + compose(self.pagePath) + ")")

    @classmethod
    def test(cls):
        """
        Test different instances of what this should and should not recognize
        """
        InternalPagePath.test()
        IncludeMacroParameter.test()
        parse("Include(FrontPage/Use Galaxy)", cls)
        parse(r'Include(/Includes, , from="= LAPTOP =", to="END_INCLUDE")', cls)
        parse('Include(/Includes, , from="= LAPTOP =\\n", to="\\nEND_INCLUDE")', cls)



        
class DivMacro(List):
    """
    This handles Div macros that don't generate any YAML.  And div macros that do generate
    YAML will have been handled before calling this class.
      <<div(solid blue)>>
      <<div(center)>>
      <<div>> (closing)
    Need to figure out what to do in each situation?  Maybe take advantage of
    CSS that we control?
    """
    grammar = contiguous(
        "div(",
        attr("divClass", re.compile(r"[\w\- ]+")),
        ")")

    def compose(self, parser, attr_of):
        return("<div class='" + self.divClass + "'>")

    @classmethod
    def test(cls):
        """
        Test different instances of what this should and should not recognize
        """
        parse("div(center)", cls)
        testFail("div", cls)
        parse("div(indent)", cls)
        parse("div(table-of-contents)", cls)



class DivEndMacro(List):
    """
    Div macros end with just <<div>>
    """
    grammar = "div"

    def compose(self, parser, attr_of):
        return("</div>")


    @classmethod
    def test(cls):
        parse("div", cls)


class SpanMacro(List):
    """
    This handles span macros
      <<span(blue)>>
    """
    grammar = contiguous(
        "span(",
        attr("spanClass", re.compile(r"[\w ]+")),
        ")")

    def compose(self, parser, attr_of):
        return("<div class='" + self.spanClass + "'>")

    @classmethod
    def test(cls):
        """
        Test different instances of what this should and should not recognize
        """
        parse("span(blue)", cls)
        testFail("span", cls)



class SpanEndMacro(List):
    """
    Span macros end with just <<span>>
    """
    grammar = "span"

    def compose(self, parser, attr_of):
        return("</span>")


    @classmethod
    def test(cls):
        parse("span", cls)


        
        
class TOCMacro(List):
    """
    TableOfContents Macros insert TOC's.  There ya go.
      <<TableOfContents>>
      <<TableOfContents([maxdepth])>>
      <<TableOfContents(2)>>
    """
    grammar = contiguous(
        "TableOfContents",
        optional(
            "(", optional(attr("maxDepth", re.compile(r"\d+"))), ")"))

    def compose(self, parser, attr_of):
        """
        Override compose method to generate Markdown.
        """
        global pageYaml

        # No markdown to generate. It all goes in YAML.
        # MaxDepth not supported in YAML.
        
        pageYaml["autotoc"] = "true"
        
        return("")


    @classmethod
    def test(cls):
        """
        Test different instances of what this should and should not recognize
        """
        parse("TableOfContents", cls)
        parse("TableOfContents(2)", cls)



class BRMacro(List):
    """
    BR macros insert a new line.
      <<BR>>

    That's it.
    """
    grammar = contiguous("BR")

    def compose(self, parser, attr_of):
        """
        Override compose method to generate Markdown.
        """
        return("<br />")

    @classmethod
    def test(cls):
        """
        Test different instances of what this should and should not recognize
        """
        parse("BR", cls)


class MailToMacro(List):
    """
    MailTo Macros look like
      <<MailTo(bioinformatics.core@ucdavis.edu, UC Davis Bioinformatics)>>
      <<MailTo(bioinformatics.core@ucdavis.edu)>>
      <<MailTo(bioinformatics.core AT ucdavis DOT edu, UC Davis Bioinformatics)>>
      <<MailTo(bioinformatics.core AT ucdavis DOT edu)>>
    """
    grammar = contiguous(
        "MailTo(",
        maybe_some(" "),
        attr("emailAddress", re.compile(r"[^\,\)]+")),
        optional(
            ",",
            maybe_some(" "),
            attr("toText", re.compile(r"[^\)]+")),
            maybe_some(" ")
            ),
        ")" )
            

    def compose(self, parser, attr_of):
        """
        Can be generated as a link in Markdown
        """
        out = "[" + self.emailAddress + "]"
        if hasattr(self, "toText"):
            out += "(" + self.toText + ")"
        else:
            out += "(" + self.emailAddress + ")"
        return(out)

    def composeHtml(self):
        out = '<a href="mailto:' + self.emailAddress + '">'
        if hasattr(self, "toText"):
            out += self.toText
        else:
            out += self.emailAddress
        out += "</a>"
        return(out)

        
    @classmethod
    def test(cls):
        """
        Test different instances of what this should and should not recognize
        """
        parse("MailTo(q)", cls)
        parse("MailTo(bioinformatics.core@ucdavis.edu)", cls)
        parse("MailTo(bioinformatics.core@ucdavis.edu, UC Davis Bioinformatics)", cls)
        parse("MailTo(bioinformatics.core AT ucdavis.edu, UC Davis Bioinformatics)", cls)
        parse('MailTo( w4mcourse2015.organisation@sb-roscoff.fr, W4M Course Organisers)', cls)
        parse("MailTo(mimodd@googlegroups.com, MiModD Google Group)", cls)
        
class FullSearchCachedMacro(List):
    """
    Macro that generates a list of pages 
      <<FullSearchCached(stringtosearchfor)>>
    """
    grammar = contiguous(
        "FullSearchCached(",
        attr("searchString", re.compile(r".+(?=\))")),
        ")")

    def compose(self, parser, attr_of):
        """
        Override compose method to generate Markdown.
        """
        return("PLACEHOLDER_FULL_SEARCH_CACHE(" + self.searchString + ")")


    @classmethod
    def test(cls):
        """
        Test different instances of what this should and should not recognize
        """
        parse("FullSearchCached(stringtosearchfor)", cls)

        

class NewPageMacro(List):
    """
    Macro that generates a list of pages 
      <<NewPage()>>
      <<NewPage(NewsTemplate, "Create a News Item page", News)>>
    """
    grammar = contiguous(
        "NewPage(",
        optional(
            attr("theRest", re.compile(r".+(?=\))"))),
        ")")
                         

    def compose(self, parser, attr_of):
        """
        Override compose method to generate Markdown.
        """
        out = "PLACEHOLDER_NEW_PAGE("
        if hasattr(self, "theRest"):
            out += self.theRest
        out += ")"
        return(out)
        
                
    @classmethod
    def test(cls):
        """
        Test different instances of what this should and should not recognize
        """
        parse("NewPage()", cls)
        parse('NewPage(NewsTemplate, "Create a News Item page", News)', cls)



class RSSReaderMacro(List):
    """
    Macro that generates a list of pages 
      <<RSSReader("http://feed43.com/galaxynotesheadlines.xml", includeStyle=False)>>
    """
    grammar = contiguous(
        "RSSReader(",
        attr("theRest", re.compile(r".+(?=\))")),
        ")")
                         

    def compose(self, parser, attr_of):
        """
        Override compose method to generate Markdown.
        """
        out = "PLACEHOLDER_RSSREADER("
        if hasattr(self, "theRest"):
            out += self.theRest
        out += ")"
        return(out)
        
                
    @classmethod
    def test(cls):
        """
        Test different instances of what this should and should not recognize
        """
        parse('RSSReader("http://feed43.com/galaxynotesheadlines.xml", includeStyle=False)', cls)

        

        
class ActionMacro(List):
    """
    Action Macros look like
      <<Action(AttachFile, Attach a file to this page.)>>
    """
    grammar = contiguous(
        "Action(",
        maybe_some(whitespace),
        attr("actionType", re.compile(r".+(?=,)")),
        maybe_some(whitespace),
        ",",
        maybe_some(whitespace),
        attr("actionText", re.compile(r".+(?=\))")),
        ")")
            

    def compose(self, parser, attr_of):
        """
        Can be generated as a link in Markdown
        """
        out = "PLACEHOLDER_ACTION(" + self.actionType + "," + self.actionText + ")"
        return(out)

        
    @classmethod
    def test(cls):
        """
        Test different instances of what this should and should not recognize
        """
        parse("Action(AttachFile, Attach a file to this page.)", cls)


class AttachListMacro(List):
    """
    Macro that generates a list of pages 
      <<AttachList>>
    """
    grammar = contiguous("AttachList")

    def compose(self, parser, attr_of):
        """
        Override compose method to generate Markdown.
        """
        return("PLACEHOLDER_ATTACH_LIST")

    @classmethod
    def test(cls):
        """
        Test different instances of what this should and should not recognize
        """
        parse("AttachList", cls)

class ShowTweetsMacro(List):
    """
    ShowTweets Macros look like
      <<ShowTweets(user="galaxyproject", maxTweets=20)>>
      
    """
    grammar = contiguous(
        "ShowTweets(",
        maybe_some(whitespace),
        attr("username", re.compile(r".+(?=,)")),
        maybe_some(whitespace),
        ",",
        maybe_some(whitespace),
        attr("maxTweets", re.compile(r".+(?=\))")),
        ")")
            

    def compose(self, parser, attr_of):
        """
        Can be generated as a link in Markdown
        """
        out = "PLACEHOLDER_SHOW_TWEETS(" + self.username + "," + self.maxTweets + ")"
        return(out)

        
    @classmethod
    def test(cls):
        """
        Test different instances of what this should and should not recognize
        """
        parse('ShowTweets(user="galaxyproject", maxTweets=20)', cls)


class DictColumnsMacro(List):
    """
    DictColumns Macros look like
      <<DictColumns(pagename=VA, names="Appliance, Technology, Domains, Description, Owners, Date Created/Updated", sort="Date Created/Updated", title="Hide", hide="Hide")>>
      
    """
    grammar = contiguous(
        "DictColumns(",
        attr("theRest", re.compile(r".+(?=\))")),
        ")")
                         

    def compose(self, parser, attr_of):
        """
        Override compose method to generate Markdown.
        """
        out = "PLACEHOLDER_DICT_COLUMNS("
        if hasattr(self, "theRest"):
            out += self.theRest
        out += ")"
        return(out)
        
    @classmethod
    def test(cls):
        """
        Test different instances of what this should and should not recognize
        """
        parse('DictColumns(pagename=VA, names="Appliance, Technology, Domains, Description, Owners, Date Created/Updated", sort="Date Created/Updated", title="Hide", hide="Hide")', cls)


class DateTimeMacro(List):
    """
    DateTime Macros look like
      <<DateTime(2011-08-30T22:27:39Z)>>
      
    """
    grammar = contiguous(
        "DateTime(",
        attr("theRest", re.compile(r".+(?=\))")),
        ")")
                         

    def compose(self, parser, attr_of):
        """
        Override compose method to generate Markdown.
        """
        out = "PLACEHOLDER_DATE_TIME("
        if hasattr(self, "theRest"):
            out += self.theRest
        out += ")"
        return(out)
        
    @classmethod
    def test(cls):
        """
        Test different instances of what this should and should not recognize
        """
        parse('DateTime(2011-08-30T22:27:39Z)")', cls)



class DateMacro(List):
    """
    Date Macros look like
      <<Date(2012-01-27T01:02:28Z)>>
      
    """
    grammar = contiguous(
        "Date(",
        attr("theRest", re.compile(r".+(?=\))")),
        ")")
                         

    def compose(self, parser, attr_of):
        """
        Override compose method to generate Markdown.
        """
        out = "PLACEHOLDER_DATE("
        if hasattr(self, "theRest"):
            out += self.theRest
        out += ")"
        return(out)
        
    @classmethod
    def test(cls):
        """
        Test different instances of what this should and should not recognize
        """
        parse('Date(2012-01-27T01:02:28Z)', cls)
                

class AnchorMacro(List):
    """
    ShowTweets Macros look like
      <<Achor(anchor text)>>
      
    """
    grammar = contiguous(
        "Anchor(",
        maybe_some(whitespace),
        attr("anchorTarget", re.compile(r".+(?=\))")),
        ")")
            

    def compose(self, parser, attr_of):
        """
        Can be generated as a link in Markdown
        """
        out = "PLACEHOLDER_ANCHOR(" + self.anchorTarget + ")"
        return(out)

        
    @classmethod
    def test(cls):
        """
        Test different instances of what this should and should not recognize
        """
        parse('Anchor(Stampede)', cls)
        
        
class Macro(List):
    """
    MoinMoin can have macros link include, or div or TableOfContents.  Sometimes they
    have parameters.
      <<Include(FrontPage/Use Galaxy)>>
      <<div(center)>>
      <<TableOfContents>>
      <<div>>
      <<Include(/Includes, , from="= LAPTOP WITH =\n", to="\nEND_INCLUDE")>>
      TODO
    """
    grammar = contiguous(
        "<<",
        attr("macro",
            [TOCMacro, IncludeMacro, DivMacro, DivEndMacro,
             SpanMacro, SpanEndMacro, BRMacro, MailToMacro, DictColumnsMacro,
             FullSearchCachedMacro, NewPageMacro, ActionMacro, AttachListMacro,
             ShowTweetsMacro, AnchorMacro, RSSReaderMacro, DateTimeMacro, DateMacro]),
        ">>")


    def compose(self, parser, attr_of):
        return(compose(self.macro))
    
    def composeHtml(self):
        """
        For cases when the subelement needs to be rendered in HTML (such as
        inside a table).
        """
        # for most macros, default to same markup as used in Markdown.
        if isinstance(self.macro, MailToMacro):
            return(self.macro.composeHtml())
        else:
            return(compose(self.macro))

    @classmethod
    def test(cls):
        MailToMacro.test()
        DivMacro.test()
        DivEndMacro.test()
        SpanMacro.test()
        SpanEndMacro.test()
        IncludeMacro.test()
        TOCMacro.test()
        BRMacro.test()
        DictColumnsMacro.test()
        FullSearchCachedMacro.test()
        NewPageMacro.test()
        ActionMacro.test()
        AttachListMacro.test()
        ShowTweetsMacro.test()
        AnchorMacro.test()
        RSSReaderMacro.test()
        DateTimeMacro.test()
        DateMacro.test()
        parse("<<div>>", cls)
        parse("<<div(center)>>", cls)
        parse("<<div(indent)>>", cls)
        parse("<<Include(FrontPage/Use Galaxy)>>", cls)
        parse("<<Include(Develop/LinkBox)>>", cls)
        parse(r'<<Include(/Includes, , from="= LA T =\n", to="\nEN_CL")>>', cls)
        


    
# ===============
# Section Header
# ===============

class SectionHeader(List):
    """
    Section headers start and end with = signs.  The more signs the smaller the header
      = Top level Header =
      == 2nd level Header ==

    That must be the only thing on the line.  Moin does not like leading or
    trailing spaces.
    """        
    grammar = contiguous(
        attr("depth", re.compile(r"^=+")),
        re.compile(" +"),
        attr("name", re.compile(r".+(?= +=+)")),
        re.compile(r" +=+\n"))

    def compose(self, parser, attr_of):
        """
        Override compose method to generate Markdown.

        How can that be dangerous?
        """
        return("#" * len(self.depth) + " " + self.name + "\n")        

        

    @classmethod
    def test(cls):
        """
        Test different instances of what this should and should not recognize
        """
        return()
        parse("= A single tool or a suite of tools per repository =\n ", cls)
        parse("= Heading 1 =\n", cls)
        parse("== Heading Too! ==\n", cls)


        
# =============
# Links
# =============


class LinkProtocol(List):
    """
    http, ftp etc.
    """
    grammar = contiguous(
        attr("protocol", re.compile(r"((http)|(https)|(ftp)|(rtsp))\://",
                                    re.IGNORECASE)))

    def compose(self, parser, attr_of):
        """
        Override compose method to generate Markdown.
        """
        return(self.protocol)
    
    @classmethod
    def test(cls):
        """
        Test different instances of what this should and should not recognize
        """
        parse("http://", cls)
        parse("ftp://", cls)
        parse("https://", cls)

    
class ExternalLink(List):
    """
    Links that go outside the wiki.
    """
    grammar = contiguous(
        "[[",
        maybe_some(whitespace),
        attr("protocol", LinkProtocol),
        attr("path", ExternalPagePath),
        maybe_some(whitespace),
        optional("|", maybe_some(whitespace),
                 attr("linkText", re.compile(r".+?(?=\]\])"))),
        "]]")

    def compose(self, parser, attr_of):
        """
        Override compose method to generate Markdown.
        """
        linkOut = compose(self.protocol) + compose(self.path)
        # Try with link text first
        try:
            out = "[" + self.linkText + "](" + linkOut + ")"
        except AttributeError:
            # err on the safe side
            out = "[" + linkOut + "](" + linkOut + ")" 
        return(out)


    def composeHtml(self):
        linkOut = compose(self.protocol) + compose(self.path)
        # Try with link text first
        try:
            out = "<a href='" + linkOut + "'>" + self.linkText + "</a>"
        except AttributeError:
            # err on the safe side
            out = "<a href='" + linkOut + "'>" + linkOut + "</a>"
        return(out)


        
    @classmethod
    def test(cls):
        """
        Test different instances of what this should and should not recognize
        """
        LinkProtocol.test()
        parse("[[http://link.com]]", cls)
        parse("[[ftp://this.here.com/path/file.txt]]", cls)
        parse("[[https://link.com/]]", cls)
        parse("[[http://link.com|Linkin somewhere]]", cls)
        parse("[[ftp://this.here.com/path/file.txt|Text for link.]]", cls)
        parse("[[https://link.com/| Whitespace test ]]", cls)


class InternalLink(List):
    """
    Links that go inside the wiki.

    GFM inverts the syntax of relative and root-derived links, compared to
    MoinMoin.
    In Moin relative links start with "/"
    In GFM relative linking is assumed, and starting a link with "/" may be
    undefined.

    So, this calls for some knowledge of the path to the current page in
    the MoinMoin directory, and the home of th enew page in the Markdown
    directory, to correctly translate.
    TODO
    """
    grammar = contiguous(
        "[[",
        maybe_some(whitespace),
        attr("path", InternalPagePath),
        optional("|", attr("linkText", re.compile(r".+?(?=\]\])"))),
        "]]")

    def compose(self, parser, attr_of):
        """
        Override compose method to generate Markdown.
        """
        # Try with link text first
        try:
            out = "[" + self.linkText + "](" + compose(self.path) + ")"
        except AttributeError:
            # err on the safe side
            out = "[" + compose(self.path) + "](" + compose(self.path) + ")" 
        return(out)


    def composeHtml(self):
        # Try with link text first
        try:
            out = "<a href='" + compose(self.path) + "'>" + self.linkText + "</a>"
        except AttributeError:
            # err on the safe side
            out = ("<a href='" + compose(self.path) + "'>" +
                   compose(self.path) + "</a>")
        return(out)

        
    @classmethod
    def test(cls):
        """
        Test different instances of what this should and should not recognize
        """
        InternalPagePath.test()
        parse("[[/PathToPage]]", cls)
        parse("[[path/file.txt]]", cls)
        parse("[[path/more/path/Page Name]]", cls)
        parse("[[/PathToPage|With Text]]", cls)
        parse("[[path/file.txt|uh-huh!]]", cls)
        parse("[[path/more/path/Page Name|Whitespace test 1]]", cls)
        parse("[[path/more/path/Page Name| Whitespace test 2 ]]", cls)
        parse("[[FrontPage/Use Galaxy|Use Galaxy]]", cls)


class InterWikiMapEntry:
    """
    Defines an InterWiki link.
    """
    def __init__(self, name, url, count):
        self.name = name
        self.url = url
        self.count = count                # just want to keep track of this somewhere

        return(None)

interWikiMap = {
    'devthread':
        InterWikiMapEntry('devthread',
                          'http://dev.list.galaxyproject.org/', 13),
    'userthread':
        InterWikiMapEntry('userthread',
                          'http://user.list.galaxyproject.org/', 3),
    'announcethread':
        InterWikiMapEntry('announcethread',
                          'http://announce.list.galaxyproject.org/', 0),
    'francethread':
        InterWikiMapEntry('francethread',
                          'http://france.list.galaxyproject.org/', 0),
    'trello':
        InterWikiMapEntry('trello',
                          'https://trello.com/b/75c1kASa/galaxy-development', 0),
    'toolshedview':
        InterWikiMapEntry('toolshedview',
                          'http://toolshed.g2.bx.psu.edu/view/', 0),
    'src':
        InterWikiMapEntry('src',
                          'https://github.com/galaxyproject/galaxy/tree/master/', 57),
    'srcdoccentral':
        InterWikiMapEntry('srcdoccentral',
                          'https://galaxy-central.readthedocs.org/en/latest/', 0),
    'srcdocdist':
        InterWikiMapEntry('srcdocdist',
                          'https://galaxy-dist.readthedocs.org/en/latest/', 0),
    'gmod':
        InterWikiMapEntry('gmod',
                          'http://gmod.org/wiki/', 106),
    'pmid':
        InterWikiMapEntry('pmid',
                          'http://www.ncbi.nlm.nih.gov/pubmed/', 10),
    'main':
        InterWikiMapEntry('main',
                          'https://usegalaxy.org/', 1),
    'data_libraries':
        InterWikiMapEntry('data_libraries',
                          'https://usegalaxy.org/library/', 0),
    'published_histories':
        InterWikiMapEntry('published_histories',
                          'https://usegalaxy.org/history/list_published', 0),
    'published_workflows':
        InterWikiMapEntry('published_workflows',
                          'https://usegalaxy.org/workflow/list_published', 1),
    'published_visualizations':
        InterWikiMapEntry('published_visualizations',
                          'https://usegalaxy.org/visualization/list_published', 0),
    'published_pages':
        InterWikiMapEntry('published_pages',
                          'https://usegalaxy.org/page/list_published', 0),
    'bbissue':
        InterWikiMapEntry('bbissue',
                          'https://bitbucket.org/galaxy/galaxy-central/issue/', 15),
    'screencast':
        InterWikiMapEntry('screencast',
                          'http://screencast.g2.bx.psu.edu/', 88), # TODO
    'devlistthread':
        InterWikiMapEntry('devlistthread',
                          'http://dev.list.galaxyproject.org/', 4),
    'moinmoin':                           # comes with moin
        InterWikiMapEntry('moinmoin',
                          'http://moinmo.in/', 6),
    'wikipedia':                           # comes with moin
        InterWikiMapEntry('wikipedia',
                          'https://en.wikipedia.org/wiki/', 1)
    }
        
class InterWikiLink(List):
    """
    Links that go to a predefined external site.

    Format is:

      [[gmod:GBrowse|GBrowse]]

    Not sure if preserving these as a special kind of link would be worth it,
    as most of them are not widely used (and many of the current links are out of date.
    """
    grammar = contiguous(
        "[[",
        maybe_some(whitespace),
        attr("interWikiName", re.compile(r"[\w]+")),
        maybe_some(whitespace),
        ':',
        maybe_some(whitespace),
        optional(attr("wikiPage", re.compile(r".+?(?=(\]\])|\|)"))),
        optional("|", attr("linkText", re.compile(r".+?(?=\]\])"))),
        "]]")


    def createMailToMacro(self):
        self.m2m = MailToMacro()
        self.m2m.emailAddress = self.wikiPage
        if hasattr(self, "linkText"):
            self.m2m.toText = self.linkText
        
    
    def compose(self, parser, attr_of):
        global interWikiMap

        if self.interWikiName.lower() == "mailto":
            # build a MailToMacro object
            self.createMailToMacro()
            out = self.m2m.compose(parser, attr_of)
        else:
            if self.interWikiName.lower() == "attachment":
                # TODO. Not an interwiki link at all!
                url = "ATTACHMENT_URL"
            else:
                url = interWikiMap[self.interWikiName.lower()].url
            if hasattr(self, 'wikiPage'):
                url += self.wikiPage
            if hasattr(self, 'linkText'):
                out =  "[" + self.linkText + "](" + url + ")"
            else:
                out =  "[" + url + "](" + url + ")"
        return(out)


    def composeHtml(self):
        global interWikiMap
        
        if self.interWikiName.lower() == "mailto":
            # build a MailToMacro object
            self.createMailToMacro()
            out = self.m2m.composeHtml()
        else:
            if self.interWikiName.lower() == "attachment":
                # TODO. Not an interwiki link at all!
                url = "PLACEHOLDER_ATTACHMENT_URL"
            else:
                url = interWikiMap[self.interWikiName.lower()].url
            if hasattr(self, 'wikiPage'):
                url += self.wikiPage

            if hasattr(self, 'linkText'):
                out =  "<a href='" + url + "'>" + self.linkText + "</a>"
            else:
                out =  "<a href='" + url + "'>" + url + "</a>"
        return(out)

        
    @classmethod
    def test(cls):
        """
        Test different instances of what this should and should not recognize
        """
        InternalPagePath.test()
        parse("[[gmod:GBrowse]]", cls)
        parse("[[GMOD:Gbrowse/Fish]]", cls)
        parse("[[bbissue:321|this bb issue]]", cls)

        
class InternalImage(List):
    """
    Internal images are shown with

      {{attachment:Images/Search.png|Search|width="120"}}
      {{attachment:Images/Search.png||width="120"}}
      {{attachment:Images/Search.png|Search|}}
      {{attachment:Images/Search.png|Search}}
      {{attachment:Images/Search.png}}

    Many images include sizing, and that is not supported in Markdown.
    """
    grammar = contiguous(
        "{{attachment:",
        attr("imagePath", InternalPagePath),
        optional(
            "|",
            optional(attr("altText", re.compile(r"[^}|]*"))),
            optional(
                "|",
                attr("imageSize", re.compile(r"[^\}]*")))),
        "}}")

    def compose(self, parser, attr_of):
        """
        Use Markdown image notation
        """
        out = "!["
        if hasattr(self, "altText"):
            out += self.altText
        out += "](" + compose(self.imagePath) + ")"
                    
        return(out)

        
    def composeHtml(self):
        # Generate HTML img link as it can deal with sizes
        out = "<img src='" + compose(self.imagePath) + "'"
        
        # Add alt text
        if hasattr(self, "altText"):
            out += " alt='" + self.altText + "'"

        if hasattr(self, "imageSize"):
            out += " " + self.imageSize
        out += " />"
                    
        return(out)


    def needsHtmlRendering(self):
        """
        Returns true if image needs HTML rendering.
        """
        if hasattr(self, "imageSize"):
            return(True)
        return(False)


    @classmethod
    def test(cls):
        """
        Test different instances of what this should and should not recognize
        """
        parse('{{attachment:Images/GalaxyLogos/GTN16.png|Training offered by GTN Member}}', cls)
        parse('{{attachment:GetGalaxySearch.png}}', cls)
        parse('{{attachment:Im/L/GGS.png|S all}}', cls)
        parse('{{attachment:Is/L/G.png|s a|width="120"}}', cls)
        parse('{{attachment:Images/Logos/w4m_logo_small.png|Traitement des données métabolomiques sous Galaxy|height="80"}}', cls)
        parse('{{attachment:Images/Logos/WACD.png|Western Association of Core Directors (WACD) Annual Meeting|height="70"}}', cls)


class ExternalImage(List):
    """
    External images are shown with

    or
      {{http://i.imgur.com/aBEEnuL.png?1||width=400}}
      {{http://i.imgur.com/aBEEnuL.png?1|Pretty pic caption|width=400}}

    Many images include sizing, and that is not supported in Markdown.
    """
    grammar = contiguous(
        "{{",
        attr("protocol", LinkProtocol),
        attr("path", ExternalPagePath),
        optional(
            "|",
            optional(attr("altText", re.compile(r"[^}|]*"))),
            optional(
                "|",
                attr("imageSize", re.compile(r"[^\}]*")))),
        "}}")

    def compose(self, parser, attr_of):
        """
        Use Markdown image notation
        """
        out = "!["
        if hasattr(self, "altText"):
            out += self.altText
        out += "](" + compose(self.protocol) + compose(self.path) + ")"
                    
        return(out)

        
    def composeHtml(self):
        # Generate HTML img link as it can deal with sizes
        out = "<img src='" + compose(self.protocol) + compose(self.path) + "'"
        
        # Add alt text
        if hasattr(self, "altText"):
            out += " alt='" + self.altText + "'"

        if hasattr(self, "imageSize"):
            out += " " + self.imageSize
        out += " />"
                    
        return(out)


    def needsHtmlRendering(self):
        """
        Returns true if image needs HTML rendering.
        """
        if hasattr(self, "imageSize"):
            return(True)
        return(False)


    @classmethod
    def test(cls):
        """
        Test different instances of what this should and should not recognize
        """
        parse('{{http://i.imgur.com/aBEEnuL.png?1||width=400}}', cls)
        parse('{{http://i.imgur.com/aBEEnuL.png?1|Pretty pic caption|width=400}}', cls)


class Image(List):
    """
    Images are shown with

      {{attachment:Images/Search.png|Search|width="120"}}
      {{attachment:Images/Search.png||width="120"}}
      {{attachment:Images/Search.png|Search|}}
      {{attachment:Images/Search.png|Search}}
      {{attachment:Images/Search.png}}

    or
      {{http://i.imgur.com/aBEEnuL.png?1||width=400}}

    Many images include sizing, and that is not supported in Markdown.
    """
    grammar = contiguous(
        attr("image", [InternalImage, ExternalImage]))

    def compose(self, parser, attr_of):
        out = compose(self.image)
        return(out)

        
    def composeHtml(self):
        # Generate HTML img link as it can deal with sizes
        out = self.image.composeHtml()                    
        return(out)


    def needsHtmlRendering(self):
        """
        Returns true if image needs HTML rendering.
        """
        return self.image.needsHtmlRendering()


    @classmethod
    def test(cls):
        """
        Test different instances of what this should and should not recognize
        """
        ExternalImage.test()
        InternalImage.test()
        parse('{{attachment:Images/GalaxyLogos/GTN16.png|Training offered by GTN Member}}', cls)
        parse('{{attachment:GetGalaxySearch.png}}', cls)
        parse('{{attachment:Im/L/GGS.png|S all}}', cls)
        parse('{{attachment:Is/L/G.png|s a|width="120"}}', cls)
        parse('{{attachment:Images/Logos/w4m_logo_small.png|Traitement des données métabolomiques sous Galaxy|height="80"}}', cls)
        parse('{{attachment:Images/Logos/WACD.png|Western Association of Core Directors (WACD) Annual Meeting|height="70"}}', cls)

        

class ImageLink(List):
    """
    Link that shows an image, rather than text.

    In MoinMoin these look like:
      [[http://address.com|{{attachment:Images/Search.png|Search|width="120"}}]]

    So, it's the 2nd part of the link that tells us this is an image.
      
    See http://stackoverflow.com/questions/30242558/how-do-you-create-a-relative-image-link-w-github-flavored-markdown
    for this Markdown solution:
      [[[/images/gravatar.jpeg]]](http://www.inf.ufrgs.br) 

    Many image links include sizing, and that is not supported in Markdown.
    May just be better to go straight to HTML?
    """
    grammar = contiguous(
        "[[",
        [(attr("protocol", LinkProtocol), attr("linkPath", ExternalPagePath)),
         attr("linkPath", InternalPagePath)],
        "|",
        attr("image", Image),
        "]]")

    def compose(self, parser, attr_of):
        """
        Override compose method to generate Markdown.
        """
        # Generate HTML img link as it can deal with alt txt and sizes
        out = "<a href='"
        try:
            out += compose(self.protocol)
        except AttributeError:
            pass
        
        out += compose(self.linkPath) + "'>"
        out += self.image.composeHtml()
        # TODO: figure out when imageLinks can be in GFM.
        out += "</a>"
                    
        return(out)
            
        
        
    def composeHtml(self):
        """
        Same markup is generated for Markdown and HTML cases.
        """
        return(compose(self))



    @classmethod
    def test(cls):
        """
        Test different instances of what this should and should not recognize
        """
        Image.test()
        parse('[[search/getgalaxy|{{attachment:GetGalaxySearch.png}}]]', cls)
        parse('[[http://gp.org/sch/getxy|{{attachment:Im/L/GGS.png|S all}}]]',
              cls)
        parse('[[http://gt.g/gy|{{attachment:Is/L/G.png|s a|width="120"}}]]',
              cls)
        parse('[[http://workflow4metabolomics.org/training/W4Mcourse2015|{{attachment:Images/Logos/w4m_logo_small.png|Traitement des données métabolomiques sous Galaxy|height="80"}}]]', cls)
        parse('[[http://wacd.abrf.org/|{{attachment:Images/Logos/WACD.png|Western Association of Core Directors (WACD) Annual Meeting|height="70"}}]]', cls)

        
       

class Link(List):
    """
    Links in Moin are enclosed in [[ ]].  Some have text, some have embedded
    images, and some have extra params.
    """
    grammar = contiguous(
        attr("link", [ImageLink, ExternalLink, InterWikiLink, InternalLink]))

        
    def compose(self, parser, attr_of):
        """
        Override compose method to generate Markdown.
        """
        return(compose(self.link))


    def composeHtml(self):
        """
        For cases when the subelement needs to be rendered in HTML (such as
        inside a table).
        """
        return(self.link.composeHtml())

        
    @classmethod
    def test(cls):
        """
        Test different instances of what this should and should not recognize
        """
        ExternalLink.test()
        InterWikiLink.test()
        InternalLink.test()
        ImageLink.test()
        parse("[[https://developers.google.com/open-source/soc|Google Summer of Code 2015]]", cls)
        parse(" [[http://link.com|Link to here]]", cls)
        parse("[[LinkToPage]]", cls)
        parse("[[LinktoPage|Text shown for link]]", cls)
        parse("[[https://developers.google.com/+/features/sign-in|Google+ sign-in]]", cls)
        parse("[[http://www.citeulike.org/group/16008/order/to_read,desc,|Galaxy papers on CituLike]]", cls)
        parse("[[http://bioblend.readthedocs.org/en/latest/|bioblend]]", cls)


# =============
# Subelements
# =============

class Subelement(List):
    """
    Subelements can occur in paragraphs or table text.

    Subelements can also be elements.
    """
    grammar = contiguous(
        [LeadingSpaces, Macro, Link, Image, SuperScriptText, StrikeThroughText,
         Underline, Bold, Italic, Monospace,
         CodeBlockStart, CodeBlockEnd,
         FontSizeChangeStart, FontSizeChangeEnd,
         InlineComment, PlainText, Punctuation])

    
    def compose(self, parser, attr_of):
        """
        Override compose method to generate Markdown.
        """
        out = ""
        for item in self:
            out += compose(item)
        return(out)


    def composeHtml(self):
        """
        For cases when the subelement needs to be rendered in HTML (such as
        inside a table).
        """
        out = ""
        for item in self:
            out += item.composeHtml()
        return(out)
        

    @classmethod
    def test(cls):
        """
        Test different instances of what this should and should not recognize
        """
        Link.test()
        Image.test()
        Macro.test()
        PlainText.test()
        SuperScriptText.test()
        StrikeThroughText.test()
        Underline.test()
        Bold.test()
        Italic.test()
        Monospace.test()
        FontSizeChangeStart.test()
        FontSizeChangeEnd.test()
        InlineComment.test()
        Punctuation.test()

class SubelementSansMacro(Subelement):

    grammar = contiguous(
        [LeadingSpaces, Link, Image, SuperScriptText, StrikeThroughText,
         Underline, Bold, Italic, Monospace,
         CodeBlockStart, CodeBlockEnd,
         FontSizeChangeStart, FontSizeChangeEnd,
         InlineComment, PlainText, Punctuation])




    
# ===========
# Lists
# ===========

class MoinListItem(List):
    """
    An individual entry in a numbered or bulleted list.

    Look like
     1. Text here.
     2. Item 2
     * Fish heads!

    """
    # itemMarker is optional because this also handles indented, but non
    # listItems embedded in lists
    grammar = contiguous(
        attr("depth", LeadingSpaces),
        optional(attr("itemMarker", re.compile(r"\d+\.|\*"))),
        optional(re.compile(r" +")),
        attr("item", some(Subelement)),
        re.compile(r" *"),
        "\n"
        )

    def compose(self, parser, attr_of):
        """
        TODO: Not able to deal with embedded code blocks that contain lines
        without any indent.
        
        See Events/GCC2014/TrainingDay/DataManagers for test case.
        """
        out = " " * MoinList.indentLevel * 2
        if hasattr(self, "itemMarker"):
            out += self.itemMarker + " "
        else:
            out += "  "
        for subelement in self.item:
            out += compose(subelement)
        out += "\n"
        return(out)

    @classmethod
    def test(cls):
        """
        Test different instances of what this should and should not recognize
        """
        parse("@INDENT-1@1. E\n", cls)
        parse("@INDENT-1@2. Electric boogaloo\n", cls)
        parse("@INDENT-1@11. A simple case.\n", cls)
        parse("@INDENT-1@12. A simple case \n", cls)
        parse("@INDENT-1@* E\n", cls)
        parse("@INDENT-1@* Electric boogaloo\n", cls)
        parse("@INDENT-1@* A simple case.\n", cls)
        parse("@INDENT-1@* A simple case \n", cls)


class MoinList(List):
    """
    Look like any combination of this
     1. Text goes here
     1. More text here
     * Bullet item!
       1. Indented numbered item.
          Sometimes non list items too
          
    at varying levels of indent
    """
    grammar = contiguous(
        re.compile(r"(?=@INDENT-\d+@(\*|\d+\.))"),  # 1st item must be list item
        attr("listItems", some(MoinListItem)))
    indentLevel = 0
    indentBase = 0

    def compose(self, parser, attr_of):
        depths = [int(self.listItems[0].depth.depth)] 
        out = ""
        for item in self.listItems:
            if CodeBlockStart.inCodeBlock and MoinList.indentBase == 0:
                MoinList.indentBase = MoinList.indentLevel
            elif not CodeBlockStart.inCodeBlock and MoinList.indentBase != 0:
                MoinList.indentBase = 0 # we are out
            MoinList.indentLevel = LeadingSpaces.trackIndent(
                item, depths, MoinList.indentBase)
            out += compose(item)
        return(out)

        
    @classmethod
    def test(cls):
        """
        Test different instances of what this should and should not recognize
        """
        MoinListItem.test()
        parse("@INDENT-1@1. One Item Only\n", cls)
        parse("@INDENT-1@2. A simple case.\n@INDENT-1@3. With two items\n", cls)
        parse("""@INDENT-1@22. A simple case.
@INDENT-3@24. With nested item
""", cls)
        parse("""@INDENT-1@17. A simpler case.
@INDENT-3@1. With nested item
@INDENT-3@1. and another
""", cls)
        parse("""@INDENT-1@1. A less simplerer case.
@INDENT-3@1. With nested item
@INDENT-3@1. And another
@INDENT-5@1. and More!
@INDENT-3@1. Uh huh.
""", cls)



# ===========
# Tables - EEK!
# ===========


class CellMoinFormatItem(List):
    """
    Moin uses special characters to modify cell format.  This captures any
    one of them.

    These include
      -2    colspan
      |2    rowspan
      50%   cell width        - have no idea if we use this.
      width="50%" cell width  ~ about 20 pages
      (           left aligned (will append text-align: left; to style)
      :           centered
      )           right aligned (will append text-align: right; to style)
      ^           aligned to top (will append vertical-align: top; to style)
      v           aligned to bottom (will append vertical-align: bottom; to style)
      style="border: none"
      bgcolor="#XXXXXX"          - used in 10 places
      #XXXXXX     bgcolor, used in a few places include Teach/ComputingPlatforms

    Not used in Galaxy Wiki:
      tablewidth="100%"
      rowbgcolor="#XXXXXX" set row background color (only valid in first cell)
      tablebgcolor="#XXXXXX" set table background color
    """
    grammar = contiguous(
        [("-", attr("colspan", re.compile(r"\d+"))),
         ("|", attr("rowspan", re.compile(r"\d+"))),
         attr("left", "("),
         attr("right", ")"),
         attr("center", ":"),
         attr("top", "^"),
         attr("bottom", "v"),
         ("style=", attr("cellStyle", QuotedString)),
         ("bgcolor=", attr("bgcolor", QuotedString)),
         ("#", attr("bgcolor", PlainText)), 
         [
             (optional("width="), attr("width", QuotedString)),
             (attr("unquotedWidth", re.compile(r"\d+(%|em|ex|px|cm|mm|in|pt|pc)")))]
        ])

    def compose(self, parser, attr_of):
        """
        Ignore CellMoinFormatItems for the time being.
        TODO
        """
        if hasattr(self, "colspan"):
            return("PLACEHOLDER_COLSPAN=" + self.colspan)
        elif hasattr(self, "rowspan"):
            return("PLACEHOLDER_ROWSPAN=" + self.rowspan)
        elif hasattr(self, "left"):
            return("PLACEHOLDER_LEFT")
        elif hasattr(self, "right"):
            return("PLACEHOLDER_RIGHT")
        elif hasattr(self, "center"):
            return("PLACEHOLDER_CENTER")
        elif hasattr(self, "top"):
            return("PLACEHOLDER_TOP")
        elif hasattr(self, "bottom"):
            return("PLACEHOLDER_BOTTOM")
        elif hasattr(self, "cellStyle"):
            return("PLACEHOLDER_STYLE=" + compose(self.cellStyle))
        elif hasattr(self, "bgcolor"):
            return("PLACEHOLDER_BGCOLOR=" + compose(self.bgcolor))
        elif hasattr(self, "width"):
            return("PLACEHOLDER_WIDTH=" + compose(self.width))
        elif hasattr(self, "unquotedWidth"):
            return("PLACEHOLDER_WIDTH=" + self.unquotedWidth)
        return("UNRECOGNOZED CELL FORMAT ITEM")

    def composeHtml(self):
        """
        render CellMoinFormatItems as HTML.

        Returns
        1) a string with the format item in HTML, and
        2) True if it's a style attirbute, and false if it's standalone
        
        Assumes you are inside a td or th already.
        """
        if hasattr(self, "colspan"):
            return("colspan=" + self.colspan, False)
        elif hasattr(self, "rowspan"):
            return("rowspan=" + self.rowspan, False)
        elif hasattr(self, "left"):
            return('text-align: left;', True)
        elif hasattr(self, "right"):
            return('text-align: right;', True)
        elif hasattr(self, "center"):
            return('text-align: center;', True)
        elif hasattr(self, "top"):
            return("vertical-align: top;", True)
        elif hasattr(self, "bottom"):
            return("vertical-align: bottom;", True)
        elif hasattr(self, "cellStyle"):
            # add semicolon at end, if it does not have it.
            styleString = self.cellStyle.justTheString()
            if styleString[-1] != ";":
                styleString += ";"
            return(styleString, True)
        elif hasattr(self, "bgcolor"):
            theColor = self.bgcolor.justTheString()
            if re.match(r"[0-9A-Fa-f]{3,6}", theColor):
                theColor = "#" + theColor
            return("background-color: " + theColor + ";",
                   True)
        elif hasattr(self, "width"):
            return("width: " + self.width.justTheString() + ";", True)
        elif hasattr(self, "unquotedWidth"):
            return("width: " + self.unquotedWidth + ";", True)
        return("UNRECOGNOZED CELL FORMAT ITEM for HTML")


    
    @classmethod
    def test(cls):
        parse("|7", cls)
        parse("-5", cls)
        
        parse("(", cls)
        parse(")", cls)
        parse(":", cls)
        parse("^", cls)
        parse("v", cls)
        parse('style="border: none"', cls)
        parse('style="border: none;"', cls)
        parse('style="border: none; width: 20%"', cls)
        parse('style="border: none; width: 20%;"', cls)
        parse('bgcolor="#fffddd"', cls)
        parse('width="20%"', cls)
        parse("20%", cls)

        
class CellClass(List):
    grammar = contiguous(
        "class=", attr("cellClass", QuotedString))     

    def compose(self, parser, attr_of):
        return("CLASS=" + compose(self.cellClass))

    def isHeader(self):
        return(self.cellClass.justTheString().lower() == "th")

        
    @classmethod
    def test(cls):
        parse('class="th"', cls)
        parse('class="not-th"', cls)


class TableCell(List):
    grammar = contiguous(
        optional(
            "<",
            some([attr("cellClass", CellClass),
                  attr("cellFormat", some([CellMoinFormatItem, omit(" ")]))]),
            ">"),
        maybe_some(" "),
        attr("cellContent", maybe_some(Subelement)), 
        maybe_some(" "),
        "||")

    def compose(self, parser, attr_of):
        """
        Compose a cell.

        It's up to the table/tablerow to make sure the leading || is already
        in place.  Each cell is responsible for its trailing ||.
        """

        # start simple; TODO
        try:
            out = ""
            for item in self.cellFormat:
                out += compose(item)
        except AttributeError:
            out = ""

        try:
            for item in self.cellContent:
                out += compose(item)
        except AttributeError:
            pass
        return(out + " |")

     
    @classmethod
    def test(cls):
        CellClass.test()
        CellMoinFormatItem.test()
        Subelement.test()
        
        parse('<-3> ||', cls)
        parse('< style="background-color: #eef"> ||', cls)
        parse('<-3 style="background-color: #eef"> ||', cls)

        parse('Topic||', cls)
        parse('<|5 -2> Topic/Event ||', cls)
        parse(" ||", cls)
        parse("<|5> Text ||", cls)
        parse("<|2> Electric boogaloo ||", cls)
        parse(" Electric boogaloo ||", cls)
        parse(' Topic/Event ||', cls)


class RowStyle(List):
    grammar = contiguous(
        "rowstyle=", attr("rowStyle", QuotedString))     

    def compose(self, parser, attr_of):
        return("ROWSTYLE=" + compose(self.rowStyle))

    @classmethod
    def test(cls):
        parse('rowstyle="border: none"', cls)    
        parse('rowstyle="border: none;"', cls)
        parse('rowstyle="border: none; width: 300px"', cls)
        parse('rowstyle="border: none; width: 300px;"', cls)



class RowClass(List):
    grammar = contiguous(
        "rowclass=", attr("rowClass", QuotedString))

    def compose(self, parser, attr_of):
        return("ROWCLASS=" + compose(self.rowClass))

    def isHeader(self):
        return(self.rowClass.justTheString().lower() == "th")


        
    @classmethod
    def test(cls):
        parse('rowclass="th"', cls)
        parse('rowclass="spangled"', cls)

        
class TableRow(List):
    """
    An individual table row

    Look like
    ||<rowclass="th" width="7em">Date ||Topic/Event ||Venue/Location ||Contact ||
    """
    
    grammar = contiguous(
        "||",
        optional(
            "<",
            some([attr("rowStyle", RowStyle),
                  attr("rowClass", RowClass),
                  attr("firstCellClass", CellClass),
                  attr("firstCellFormat", some([CellMoinFormatItem, omit(" ")])),
                  " "]),
            ">"),
        maybe_some(" "),
        attr("firstCellContent", maybe_some(Subelement)),
        maybe_some(" "),
        "||",
        attr("rowCells", maybe_some(TableCell)),
        "\n"
        )
    def compose(self, parser, attr_of):
        """
        Generate a table row in Markdown.
    
        This is only invoked where the table can be generated using Markdown.
        """
        firstCellText = "| "
        for item in self.firstCellContent:
            firstCellText += compose(item)
        out = firstCellText + "| "
        if self.rowIsHeader():
            headerOut = "| " + "-" * (len(firstCellText)-3) + " | "

        for cell in self.rowCells:
            cellText = " "
            for item in cell.cellContent:
                cellText += compose(item)
            out += cellText + " | "
            if self.rowIsHeader():
                headerOut += "-" * (len(cellText)-1) + " | "
        
        out += "\n"
        if self.rowIsHeader():
            out += headerOut + "\n"
            
        return(out)

    def rowIsHeader(self):
        """
        Return true if every cell in the row is a header cell.
        """
        # Check whole row first
        if hasattr(self, "rowClass") and self.rowClass.isHeader():
            return(True)                   # is header at row level.
            
        elif hasattr(self, "firstCellClass") and self.firstCellClass.isHeader():
            # or, every cell might be indivudaully specified as th.
            for cell in self.rowCells:
                if hasattr(cell, "cellClass") and cell.cellClass.isHeader():
                    pass                  # is header so far.
                else:
                    return(False)

            return(True)                  # is header in every cell


    def getRowClass(self):
        """
        Return the class of the row, if one exists, as a quoted string,
        or None if not.
        """
        if hasattr(self, "rowClass"):
            return(compose(self.rowClass))
        return None
        
        
    @classmethod
    def test(cls):
        """
        Test different instances of what this should and should not recognize
        """
        RowStyle.test()
        RowClass.test()
        CellClass.test()
        CellMoinFormatItem.test()
        Subelement.test()
        TableCell.test()
        parse('||<class="th"> ||<-3 style="background-color: #eef"> ||\n', cls)
        parse('||<rowclass="th"> Date||\n', cls)
        parse('||<rowclass="th" width="7em">Date ||Topic/Event ||Venue/Location ||Contact ||\n', cls)
        parse('|| a ||\n', cls)
        parse('||<|2> ||\n', cls)
        parse('||<|7 rowclass="th"> ||\n', cls)
        parse("||<|5> Text ||\n", cls)
        parse("|| Electric boogaloo||\n", cls)
        parse("""|| <<MailTo( w4mcourse2015.organisation@sb-roscoff.fr, W4M Course Organisers)>> ||\n""", cls)
        parse("""|| ||<<div(right)>>[[http://bit.ly/gxytrnGUGGO|{{attachment:Images/GalaxyLogos/GTN16.png|Training offered by GTN Member}}]]<<div>> <<MailTo( w4mcourse2015.organisation@sb-roscoff.fr, W4M Course Organisers)>> ||\n""", cls)
        parse("""||<class="th"> September 21-25 || || <<MailTo( w4mcourse2015.organisation@sb-roscoff.fr, W4M Course Organisers)>> ||\n""", cls)
        parse("""||<class="th"> September 21-25 || ''[[http://workflow4metabolomics.org/training/W4Mcourse2015|Traitement des données métabolomiques sous Galaxy]]'' ||<<Include(Events/Badges/Europe)>> Station Biologique de Roscoff, France ||<<div(right)>>[[http://bit.ly/gxytrnGUGGO|{{attachment:Images/GalaxyLogos/GTN16.png|Training offered by GTN Member}}]]<<div>> <<MailTo( w4mcourse2015.organisation@sb-roscoff.fr, W4M Course Organisers)>> ||\n""", cls)
        parse("""||<class="th"> September 28 || ''[[http://www.emgs-us.org/AM2015/agendamon.asp|Mutational Analysis with Random DNA Identifiers (MARDI), a High-Fidelity NGS Approach That Simultaneously Identifies Gene Marker Mutations from Heterogeneous Mutant Cell Populations]]'' ||<<Include(Events/Badges/NorthAmerica)>> [[http://www.emgs-us.org/AM2015/index.asp|Environmental Mutagenesis and Genomics Society (EMGS)]], New Orleans, Louisiana, United States || Javier Revollo ||\n""", cls)
        parse("""||<class="th"> September 21-23 || [[https://www.regonline.com/builder/site/Default.aspx?EventID=1692764|JHU-DaSH: Data Science Hackathon]] ||<<Include(Events/Badges/NorthAmerica)>> [[https://www.regonline.com/builder/site/tab2.aspx?EventID=1692764|Baltimore]], Maryland, United States || <<MailTo(jhuDaSH@jhu.edu, Email)>> ||\n""", cls)



        
class Table(List):
    """
    There is no explicit table start or end text in MoinMoin.  A table starts
    with the first row, and then goes until there is no more rows.

    The first cell of the first row is also special, but only because only the
    first row can be special in GFM.
    """
    grammar = contiguous(attr("tableRows", some(TableRow)))

    def compose(self, parser, attr_of):

        # Can this table be rendered in GFM, or does it need HTML?
        if self.needsHTMLRendering():
            out = self.composeHtml()
        else:
            out = ""
            for row in self.tableRows:
                out += compose(row)
            
        return(out)

    def needsHTMLRendering(self):
        """
        Answers the question: does this table need to be rendered in HTML?

        What can be rendered in GFM:
         - same number of cells in every row (no rowspans or colspans)
         - must have a header row
         - Cells without any markdown
        If the table meets all those criteria it can be rendered in GFM.
         
        Q: Why not just render everying in HTML?  The whole point of a wiki
        is to make it easy to edit.  GFM table notation is way easier than
        HTML.
        """

        # Walk though each row looking for markup we can't deal with        
        rowIdx = 0
        firstRowIsHeader = False
        for row in self.tableRows:
            if hasattr(row, "rowClass"):
                # if first row is not a header, or if a row other than
                # the first one has a class then it must be rendered in HTML
                if row.rowIsHeader() and rowIdx == 0:
                    firstRowIsHeader = True
                else:
                    return True           # needs to be in HTML

            if hasattr(row, "rowStyle") or hasattr(row, "firstCellFormat"):
                return(True)              # no styling supported in GFM

            # Only styling permitted from here on (for GFM) is all cells in
            # first row can be header cells.
            if hasattr(row, "firstCellClass"):
                if rowIdx > 0 or not row.firstCellClass.isHeader():
                    return(True)          # Sorry, not header

            for cell in row.rowCells:
                if hasattr(cell, "cellClass"):
                    if rowIdx > 0 or not cell.cellClass.isHeader():
                        return(True) 
                if hasattr(cell, "cellStyle"):
                    return(True)          # no style supported anywhere
            
            rowIdx += 1

        if firstRowIsHeader:
            return(False)

        return(True)                     # Does not require HTML


    def composeCellHtml(self, row, cellClass, cellFormat, cellContent):
        """
        compose a cell in HTML.

        If is HTML then all markup in it must be in HTML too.
        
        This routine exists here (rather than as a method of TableCell because
        the first cell of a row is problematic.
        """
        
        # render first cell
        cellType = "td"
        cellStyle = ""
        cellAttribs = ""

        if row.rowIsHeader() or (cellClass != None and cellClass.isHeader()):
            cellType = "th"
        if cellClass != None and not cellClass.isHeader():
            cellStyle += " class=" + compose(cellClass.cellClass) + " "
        if cellFormat != None:
            for formatItem in cellFormat:
                formatText, inStyle = formatItem.composeHtml()
                if inStyle:
                    cellStyle += " " + formatText
                else:
                    cellAttribs += " " + formatText

        if cellStyle:
            cellStyle = ' style="' + cellStyle + '"'

        cellContentText = ""
        for item in cellContent:
            cellContentText += item.composeHtml()
        cellHtml = (
            "    <" + cellType + cellAttribs + cellStyle + "> " +
            cellContentText + "</" + cellType + ">\n")
        return(cellHtml)


                
    def composeHtml(self):
        """
        Table contains markup that cannot be rendered in GFM.
        """
        out = "<table>\n"

        for row in self.tableRows:
            # generate the row header
            rowHtml = "  <tr"
            if hasattr(row, "rowClass"):
                rowHtml += " class=" + row.rowClass.rowClass.quotedText + " "
            if hasattr(row, "rowStyle"):
                rowHtml += " style=" + row.rowStyle.rowStyle.quotedText + " "
            rowHtml += ">\n"
            out += rowHtml
            
            # render first cell
            cellClass = None
            if hasattr(row, "firstCellClass"):
                cellClass = row.firstCellClass
            cellFormat = None
            if hasattr(row, "firstCellFormat"):
                cellFormat = row.firstCellFormat
            out += self.composeCellHtml(row, cellClass, cellFormat,
                                        row.firstCellContent)
            
            # render the rest of the cells
            for cell in row.rowCells:
                cellClass = None
                if hasattr(cell, "cellClass"):
                    cellClass = cell.cellClass
                cellFormat = None
                if hasattr(cell, "cellFormat"):
                    cellFormat = cell.cellFormat
                out += self.composeCellHtml(row, cellClass, cellFormat,
                                            cell.cellContent)

            # Render the end of the row
            out += "  </tr>\n"

        # render the end of the table
        out += "</table>\n\n"

        return(out)



    @classmethod
    def test(cls):
        """
        Test different instances of what this should and should not recognize
        """
        TableRow.test()
        parse('||<rowclass="th"> Date ||\n', cls)

        parse('||<rowclass="th" width="7em">Date ||\n', cls)

        parse('||<rowclass="th" width="7em">Date ||Topic/Event ||Venue/Location ||Contact ||\n||<class="th"> September 14-18 || ''[[http://training.bioinformatics.ucdavis.edu/2015/01/13/using-galaxy-for-analysis-of-high-throughput-sequence-data-september-14-18-2015/|Using Galaxy for Analysis of High Throughput Sequence Data]]'' ||<<Include(Events/Badges/NorthAmerica)>> [[http://bioinformatics.ucdavis.edu/|UC Davis Bioinformatics Core]], Davis, California, United States ||<<div(right)>>[[http://bit.ly/gxytrnUCDavis|{{attachment:Images/GalaxyLogos/GTN16.png|Training offered by GTN Member}}]]<<div>>  ||\n', cls)
        
        parse("""||<class="th"> September 21-23 || [[https://www.regonline.com/builder/site/Default.aspx?EventID=1692764|JHU-DaSH: Data Science Hackathon]] ||<<Include(Events/Badges/NorthAmerica)>> [[https://www.regonline.com/builder/site/tab2.aspx?EventID=1692764|Baltimore]], Maryland, United States || <<MailTo(jhuDaSH@jhu.edu, Email)>> ||
||<class="th"> September 21-25 || ''[[http://workflow4metabolomics.org/training/W4Mcourse2015|Traitement des données métabolomiques sous Galaxy]]'' ||<<Include(Events/Badges/Europe)>> Station Biologique de Roscoff, France ||<<div(right)>>[[http://bit.ly/gxytrnGUGGO|{{attachment:Images/GalaxyLogos/GTN16.png|Training offered by GTN Member}}]]<<div>> <<MailTo( w4mcourse2015.organisation@sb-roscoff.fr, W4M Course Organisers)>> ||
||<class="th"> September 28 || ''[[http://www.emgs-us.org/AM2015/agendamon.asp|Mutational Analysis with Random DNA Identifiers (MARDI), a High-Fidelity NGS Approach That Simultaneously Identifies Gene Marker Mutations from Heterogeneous Mutant Cell Populations]]'' ||<<Include(Events/Badges/NorthAmerica)>> [[http://www.emgs-us.org/AM2015/index.asp|Environmental Mutagenesis and Genomics Society (EMGS)]], New Orleans, Louisiana, United States || Javier Revollo ||\n""", cls)        
        parse("""||<class="th"> September 17-18 || '''[[News/ToolsCollectionsHack|Remote Hackathon for Tools and Dataset Collections]]''' || <<Include(Events/Badges/World)>> ''Online'' || <<MailTo(galaxy-iuc@lists.galaxyproject.org, IUC)>> ||
||<class="th"> September 17-18 || ''Utilizing the Galaxy Analysis Framework at Core Facilities'' || <<Include(Events/Badges/NorthAmerica)>> [[http://wacd.abrf.org/|Western Association of Core Directors (WACD) Annual Meeting]], Portland, Oregon, United States || [[DaveClements|Dave Clements]] ||
||<class="th"> September 21-23 || [[https://www.regonline.com/builder/site/Default.aspx?EventID=1692764|JHU-DaSH: Data Science Hackathon]] ||<<Include(Events/Badges/NorthAmerica)>> [[https://www.regonline.com/builder/site/tab2.aspx?EventID=1692764|Baltimore]], Maryland, United States || <<MailTo(jhuDaSH@jhu.edu, Email)>> ||
||<class="th"> September 21-25 || ''[[http://workflow4metabolomics.org/training/W4Mcourse2015|Traitement des données métabolomiques sous Galaxy]]'' ||<<Include(Events/Badges/Europe)>> Station Biologique de Roscoff, France ||<<div(right)>>[[http://bit.ly/gxytrnGUGGO|{{attachment:Images/GalaxyLogos/GTN16.png|Training offered by GTN Member}}]]<<div>> <<MailTo( w4mcourse2015.organisation@sb-roscoff.fr, W4M Course Organisers)>> ||
||<class="th"> September 28 || ''[[http://www.emgs-us.org/AM2015/agendamon.asp|Mutational Analysis with Random DNA Identifiers (MARDI), a High-Fidelity NGS Approach That Simultaneously Identifies Gene Marker Mutations from Heterogeneous Mutant Cell Populations]]'' ||<<Include(Events/Badges/NorthAmerica)>> [[http://www.emgs-us.org/AM2015/index.asp|Environmental Mutagenesis and Genomics Society (EMGS)]], New Orleans, Louisiana, United States || Javier Revollo ||
||<class="th"> September 28-30 || ''[[http://biosb.nl/events/course-next-generation-sequencing-ngs-data-analysis-2015/|Next generation sequencing (NGS) data analysis]]'' ||<<Include(Events/Badges/Europe)>> [[http://www.medgencentre.nl/|University Medical Centre Groningen]], The Netherlands ||<<Include(Teach/GTN/Badge16)>>  <<MailTo(education@biosb.nl, BioSB Education)>> ||
""", cls)
        

# ================
# Paragraph
# ================

class Paragraph(List):
    """
    Paragraphs are text separated by blank lines or other tokens.
    """
    grammar = contiguous(some(Subelement))

    def compose(self, parser, attr_of):
        out = ""
        for item in self:
            out += compose(item)
        return(out)

    @classmethod
    def test(cls):
        """
        Test different instances of what this should and should not recognize
        """
        parse("""Let's try plain text first.
        
        """, cls)


# ================
# YAML Macros
# ===============

class TitleDiv(List):
    """
    Title Div may get special handling because it might affect the YAML.
    """
    grammar = contiguous(
        "<<div(",
        maybe_some(whitespace),
        "title",
        maybe_some(whitespace),
        ")>>",
        attr("title", some(SubelementSansMacro)),
        maybe_some(whitespace),
        "<<div>>")

    def compose(self, parser, attr_of):
        global pageYaml

        # Everything generated is placed in YAML
        
        pageYaml["pagetitle"] = compose(self.title)

        return("")

    @classmethod
    def test(cls):
        """
        Test different instances of what this should and should not recognize
        """
        parse("<<div(title)>> A Wonderful Title<<div>>", cls)
        parse("<<div(title)>> A Wonderful Title.<<div>>", cls)
        parse("<<div(title)>>[[http://www.researchgate.net/profile/Carrie_Ganote|Carrie Ganote]]<<div>>", cls)
    


class YamlMacro(List):
    """
    Anything parsed by this requires something other than just generating a
    markdown
    """
    grammar = contiguous(TitleDiv)



    @classmethod
    def test(cls):
        TitleDiv.test()
    

# ================
# Elements
# ===============
    
class Element(List):
    """
    An element is anything that can stand on it's own, at the the highest level
    of the Document.

    Elements don't have to be at the top level, but they can be.
    """
    grammar = contiguous(
        [SectionHeader, YamlMacro, MoinList, Table, Macro,
         CodeBlockStart, CodeBlockEnd, FontSizeChangeStart, FontSizeChangeEnd,
         Comment, Paragraph, TrailingWhitespace])


    def compose(self, parser, attr_of):
        """
        Override compose method to generate Markdown.
        """
        return(compose(self[0]))

    @classmethod
    def test(cls):
        """
        Test different instances of what this should and should not recognize
        """
        Table.test()
        SectionHeader.test()
        YamlMacro.test()
        MoinList.test()
        Macro.test()
        CodeBlockStart.test()
        CodeBlockEnd.test()
        Comment.test()
        Paragraph.test()
        #TrailingWhitespace.test()
            

# =================
# Processing Instructions
# =================


class FormatPI(List):
    grammar = contiguous(
        "#format ",
        attr("format", re.compile(r"[\w/]+")))

    def compose(self, parser, attr_of):
        if self.format == "wiki":
            return("")
        else:
            raise NotImplementedError(self.format + " parsing is not supported.")

#    @classmethod
#    def parse(cls, parser, text, pos):
#        print("YES", text, pos)

    @classmethod
    def test(cls):
        """
        Test different instances of what this should and should not recognize
        """
        parse("#format wiki", cls)
        parse("#format text/creole", cls)
        

class RedirectPI(List):
    """
    Not sure what to do with redirects.

    Probably want to have a clean slate as far as redirects go.  Which
    means don't do anything with them.
    """
    grammar = contiguous(
        re.compile(r"#REDIRECT ", re.IGNORECASE),
        attr("redirect", InternalPagePath))

    def compose(self, parser, attr_of):
        raise NotImplementedError("Not generating REDIRECT Pages. Letting them die.")

    @classmethod
    def test(cls):
        """
        Test different instances of what this should and should not recognize
        """
        parse("#REDIRECT CloudMan/AWS/AMIs\n", cls)
        parse("#REDIRECT Learn/IntervalOperations", cls)
        parse("#redirect Events/Meetups/Baltimore/20150122", cls)
        parse("#redirect Events/Meetups/Baltimore/2015-01-22", cls)
        parse("#redirect Events/Meetups/Baltimore/2015-01-22\n", cls)
        parse("#redirect Events/Meetups/Baltimore/2015-01-22 \n", cls)

class RefreshPI(List):
    """
    The refresh is effectively a redirect to an external page.

    We aren't propoagating redirects, don't propagate refreshes either.
    """
    grammar = contiguous(
        re.compile(r"#refresh "),
        attr("redirect", restline))

    def compose(self, parser, attr_of):
        raise NotImplementedError("Not generating refresh Pages. Letting them die.")

    @classmethod
    def test(cls):
        """
        Test different instances of what this should and should not recognize
        """
        parse("#refresh http:/a.b.c/CloudMan/AWS/AMIs\n", cls)
        parse("#refresh https://Learn/IntervalOperations#fish", cls)

class PragmaPI(List):
    """
    Pragma is used to control some behavious.  The only one we have is

      #pragma section-numbers off    

    I'm going to make an executive decision that we don't care about these
    """
    grammar = contiguous(
        re.compile(r"#pragma "),
        attr("pragma", restline))

    def compose(self, parser, attr_of):
        return("")

    @classmethod
    def test(cls):
        """
        Test different instances of what this should and should not recognize
        """
        parse("#pragma section-numbers off", cls)

        
class ProcessingInstruction(List):
    """
    Happen at top of file.

    Have the form
     #format        - lots 
     #redirect      - lots
     #refresh       - have one of these
     #pragma        - have 2 both are
       #pragma section-numbers off
     #deprecated    - have 0
     #language      - have 51 of these, all en

    Comments, which start with ## are handled elsewhwere.
    """
    grammar = contiguous(
        attr("pi", [FormatPI, RedirectPI, RefreshPI, PragmaPI]))

    
#        attr("pi",[FormatPI, RedirectPI, RefreshPI, PragmaPI, LanguagePI]),

    
    def compose(self, parser, attr_of):
        return(compose(self.pi))
    
    @classmethod
    def test(cls):
        """
        Test different instances of what this should and should not recognize
        """
        FormatPI.test()
        #RedirectPI.test()
        #RefreshPI.test()
        PragmaPI.test()
        parse("#format wiki\n", cls)
        parse("#format text/creole\n", cls)
        
        
class Document(List):
    """
    Parse the whole page.

    Moin pages don't have to contain anything, and most items do not have to be in a
    particular order.

    Does the page arrive as a list of text lines?
    """
    grammar = contiguous(
        maybe_some([ProcessingInstruction, Comment]),
        maybe_some(Element))


    @classmethod
    def test(cls):
        parse("""#REDIRECT CloudMan/AWS/AMIs
""", cls)



# =================================
# Non grammar subs
# =================================

class Argghhs(object):
    """
    Process and provide access to command line arguments.
    """

    def __init__(self):
        argParser = argparse.ArgumentParser(
            description="Convert a single wiki page (a file) from MoinMoin to Github Flavored Markdown. Running this with no params does nothing.  Running with --debug produces a LOT of output. Markdown is sent to stdout.",
            epilog="Example: " + os.path.basename(__file__) +
            " --moinpage=Admin.moin --mdpage=Admin.md --debug")
        argParser.add_argument(
            "--moinpage", required=False, default=None,
            help="File containing a single MoinMoin page.")
        argParser.add_argument(
            "--mdpage", required=False, default=None,
            help="Where to put the resulting markdown page.")
        argParser.add_argument(
            "--runtests", required=False, 
            help="Run Unit Tests.",
            action="store_true")
        argParser.add_argument(
            "--debug", required=False, 
            help="Include debug output",
            action="store_true")
        self.args = argParser.parse_args()

        return(None)


def testFail(testText, cls):
    """
    Run a parse test that should fail.
    """
    try:
        parsed = parse(testText, cls)
        print(parsed)
        print("ERROR: Test that should have failed did not fail.")
        print("Test:")
        print(testText)
        printList(parsed)
        raise BaseException(cls.__name__)
    except (SyntaxError, TypeError):
        pass                              # TypeError is b/c of pypeg bug.
    return()


def insertIndentFlag(match):
    indent = len(match.group('leading'))
    return("@INDENT-" + str(indent) + "@") 

def identifyIndents(moinText):
    """
    PyPeg strips leading space on lines, complicating our goal of determining
    depth in lists, and when text should be indented.
    Resolve this by replacing leading spaces with a unique string that also
    identifies how much indent there is.
    """
    return(re.sub(r"^(?P<leading> +)(?=\S)", insertIndentFlag, moinText,
                  flags=re.MULTILINE))

def printList(list, indent=0):
    for item in list:
        print("." * indent, item)
        if item != None and not isinstance(item, str):
            print("c" * indent, compose(item))
            printList(item, indent+2)
        else:
            print("n" * indent, "None")
    try:
        for name, item in list.__dict__.items():
            if name not in ["position_in_text"]:
                print("d" * indent, name, ":", item)
                if item != None and not isinstance(item, str):
                    if len(item) > 0:
                        print("c" * indent, name, ":", compose(item))
                        printList(item, indent+2)
                else:
                    print("n" * indent, name, ": None")
    except AttributeError:
        pass               # Classes that don't name any attr's have no dict

def runTests():
    global args
    global pageYaml
    
    pageYaml = {}

    CellMoinFormatItem.test()
    CellClass.test()
    TableCell.test()
    RowStyle.test()
    RowClass.test()
    TableRow.test()
    Table.test()
    
    ProcessingInstruction.test()
    MoinList.test()
    SectionHeader.test()
    PlainText.test()
    Link.test()
    QuotedString.test()
    InternalPagePath.test()
    ExternalPagePath.test()
    IncludeMacro.test()
    Macro.test()
    Subelement.test()
    Paragraph.test()
    Element.test()
    Document.test()

    text = identifyIndents("""
<<Include(Develop/LinkBox)>>
<<Include(Admin/LinkBox)>>
<<Include(FAQs/LinkBox)>>

= Galaxy Administration =
This is the '''hub page''' for the section of ''this wiki'' on how to deploy and administer your own copy of Galaxy.

== Deploying ==

 * [[CloudMan]]
   * [[/GetGalaxy#This is a 23 Link-to|Install own Galaxy]]
   * [[CloudMan|Install on the Cloud Infrastructure]]
 * [[Admin/Maintenance|Maintaining an Instance]]
 * [[http://deploy.com]]

== Other ==
 * [[Admin/License|License]]
 * [[Admin/RunningTests|Running Tests]]
 * [[Community/GalaxyAdmins|Galaxy-Admins discussion group]]
 * [[Admin/SwitchingToGithubFromBitbucket|Switching to Github from Bitbucket]]

<<div(center)>>
[[http://galaxyproject.org/search/getgalaxy|{{attachment:Images/Logos/GetGalaxySearch.png|Search all Galaxy administration resources|width="120"}}]]

[[http://galaxyproject.org/search/getgalaxy|Search all Galaxy administration resources]]
<<div>>
 
""")

    f = parse(text, Document)

    if args.args.debug:
        print("DEBUG: DOCUMENT UNIT TEST in COMPILED FORMAT:")
        printList(f, 2)

    # What can we do with that parse now that we have it?

    markdownText = compose(f)

    if args.args.debug:
        print("\n====\n====\nDEBUG: DOCUMENT UNIT TEST DONE\n====\n====")

    return


# #########################################
# MAIN
#
# Can be run as a standalone program or called from another program.
# #########################################

def translate(srcFilePath, destFilePath):
    """
    Translate a file from MoinMoin markup to GFM.
    """
    moinFile = open(srcFilePath, "r")
    moinText = moinFile.read()
    moinFile.close()

    # if it's creole, give it up, as the parsing errors can happen anywhere.
    if moinText[0:19] == "#format text/creole":
        raise NotImplementedError("Creole parsing is not supported.")

    # Replace the mystery character with a space.
    moinText = re.sub(" ", " ", moinText)

    # Replace leading spaces on lines  with @INDENT-n@ where n is the
    # number of spaces. PyPeg often strips them, causing havoc with lists.  
    moinText = identifyIndents(moinText)

    # Each page can have leading YAML.  There's probably a way to deal with this
    # gracefully in PyPeg, but I'll just hack it with a Global.
    global pageYaml
    pageYaml = {}
        
    parsedMoin = parse(moinText, Document)
    markdownText = compose(parsedMoin)
    markdownFile = open(destFilePath, "w")

    if len(pageYaml) > 0:
        markdownFile.write("----\n")
        for name, value in pageYaml.items():
            markdownFile.write(name +": " + value + "\n")
        markdownFile.write("----\n")
            
    markdownFile.write(markdownText)
    markdownFile.close()

    return(parsedMoin)

    
if __name__ == "__main__":

    args = Argghhs()                          # process command line arguments

    if args.args.runtests:
        runTests()

    if args.args.moinpage:
        parsedMoin = translate(args.args.moinpage, args.args.mdpage)
        if args.args.debug:
            print("DEBUG: DOCUMENT in PARSED FORM:")
            printList(parsedMoin, 2)
            print("====\n====\nEND DOCUMENT in PARSED FORM\n====\n====")


class WikiWordLinks(List):
    """
    Need to handle Camel Case words that are links.
    """
class CategoryLinks(List):
    """
    What to do with Category links?

    They are WikiWordLinks that start with the word "Category".
    """


