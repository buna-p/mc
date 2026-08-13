import re
from dataclasses import asdict, dataclass


@dataclass
class AddressResult:
    source: str  # исходник
    normalized: str  # нормализованные данные
    country: str = "РОССИЯ"
    postal_code: str = ''
    region: str = ''
    city: str = ''
    street: str = ''
    house: str = ''
    building: str = ''
    apartment: str = ''
    status: str = 'GOOD'  # GOOD/WARNING/BAD/ERROR
    comment: str = ''


ADDRESS_PREFIX = 'Адрес_регистрации_str: '

NUMBER_PATTERN = r'\d+[А-ЯA-Z]?(?:[/\-]\d+[А-ЯA-Z]?)?'  # паттерн для определения номера в адресе (дом, корп, кв)

COUNTRY_VALUES = frozenset({'РОССИЯ', 'РФ', 'РОССИЙСКАЯ ФЕДЕРАЦИЯ', 'РОС ФЕД', 'РОСИЯ'})

REGION_MARKERS = (
    'ОБЛ', 'ОБЛ.', 'ОБЛАСТЬ',
    'КР', 'КР.', 'КРАЙ',
    'РЕСП', 'РЕСП.', 'РЕСПУБЛИКА',
    'АО', 'АВТОНОМНЫЙ ОКРУГ',
    'РАЙОН', 'Р-Н')


SETTLEMENT_MARKERS = (
    r'ГОРОД\s+ТИПА|ГОРОД|Г\.?|'
    r'ДЕРЕВНЯ|ДЕР\.?|'
    r'СЕЛО|С\.?|'
    r'ПОС[ЕЁ]ЛОК|ПОС\.?|'
    r'ПГТ|П\.\s*Г\.\s*Т\.?|'
    r'СТАНИЦА|СТ-ЦА|СТ\.?|'
    r'ХУТОР|ХУТ\.?|Х\.?|'
    r'Д\.?'  # деревня — последним (конфликтует с домом)
)

STREET_MARKERS = (
    r'УЛИЦА|УЛ\.?|'
    r'ПЕРЕУЛОК|ПРОУЛОК|ПЕР\.?|'
    r'ПРОСПЕКТ|ПР-КТ|'
    r'ПРОЕЗД|ПР-Д|'
    r'БУЛЬВАР|Б-Р|'
    r'НАБЕРЕЖНАЯ|НАБ\.?|'
    r'ШОССЕ|ШОС\.?|Ш\.?|'
    r'МИКРОРАЙОН|МКР\.?|'
    r'КВАРТАЛ|КВ-Л|' #КВ - квартира
    r'ПЛОЩАДЬ|ПЛ\.?|'
    r'АЛЛЕЯ|АЛ\.?|'
)

HOUSE_MARKERS = (
    r'ДОМ\.?|Д\.?|'
    r'ДОМОВЛАДЕНИЕ|ДВЛД\.?|'
)

KNOWN_CITIES = {
    "МОСКВА", "САНКТ-ПЕТЕРБУРГ", "НОВОСИБИРСК", "ЕКАТЕРИНБУРГ", "КАЗАНЬ", "НИЖНИЙ НОВГОРОД",
    "ЧЕЛЯБИНСК", "САМАРА", "ОМСК", "РОСТОВ-НА-ДОНУ", "УФА", "КРАСНОЯРСК", "ПЕРМЬ", "ВОРОНЕЖ",
    "ВОЛГОГРАД", "КРАСНОДАР", "САРАТОВ", "ТЮМЕНЬ", "ТОЛЬЯТТИ", "ИЖЕВСК", "БАРНАУЛ", "УЛЬЯНОВСК",
    "ИРКУТСК", "ХАБАРОВСК", "ЯРОСЛАВЛЬ", "ВЛАДИВОСТОК", "МАХАЧКАЛА", "ТОМСК", "ОРЕНБУРГ",
    "КЕМЕРОВО", "НОВОКУЗНЕЦК", "РЯЗАНЬ", "АСТРАХАНЬ", "ПЕНЗА", "ЛИПЕЦК", "ТУЛА", "КИРОВ",
    "ЧЕБОКСАРЫ", "КАЛИНИНГРАД", "БРЯНСК", "КУРСК", "ИВАНОВО", "ТВЕРЬ", "СТАВРОПОЛЬ", "БЕЛГОРОД",
    "СОЧИ", "СЕВАСТОПОЛЬ", "СИМФЕРОПОЛЬ",
}

