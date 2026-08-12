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


'''def check_latin(data: str, field_name: str) -> str:
    if re.search(r'[A-Z]', data):
        return f'{field_name}: СОДЕРЖИТ ЛАТИНИЦУ — ВОЗМОЖЕН ВВОД НА АНГЛИЙСКОЙ РАСКЛАДКЕ'
    return data'''


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


def extract_settlement(address: str) -> str | None:
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
    city = extract_settlement(normalized)
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
        # Полные с запятыми
        "142703, Россия, Московская Обл г Видное, мкр Солнечный, д. 4, кв. 36",
        "344116, обл. Ростовская, г. Ростов-на-Дону, пер. Салютина, дом 2, квартира 237",
        "460004, г Оренбург, ул.Ткачева,дом 91,кв.22",
        "115407, Москва, Затонная улица, д.5, к.1, кв.9",
        "426000, РФ, Удмуртская республика, г. Ижевск, ул. Холмогорова, д. 90, кв. 55",

        # Без запятых
        "Белебей ул. Шоссейная д. 13",

        # Немаркированные
        "Белорецк, Кирова, 68, 42",

        # Суффиксная улица
        "г. Казань, Ленина улица, д. 5",
        "Москва, Мира проспект, д. 12, кв. 3",
        "Челябинск, Гагарина переулок, 8",

        # Слипшиеся маркеры
        "460004, г Оренбург, ул.Ткачева,Д5,КВ22",
        "115407, Москва, Затонная ул.,Д.5,КОРП1,К.9",

        # С префиксом
        "АДРЕС_РЕГИСТРАЦИИ_STR: 142703, Россия, Московская Обл, г Видное, мкр Солнечный, д. 4, кв. 36",

        # Краевые случаи
        "109012, Москва, ул. Ильинка, д. 4",
        "г. Санкт-Петербург, Невский проспект, д. 28",
        "Казань, ул. Баумана, 5",
        "620014, Свердловская обл., г. Екатеринбург, ул. Малышева, д. 31, корп. 2",

        # ─── Деревни, сёла, пгт ───
        "143500, Московская обл., д. Петрово, ул. Центральная, д. 5",
        "Тверская обл., с. Медное, ул. Школьная, д. 12",
        "Ленинградская обл., пгт. Сиверский, ул. Вокзальная, д. 3, кв. 8",
        "Краснодарский край, ст-ца Староминская, ул. Красная, д. 15",
        "Ростовская обл., х. Калинин, ул. Степная, д. 7",
        "Московская обл., п. ВНИИССОК, ул. Институтская, д. 1",
        "Тверская обл., деревня Захарово, ул. Новая, д. 22",
        "село Богатое, ул. Советская, д. 5",
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