
"""
ANSI -> html converter

Credit for original idea and implementation
goes to Muhammad Alkarouri and his
snippet #577349 on http://code.activestate.com.

(extensively modified by Griatch 2010)
"""

import re
import cgi
from ansi import *


class TextToHTMLparser(object):
    """
    This class describes a parser for converting from ansi to html.
    """

    tabstop = 4
    # mapping html color name <-> ansi code.
    hilite = ANSI_HILITE
    normal = ANSI_NORMAL
    underline = ANSI_UNDERLINE
    colorcodes = [
            ('red', hilite + ANSI_RED),
            ('maroon', ANSI_RED),
            ('lime', hilite + ANSI_GREEN),
            ('green', ANSI_GREEN),
            ('yellow', hilite + ANSI_YELLOW),
            ('olive', ANSI_YELLOW),
            ('blue', hilite + ANSI_BLUE),
            ('navy', ANSI_BLUE),
            ('magenta', hilite + ANSI_MAGENTA),
            ('purple', ANSI_MAGENTA),
            ('cyan', hilite + ANSI_CYAN),
            ('teal', ANSI_CYAN),
            ('white', hilite + ANSI_WHITE),  # pure white
            ('gray', ANSI_WHITE),  # light grey
            ('dimgray', hilite + ANSI_BLACK),  # dark grey
            ('black', ANSI_BLACK),  # pure black
    ]
    colorback = [
            ('bgred', hilite + ANSI_BACK_RED),
            ('bgmaroon', ANSI_BACK_RED),
            ('bglime', hilite + ANSI_BACK_GREEN),
            ('bggreen', ANSI_BACK_GREEN),
            ('bgyellow', hilite + ANSI_BACK_YELLOW),
            ('bgolive', ANSI_BACK_YELLOW),
            ('bgblue', hilite + ANSI_BACK_BLUE),
            ('bgnavy', ANSI_BACK_BLUE),
            ('bgmagenta', hilite + ANSI_BACK_MAGENTA),
            ('bgpurple', ANSI_BACK_MAGENTA),
            ('bgcyan', hilite + ANSI_BACK_CYAN),
            ('bgteal', ANSI_BACK_CYAN),
            ('bgwhite', hilite + ANSI_BACK_WHITE),
            ('bggray', ANSI_BACK_WHITE),
            ('bgdimgray', hilite + ANSI_BACK_BLACK),
            ('bgblack', ANSI_BACK_BLACK),
    ]

    # make sure to escape [
    colorcodes = [(c, code.replace("[", r"\[")) for c, code in colorcodes]
    colorback = [(c, code.replace("[", r"\[")) for c, code in colorback]
    # create stop markers
    fgstop = [("", c.replace("[", r"\[")) for c in (normal, hilite, underline)]
    bgstop = [("", c.replace("[", r"\[")) for c in (normal,)]
    fgstop = "|".join(co[1] for co in colorcodes + fgstop + [("", "$")])
    bgstop = "|".join(co[1] for co in colorback + bgstop + [("", "$")])

    # pre-compile regexes
    re_fgs = [(cname, re.compile("(?:%s)(.*?)(?=%s)" % (code, fgstop))) for cname, code in colorcodes]
    re_bgs = [(cname, re.compile("(?:%s)(.*?)(?=%s)" % (code, bgstop))) for cname, code in colorback]
    re_normal = re.compile(normal.replace("[", r"\["))
    re_hilite = re.compile("(?:%s)(.*)(?=%s)" % (hilite.replace("[", r"\["), fgstop))
    re_uline = re.compile("(?:%s)(.*?)(?=%s)" % (ANSI_UNDERLINE.replace("[", r"\["), fgstop))
    re_string = re.compile(r'(?P<htmlchars>[<&>])|(?P<space> [ \t]+)|(?P<lineend>\r\n|\r|\n)', re.S|re.M|re.I)

    def re_color(self, text):
        """
        Replace ansi colors with html color class names.
        Let the client choose how it will display colors, if it wishes to.  """
        for colorname, regex in self.re_fgs:
            text = regex.sub(r'''<span class="%s">\1</span>''' % colorname, text)
        for bgname, regex in self.re_bgs:
            text = regex.sub(r'''<span class="%s">\1</span>''' % bgname, text)
        return self.re_normal.sub("", text)

    def re_bold(self, text):
        "Clean out superfluous hilights rather than set <strong>to make it match the look of telnet."
        return self.re_hilite.sub(r'<strong>\1</strong>', text)

    def re_underline(self, text):
        "Replace ansi underline with html underline class name."
        return self.re_uline.sub(r'<span class="underline">\1</span>', text)

    def remove_bells(self, text):
        "Remove ansi specials"
        return text.replace('\07', '')

    def remove_backspaces(self, text):
        "Removes special escape sequences"
        backspace_or_eol = r'(.\010)|(\033\[K)'
        n = 1
        while n > 0:
            text, n = re.subn(backspace_or_eol, '', text, 1)
        return text

    def convert_linebreaks(self, text):
        "Extra method for cleaning linebreaks"
        return text.replace(r'\n', r'<br>')

    def convert_urls(self, text):
        "Replace urls (http://...) by valid HTML"
        regexp = r"((ftp|www|http)(\W+\S+[^).,:;?\]\}(\<span\>) \r\n$\"\']+))"
        # -> added target to output prevent the web browser from attempting to
        # change pages (and losing our webclient session).
        return re.sub(regexp, r'<a href="\1" target="_blank">\1</a>', text)

    def do_sub(self, m):
        "Helper method to be passed to re.sub."
        c = m.groupdict()
        if c['htmlchars']:
            return cgi.escape(c['htmlchars'])
        if c['lineend']:
            return '<br>'
        elif c['space'] == '\t':
            return ' ' * self.tabstop
        elif c['space']:
            t = m.group().replace('\t', '&nbsp;' * self.tabstop)
            t = t.replace(' ', '&nbsp;')
            return t

    def parse(self, text, strip_ansi=False):
        """
        Main access function, converts a text containing
        ansi codes into html statements.
        """
        # parse everything to ansi first
        text = parse_ansi(text, strip_ansi=strip_ansi, xterm256=False)
        # convert all ansi to html
        result = re.sub(self.re_string, self.do_sub, text)
        result = self.re_color(result)
        result = self.re_bold(result)
        result = self.re_underline(result)
        result = self.remove_bells(result)
        result = self.convert_linebreaks(result)
        result = self.remove_backspaces(result)
        result = self.convert_urls(result)
        # clean out eventual ansi that was missed
        #result = parse_ansi(result, strip_ansi=True)

        return result

HTML_PARSER = TextToHTMLparser()


#
# Access function
#

def parse_html(string, strip_ansi=False, parser=HTML_PARSER):
    """
    Parses a string, replace ansi markup with html
    """
    return parser.parse(string, strip_ansi=strip_ansi)
