"""
Pure Python Gemini Watermark Remover
Reverse Alpha Blending Engine using NumPy & PIL.
Completely standalone: zero Node.js / npm dependencies, works out of the box on Windows/Mac/Linux.
"""

import os
import sys
import base64
import concurrent.futures
from typing import List, Optional, Tuple, Callable, Any
import numpy as np
from PIL import Image

# Hardcoded fallback alpha 48x48
B64_ALPHA_48 = (
    "gYAAPIGAgDuBgIA7AAAAAAAAAAAAAAAAAAAAAIGAgDsAAAAAAAAAAAAAAAAAAAAAgYCAO4GAgDsAAAAAAAAAAIGAgDuBgIA7gYCAOwAAAAAAAAAAg"
    "YCAOwAAAADj4uI+4eDgPoGAgDuBgIA7gYCAO4GAgDuBgIA7gYAAPIGAgDuBgIA7gYAAPIGAgDuBgIA7gYAAPMHAQDyBgIA7gYCAO4GAgDuBgIA7"
    "gYAAPIGAgDvBwEA8gYAAPIGAgDuBgIA7AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAgYCAO4GAgDsAAAAAAAAAAAAAAAAAAAAAAAAAAIGAgDuBgIA7"
    "gYCAOwAAAAAAAAAAAAAAAIGAgDsAAAAAgYCAO4WEBD6BgAA/gYAAP4GAAD4AAAAAgYAAPAAAAACBgIA7gYCAO4GAgDuBgIA7gYCAO4GAgDuBgAA8"
    "gYAAPIGAADyBgIA7gYCAO4GAgDuBgIA7gYCAO4GAADyBgAA8wcBAPIGAgDuBgIA7gYCAOwAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAIGAgDsAAAAAg"
    "YCAO4GAADyBgAA8gYCAOwAAAAAAAAAAgYAAPIGAgDsAAAAAAAAAAIGAgDsAAAAAgYCAO5GQkD6BgAA/gYAAP5GQkD4AAAAAgYCAOwAAAACBgIA7g"
    "YCAO4GAgDuBgAA8gYAAPAAAAACBgAA8wcBAPMHAQDyBgIA7gYCAO4GAADyBgAA8gYAAPMHAQDyBgIA7gYCAO4GAgDuBgIA7gYCAO4GAADwAAAAA"
    "AAAAAIGAgDsAAAAAAAAAAIGAgDsAAAAAgYCAO4GAgDuBgIA7gYCAO4GAgDuBgIA7gYCAO4GAgDuBgAA8gYCAO4GAgDsAAAAAgYCAO+Hg4D6BgAA/"
    "gYAAP/Hw8D4AAAAAgYCAO4GAgDuBgIA7gYAAPIGAgDuBgAA8wcBAPIGAgDuBgIA7gYAAPIGAADyBgIA7gYCAO4GAADyBgAA8gYAAPIGAgDuBgIA"
    "7gYCAO4GAADyBgAA8AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAIGAgDsAAAAAAAAAAIGAgDuBgIA7AAAAAAAAAACBgIA7AAAAAAAAAAAAAAAA"
    "AAAAAIGAgDsAAAAAgYAAPoGAAD+BgAA/gYAAP4GAAD+BgAA+AAAAAAAAAACBgIA7gYAAPAAAAACBgAA8gYAAPIGAgDuBgIA7gYCAOwAAAADBwEA8"
    "wcBAPIGAADyBgAA8gYCAO4GAgDuBgIA7gYCAO4GAgDuBgIA7AAAAAIGAADwAAAAAAAAAAIGAgDsAAAAAgYCAO4GAgDuBgIA7gYCAOwAAAAAAAAAA"
    "gYCAOwAAAAAAAAAAAAAAAAAAAACBgIA7AAAAAAAAAACBgIA7oaCgPoGAAD+BgAA/gYAAP4GAAD/BwMA+AAAAAAAAAACBgIA7AAAAAIGAgDuBgAA8"
    "gYAAPAAAAACBgIA7gYCAO4GAgDuBgAA8wcBAPMHAQDzBwEA8gYCAO4GAgDsAAAAAAAAAAIGAgDuBgIA7gYCAOwAAAAAAAAAAAAAAAIGAgDsAAAAA"
    "wcBAPIGAgDuBgIA7gYCAOwAAAAAAAAAAgYCAO4GAgDuBgIA7gYAAPIGAADwAAAAAAAAAAIGAADyJiIg9gYAAP4GAAD+BgAA/gYAAP4GAAD+BgAA/"
    "gYCAPQAAAACBgIA7AAAAAAAAAAAAAAAAgYCAO4GAADyBgAA8gYCAO4GAgDuBgIA7gYCAO4GAgDuBgIA7gYCAO4GAgDuBgIA7gYCAO4GAgDuBgIA"
    "7AAAAAAAAAAAAAAAAAAAAAIGAADwAAAAAgYCAO4GAADyBgIA7gYCAOwAAAAAAAAAAgYCAO8HAQDyBgIA7gYCAO4GAgDsAAAAAgYCAO4GAgDuhoKA"
    "+gYAAP4GAAD+BgAA/gYAAP4GAAD+BgAA/o6KiPoGAgDuBgAA8AAAAAIGAgDuBgIA7gYCAO8HAQDyBgAA8gYCAO4GAgDuBgAA8gYAAPIGAgDuBgI"
    "A7gYCAO4GAgDuBgIA7gYCAO4GAgDuBgIA7gYAAPAAAAAAAAAAAgYCAO4GAADyBgIA7gYAAPIGAgDuBgIA7gYAAPIGAADyBgIA7gYCAO4GAgDuBg"
    "AA8gYCAO4GAADyBgAA8gYCAO4mIiD2BgAA/gYAAP4GAAD+CgQE/gYAAP4GAAD+BgAA/gYAAP4GAAD6BgAA8gYCAO4GAADwAAAAAgYCAO4GAADy"
    "BgIA7wcBAPIGAADyBgAA8wcBAPMHAQDzBwEA8gYAAPIGAADyBgIA7gYCAO4GAADyBgAA8gYCAOwAAAAAAAAAAgYCAO4GAgDuBgIA7AAAAAIGAAD"
    "yBgIA7AAAAAIGAgDuBgIA7AAAAAIGAgDsAAAAAgYCAOwAAAACBgIA7gYCAO+Hg4D6BgAA/gYAAP4GAAD+BgAA/gYAAP4GAAD+BgAA/gYAAP8HAw"
    "D6BgIA7gYCAO4GAgDuBgIA7gYCAO4GAgDuBgIA7gYCAO4GAgDvBwEA8wcBAPMHAQDyBgAA8wcBAPIGAADyBgIA7gYCAO4GAADyBgAA8gYAAPIG"
    "AgDsAAAAAAAAAAIGAgDuBgAA8AAAAAIGAgDuBgIA7AAAAAAAAAAAAAAAAgYAAPIGAgDuBgIA7gYAAPAAAAACBgIA7gYCAPoGAAD+BgAA/gYAAP4G"
    "AAD+BgAA/gYAAP4GAAD+BgAA/gYAAP4GAAD/h4GA+AAAAAAAAAACBgAA8gYAAPMHAQDyBgIA7gYAAPIGAADyBgIA7gYAAPIGAADyBgAA8gYCAO4"
    "GAgDuBgAA8gYAAPIGAgDuBgIA7AAAAAAAAAACBgIA7AAAAAAAAAACBgIA7gYCAO8HAQDwAAAAAgYCAO4GAADwAAAAAgYAAPAAAAACBgAA8gYCAOw"
    "AAAACBgIA9gYAAP4GAAD+BgAA/gYAAP4GAAD+BgAA/gYAAP4GAAD+BgAA/gYAAP4GAAD/x8PA+wcDAPYGAgDuBgAA8wcBAPIGAADyBgAA8gYAAP"
    "IGAADwAAAAAgYCAO4GAgDuBgIA7gYCAO4GAADyBgAA8gYAAPIGAgDuBgIA7gYCAOwAAAACBgIA7gYCAOwAAAAAAAAAAAAAAAIGAgDsAAAAAgYCAO"
    "4GAgDuBgIA7AAAAAMHAQDyBgAA8gYCAO4GAgD3h4OA+gYAAP4GAAD+BgAA/gYAAP4GAAD+BgAA/gYAAP4GAAD+BgAA/gYAAP4GAAD+BgAA/4eD"
    "gPoGAAD2BgIA7gYCAOwAAAACBgIA7gYCAO4GAgDuBgAA8gYAAPIGAgDuBgIA7gYAAPIGAADyBgAA8gYAAPIGAgDuBgAA8gYCAOwAAAACBgIA7AA"
    "AAAAAAAACBgIA7AAAAAIGAgDsAAAAAgYCAOwAAAACBgIA7gYCAO4GAgDuBgIA7gYCAO9PS0j6BgAA/gYAAP4GAAD+BgAA/gYAAP4GAAD+BgAA/g"
    "YAAP4GAAD+BgAA/gYAAP4GAAD+BgAA/gYAAP8HAwD6BgAA8gYCAO4GAgDuBgIA7gYCAO4GAgDuBgAA8gYAAPIGAgDuBgIA7gYAAPIGAADyBgAA8"
    "gYAAPIGAgDuBgAA8gYCAO4GAgDuBgIA7AAAAAAAAAACBgIA7AAAAAAAAAAAAAAAAAAAAAIGAgDsAAAAAgYAAPIGAgDuBgIA7o6KiPoGAAD+BgAA/g"
    "YAAP4GAAD+BgAA/gYAAP4GAAD+BgAA/gYAAP4GAAD+BgAA/gYAAP4GAAD+BgAA/gYAAP4GAAD+hoKA+gYCAOwAAAACBgIA7gYCAO4GAgDvBwEA8"
    "gYCAO4GAgDuBgIA7gYCAO4GAADyBgAA8gYAAPIGAgDuBgIA7AAAAAAAAAAAAAAAAgYCAO4GAgDsAAAAAAAAAAIGAgDsAAAAAgYCAOwAAAAAAAAAA"
    "gYCAO4GAgDuhoKA+gYAAP4GAAD+BgAA/gYAAP4GAAD+BgAA/gYAAP4GAAD+BgAA/gYAAP4GAAD+BgAA/gYAAP4GAAD+BgAA/gYAAP4GAAD+BgAA"
    "/oaCgPgAAAACBgIA7gYCAO4GAgDvBwEA8gYCAO4GAgDuBgIA7gYCAO4GAgDuBgAA8gYAAPIGAgDuBgIA7AAAAAIGAADwAAAAAgYCAO4GAgDsAAA"
    "AAAAAAAIGAgDsAAAAAAAAAAAAAAACBgIA7gYAAPcHAwD6BgAA/gYAAP4GAAD+BgAA/goEBP4GAAD+BgAA/gYAAP4GAAD+BgAA/gYAAP4GAAD+Bg"
    "AA/gYAAP4GAAD+BgAA/gYAAP4GAAD+BgAA/gYAAP9HQ0D6BgIA9gYAAPIGAADyBgIA7gYCAO4GAgDuBgIA7wcBAPIGAgDzBwEA8gYAAPAAAAACB"
    "gIA7gYCAOwAAAACBgIA7gYCAOwAAAACBgIA7gYCAO4GAgDuBgIA7AAAAAAAAAADBwMA94eDgPoGAAD+BgAA/gYAAP4GAAD+BgAA/goEBP4GAAD+"
    "BgAA/gYAAP4GAAD+BgAA/gYAAP4GAAD+BgAA/gYAAP4GAAD+BgAA/gYAAP4GAAD+BgAA/gYAAP4GAAD/h4OA+iYiIPYGAgDyBgAA8gYCAO4GAgD"
    "uBgIA7gYAAPIGAgDuBgAA8gYAAPIGAgDuBgIA7gYCAOwAAAAAAAAAAgYCAO4GAgDsAAAAAAAAAAIGAgDsAAAAAAAAAAOHgYD7x8PA+gYAAP4GAAD"
    "+BgAA/gYAAP4GAAD+BgAA/gYAAP4GAAD+BgAA/gYAAP4GAAD+BgAA/gYAAP4GAAD+BgAA/gYAAP4GAAD+BgAA/gYAAP4GAAD+BgAA/gYAAP4GA"
    "AD+BgAA/gYAAP4WEhD6BgIA7gYCAO4GAADzBwEA8gYAAPMHAQDzBwEA8gYCAO4GAgDsAAAAAgYAAPIGAgDsAAAAAgYCAOwAAAAAAAAAAgYAAPIG"
    "AgDuBgAA+wcDAPoGAAD+BgAA/gYAAP4GAAD+BgAA/gYAAP4GAAD+BgAA/gYAAP4GAAD+BgAA/gYAAP4GAAD+BgAA/gYAAP4GAAD+BgAA/gYAAP4"
    "GAAD+BgAA/gYAAP4GAAD+BgAA/gYAAP4GAAD+BgAA/gYAAP4GAAD/h4OA+gYCAPYGAADzBwEA8gYAAPIGAADyBgAA8gYAAPIGAgDuBgIA7AAAAA"
    "IGAgDsAAAAAAAAAAAAAAAAAAAAAgYCAPaOioj6BgAA/gYAAP4GAAD+BgAA/gYAAP4GAAD+BgAA/gYAAP4GAAD+BgAA/gYAAP4GAAD+BgAA/gYAAP"
    "4GAAD+BgAA/gYAAP4GAAD+BgAA/gYAAP4GAAD+BgAA/goEBP4GAAD+BgAA/gYAAP4GAAD+BgAA/gYAAP4GAAD+BgAA/gYAAP6GgoD6BgIA9gYAA"
    "PIGAgDuBgAA8gYAAPIGAgDuBgIA7AAAAAIGAgDsAAAAAgYCAO4WEBD7BwMA+gYAAP4GAAD+BgAA/gYAAP4GAAD+BgAA/goEBP4GAAD+BgAA/gYAA"
    "P4GAAD+BgAA/gYAAP4GAAD+BgAA/gYAAP4GAAD+BgAA/gYAAP4GAAD+BgAA/gYAAP4GAAD+BgAA/gYAAP4GAAD+BgAA/gYAAP4GAAD+BgAA/gYA"
    "AP4GAAD+BgAA/gYAAP4GAAD+hoKA+gYAAD6BgIA7gYAAPIGAgDuBgIA7AAAAAIGAAD6RkJA+8fDwPoGAAD+BgAA/gYAAP4GAAD+BgAA/gYAAP4G"
    "AAD+BgAA/gYAAP4GAAD+BgAA/gYAAP4GAAD+BgAA/gYAAP4GAAD+BgAA/gYAAP4GAAD+BgAA/gYAAP4GAAD+BgAA/gYAAP4GAAD+BgAA/gYAAP4"
    "GAAD+BgAA/gYAAP4GAAD+BgAA/gYAAP4GAAD+BgAA/gYAAP4GAAD+BgAA/gYAAP4GAAD/h4OA+kZCQPoGAAD6BgIA84eDgPoGAAD+BgAA/gYAAP"
    "4GAAD+BgAA/gYAAP4GAAD+BgAA/gYAAP4GAAD+BgAA/gYAAP4GAAD+BgAA/gYAAP4GAAD+BgAA/gYAAP4GAAD+BgAA/gYAAP4GAAD+BgAA/gYAA"
    "P4GAAD+BgAA/gYAAP4GAAD+BgAA/gYAAP4GAAD+BgAA/gYAAP4GAAD+BgAA/gYAAP4GAAD+BgAA/gYAAP4GAAD+BgAA/gYAAP4GAAD+BgAA/4+L"
    "iPuHg4D6BgAA/gYAAP4GAAD+BgAA/gYAAP4GAAD+BgAA/gYAAP4GAAD+BgAA/gYAAP4GAAD+BgAA/gYAAP4GAAD+BgAA/gYAAP4GAAD+BgAA/gY"
    "AAP4GAAD+BgAA/gYAAP4GAAD+BgAA/gYAAP4GAAD+BgAA/gYAAP4GAAD+BgAA/gYAAP4GAAD+BgAA/gYAAP4GAAD+BgAA/gYAAP4GAAD+BgAA/g"
    "YAAP4GAAD+BgAA/4eDgPoGAgDuBgAA+kZCQPuHg4D6BgAA/gYAAP4GAAD+BgAA/gYAAP4GAAD+BgAA/gYAAP4GAAD+BgAA/gYAAP4GAAD+BgAA/g"
    "YAAP4GAAD+BgAA/gYAAP4GAAD+BgAA/gYAAP4GAAD+BgAA/gYAAP4GAAD+BgAA/gYAAP4GAAD+BgAA/gYAAP4GAAD+BgAA/gYAAP4GAAD+BgAA/g"
    "YAAP4GAAD+BgAA/gYAAP/Hw8D6RkJA+gYAAPoGAgDuBgIA7wcBAPAAAAACBgIA7gYAAPqGgoD6BgAA/gYAAP4GAAD+BgAA/gYAAP4GAAD+BgAA/g"
    "YAAP4GAAD+BgAA/gYAAP4GAAD+BgAA/gYAAP4GAAD+BgAA/gYAAP4GAAD+BgAA/gYAAP4GAAD+BgAA/gYAAP4GAAD+BgAA/gYAAP4GAAD+BgAA/g"
    "YAAP4GAAD+BgAA/gYAAP4GAAD+BgAA/wcDAPoGAAD6BgAA8gYAAPIGAgDuBgIA7AAAAAIGAgDuBgIA7AAAAAAAAAACBgAA8gYCAPaOioj6BgAA/g"
    "YAAP4GAAD+BgAA/goEBP4GAAD+BgAA/gYAAP4GAAD+BgAA/gYAAP4GAAD+BgAA/gYAAP4GAAD+BgAA/gYAAP4KBAT+BgAA/gYAAP4GAAD+BgAA/g"
    "YAAP4GAAD+BgAA/gYAAP4GAAD+BgAA/gYAAP4GAAD+BgAA/o6KiPomIiD2BgIA7gYCAO4GAADyBgAA8gYCAO4GAgDuBgIA7gYAAPIGAgDuBgIA7"
    "AAAAAIGAgDsAAAAAAAAAAIGAgDuBgAA8gYCAPeHg4D6BgAA/gYAAP4GAAD+BgAA/gYAAP4GAAD+BgAA/gYAAP4GAAD+BgAA/gYAAP4GAAD+BgAA/"
    "gYAAP4GAAD+BgAA/gYAAP4GAAD+BgAA/gYAAP4GAAD+BgAA/gYAAP4GAAD+BgAA/gYAAP4GAAD/BwMA+gYAAPoGAgDuBgIA7gYCAO4GAgDuBgIA"
    "7gYCAO4GAgDuBgIA7gYCAO4GAgDuBgIA7gYCAOwAAAAAAAAAAAAAAAIGAgDsAAAAAgYCAO4GAgD6BgAA/gYAAP4GAAD+BgAA/gYAAP4GAAD+BgAA"
    "/gYAAP4GAAD+BgAA/gYAAP4GAAD+BgAA/gYAAP4GAAD+BgAA/gYAAP4GAAD+BgAA/gYAAP4GAAD+BgAA/gYAAP4GAAD/z8vI+5eRkPoGAgDuBgI"
    "A7gYCAO4GAgDuBgIA7gYCAO4GAgDuBgIA7gYCAO4GAgDsAAAAAgYCAOwAAAACBgIA7AAAAAAAAAAAAAAAAgYAAPAAAAACBgIA94+LiPoGAAD+BgAA"
    "/gYAAP4GAAD+BgAA/gYAAP4GAAD+CgQE/gYAAP4GAAD+BgAA/gYAAP4GAAD+BgAA/gYAAP4GAAD+BgAA/gYAAP4GAAD+BgAA/gYAAP+Hg4D7BwMA"
    "9gYCAO4GAgDuBgIA7gYAAPIGAADyBgIA7gYCAO4GAADyBgAA8gYCAO4GAgDuBgIA7gYCAOwAAAACBgIA7AAAAAIGAgDsAAAAAAAAAAAAAAAAAAAA"
    "AgYCAPdHQ0D6BgAA/gYAAP4GAAD+BgAA/gYAAP4GAAD+BgAA/gYAAP4GAAD+BgAA/gYAAP4GAAD+BgAA/gYAAP4GAAD+BgAA/gYAAP4GAAD+BgAA"
    "/wcDAPoGAAD2BgIA7gYCAO4GAgDuBgIA7gYAAPIGAADyBgIA7gYCAO4GAADyBgAA8gYCAO4GAgDuBgIA7gYCAO4GAgDuBgIA7gYAAPIGAgDuBgI"
    "A7gYCAOwAAAAAAAAAAAAAAAAAAAAAgYCAO4GAgDuhoKA+gYAAP4GAAD+BgAA/gYAAP4GAAD+BgAA/goEBP4GAAD+BgAA/gYAAP4GAAD+BgAA/gYA"
    "AP4KBAT+CgQE/gYAAP4GAAD+BgAA/oaCgPsHAQDzBwEA8gYAAPIGAgDuBgAA8gYAAPIGAgDuBgIA7wcBAPMHAQDyBgAA8gYAAPIGAgDsAAAAAgYC"
    "AO4GAgDsAAAAAgYCAO4GAgDuBgIA7gYCAOwAAAAAAAAAAAAAAAAAAAACBgIA7gYCAO4GAADyBgIA7oaCgPoGAAD+BgAA/goEBP4GAAD+BgAA/goE"
    "BP4GAAD+BgAA/gYAAP4GAAD+BgAA/gYAAP4KBAT+CgQE/gYAAP4GAAD+hoKA+gYCAO4GAgDyBgIA8gYAAPIGAADyBgAA8gYAAPIGAgDuBgIA7wcB"
    "APMHAQDyBgIA7gYAAPIGAgDuBgIA7gYCAO4GAgDuBgAA8gYAAPIGAgDuBgAA8wcBAPMHAQDyBgAA8gYAAPIGAADyBgAA8gYCAO4GAgDuBgIA7gYC"
    "AO8PCwj6BgAA/gYAAP4GAAD+BgAA/gYAAP4GAAD+BgAA/gYAAP4GAAD+BgAA/gYAAP4GAAD+BgAA/gYAAP9HQ0D6BgAA8gYAAPMHAQDzBwEA8gYC"
    "AOwAAAACBgIA7gYAAPIGAADyBgAA8wcBAPMHAQDyBgIA7gYCAO8HAQDzBwEA8gYCAO4GAgDuBgAA8gYAAPIGAgDuBgIA7gYCAPMHAQDyBgAA8wcB"
    "APIGAADzBwEA8gYCAO4GAgDuBgIA7gYCAO6GgID3j4uI+gYAAP4GAAD+BgAA/gYAAP4GAAD+BgAA/goEBP4GAAD+BgAA/gYAAP4GAAD+BgAA/4eD"
    "gPoGAgD2BgAA8wcBAPMHAQDzBwEA8gYCAO4GAgDuBgIA7gYAAPIGAADyBgAA8gYCAPMHAQDwAAAAAgYCAO8HAQDzBwEA8gYAAPIGAADyBgAA8gYC"
    "AO4GAADyBgAA8AAAAAAAAAACBgAA8wcBAPIGAADzBwEA8gYAAPIGAADwAAAAAgYCAO4GAADzJyMg98fDwPoGAAD+BgAA/gYAAP4GAAD+BgAA/gYA"
    "AP4GAAD+BgAA/gYAAP4GAAD+BgAA/gYCAPQAAAACBgAA8gYAAPAAAAAAAAAAAgYCAO4GAgDuBgAA8wcBAPIGAADyBgIA7AAAAAAAAAACBgIA7gYC"
    "AO4GAgDuBgIA7gYAAPIGAADyBgAA8gYAAPMHAQDyBgAA8gYCAO4GAgDuBgAA8gYAAPIGAADyBgAA8gYAAPIGAADyBgIA7gYCAO4GAADyBgAA84eB"
    "gPoGAAD+BgAA/gYAAP4GAAD+BgAA/gYAAP4GAAD+BgAA/gYAAP4GAAD+BgIA+gYCAO4GAgDvBwEA8gYAAPIGAgDsAAAAAgYCAO4GAgDvBwEA8wcB"
    "APIGAgDuBgAA8gYCAOwAAAAAAAAAAAAAAAIGAgDuBgIA7gYAAPIGAgDuBgIA7gYCAO4GAgDuBgIA7gYCAO4GAgDuBgIA7gYCAO4GAgDuBgIA7AAA"
    "AAIGAgDuBgAA8gYAAPIGAADyBgAA8AAAAAMHAwD6BgAA/gYAAP4GAAD+BgAA/gYAAP4GAAD+BgAA/gYAAP+Hg4D6BgIA7gYCAO4GAgDuBgAA8gYA"
    "APAAAAACBgAA8gYCAO4GAgDuBgAA8gYCAO4GAgDsAAAAAgYCAOwAAAAAAAAAAgYCAO4GAgDuBgIA7gYAAPIGAADyBgIA7gYCAO4GAgDuBgIA7gYC"
    "AO4GAgDuBgIA7gYCAO4GAgDuBgIA7gYCAO4GAgDuBgAA8gYAAPMHAQDyBgAA8gYCAO4GAAD6BgAA/gYAAP4GAAD+BgAA/gYAAP4GAAD+BgAA/gYA"
    "AP4GAgD2BgIA7gYCAOwAAAACBgAA8gYAAPIGAgDuBgAA8gYCAO4GAgDuBgIA7gYCAO4GAgDuBgAA8gYCAO4GAgDuBgIA7gYCAO4GAgDuBgIA7gYC"
    "AO4GAgDuBgIA7gYCAO4GAgDuBgIA7gYCAO4GAgDuBgAA8gYAAPAAAAAAAAAAAgYCAOwAAAACBgAA8gYAAPIGAADyBgIA7gYCAOwAAAAChoKA+gYA"
    "AP4GAAD+BgAA/gYAAP4GAAD+BgAA/oaCgPoGAgDuBgIA7gYCAO4GAgDuBgAA8wcBAPAAAAACBgIA7gYCAO4GAgDuBgIA7gYCAO4GAgDuBgIA7gYA"
    "APIGAADyBgIA7gYCAO4GAgDuBgIA7gYCAO4GAgDuBgIA7gYCAO4GAgDuBgIA7gYCAO4GAgDuBgAA8gYAAPAAAAACBgIA7gYCAO4GAADyBgAA8gYA"
    "APIGAgDuBgIA7AAAAAIGAgDuBgIA9gYAAP4GAAD+BgAA/gYAAP4GAAD+BgAA/gYCAPYGAgDuBgIA7gYCAO4GAgDuBgAA8gYAAPIGAADyBgIA7gYC"
    "AO4GAgDuBgIA7gYCAO4GAgDuBgIA7gYAAPIGAADyBgIA7gYCAO4GAgDuBgIA7gYAAPIGAADyBgAA8gYAAPIGAADyBgAA8gYCAO4GAgDuBgIA7gYA"
    "APIGAgDuBgIA7gYCAO4GAADyBgAA8gYCAO4GAgDuBgIA7gYCAO4GAgDsAAAAAw8LCPoKBAT+CgQE/gYAAP4GAAD+hoKA+gYCAO4GAADyBgAA8gYA"
    "APIGAgDuBgIA7gYCAO4GAgDuBgIA7gYAAPIGAADyBgIA7gYCAO4GAgDuBgIA7gYCAO4GAgDuBgAA8gYAAPIGAgDuBgIA7gYAAPIGAADyBgAA8gYA"
    "APIGAADyBgAA8gYCAO4GAgDuBgIA7gYCAO4GAgDsAAAAAgYAAPIGAADyBgIA7AAAAAIGAgDuBgIA7gYAAPMHAQDyBgIA7gYAAPoKBAT+BgAA/gYA"
    "AP4GAAD+BgAA+gYCAO4GAADyBgAA8AAAAAIGAgDuBgIA7gYCAO4GAgDuBgIA7gYAAPIGAADyBgIA7gYCAO4GAgDuBgIA7gYCAO4GAgDuBgAA8gYA"
    "APIGAgDuBgIA7gYAAPIGAADyBgAA8gYAAPIGAgDuBgIA7gYAAPIGAgDuBgIA7gYCAO4GAgDuBgIA7gYAAPIGAADyBgAA8gYAAPAAAAAAAAAAAgYA"
    "APIGAADyBgIA7gYCAO/Py8j6BgAA/gYAAP+Hg4D6BgIA7gYCAO4GAADzBwEA8gYCAO4GAgDuBgAA8gYAAPAAAAAAAAAAAgYCAO4GAgDuBgIA7gYC"
    "AO4GAgDuBgIA7gYCAO4GAgDuBgAA8gYAAPIGAgDuBgIA7gYAAPIGAADyBgAA8gYAAPIGAgDsAAAAAgYAAPIGAADyBgIA7gYCAO4GAgDuBgIA7gYA"
    "APIGAADyBgAA8gYAAPIGAgDuBgIA7gYAAPIGAADyBgIA7gYCAO5OSkj6BgAA/gYAAP5OSkj6BgIA7gYCAO4GAADyBgAA8gYCAO4GAgDuBgIA7gYA"
    "APIGAgDuBgIA7gYCAO4GAgDuBgIA7gYCAO4GAgDuBgIA7gYCAO4GAgDuBgAA8gYAAPIGAgDuBgIA7gYCAO4GAgDuBgIA7gYCAO4GAADyBgAA8gYC"
    "AO4GAgDuBgAA8gYCAO4GAADyBgIA7AAAAAIGAgDvBwEA8wcBAPIGAgDsAAAAAgYCAO4GAgDuBgAA8gYAAPIGAAD6BgAA/gYAAP4WEBD6BgIA7gYC"
    "AO4GAADyBgAA8gYAAPIGAADwAAAAAgYCAOwAAAACBgIA7gYAAPIGAADyBgIA7gYCAO4GAADyBgAA8gYCAO4GAgDuBgAA8gYAAPIGAgDuBgIA7gYC"
    "AO4GAgDuBgIA7gYCAO4GAADyBgAA8gYCAO4GAgDuBgIA7AAAAAIGAgDuBgIA7gYCAO4GAgDuBgIA7gYAAPIGAgDuBgIA7gYCAOwAAAADBwEA8gYA"
    "APIGAgDvh4OA+4eDgPoGAgDuBgIA7gYCAO4GAADyBgAA8gYAAPIGAADyBgIA7AAAAAIGAgDsAAAAAgYAAPIGAADyBgIA7gYCAO4GAADyBgAA8gYC"
    "AO4GAgDuBgAA8gYAAPIGAgDuBgIA7"
)

