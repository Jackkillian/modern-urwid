from typing import Literal, Union

from urwid import WHSettings


class SizeOptions:
    def __init__(
        self,
        wh_type: Union[
            Literal["pack", "given", "weight"], WHSettings
        ] = WHSettings.WEIGHT,
        wh_amount: Union[int, float, None] = 1,
    ):
        self.wh_type = wh_type
        self.wh_amount = wh_amount