STREET_SHORT = {
    "УЛ": "УЛ.", "УЛИЦА": "УЛ.",
    "ПЕР": "ПЕР.", "ПЕРЕУЛОК": "ПЕР.",
    "ПРОСПЕКТ": "ПР-КТ", "ПР-КТ": "ПР-КТ",
    "ПРОЕЗД": "ПР-Д", "ПР-Д": "ПР-Д",
    "БУЛЬВАР": "Б-Р", "Б-Р": "Б-Р",
    "НАБЕРЕЖНАЯ": "НАБ.", "НАБ": "НАБ.",
    "ШОССЕ": "Ш.", "Ш": "Ш.",
    "МИКРОРАЙОН": "МКР.", "МКР": "МКР.",
    "КВАРТАЛ": "КВ-Л", "КВ-Л": "КВ-Л",
    "ПЛОЩАДЬ": "ПЛ.", "ПЛ": "ПЛ.",
    "АЛЛЕЯ": "АЛ.", "АЛ": "АЛ.",
}

SETTLEMENT_SHORT = {
    "Г": "Г.", "ГОРОД": "Г.", "ГОР": "Г.", "ГОР.": "Г.",
    "Д": "Д.", "ДЕРЕВНЯ": "Д.", "ДЕР": "Д.", "ДЕР.": "Д.",
    "С": "С.", "СЕЛО": "С.", "СЕЛ": "С.", "СЕЛ.": "С.",
    "ПОС": "ПОС.", "ПОСЕЛОК": "ПОС.", "ПОСЁЛОК": "ПОС.",
    "П": "П.",
    "ПГТ": "ПГТ.", "П.Г.Т": "ПГТ.",
    "СТ-ЦА": "СТ-ЦА", "СТАНИЦА": "СТ-ЦА",
    "Х": "Х.", "ХУТОР": "Х.", "ХУТ.": "Х.", "ХУТ": "Х.",
}


def normalize_address(data: str) -> str:
    if not isinstance(data, str):
        return ''

    address = data.removeprefix(ADDRESS_PREFIX)
    address = address.strip().upper().replace('Ё', 'Е')
    address = re.sub(r'\s+', ' ', address)
    address = re.sub(r'\s*,\s*', ', ', address)
    address = re.sub(r',+', ',', address)
    address = re.sub(r'\b(Д|ДОМ|ДВЛД|ДОМОВЛАДЕНИЕ|К|КОР|КОРП|КОРПУС|ЛИТ|ЛИТЕР|СТР|СТРОЕНИЕ|КВ|КВАРТИРА)(?=\d)', r'\1. ', address)
    address = re.sub(r'\.(?=[А-ЯA-Z0-9])', '. ', address)
    address = re.sub(r'\s+', ' ', address)
    return address.strip(',. ')


def split_address(address: str) -> list[str]:
    return [part.strip() for part in address.split(',') if part.strip()]


def clean_name(data: str) -> str:
    value = re.sub(r'\s+', ' ', data)
    return value.strip(',. ')


def _extract_number(data: str, marker:str) -> str | None:
    pattern = (r'\b(?:' + marker + r')'
    r'\.?\s*'
    r'(?P<number>' + NUMBER_PATTERN + r')\b')
    match = re.search(pattern, data)
    return match.group('number').strip().upper() if match else None


def extract_postal_code(address: str) -> str | None:
    match = re.search(r'(?<!\d)(\d{6})(?!\d)', address)
    return match.group(1) if match else None


def extract_apartment(address: str) -> str | None:
    return _extract_number(address, r'КВ|КВАРТИРА')


def extract_building(address: str, apartment_found: bool = False) -> str | None:
    if apartment_found:
        return _extract_number(address, r'К|КОР|КОРП|КОРПУС|ЛИТ|ЛИТЕР|СТР|СТРОЕНИЕ')
    else:
        return _extract_number(address, r'КОР|КОРП|КОРПУС|ЛИТ|ЛИТЕР|СТР|СТРОЕНИЕ')


def extract_house(address: str) -> str | None:
    return _extract_number(address, r'Д|ДОМ|ДВЛД|ДОМОВЛАДЕНИЕ')


def _normalize_settlement_marker(marker: str) -> str:
    marker = marker.strip().upper().rstrip('.')
    mapping = SETTLEMENT_SHORT
    return mapping.get(marker, marker)


def _normalize_street_marker(marker: str) -> str:
    marker = marker.upper().rstrip('.')
    mapping = STREET_SHORT
    return mapping.get(marker, marker)


'''def extract_settlement(address: str) -> str | None:
    match = re.search(
        r'(?:^|,\s*|\s)'
        r'(?P<marker>' + SETTLEMENT_MARKERS + r')'
        r'\s+'
        r'(?P<name>[А-Я][А-Я0-9\- ]*?)'
        r'(?=\s*,|\s+(?:' + STREET_MARKERS + r'|ДОМ\.?|ДОМОВЛАДЕНИЕ|ДВЛД\.?|Д\.?)\s*\d|$)',
        address,
        )
    if not match:
        return None
    marker = match.group('marker').strip()
    name = clean_name(match.group('name'))
    if not name:
        return None
    if re.fullmatch(r'Д\.?', marker, re.IGNORECASE) and re.fullmatch(r'"\d+.*', name):
        return None
    normalized_marker = _normalize_settlement_marker(marker)
    return f'{normalized_marker} {name}'''


