from typing import (
    Any,
    Callable,
    Dict,
    FrozenSet,
    Generic,
    Iterable,
    List,
    Mapping,
    Tuple,
    TypeVar,
    Union,
)

from _garnet.events.filter import Filter
from _garnet.vars.query import Query

ET = TypeVar("ET")
DefaultT = TypeVar("DefaultT")
ResultT = TypeVar("ResultT", bound=Mapping[str, str])
QItemT = Tuple[str, Callable[[str], Any]]


class QueryBaker(Generic[ResultT]):
    """
    QueryBaker or "builder" instead of "baker".
        - Generates callback query
        - Parses callback query to dict, respecting own configurations
        - Creates garnet filter to validate user-sent postback data
        - (Also manages `garnet.ctx::Query` context variable)

    Example ::

        >>> from garnet.filters import QueryBaker
        >>> qb = QueryBaker("arg", "arg1", ("not-checked-arg"), "sep", 5)
        >>>
        >>> check_completed_well = False
        >>>     try:
        ...         qb.get_checked("a" * 6)  # too long, out limit set to 5
        ...     except ValueError:
        ...         check_completed_well = True
        ...
        >>> assert check_completed_well
    """

    __slots__ = ("typed_args", "sep", "maxlen", "ignored")

    def __init__(
        self,
        *args_with_factories: Iterable[Union[str, QItemT]],
        ignored: Iterable[str] = (),
        sep: str = ":",
        maxlen: int = 64,
    ) -> None:
        """
        :param args_with_factories: argument names with their factories
        :param ignored: ignored args are converted but not checked for filter
        :param sep: postback separator
        :param maxlen: max length for postback, telegram default is 64
        """
        self.typed_args: List[QItemT] = []
        self.ignored: FrozenSet[str] = frozenset(ignored)
        self.sep = sep
        self.maxlen = maxlen

        for arg in args_with_factories:
            if isinstance(arg, str):
                self.typed_args.append((arg, str))
            elif isinstance(arg, tuple):
                name, tp = arg
                self.typed_args.append((name, tp))
            else:
                raise TypeError(
                    "Query item should be either: "
                    "tuple[str, (str,) -> T] or str, "
                    f"but got `{type(arg).__name__}`"
                )

    def get_checked(self, **kwargs: str):
        """Get checked postback string (respecting maxlen)."""
        postback = self.sep.join(kwargs.pop(key) for key, _ in self.typed_args)

        if len(postback) >= self.maxlen:
            raise ValueError(
                f"Generated is too long ({len(postback)=} >= {self.maxlen=})"
            )

        return postback

    def _get_filter(self, test_values: Dict[str, Any], /):
        async def anonymous(event: ET) -> bool:
            """Fake anonymous function from QueryBaker."""
            postback = event.data.decode()
            converted_data = self.parse(postback)

            for arg, factor in self.typed_args:
                if arg in self.ignored:
                    continue
                if converted_data[arg] != test_values[arg]:
                    break
            else:
                Query.set(converted_data)
                return True

            return False

        return anonymous

    def filter(
        self, ignore: Iterable[str] = (), /, **kwargs: str,
    ) -> Filter[ET]:
        """
        Get Filter instance.

        :param ignore: arguments to ignore (will extend ignore set)
        :param kwargs: arguments to check `.filter(some=test_val)`
        """
        ignored = frozenset((*ignore, *self.ignored))

        for arg, _ in self.typed_args:
            if arg not in ignored and arg not in kwargs:
                raise ValueError(
                    f"{arg} is declared as *required* but not passed to filter."
                )

        return Filter(self._get_filter(kwargs))

    def parse(self, cb_data: str) -> ResultT:
        """Parse postback sent by user (actually, by telegram)."""
        res = {}

        for (name, factory), value in zip(
            self.typed_args, cb_data.split(self.sep),
        ):
            res[name] = factory(value)

        return res
