from collections.abc import Mapping
from typing import Any

def format_path(path: tuple[str, ...]) -> str:
    return ".".join(path) if path else "<root>"

class TosuDataError(Exception):
    """Base class for data lookup failures."""

    def __init__(
        self,
        path: tuple[str, ...],
        failed_at: tuple[str, ...],
        message: str,
    ) -> None:
        self.path = path
        self.failed_at = failed_at
        super().__init__(message)

class MissingPathError(TosuDataError):
    """A key needed to reach the requested value is absent."""


class InvalidStructureError(TosuDataError):
    """Traversal encountered something other than a mapping."""

_UNSET = object()
"""Default value for the `default` parameter in `TosuDataGetter.get`.

Used to indicate that no default value was provided. 
This distinguishes it from a default value of `None`."""

# getter for tosu data from tosu data dict (handles missing data warnings/errors aswell)
# It's a class because new data is processed many times in a loop, and it needs to know
# about what prior warnings/errors have occurred to handle them correctly.
class TosuDataGetter:
    def get(
        self,
        data: Mapping[str, Any],
        path: tuple[str, ...],
        *,
        default: Any = _UNSET,
    ) -> Any:
        """Look up a nested value. 
        If default is set by caller, it will be returned when a key is missing.
        Otherwise, a `MissingPathError` is raised.
        
        Raises:
            MissingPathError: If a key is missing and no default is provided.
            InvalidStructureError: If a non-mapping is encountered during traversal.
        """
        if not path:
            raise ValueError("The lookup path must not be empty.")

        # Current value we inspect as we traverse the path
        current: Any = data

        # Traverse the path. Check for missing keys and values that are not mappings.
        for index, key in enumerate(path):
            # If current is not a mapping, we cannot find `key` within it.
            if not isinstance(current, Mapping):
                location = path[:index]
                raise InvalidStructureError(
                    path,
                    location,
                    f"Cannot read {format_path(path)!r}: "
                    f"expected a mapping at {format_path(location)!r}, "
                    f"got {type(current).__name__}.",
                )

            # If it's a mapping but it doesn't contain the `key`
            if key not in current:
                if default is not _UNSET:
                    return default

                location = path[:index + 1]

                raise MissingPathError(
                    path,
                    location,
                    f"Cannot read {format_path(path)!r}: "
                    f"missing key at {format_path(location)!r}.",
                )

            current = current[key]

        return current