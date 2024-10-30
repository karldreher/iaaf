from typing import Union

from pydantic import BaseModel,computed_field

# https://archive.org/advancedsearch.php
MEDIA_TYPES = ["audio", "collection", "data", "image", "movies", "texts", "web"]


class Size(BaseModel):
    """A size in bytes, MB, or GB."""

    size: Union[int, str]

    @computed_field
    def size_in_bytes(self) -> int:
        if isinstance(self.size, int):
            return self.size
        if isinstance(self.size, str):
            size = self.size.upper()
            if size[-2:] == "MB" or size[-2:] == "GB":
                if size[-2:] == "MB":
                    return int(size[:-2]) * 1024 * 1024
                elif size[-2:] == "GB":
                    return int(size[:-2]) * 1024 * 1024 * 1024
                return int(size)
            else:
                raise ValueError("Size must be in bytes(int), MB, or GB.")
        else:
            raise ValueError("Size must be in bytes(int), MB, or GB.")