def extract_region(address: str) -> str | None:
    flat = '|'.join(re.escape(marker.rstrip('.')) for marker in REGION_MARKERS)
    all_after = SETTLEMENT_MARKERS + '|' + STREET_MARKERS + '|' + HOUSE_MARKERS
    for part in split_address(address):
        for marker in REGION_MARKERS:
            if re.search(rf"\b{re.escape(marker.rstrip('.'))}\.?\b", part):
                region_only = re.split(
                    rf'\s+(?:{all_after})\s+',
                    part,
                    maxsplit=1
                )[0]
                return clean_name(region_only)
    match = re.search(
        r'[А-Я][А-Я\- ]*?\s*(?:' + flat + r')\.?\b',
        address,
    )
    if match:
        return clean_name(match.group())
    match = re.search(
        r'\b(?:' + flat + r')\.?\s+[А-Я][А-Я\-]+'
        r'(?:\s+[А-Я][А-Я\-]+)*'
        r'(?=\s*,|\s+(?:' + all_after + r')\b|$)',
        address,
    )
    return clean_name(match.group()) if match else None


def extract_city(address: str) -> str | None:
    split_on = STREET_MARKERS + '|' + HOUSE_MARKERS
    for part in split_address(address):
        match = re.search(
            r'(?P<marker>' + SETTLEMENT_MARKERS + r')\s+',
            part,
        )
        if not match:
            continue

        marker = match.group('marker').strip()
        after_marker = part[match.end():]

        name = re.split(r'\s+(?:' + split_on + r')\s+', after_marker, maxsplit=1)[0]
        name = clean_name(name)

        if not name:
            continue
        if re.fullmatch(r'Д\.?', marker, re.IGNORECASE) and re.fullmatch(r'"\d+.*', name):
            continue

        normalized_marker = _normalize_settlement_marker(marker)
        return f'{normalized_marker} {name}'

    return None


def extract_street(address: str) -> str | None:
    prefix_match = re.search(
        r'(?:^|,\s*|\s)'
        r'(?P<type>' + STREET_MARKERS + r')'
        r'\s+'
        r'(?P<name>[А-ЯA-Z0-9][А-ЯA-Z0-9\- ]*?)'
        r'(?=\s*,|\s+(?:ДОМ|Д\.?|КОРПУС|КОРП\.?|КВАРТИРА|КВ\.)\s*\d|$)',
        address,
    )
    if prefix_match:
        street_type = _normalize_street_marker(prefix_match.group('type'))
        name = clean_name(prefix_match.group('name'))
        if name:
            return f'{street_type} {name}'
    suffix_match = re.search(
        r'(?:^|,\s*)'
        r'(?P<name>[А-ЯA-Z0-9][А-ЯA-Z0-9\- ]*?)\s+'
        r'(?P<type>' + STREET_MARKERS + r')'
        r'(?=\s*,|$)',
        address,
    )
    if suffix_match:
        street_type = _normalize_street_marker(suffix_match.group('type'))
        name = clean_name(suffix_match.group('name'))
        if name:
            return f'{street_type} {name}'
    return None


def _is_region(part: str) -> bool:
    for marker in REGION_MARKERS:
        if re.search(rf'\b{re.escape(marker.rstrip("."))}\.?\b', part):
            return True
    return False


def extract_city_before_street_marker(address: str) -> str | None:
    flat = '|'.join(re.escape(marker.rstrip('.')) for marker in COUNTRY_VALUES)
    street_marker_pattern = (
        r'\b(?:' + STREET_MARKERS + r')\s+'
    )
    match = re.search(street_marker_pattern, address)
    if not match:
        return None
    before_street = address[:match.start()].strip(' ,.')
    before_street = re.sub(r'^\d{6}\s*', '', before_street).strip(' ,')
    before_street = re.sub(
        r'^(?:' + flat + r')\s*', '', before_street).strip(' ,')
    for marker in REGION_MARKERS:
        before_street = re.sub(
            rf'[А-ЯA-Z\- ]*?\b{re.escape(marker.rstrip("."))}\.?\b\s*',
            '', before_street, flags=re.IGNORECASE
        ).strip(' ,')
    if not before_street:
        return None
    if _is_region(before_street):
        return None
    return f'{clean_name(before_street)}'


def _is_explicit_component(part: str) -> bool:
    return bool(
        re.match(
            r"^(?:ДОМ|Д|КОРПУС|КОРП|КВАРТИРА|КВ)\.?\s*\d",
            part,
        )
    )


def _is_postal_code(part: str) -> bool:
    return bool(re.fullmatch(r"\d{6}", part))


def _is_country(part: str) -> bool:
    return part.strip(" .") in COUNTRY_VALUES


def _is_number(part: str) -> bool:
    return bool(re.fullmatch(NUMBER_PATTERN, part))


def _is_capitalized_word(part: str) -> bool:
    return bool(re.fullmatch(r"[А-ЯA-Z][А-ЯA-Z\- ]+", part))


