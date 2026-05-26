from pathlib import Path

from tree_sitter import Node


def summarize_python_symbols(path: Path) -> list[str]:
    """Extrae nombres de funciones/clases Python con tree-sitter si esta disponible."""
    import tree_sitter_python as tspython
    from tree_sitter import Language, Parser

    language = Language(tspython.language())
    parser = Parser()
    parser.language = language

    source = path.read_bytes()
    tree = parser.parse(source)
    symbols: list[str] = []

    def visit(node: Node) -> None:
        if node.type in {"function_definition", "class_definition"}:
            for child in node.children:
                if child.type == "identifier":
                    symbols.append(source[child.start_byte : child.end_byte].decode("utf-8"))
                    break
        for child in node.children:
            visit(child)

    visit(tree.root_node)
    return symbols