_CACHED_MAPS = {}

def find_alpha_maps_npz() -> Optional[str]:
    """Locate assets/gemini_alpha_maps.npz across source and PyInstaller environments (Windows & macOS)."""
    candidates = []
    if getattr(sys, 'frozen', False):
        meipass = getattr(sys, '_MEIPASS', '')
        if meipass:
            candidates.append(os.path.join(meipass, 'assets', 'gemini_alpha_maps.npz'))
        exe_dir = os.path.dirname(sys.executable)
        candidates.append(os.path.join(exe_dir, 'assets', 'gemini_alpha_maps.npz'))
        # macOS App bundle structure: AutoCapCut.app/Contents/MacOS/AutoCapCut
        candidates.append(os.path.join(exe_dir, '..', 'Resources', 'assets', 'gemini_alpha_maps.npz'))
        candidates.append(os.path.join(exe_dir, '..', 'Resources', 'gemini_alpha_maps.npz'))
        candidates.append(os.path.join(exe_dir, '..', 'Frameworks', 'assets', 'gemini_alpha_maps.npz'))

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    candidates.append(os.path.join(base_dir, 'assets', 'gemini_alpha_maps.npz'))
    candidates.append(os.path.join('assets', 'gemini_alpha_maps.npz'))

    for c in candidates:
        if os.path.isfile(c):
            return c
    return None


