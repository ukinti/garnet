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
        >>> qb = QueryBaker("user", "action", ignore=("user",))
        >>> qb.filter(action=)
    """

    __slots__ = ("typed_args", "sep", "maxlen", "ignore", "prefix")

    def __init__(
        self,
        prefix: str,
        /,
        *args_with_factories: Iterable[Union[str, QItemT]],
        ignore: Iterable[str] = (),
        sep: str = ":",
        maxlen: int = 64,
    ) -> None:
        """
        :param prefix: unique prefix for baker
        :param args_with_factories: argument names with their factories
        :param ignore: ignored args are converted but not checked for filter
        :param sep: postback separator
        :param maxlen: max length for postback, telegram default is 64
        """
        self.prefix = prefix
        self.typed_args: List[QItemT] = []
        self.ignore: Tuple[str] = tuple(ignore)
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
        try:
            postback = self.sep.join(
                (self.prefix, *(kwargs.pop(key) for key, _ in self.typed_args),)
            )
        except KeyError as ctx:
            raise KeyError(
                f"get_checked call is missing key {ctx.args} from {self!r}"
            ) from None

        if len(postback) >= self.maxlen:
            raise ValueError(
                f"Generated is too long ({len(postback)=} >= {self.maxlen=})"
            )

        return postback

    def _get_filter(
        self, test_values: Dict[str, Any], ignore: FrozenSet[str], /,
    ):
        async def anonymous(event: ET) -> bool:
            """Fake anonymous function from QueryBaker."""
            try:
                postback: str = event.data.decode()
                prefix, data = postback.split(self.sep, maxsplit=1)
            except ValueError:
                return False

            if prefix != self.prefix:
                return False

            converted_data = self.parse(data)

            for arg, factor in self.typed_args:
                if arg in ignore:
                    continue
                if converted_data[arg] != test_values[arg]:
                    break
            else:
                Query.set(converted_data)
                return True

            return False

        return anonymous

    def filter(
        self, ignore: Iterable[str] = (), /, **non_ignored: str,
    ) -> Filter[ET]:
        """
        Get Filter instance.

        :param ignore: arguments to ignore (will extend ignore set)
        :param non_ignored: arguments to check `.filter(some=test_val)`
        """
        ignore = frozenset((*ignore, *self.ignore))

        for arg, _ in self.typed_args:
            if arg not in ignore and arg not in non_ignored:
                raise ValueError(
                    f"{arg} is declared as *required* but not passed to filter."
                )

        return Filter(self._get_filter(non_ignored, ignore))

    def parse(self, cb_data: str) -> ResultT:
        """Parse postback sent by user (actually, by telegram)."""
        res = {}

        for (name, factory), value in zip(
            self.typed_args, cb_data.split(self.sep),
        ):
            res[name] = factory(value)

        return res

    def __repr__(self) -> str:
        return f"Query(prefix='{self.prefix}') at {hex(id(self))}"
