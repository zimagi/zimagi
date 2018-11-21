from terminaltables import AsciiTable


def print_table(data):
    print(AsciiTable(data).table)