def _init_alpha_maps():
    global _CACHED_MAPS
    if _CACHED_MAPS:
        return _CACHED_MAPS

    # 1. Try loading from assets/gemini_alpha_maps.npz
    npz_path = find_alpha_maps_npz()
    if npz_path:
        try:
            with np.load(npz_path) as data:
                _CACHED_MAPS[48] = data['alpha48']
                _CACHED_MAPS[96] = data['alpha96']
                _CACHED_MAPS['96-20260520'] = data['alpha96_v2']
                _CACHED_MAPS['36-v2'] = data['alpha36']
                return _CACHED_MAPS
        except Exception:
            pass

    # 2. Hardcoded fallback for 48x48
    b48 = base64.b64decode(B64_ALPHA_48)
    alpha48 = np.frombuffer(b48, dtype=np.float32).reshape((48, 48))
    _CACHED_MAPS[48] = alpha48

    # 3. Interpolate 96x96 if npz missing
    im = Image.fromarray(alpha48)
    im96 = im.resize((96, 96), Image.Resampling.BICUBIC)
    _CACHED_MAPS[96] = np.array(im96, dtype=np.float32)

    return _CACHED_MAPS


def get_alpha_map(size: int = 96) -> np.ndarray:
    maps = _init_alpha_maps()
    return maps.get(size, maps.get(96 if size >= 64 else 48))


