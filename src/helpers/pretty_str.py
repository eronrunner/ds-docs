from enum import Enum


class Font(Enum):
    BOLD = '\033[1m'
    TRANSPARENT = '\033[100;1m'
    UNDERLINE = '\033[4m'
    ITALIC = '\033[3m'
    END = '\033[0m'
    HIGHLIGHT = '\033[7m'
    CROSS = '\033[9m'

    @classmethod
    def bold(cls, text):
        return f"{cls.BOLD.value}{text}{cls.END.value}"

    @classmethod
    def un(cls, text):
        return f"{cls.UNDERLINE.value}{text}{cls.END.value}"

    @classmethod
    def it(cls, text):
        return f"{cls.ITALIC.value}{text}{cls.END.value}"

    @classmethod
    def hl(cls, text):
        return f"{cls.HIGHLIGHT.value}{text}{cls.END.value}"

    @classmethod
    def cr(cls, text):
        return f"{cls.CROSS.value}{text}{cls.END.value}"

    @classmethod
    def tr(cls, text):
        return f"{cls.TRANSPARENT.value}{text}{cls.END.value}"


class Layout:

    TAB = '\t'
    NEW_LINE = '\n'
    SPACE = ' '
    DOUBLE_SPACE = '  '
    ALIGN_LEFT = '<'
    ALIGN_RIGHT = '>'
    ALIGN_CENTER = '^'
    ALIGN_JUSTIFY = '='

    def __init__(self, align=ALIGN_LEFT, num=0, char=""):
        self.align = align
        self.num = num
        self.char = char

    def left(self, text):
        return f"{text}{self.char * self.num}"

    def right(self, text):
        return f"{self.char * self.num}{text}"

    def center(self, text):
        return f"{self.char * self.num}{text}{self.char * self.num}"

    def justify(self, text):
        return f"{self.char * self.num}{text}{self.char * self.num}"

    def apply(self, text):
        if self.align == self.ALIGN_LEFT:
            return self.left(text)
        elif self.align == self.ALIGN_RIGHT:
            return self.right(text)
        elif self.align == self.ALIGN_CENTER:
            return self.center(text)
        elif self.align == self.ALIGN_JUSTIFY:
            return self.justify(text)
        else:
            return text


class Color(Enum):

    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    END = '\033[0m'

    @classmethod
    def color(cls, text, color):
        return f"{color}{text}{cls.END}"


class Style:

    def __init__(self, color: Color, font: [Font], layout: Layout):
        self.color = color
        self.font = font
        self.layout = layout

    def apply(self, text):
        return f"{self.color.value}{''.join([f.value for f in self.font])}{self.layout.apply(text)}{Font.END.value}"


class Theme:

    def __init__(self, h1: Style, h2: Style,
                 h3: Style, highlight: Style,
                 normal: Style, info: Style,
                 warning: Style, error: Style,
                 debug: Style, critical: Style):
        self._h1 = h1
        self._h2 = h2
        self._h3 = h3
        self._highlight = highlight
        self._normal = normal
        self._info = info
        self._warning = warning
        self._error = error
        self._debug = debug
        self._critical = critical

    def h1(self, text):
        return self._h1.apply(text)

    def h2(self, text):
        return self._h2.apply(text)

    def h3(self, text):
        return self._h3.apply(text)

    def highlight(self, text):
        return self._highlight.apply(text)

    def normal(self, text):
        return self._normal.apply(text)

    def info(self, text):
        return self._info.apply(text)

    def warning(self, text):
        return self._warning.apply(text)

    def error(self, text):
        return self._error.apply(text)

    def debug(self, text):
        return self._debug.apply(text)

    def critical(self, text):
        return self._critical.apply(text)


default_theme = Theme(
    h1=Style(Color.BLUE, [Font.BOLD], Layout(align=Layout.ALIGN_LEFT)),
    h2=Style(Color.MAGENTA, [Font.BOLD], Layout(align=Layout.ALIGN_RIGHT, num=1, char=Layout.TAB)),
    h3=Style(Color.CYAN, [Font.BOLD], Layout(align=Layout.ALIGN_RIGHT, num=2, char=Layout.TAB)),
    highlight=Style(Color.MAGENTA, [Font.HIGHLIGHT, Font.ITALIC], Layout()),
    normal=Style(Color.GREEN, [], Layout()),
    info=Style(Color.CYAN, [Font.BOLD], Layout()),
    warning=Style(Color.YELLOW, [Font.ITALIC], Layout()),
    error=Style(Color.RED, [Font.BOLD], Layout()),
    debug=Style(Color.WHITE, [Font.BOLD], Layout()),
    critical=Style(Color.RED, [Font.BOLD, Font.ITALIC], Layout())
)

if __name__ == '__main__':
    print(Font.bold("Hello, World!"))
    print(Font.un("Hello, World!"))
    print(Font.it("Hello, World!"))
    print(Font.hl("Hello, World!"))
    print(Font.cr("Hello, World!"))
    print(Font.tr("Hello, World!"))
    print(default_theme.h1("HEADER1"))
    print(default_theme.h2("HEADER2"))
    print(default_theme.h3("HEADER3"))
    print(default_theme.highlight("HIGHLIGHT"))
    print(default_theme.normal("NORMAL"))
    print(default_theme.info("INFO"))
    print(default_theme.warning("WARNING"))
    print(default_theme.error("ERROR"))
    print(default_theme.debug("DEBUG"))
    print(default_theme.critical("CRITICAL"))

