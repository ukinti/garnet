class Var:
    """
    Makes string from var name and sets it to var
    Pulled from https://github.com/uwinx/tamtam.py
    """

    def __init__(self, prefix: str = '', value=None, suffix: str = ''):
        self.value = value
        self.prefix = prefix
        self.suffix = suffix

    def __set_name__(self, owner, val):
        if not self.value:
            self.value = ''.join(self.prefix + val + self.suffix)

    def __get__(self, instance, owner):
        return self.value
