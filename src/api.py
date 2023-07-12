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
        self.codes = {
            "AFN": "Afghan Afghani",
            "ALL": "Albanian Lek",
            "DZD": "Algerian Dinar",
            "AOA": "Angolan Kwanza",
            "ARS": "Argentine Peso",
            "AMD": "Armenian Dram",
            "AWG": "Aruban Florin",
            "AUD": "Australian Dollar",
            "AZN": "Azerbaijani Manat",
            "BSD": "Bahamian Dollar",
            "BHD": "Bahraini Dinar",
            "BBD": "Bajan dollar",
            "BDT": "Bangladeshi Taka",
            "BYR": "Belarusian Ruble",
            "BYN": "Belarusian Ruble",
            "BZD": "Belize Dollar",
            "BMD": "Bermudan Dollar",
            "BTN": "Bhutan currency",
            "BTC": "Bitcoin",
            "BCH": "Bitcoin Cash",
            "BOB": "Bolivian Boliviano",
            "BAM": "Bosnia-Herzegovina Convertible Mark",
            "BWP": "Botswanan Pula",
            "BRL": "Brazilian Real",
            "BND": "Brunei Dollar",
            "BGN": "Bulgarian Lev",
            "BIF": "Burundian Franc",
            "XPF": "CFP Franc",
            "KHR": "Cambodian riel",
            "CAD": "Canadian Dollar",
            "CVE": "Cape Verdean Escudo",
            "KYD": "Cayman Islands Dollar",
            "XAF": "Central African CFA franc",
            "CLP": "Chilean Peso",
            "CLF": "Chilean Unit of Account (UF)",
            "CNY": "Chinese Yuan",
            "CNH": "Chinese Yuan (offshore)",
            "COP": "Colombian Peso",
            "KMF": "Comorian franc",
            "CDF": "Congolese Franc",
            "CRC": "Costa Rican Colón",
            "HRK": "Croatian Kuna",
            "CUP": "Cuban Peso",
            "CZK": "Czech Koruna",
            "DKK": "Danish Krone",
            "DJF": "Djiboutian Franc",
            "DOP": "Dominican Peso",
            "XCD": "East Caribbean Dollar",
            "EGP": "Egyptian Pound",
            "ETH": "Ether",
            "ETB": "Ethiopian Birr",
            "EUR": "Euro",
            "FJD": "Fijian Dollar",
            "GMD": "Gambian dalasi",
            "GEL": "Georgian Lari",
            "GHC": "Ghanaian Cedi",
            "GHS": "Ghanaian Cedi",
            "GIP": "Gibraltar Pound",
            "GTQ": "Guatemalan Quetzal",
            "GNF": "Guinean Franc",
            "GYD": "Guyanaese Dollar",
            "HTG": "Haitian Gourde",
            "HNL": "Honduran Lempira",
            "HKD": "Hong Kong Dollar",
            "HUF": "Hungarian Forint",
            "ISK": "Icelandic Króna",
            "INR": "Indian Rupee",
            "IDR": "Indonesian Rupiah",
            "IRR": "Iranian Rial",
            "IQD": "Iraqi Dinar",
            "ILS": "Israeli New Shekel",
            "JMD": "Jamaican Dollar",
            "JPY": "Japanese Yen",
            "JOD": "Jordanian Dinar",
            "KZT": "Kazakhstani Tenge",
            "KES": "Kenyan Shilling",
            "KWD": "Kuwaiti Dinar",
            "KGS": "Kyrgystani Som",
            "LAK": "Laotian Kip",
            "LBP": "Lebanese pound",
            "LSL": "Lesotho loti",
            "LRD": "Liberian Dollar",
            "LYD": "Libyan Dinar",
            "LTC": "Litecoin",
            "MOP": "Macanese Pataca",
            "MKD": "Macedonian Denar",
            "MGA": "Malagasy Ariary",
            "MWK": "Malawian Kwacha",
            "MYR": "Malaysian Ringgit",
            "MVR": "Maldivian Rufiyaa",
            "MRO": "Mauritanian Ouguiya (1973–2017)",
            "MUR": "Mauritian Rupee",
            "MXN": "Mexican Peso",
            "MDL": "Moldovan Leu",
            "MAD": "Moroccan Dirham",
            "MZM": "Mozambican metical",
            "MZN": "Mozambican metical",
            "MMK": "Myanmar Kyat",
            "TWD": "New Taiwan dollar",
            "NAD": "Namibian dollar",
            "NPR": "Nepalese Rupee",
            "ANG": "Netherlands Antillean Guilder",
            "NZD": "New Zealand Dollar",
            "NIO": "Nicaraguan Córdoba",
            "NGN": "Nigerian Naira",
            "NOK": "Norwegian Krone",
            "OMR": "Omani Rial",
            "PKR": "Pakistani Rupee",
            "PAB": "Panamanian Balboa",
            "PGK": "Papua New Guinean Kina",
            "PYG": "Paraguayan Guarani",
            "PHP": "Philippine Piso",
            "PLN": "Poland złoty",
            "GBP": "Pound sterling",
            "QAR": "Qatari Rial",
            "ROL": "Romanian Leu",
            "RON": "Romanian Leu",
            "RUR": "Russian Ruble",
            "RUB": "Russian Ruble",
            "RWF": "Rwandan franc",
            "SVC": "Salvadoran Colón",
            "SAR": "Saudi Riyal",
            "CSD": "Serbian Dinar",
            "RSD": "Serbian Dinar",
            "SCR": "Seychellois Rupee",
            "SLL": "Sierra Leonean Leone",
            "SGD": "Singapore Dollar",
            "PEN": "Sol",
            "SBD": "Solomon Islands Dollar",
            "SOS": "Somali Shilling",
            "ZAR": "South African Rand",
            "KRW": "South Korean won",
            "VEF": "Sovereign Bolivar",
            "XDR": "Special Drawing Rights",
            "LKR": "Sri Lankan Rupee",
            "SSP": "Sudanese pound",
            "SDG": "Sudanese pound",
            "SRD": "Surinamese Dollar",
            "SZL": "Swazi Lilangeni",
            "SEK": "Swedish Krona",
            "CHF": "Swiss Franc",
            "TJS": "Tajikistani Somoni",
            "TZS": "Tanzanian Shilling",
            "THB": "Thai Baht",
            "TOP": "Tongan Paʻanga",
            "TTD": "Trinidad & Tobago Dollar",
            "TND": "Tunisian Dinar",
            "TRY": "Turkish lira",
            "TMM": "Turkmenistan manat",
            "TMT": "Turkmenistan manat",
            "UGX": "Ugandan Shilling",
            "UAH": "Ukrainian hryvnia",
            "AED": "United Arab Emirates Dirham",
            "USD": "United States Dollar",
            "UYU": "Uruguayan Peso",
            "UZS": "Uzbekistani Som",
            "VND": "Vietnamese dong",
            "XOF": "West African CFA franc",
            "YER": "Yemeni Rial",
            "ZMW": "Zambian Kwacha",
        }
    def request(self, src, dest):
        url = f'https://www.google.com/finance/quote/{src}-{dest}'
        page = requests.get(url)
        soup = BeautifulSoup(page.text, 'html.parser')
        value = soup.find(class_="YMlKec fxKbKc")
        info = soup.find(class_="ygUjEc")
        if value and info:
            return {
                "value": value.get_text(),
                "info": info.get_text().replace("Disclaimer", ""),
                "disclaimer": info.a["href"]
            }

