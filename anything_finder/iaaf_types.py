from pydantic import BaseModel
from typing import Union

# https://archive.org/advancedsearch.php
MEDIA_TYPES = ["audio", "collection", "data", "image", "movies", "texts", "web"]

class Size(BaseModel):
    """A size in bytes, MB, or GB."""
    size: Union[int, str]