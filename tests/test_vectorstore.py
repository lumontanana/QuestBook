from questbook.vectorstore import escape_milvus_string


def test_escape_milvus_string_escapes_quotes_and_backslashes() -> None:
    assert escape_milvus_string('C:\\books\\"quoted".pdf') == 'C:\\\\books\\\\\\"quoted\\".pdf'
