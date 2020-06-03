class Var:
    """
    Set string object values of class attributes as their link names.
    Pulled from https://github.com/uwinx/tamtam.py [modified]
    """
    __slots__ = "value", "prefix", "suffix"

    def __init__(self, prefix: str = "", value=None, suffix: str = "") -> None:
        self.value = value
        self.prefix = prefix
        self.suffix = suffix

    def __set_name__(self, owner, val) -> None:
        if not self.value:
            self.value = self.prefix + val + self.suffix

    def __get__(self, instance, owner) -> str:
        return self.value

    def __str__(self) -> str:
        return self.value.__str__()
