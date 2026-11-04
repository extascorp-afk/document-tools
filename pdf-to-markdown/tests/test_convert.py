from my_actor.convert import table_to_markdown


def test_table_to_markdown_pads_rows_and_escapes_pipes() -> None:
    md = table_to_markdown([['A', 'B'], ['1 | x'], [None, None], ['2', ' multi\nline ']])
    assert md == '| A | B |\n| --- | --- |\n| 1 \\| x |  |\n| 2 | multi line |'


def test_table_to_markdown_empty() -> None:
    assert table_to_markdown([[None, ''], []]) == ''


if __name__ == '__main__':
    test_table_to_markdown_pads_rows_and_escapes_pipes()
    test_table_to_markdown_empty()
    print('ok')
