from django.conf import settings

import textwrap
import re


def split_lines(text):
    return text.split("\n")

def split_paragraphs(text):
    para_edge = re.compile(r"(\n\s*\n)", re.MULTILINE)
    return para_edge.split(text)


def wrap(text, width, init_indent = '', init_style = None, indent = '', style = None):
    wrapper = TextWrapper(width = width)
    lines = wrapper.wrap(text)
    count = len(lines)

    if count:
        header = True
        content = init_style(lines[0]) if init_style else lines[0]
        lines[0] = "{}{}".format(init_indent, content)

        if count > 1:
            for index in range(1, len(lines)):
                if header and lines[index] == '':
                    header = False
                    content = lines[index]
                else:
                    if header:
                        content = init_style(lines[index]) if init_style else lines[index]
                    else:
                        content = style(lines[index]) if style else lines[index]

                lines[index] = "{}{}".format(indent, content)

        lines[-1] = "{}\n".format(lines[-1])

    return lines

def wrap_page(text, init_indent = '', init_style = None, indent = '', style = None):
    return wrap(text, settings.DISPLAY_WIDTH, init_indent, init_style, indent, style)


class TextWrapper(textwrap.TextWrapper):

    def wrap(self, text):
        paragraphs = split_paragraphs(text)
        wrapped_lines = []

        for para in paragraphs:
            if para.isspace():
                if not self.replace_whitespace:
                    if self.expand_tabs:
                        para = para.expandtabs()

                    wrapped_lines.append(para[1:-1])
                else:
                    wrapped_lines.append('')
            else:
                wrapped_lines.extend(textwrap.TextWrapper.wrap(self, para))

        return wrapped_lines