def _compute_ncc(gray_roi: np.ndarray, alpha_map: np.ndarray) -> float:
    """Calculate Normalized Cross-Correlation (NCC) between image ROI and alpha template."""
    a = gray_roi.flatten().astype(np.float32)
    b = alpha_map.flatten().astype(np.float32)
    a = a - a.mean()
    b = b - b.mean()
    std_a = np.std(a)
    std_b = np.std(b)
    if std_a < 1e-6 or std_b < 1e-6:
        return 0.0
    return float(np.dot(a, b) / (len(a) * std_a * std_b))


def detect_watermark_position(width: int, height: int, gray_img: Optional[np.ndarray] = None) -> Tuple[int, int, int, np.ndarray]:
    """
    Detect the exact watermark position (x, y, size, alpha_map).
    Uses size-based priors combined with NCC template matching if image data is provided.
    """
    # 1. Determine standard configuration
    if width > 1024 and height > 1024:
        primary_size = 96
        primary_margin = 64
    else:
        primary_size = 48
        primary_margin = 32

    # Known official fixed variants from GargantuaX/geminiSizeCatalog
    KNOWN_FIXED_CONFIGS = {
        '1376x768': (48, 73, 73),
        '768x1376': (48, 73, 73),
        '1408x768': (48, 32, 32),
        '2752x1536': (48, 89, 89),
        '2816x1536': (96, 64, 64),
    }

    size_key = f"{width}x{height}"
    if size_key in KNOWN_FIXED_CONFIGS:
        fixed_size, fixed_mr, fixed_mb = KNOWN_FIXED_CONFIGS[size_key]
        primary_size = fixed_size
        primary_margin = fixed_mr

    primary_alpha = get_alpha_map(primary_size)
    px = width - primary_margin - primary_size
    py = height - primary_margin - primary_size

    if gray_img is None:
        return px, py, primary_size, primary_alpha

    # 2. Candidate evaluation using NCC
    candidates = [
        (primary_size, primary_margin, primary_margin, primary_alpha),
        (48, 73, 73, get_alpha_map(48)),
        (48, 32, 32, get_alpha_map(48)),
        (48, 96, 96, get_alpha_map(48)),
        (96, 64, 64, get_alpha_map(96)),
        (96, 192, 192, get_alpha_map(96)),
    ]

    best_cand = candidates[0]
    best_score = -1.0

    for size, mr, mb, alpha in candidates:
        cx = width - mr - size
        cy = height - mb - size
        if cx < 0 or cy < 0 or cx + size > width or cy + size > height:
            continue
        roi = gray_img[cy:cy+size, cx:cx+size]
        score = _compute_ncc(roi, alpha)
        if score > best_score:
            best_score = score
            best_cand = (size, mr, mb, alpha)

    # If best candidate is strong (NCC > 0.20), use it; otherwise fallback to primary
    if best_score >= 0.20:
        c_size, c_mr, c_mb, c_alpha = best_cand
        return width - c_mr - c_size, height - c_mb - c_size, c_size, c_alpha

    return px, py, primary_size, primary_alpha


