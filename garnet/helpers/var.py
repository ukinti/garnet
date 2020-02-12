class Var:
    """
    Set string object values of class attributes as their link names.
    Pulled from https://github.com/uwinx/tamtam.py [modified]
    """

    def __init__(self, prefix: str = "", value=None, suffix: str = ""):
        self.value = value
        self.prefix = prefix
        self.suffix = suffix

    def __set_name__(self, owner, val):
        if not self.value:
            self.value = self.prefix + val + self.suffix

    def __get__(self, instance, owner):
        return self.value

    def __str__(self):
        return self.value.__str__()
