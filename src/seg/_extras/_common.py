from .._exceptions import SEGError

INSTRUCTIONS = """

SEG error:

    missing `{library}`

This feature requires additional dependencies:

    $ pip install seg[{extra}]

"""


def format_instructions(*, library: str, extra: str) -> str:
    return INSTRUCTIONS.format(library=library, extra=extra)


class MissingDependencyError(SEGError):
    pass