def extract_unmarked_parts(address: str, city: str | None, street: str | None, house: str | None, apartment: str | None) -> tuple[str | None, str | None, str | None, str | None, bool]:
    parts = split_address(address)
    used_assumption = False

    remaining = []
    for part in parts:
        if _is_postal_code(part):
            continue
        if _is_country(part):
            continue
        if _is_region(part):
            continue
        if _is_explicit_component(part):
            continue
        remaining.append(part)

    if city:
        city_name = re.sub(r"^[А-Я]+\.\s*", "", city)
        remaining = [p for p in remaining if city_name not in p]
    if street:
        street_name_match = re.match(
            r"^(?:УЛ\.|ПЕР\.|ПР-КТ|ПР-Д|Б-Р|НАБ\.|Ш\.|МКР\.|КВ-Л|ПЛ\.)\s*(.+)",
            street,
        )
        if street_name_match:
            street_name = street_name_match.group(1)
            remaining = [p for p in remaining if street_name not in p]

    text_parts = [p for p in remaining if not _is_number(p)]
    number_parts = [p for p in remaining if _is_number(p)]

    if city is None and text_parts:
        first_text = text_parts[0]
        if first_text in KNOWN_CITIES or _is_capitalized_word(first_text):
            city = f"Г. {clean_name(first_text)}"
            text_parts = text_parts[1:]
            used_assumption = True

    if street is None and text_parts:
        street = f"УЛ. {clean_name(text_parts[0])}"
        used_assumption = True

    if house is None and number_parts:
        house = number_parts[0]
        used_assumption = True

    if apartment is None and len(number_parts) >= 2:
        apartment = number_parts[1]
        used_assumption = True

    return city, street, house, apartment, used_assumption


def resolve_building_vs_apartment(
    address: str,
    building: str | None,
    apartment: str | None,
) -> tuple[str | None, str | None, bool]:
    changed = False

    if building and apartment:
        return building, apartment, changed

    if building and re.search(r"\bКОРПУС\b|\bКОРП\b", address):
        return building, apartment, changed

    has_kv = bool(re.search(r"\b(?:КВАРТИРА|КВ)\.?\s*\d", address))
    has_k = bool(re.search(r"\bК\.?\s*\d", address))

    if has_kv and has_k and not building:
        match = re.search(r"\bК\.?\s*(?P<number>" + NUMBER_PATTERN + r")", address)
        if match:
            building = match.group("number")
            changed = True

    if has_k and not has_kv and not apartment:
        match = re.search(r"\bК\.?\s*(?P<number>" + NUMBER_PATTERN + r")", address)
        if match:
            before_k = address[:match.start()]
            has_house_before = bool(re.search(r"\b(?:ДОМ|Д)\.?\s*\d", before_k))

            if has_house_before and not building:
                building = match.group("number")
                changed = True
            elif not apartment:
                apartment = match.group("number")
                changed = True

    return building, apartment, changed


def parse_address(address: str) -> dict:
    if not isinstance(address, str) or not address.strip():
        result = AddressResult(
            source='' if address is None else str(address),
            normalized='',
            status='ERROR',
            comment='АДРЕС: ПУСТО ИЛИ ИМЕЕТ НЕКОРРЕКТНЫЙ ТИП',
        )
        return asdict(result)

    normalized = normalize_address(address)
    used_assumption = False

    postal_code = extract_postal_code(normalized) or ''
    region = extract_region(normalized) or ''
    city = extract_city(normalized)
    street = extract_street(normalized)
    house = extract_house(normalized)
    apartment = extract_apartment(normalized)
    building = extract_building(normalized, apartment_found=bool(apartment))

    if city is None:
        city = extract_city_before_street_marker(normalized)
        if city is not None:
            used_assumption = True

    if city is None:
        parts = split_address(normalized)
        for part in parts:
            if part in KNOWN_CITIES:
                city = f'{part}'
                used_assumption = True
                break

    if city is None or street is None or house is None:
        city, street, house, apartment, fallback_used = extract_unmarked_parts(
            address=normalized,
            city=city,
            street=street,
            house=house,
            apartment=apartment,
        )
        used_assumption = used_assumption or fallback_used

    # ── Этап 5: контекстная коррекция «К.» ──
    building, apartment, resolve_changed = resolve_building_vs_apartment(
        normalized, building, apartment
    )
    if resolve_changed:
        used_assumption = True

    # ── Этап 6: статус ──
    missing = []
    if not city:
        missing.append("ГОРОД")
    if not street:
        missing.append("УЛИЦА")
    if not house:
        missing.append("ДОМ")

    if missing:
        status = "MANUAL"
        comment = "НЕ РАСПОЗНАНО: " + ", ".join(missing)
    elif used_assumption:
        status = "WARNING"
        comment = "ЧАСТЬ ДАННЫХ ОПРЕДЕЛЕНА ЭВРИСТИЧЕСКИ"
    else:
        status = "GOOD"
        comment = ""

    result = AddressResult(
        source=address,
        normalized=normalized,
        country="РОССИЯ",
        postal_code=postal_code,
        region=region,
        city=city or "",
        street=street or "",
        house=house or "",
        building=building or "",
        apartment=apartment or "",
        status=status,
        comment=comment,
    )

    return asdict(result)







