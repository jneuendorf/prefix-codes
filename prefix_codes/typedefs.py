from collections import Iterable, Generator
from typing import Literal

Bit = Literal[0, 1]
BitStream = Iterable[Bit]
BitGenerator = Generator[Bit, None, None]
