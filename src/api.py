# api.py
#
# Copyright 2023 Ideve Core
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# SPDX-License-Identifier: GPL-3.0-or-later

import logging
import json
import re
from gi.repository import Gio, GObject
import requests
from bs4 import BeautifulSoup

from currencyconverter.define import CODES

def get_currency_name(code):
    name = gettext(CODES.get(code, ''))
    return name if name else None

class CurrencyObject(GObject.Object):
    __gtype_name__ = 'CurrencyObject'

    code = GObject.Property(type=str)
    name = GObject.Property(type=str)
    selected = GObject.Property(type=bool, default=False)

    def __init__(self, code, name, selected=False):
        super().__init__()
        self.code = code
        self.name = name
        self.selected = selected

    def __str__(self):
        return self.code

class CurrenciesListModel(GObject.GObject, Gio.ListModel):
    __gtype_name__ = 'CurrenciesListModel'

    def __init__(self, names_func=get_currency_name):
        super().__init__()

        self.names_func = names_func
        self.currencies = []

    def __iter__(self):
        return iter(self.currencies)

    def do_get_item(self, position):
        return self.currencies[position]

    def do_get_item_type(self):
        return CurrencyObject

    def do_get_n_items(self):
        return len(self.currencies)

    def set_langs(self, currencies, auto=False):
        removed = len(self.currencies)
        self.currencies.clear()
        if auto:
            self.currencies.append(CurrencyObject('auto', _('Auto')))
        for code in currencies:
            self.currencies.append(CurrencyObject(code, self.names_func(code)))
        self.items_changed(0, removed, len(self.currencies))

    def set_selected(self, code):
        for item in self.currencies:
            item.props.selected = (item.code == code)

class Api():
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def request(self, src, dest):
        url = f'https://www.google.com/finance/quote/{src}-{dest}'
        page = requests.get(url)
        soup = BeautifulSoup(page.text, 'html.parser')
        value = soup.find(class_="YMlKec fxKbKc")
        info = soup.find(class_="ygUjEc")
        if value and info:
            return {
                "value": value.get_text().replace(',', ''),
                "info": info.get_text().replace("Disclaimer", ""),
                "disclaimer": info.a["href"]
            }