if __name__ == "__main__":
    test_addresses = [
        "Адрес_регистрации_str: Московская обл., г. Электросталь, проезд Полярный, д. 5А, кв. 27",
        "Адрес_регистрации_str: Г. САНКТ-ПЕТЕРБУРГ, УЛИЦА ОКТЯБРЬСКАЯ НАБ. Д. 90, К. 6, КВ. 64",
        "Адрес_регистрации_str: Красноярск ул.Матросова д.40 кв.146",
        "Адрес_регистрации_str: г. Новосибирск ул. Фрунзе 20-135",
        "Адрес_регистрации_str: 624250 Российская Федерация, обл Свердловская, г Заречный, ул Ленина, д. 35А, кв. 57",
        "Адрес_регистрации_str: Верхняя салда Карла Либкнехта д.1, кв. 11",
        "Адрес_регистрации_str: г. Новосибирск, ул. Фрунзе 20-135",
        "Адрес_регистрации_str: Республика Башкортостан Татышлинский район село Ялгы-Нарат улица Центральная дом 15",
        "Адрес_регистрации_str: г. Ижевск, ул. Березняковская, д. 2",
        "Адрес_регистрации_str: Республика Башкортостан, г. Ишимбай, ул. Гагарина, д. 28, кв. 72",
        "Адрес_регистрации_str: п.Н.Доскино,л.16,д.18",
        "Адрес_регистрации_str: 624250 Российская Федерация, обл Свердловская, г Заречный, ул Ленина, д. 35А, кв. 57",
        "Адрес_регистрации_str: Москва ул. Халтуринская 17 кв.78",
        "Адрес_регистрации_str: с. Топольное ул. В. Табачкова 24аби1",
        "Адрес_регистрации_str: г. Иркутск ул 4-я Советская д 19А",
        "Адрес_регистрации_str: Ханты-Мансийский автономный округ - Югра, г.Нефтеюганск, 13 микрорайон, д. 8, кв.48",
        "Адрес_регистрации_str: г. Самара, ул. Георгия Ратнера, д. 21, кв. 78",
        "Адрес_регистрации_str: г. Москва, пер. Ангелов, д. 6, к. 3, кв. 507",
        "Адрес_регистрации_str: Самарская область, пгт. Безенчук, ул. Новостепановка, д. 3,.кв. 3",
        "Адрес_регистрации_str: Обл. Московская. г. Красногорск, РП.Нахабино, д.7,кв.441",
        "Адрес_регистрации_str: Волгоград  пр.Столетова дом 6 кв.89",
        "Адрес_регистрации_str: Город Сочи адлерский р-он с. Казачий брод ул краснофлотская дом 26 «снт Солнышко»",
        "Адрес_регистрации_str: Омск, улица Бородина д.15 кв.77",
        "Адрес_регистрации_str: 420140, г. Казань, ул. Центральная 37А",
        "Адрес_регистрации_str: обл. Пензенская, г. Пенза, ул. Пушкина, д. 91, кв. 28",
        "Адрес_регистрации_str: Московская область, г. Шатура, ул. Советская, д. 40, кв. 57",
        "Адрес_регистрации_str: Республика Алтай, Чемальский район, с. Чемал, ул. Анохина 32",
        "Адрес_регистрации_str: с. Октябрьское ул. Почтовая 59",
        "Адрес_регистрации_str: П. Краснооктябрьский ул. Ленина д.2 КВ.1",
        "Адрес_регистрации_str: Краснооктябрьский ул. Ленина д2 кв1",
        "Адрес_регистрации_str: Пензенская обл, г Сердобск, ул Каракозова, двлд 8",
        "Адрес_регистрации_str: Ст. Ленинградская улица Тихая 140",
        "Адрес_регистрации_str: Респ. Карелия г. Петрозаводск ул Пархоменко д. 33,  кв. 120",
        "Адрес_регистрации_str: Ставропольский край г. Лермонтов ул. Патриса Лумумбы д. 5 кв. 33",
        "Адрес_регистрации_str: Пермский край, Пермь, Охотников 32, кв. 37",
        "Адрес_регистрации_str: Республика Башкортостан, город Давлеканово , переулок Степной д. 12",
        "Адрес_регистрации_str: Г. Якутск, ул. Курнатовского 1/4 кв44",
        "Адрес_регистрации_str: Тюмень Газопромысловая 8",
        "Адрес_регистрации_str: Попов проезд, д.1, к.1, кв.53",
        "Адрес_регистрации_str: Свердловская область, г.Верхняя Пышма, ул.Ураьльских рабочих, д.48, кв.71",
        "Адрес_регистрации_str: Город МОСКВА, Улица ГУРЬЯНОВА, дом 6, корпус 1",
        "Адрес_регистрации_str: 625520, Тюменская обл, рп. Богандинский, ул. Крестьянская 17",
        "Адрес_регистрации_str: Г. Заречный, ул алещенкова 26, кв 25",
        "Адрес_регистрации_str: липецкая область, город липецк, ул. северная, д.26а",
        "Адрес_регистрации_str: г. Светлоград, ул. 9 января, д. 89",
        "Адрес_регистрации_str: г. Калуга, пер. 1-й Пестеля, д. 30, к. 1, кв. 15",
        "Адрес_регистрации_str: Г. Барнаул.Советской Армии 50 а к/2 КВ 69",
        "Адрес_регистрации_str: Ул строителей 27-30",
        "Адрес_регистрации_str: Томск проспект Кирова 53/6 кв 16",
        "Адрес_регистрации_str: Г. Заречный, ул алещенкова 26, кв 25",
        "Адрес_регистрации_str: г. Ижевск, ул. Березняковская, д. 2",
        "Адрес_регистрации_str: Алтайский край, г. Заринск, ул. Союза Республик, 12, кв 241",
        "Адрес_регистрации_str: Москва, улица Родионовская дом2 квартира46",
        "Адрес_регистрации_str: г. Москва. ул. Генерала Глаголева, дом 30, корп. 3, кв. 271.",
        "Адрес_регистрации_str: Алтайский край, г.Барнаул, проезд Южно Власихинский,28а-2",
        "Адрес_регистрации_str: г. Владимир, ул. Чайковского, д.38В, кв30",
        "Адрес_регистрации_str: Калининградская область. г. Гусев ул Ю. Смирнова д 18 кв 11",
        "Адрес_регистрации_str: Воронеж, улица 20-летия Октября,38А",
        "Адрес_регистрации_str: Москва, Рязанский проспект, д. 64, к.2, кв. 390",
        "Адрес_регистрации_str: проезд. Матросова, д. 18",
        "Адрес_регистрации_str: 109386, Г. МОСКВА, УЛ. НОВОРОССИЙСКАЯ Д.21, КВ.61",
        "Адрес_регистрации_str: Самарская область город Новокуйбышевск проспект победы 15-129",
        "Адрес_регистрации_str: Г. Нововоронеж ул. Аленовская д. 42, кв 82",
        "Адрес_регистрации_str: Г. Якутск, ул Курнатовского 1/4, кв. 44",
        "Адрес_регистрации_str: г. Самара, ул. Георгия Ратнера, д. 21, кв. 78",
        "Адрес_регистрации_str: Самарская область город Новокуйбышевск проспект Победы 42 квартира 65",
        "Адрес_регистрации_str: Самарская область, город Новокуйбышевск, улица Островского д.8 кв.130",
        "Адрес_регистрации_str: Самарская обл, г Новокуйбышевск, ул Кадомцева, д 7, кв 24",
        "Адрес_регистрации_str: Великий Новгород, Большая Московская 132-135",
        "Адрес_регистрации_str: г. Москва, г. Зеленоград, корпус 360, квартира 149",
        "Адрес_регистрации_str: Чувашская Республика - Чувашия,Чебоксарский район, Чиршкасы (Сирмапосинского с/п ) д, 11 пятилетки дом 5, кв 12",
        "Адрес_регистрации_str: П. Маяк, ул. Дорожная д.6 кв 8",
        "Адрес_регистрации_str: Обл. Свердловская гор. Ирбит ул. Школьная дом 38",
        "Адрес_регистрации_str: г.Чебоксары пер.Ягодный 6 к1 кв3",
        "Адрес_регистрации_str: Самарская обл, г Новокуйбышевск, ул Кадомцева, д 7, кв 24",
        "Адрес_регистрации_str: ГОР, КРАСНОДАР УЛ. МИЧУРИНА д. 33",
        "Адрес_регистрации_str: Ульяновск, герасимова 45кв2",
        "Адрес_регистрации_str: Забайкальский край в Черновском р-н г Читы ул Староивановская 37а",
        "Адрес_регистрации_str: Г. Заречный, ул алещенкова 26, кв 25Екатеринбург",
        "Адрес_регистрации_str: Г. Самара ул.Революционная Д.101в кв.68",
        "Адрес_регистрации_str: Московская обл., г. Воскресенск, ул. Зелинского, д. 5А, кв. 59",
        "Адрес_регистрации_str: Нижний Новгород, пр.Ленина, д.59, корп.7, кв.15",
        "Адрес_регистрации_str: Московская обл., г. Воскресенск, ул. Зелинского, д. 5А, кв. 59",
        "Адрес_регистрации_str: Курская обл. г.Курчатов ул. Энергетиков д.31 кв. 88",
        "Адрес_регистрации_str: Республика Коми УСТЬ-ВЫМЬСКИЙ район г. МИКУНЬ ул. Ленина д. 19а кв. 53",
        "Адрес_регистрации_str: Воронежская обл, с. Новая Усмань, ул Красная Поляна, д 64",
        "Адрес_регистрации_str: Г. МОСКВА, УЛ. НОВОРОССИЙСКАЯ, Д.21, КВ.61",
        "Адрес_регистрации_str: Курский р-он, д. 1-е Цветово, ул. Луговая, д.5",
        "Адрес_регистрации_str: 660118, край Красноярский, г Красноярск, ул Мате Залки, д 38, кв 32",
        "Адрес_регистрации_str: Калининградская обл., Светловский городской округ, посёлок Веселовка, ул. Тенистая, дом 14, кв. 1",
        "Адрес_регистрации_str: Новокуйбышевск  ул. Дзержинского  д.8 кв.99",
        "Адрес_регистрации_str: РЕСПУБЛИКА КАЛМЫКИЯ ЯШКУЛЬСКИЙ РАЙОН ПОС. ЯШКУЛЬ ПЕР. ОКТЯБРЬСКИЙ ДОМ 1",
        "Адрес_регистрации_str: Самарская область город Новокуйбышевск проспект Победы 42 квартира 65",
        "Адрес_регистрации_str: СПБ, Московское шоссе 16 корпус 1, квартира 70",
        "Адрес_регистрации_str: г. Чебоксары, ул. Пролетарская, д.27, КВ. 294",
        "Адрес_регистрации_str: Казань ул. утренняя д.36",
        "Адрес_регистрации_str: Г. Заречный, ул алещенкова 26, кв 25",
        "Адрес_регистрации_str: Ростовская область город Таганрог ул. Яблочкина дом 15 кв. 6",
        "Адрес_регистрации_str: Новосибирская область ,Ордынский район, село Чингис,,ул.Кустарная,д.3",
        "Адрес_регистрации_str: Город Верхняя Пышма, ул. Уральских Рабочих, д. 2а, кв. 8",
        "Адрес_регистрации_str: Кемеровская область город Мыски улица Гвардейская дом 23",
        "Адрес_регистрации_str: Краснооктябрьский ул Ленина",
        "Адрес_регистрации_str: Оренбургская обл., Оренбургский р-он, с. Южный Урал, ул. Буденного д.12 кв.2",
        "Адрес_регистрации_str: Республика Башкортостан г. Белебей ул шоссейная д. 13",
        "Адрес_регистрации_str: Кемеровская область поселок Металлплощадка б-р Строителей 71 к 8. Кв. 26",
        "Адрес_регистрации_str: Нагатинская набережная 40/1 328",
        "Адрес_регистрации_str: САМАРСКАЯ ОБЛАСТЬ Г.СЫЗРАНЬ, УЛ РАБОЧАЯ Д.68 КВ.1",
        "Адрес_регистрации_str: Кировская область г. КИРОВ. УЛ. АРХИТЕКТОРА ВАЛЕРИЯ ЗЯНКИНА Д. 11.КОР.1 КВ. 82",
        "Адрес_регистрации_str: Город Верхняя Пышма, ул. Уральских Рабочих, д. 2а, кв. 8",
        "Адрес_регистрации_str: Воронежская область, с. Новая Усмань, ул. Красная Поляна, д. 64",
        "Адрес_регистрации_str: Обл. Ростовская , р-н Аксайский , г. Аксай, ул. Садовая 31А",
        "Адрес_регистрации_str: Г.Ростов-на-Дону ул. Куприна дом 7а стр 3",
        "Адрес_регистрации_str: Свердловская область город Екатеринбург улица Академика Парина дом 33 квартира 617",
        "Адрес_регистрации_str: САРАТОВСКАЯ ОБЛ, Г. САРАТОВ, УЛ. СОВЕТСКАЯ, Д. 90/96, КВ. 35",
        "Адрес_регистрации_str: Г.Ростов-на-Дону ул. Куприна д7а стр 3",
        "Адрес_регистрации_str: г. Москва, ул. 6-я Кожуховская, д. 10, кв. 122",
        "Адрес_регистрации_str: Липецк г, Меркулова,д 3,кв 13",
        "Адрес_регистрации_str: Отрадный Победы 5а 34",
        "Адрес_регистрации_str: г. Санкт-Петербург, ул. Среднерогатская, д. 9, лит. А, кв. 216",
        "Адрес_регистрации_str: Отрадный Победы 5а 34",
        "Адрес_регистрации_str: Г Кемерово. Улица свободы 17-44",
        "Адрес_регистрации_str: с. Смоленское ул. Энергетическая 36 кв2",
        "Адрес_регистрации_str: Г. Липецк, ул. Металлистов, д. 4, кв. 11",
        "Адрес_регистрации_str: Воронеж ул Черноморская д21",
        "Адрес_регистрации_str: Ивановская область, г. Шуя, ул. 3-я Пушкинская, 47",
        "Адрес_регистрации_str: Москва ул.Недорубова д 27 кв 3",
        "Адрес_регистрации_str: Липецк г, Водопьянова ул, 15",
        "Адрес_регистрации_str: Ул. Ратная, д. 8, к. 3, кв. 141",
        "Адрес_регистрации_str: Бульвар ботанический 15-302",
        "Адрес_регистрации_str: ул. Авиаконструктора Петлякова, д.11, кв.11",
        "Адрес_регистрации_str: г. Москва, Алтуфьевское шоссе, д. 92, кв. 288",
        "Адрес_регистрации_str: Обл Московская; г Реутов улица Октябра д 52 ; кв1006",
        "Адрес_регистрации_str: г. Москва, Славянский б-р., дом 9, корп. 6, кв. 152",
        "Адрес_регистрации_str: Курская область, г.Курчатов, ул.Садовая, д.21, кв.16",
        "Адрес_регистрации_str: г. Красноярск, ул. Соколовская, д. 74 кв. 308",
        "Адрес_регистрации_str: Московская обл., ул. 9 мая д.14 кв. 1",
        "Адрес_регистрации_str: г. Калининград, ул. Памяти павших в Афганистане 17. кв 15",
        "Адрес_регистрации_str: Республика Дагестан Цумадинский р-н С метрада ул И Шамиля д46",
        "Адрес_регистрации_str: Челябинская область Сосновский район поселок Рощино Ленина 2 квартира 2",
        "Адрес_регистрации_str: Г.Иваново Ивановская область , микрорайон ТЭЦ-3 , д.10 кв.32",
        "Адрес_регистрации_str: Челябинск",
        "Адрес_регистрации_str: Ульяновская область, Старокулаткинский район, село Кармалей, ул. Кооперативная дом 4",
        "Адрес_регистрации_str: с.Сергиевское Радиоцентра №5,д.16-115",
        "Адрес_регистрации_str: Подольск, Пионерская 15,137",
        "Адрес_регистрации_str: Химки, 9 мая, 3, 147",
        "Адрес_регистрации_str: г.Москва,ул.Зеленоградская д.17,кв.224",
        "Адрес_регистрации_str: Г. Ростов-на-Дону ул. Куприна дом 7а стр 3",
        "Адрес_регистрации_str: УЛ. БЕЛОМОРСКАЯ ДОМ 12, КВ. 59",
        "Адрес_регистрации_str: Кировская область город Вятские Поляны улица Чехова дом 33",
        "Адрес_регистрации_str: Москва, ул. Авиационная, д. 74, к. 2, кв. 11",
        "Адрес_регистрации_str: г.Омск 24 северная дом 198 кВ.84",
        "Адрес_регистрации_str: г.Новосибирск, ул. Вавилова, 7-85",
        "Адрес_регистрации_str: Волгоградская область, г. Котельниково, улица Советская д.19 кв. 102",
        "Адрес_регистрации_str: Алтайский край, р-н Смоленский, с. Смоленское, ул. Энергетическая дом 36 кв 2",
        "Адрес_регистрации_str: Реутов МО, Юбилейный проспект., д. 60 кв. 375",
        "Адрес_регистрации_str: Недорубова 27 кв 3",
        "Адрес_регистрации_str: Оренбургский район, с. Нежинка ул. Фестивальная 17 кв. 29",
        "Адрес_регистрации_str: Коммунаров",
        "Адрес_регистрации_str: 121351 г.москва, ул. ивана франко д.42/2 кв.114",
        "Адрес_регистрации_str: 655017, Респ. Хакасия, г. Абакан, ул. Чертыгашева, д 42, кв 17",
        "Адрес_регистрации_str: ГОРОД МОСКВА УЛИЦА ХАЧАТУРЯНА ДОМ 7 КВАРТИРА 73",
        "Адрес_регистрации_str: 121351 г.москва, ул. ивана франко д.42/2 кв.114",
        "Адрес_регистрации_str: г.Новосибирск, ул. Вавилова, 7-85",
        "Адрес_регистрации_str: Новосибирск, ул Макаренко д 7 кв 92",
        "Адрес_регистрации_str: Недорубова 27  кв 3",
        "Адрес_регистрации_str: РМЭ, Советский район, п.Ургакш, ул. Новая, д.4, кв.15",
        "Адрес_регистрации_str: г. Калининград ул. Лужская 23Б к. 1 кв. 96",
    ]

    for addr in test_addresses:
        parsed = parse_address(addr)
        print(f"{'─' * 70}")
        print(f"ВХОД:     {addr}")
        if parsed['comment']:
            print(f"СТАТУС:   {parsed['status']} | {parsed['comment']}")
        else:
            print(f"СТАТУС:   {parsed['status']}")
        print(f"ИНДЕКС:   {parsed['postal_code']}")
        print(f"РЕГИОН:   {parsed['region']}")
        print(f"ГОРОД:    {parsed['city']}")
        print(f"УЛИЦА:    {parsed['street']}")
        print(f"ДОМ:      {parsed['house']}")
        print(f"КОРПУС:   {parsed['building']}")
        print(f"КВАРТИРА: {parsed['apartment']}")