def remove_watermark_array(
    img_np: np.ndarray,
    alpha_map: np.ndarray,
    x: int,
    y: int,
    alpha_gain: float = 1.0,
    logo_value: float = 255.0
) -> np.ndarray:
    """
    Remove watermark using Reverse Alpha Blending:
    watermarked = alpha * logo + (1 - alpha) * original
    original = (watermarked - alpha * logo) / (1 - alpha)
    """
    h, w = alpha_map.shape
    img_h, img_w, _ = img_np.shape

    if x < 0 or y < 0 or x + w > img_w or y + h > img_h:
        return img_np

    ALPHA_NOISE_FLOOR = 3.0 / 255.0
    ALPHA_THRESHOLD = 0.002
    MAX_ALPHA = 0.99

    alpha_mag = np.abs(alpha_map)
    signal_alpha = np.maximum(0.0, alpha_mag - ALPHA_NOISE_FLOOR) * alpha_gain
    active_mask = signal_alpha >= ALPHA_THRESHOLD

    alpha = np.minimum(alpha_mag * alpha_gain, MAX_ALPHA)
    one_minus_alpha = 1.0 - alpha

    roi = img_np[y:y+h, x:x+w, :3].astype(np.float32)
    alpha_3d = alpha[:, :, np.newaxis]
    one_minus_alpha_3d = one_minus_alpha[:, :, np.newaxis]
    mask_3d = active_mask[:, :, np.newaxis]

    restored_roi = (roi - alpha_3d * logo_value) / one_minus_alpha_3d
    restored_roi = np.clip(np.round(restored_roi), 0, 255).astype(np.uint8)

    orig_roi = img_np[y:y+h, x:x+w, :3]
    img_np[y:y+h, x:x+w, :3] = np.where(mask_3d, restored_roi, orig_roi)
    return img_np


def clean_image(input_path: str, output_path: str, overwrite: bool = True) -> bool:
    """
    Clean Gemini watermark from an image file and save to output_path.
    Returns True if successfully processed, False otherwise.
    """
    try:
        if not overwrite and os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            return True

        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        with Image.open(input_path) as im:
            has_alpha = im.mode in ('RGBA', 'LA') or (im.mode == 'P' and 'transparency' in im.info)
            work_im = im.convert('RGBA') if has_alpha else im.convert('RGB')
            w, h = work_im.size

            # Fast grayscale for candidate matching
            gray = np.array(work_im.convert('L'))
            x, y, size, alpha_map = detect_watermark_position(w, h, gray)

            arr = np.array(work_im)
            cleaned_arr = remove_watermark_array(arr, alpha_map, x, y)
            cleaned_im = Image.fromarray(cleaned_arr, mode=work_im.mode)

            ext = os.path.splitext(output_path)[1].lower()
            if ext in {'.jpg', '.jpeg'}:
                if cleaned_im.mode != 'RGB':
                    cleaned_im = cleaned_im.convert('RGB')
                cleaned_im.save(output_path, 'JPEG', quality=95, optimize=True)
            elif ext == '.webp':
                cleaned_im.save(output_path, 'WEBP', quality=95)
            elif ext == '.png':
                cleaned_im.save(output_path, 'PNG', optimize=True)
            else:
                cleaned_im.save(output_path)

        return True
    except Exception as e:
        print(f"[GeminiRemoverPy] Failed on {input_path}: {e}")
        return False


def batch_clean_images(
    image_paths: List[str],
    output_cache_dir: str,
    progress_callback: Optional[Callable[[str, float], None]] = None,
    overwrite: bool = True,
    max_workers: int = 4,
    cancel_event: Optional[Any] = None
) -> List[str]:
    """
    Batch clean Gemini watermarks from multiple images using multithreaded Python workers.
    Returns list of cleaned image paths.
    """
    os.makedirs(output_cache_dir, exist_ok=True)
    tasks = []
    cleaned_paths = []

    for p in image_paths:
        ext = os.path.splitext(p)[1].lower()
        if ext in {'.jpg', '.jpeg', '.png', '.webp', '.bmp'}:
            out_p = os.path.join(output_cache_dir, f"clean_{os.path.basename(p)}")
            cleaned_paths.append(out_p)
            tasks.append((p, out_p))
        else:
            cleaned_paths.append(p)

    if not tasks:
        return cleaned_paths

    total = len(tasks)
    completed = 0

    def worker(task):
        if cancel_event and cancel_event.is_set():
            return False, task[0]
        inp, outp = task
        ok = clean_image(inp, outp, overwrite=overwrite)
        return ok, outp if ok else inp

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(worker, t): t for t in tasks}
        for fut in concurrent.futures.as_completed(futures):
            if cancel_event and cancel_event.is_set():
                executor.shutdown(wait=False, cancel_futures=True)
                raise InterruptedError("Tiến trình đã được dừng bởi người dùng.")
            completed += 1
            if progress_callback:
                pct = completed / total
                progress_callback(f"Xóa watermark ({completed}/{total})", pct)

    final_paths = []
    for orig, cleaned in zip(image_paths, cleaned_paths):
        if os.path.exists(cleaned) and os.path.getsize(cleaned) > 0:
            final_paths.append(cleaned)
        else:
            final_paths.append(orig)

    return final_paths
