import re
from dataclasses import asdict, dataclass


@dataclass
class AddressResult:
    source: str  # исходник
    normalized: str  # нормализованные данные
    country: str = 'РОССИЯ'
    postal_code: str = ''
    city: str = ''
    street: str = ''
    house: str = ''
    building: str = ''
    apartment: str = ''
    status: str = 'GOOD'  # GOOD/WARNING/ERROR
    comment: str = ''


KNOWN_CITIES = (
    "МОСКВА", "САНКТ-ПЕТЕРБУРГ", "НОВОСИБИРСК", "ЕКАТЕРИНБУРГ", "КАЗАНЬ",
    "НИЖНИЙ НОВГОРОД", "ЧЕЛЯБИНСК", "САМАРА", "ОМСК", "РОСТОВ-НА-ДОНУ", "УФА",
    "КРАСНОЯРСК", "ПЕРМЬ", "ВОРОНЕЖ", "ВОЛГОГРАД", "КРАСНОДАР", "САРАТОВ",
    "ТЮМЕНЬ", "ТОЛЬЯТТИ", "ИЖЕВСК", "БАРНАУЛ", "УЛЬЯНОВСК", "ИРКУТСК",
    "ХАБАРОВСК", "ЯРОСЛАВЛЬ", "ВЛАДИВОСТОК", "МАХАЧКАЛА", "ТОМСК", "ОРЕНБУРГ",
    "КЕМЕРОВО", "НОВОКУЗНЕЦК", "РЯЗАНЬ", "АСТРАХАНЬ", "ПЕНЗА", "ЛИПЕЦК", "ТУЛА",
    "КИРОВ", "ЧЕБОКСАРЫ", "КАЛИНИНГРАД", "БРЯНСК", "КУРСК", "ИВАНОВО", "ТВЕРЬ",
    "СТАВРОПОЛЬ", "БЕЛГОРОД", "СОЧИ", "СЕВАСТОПОЛЬ", "СИМФЕРОПОЛЬ",
)

MAX_CITY_WORDS = max(len(c.split()) for c in KNOWN_CITIES)

KNOWN_CITIES_SET = frozenset(KNOWN_CITIES)

REGION_MARKERS = (
    'ОБЛАСТЬ', 'ОБЛ',
    'КРАЙ', 'КР',
    'РЕСПУБЛИКА', 'РЕСП',
    'АВТОНОМНЫЙ ОКРУГ', 'АО',
    'РАЙОН', 'Р-Н')

CITY_MARKERS = (
    'ГОРОД', 'ГОР', 'Г',
    'ПОСЕЛОК ГОРОДСКОГО ТИПА', 'ПГТ',
    'РАБОЧИЙ ПОСЕЛОК', 'РП',
    'ПОСЕЛОК', 'ПОС', 'П',
    'СТАНИЦА', 'СТ', 'СТ-ЦА',
    'ХУТОР', 'ХУТ', 'Х',
    'СЕЛО', 'СЕЛ', 'С',
    'ДЕРЕВНЯ', 'ДЕР',  # д. конфликтует с домом
)

STREET_MARKERS = (
    'УЛИЦА', 'УЛ',
    'ПЕРЕУЛОК', 'ПЕР',
    'ПРОУЛОК',
    'ПРОСПЕКТ', 'ПР-КТ', 'ПР',
    'ПРОЕЗД', 'ПР-Д',
    'БУЛЬВАР', 'БУЛ', 'Б-Р',
    'НАБЕРЕЖНАЯ', 'НАБ',
    'ШОССЕ', 'ШОС', 'Ш',
    'МИКРОРАЙОН', 'МКР',
    'КВАРТАЛ', 'КВ-Л',   # КВ - квартира
    'ПЛОЩАДЬ', 'ПЛ',
    'АЛЛЕЯ', 'АЛ'
)

STREET_MARKERS_SET = frozenset(STREET_MARKERS)

HOUSE_MARKERS = (
    'Д', 'ДОМ', 'ДВЛД', 'ДОМОВЛАДЕНИЕ'
)

BUILDING_MARKERS = (
    'К', 'КОР', 'КОРП', 'КОРПУС',
    'ЛИТ', 'ЛИТЕР',
    'СТР', 'СТРОЕНИЕ'
)

APARTMENT_MARKERS = (
    'КВ', 'КВАРТИРА'
)


def normalize_address(data: str) -> str:
    if not isinstance(data, str):
        return ''
    all_markers = HOUSE_MARKERS + BUILDING_MARKERS + APARTMENT_MARKERS
    markers = '|'.join(sorted(all_markers, key=len, reverse=True))
    address = data.removeprefix('Адрес_регистрации_str: '.upper())
    address = address.strip().upper().replace('Ё', 'Е')
    address = re.sub(r'\s+', ' ', address)
    address = re.sub(r'\s*,\s*', ', ', address)
    address = re.sub(r',+', ',', address)
    address = re.sub(rf'\b({markers})(?=\d)', r'\1. ', address)
    address = re.sub(r'\.(?=[А-ЯA-Z0-9])', '. ', address)
    address = re.sub(r'\s+', ' ', address)
    return address.strip(',. ')


def check_latin(text: str) -> bool:
    return bool(re.search(r'[A-Z]', text))


def split_address(address: str) -> list[str]:
    return [part.strip() for part in address.split(',') if part.strip()]


def clean_name(data: str) -> str:
    value = re.sub(r'\s+', ' ', data)
    return value.strip(',. ')


def extract_postal_code(address: str) -> str | None:
    match = re.search(r'(?<!\d)(\d{6})(?!\d)', address)
    return match.group(1) if match else None


def extract_city(address: str) -> str | None:
    markers = '|'.join(CITY_MARKERS)
    markers_after = '|'.join(STREET_MARKERS + HOUSE_MARKERS + BUILDING_MARKERS)
    for part in split_address(address):
        for marker in CITY_MARKERS:
            match = re.search(rf'\b{marker}(?:\.|\b)\s*(?=[А-Я0-9])', part)
            if match:
                tail = part[match.end():]
                city_only = re.split(
                    rf'\s+(?:{markers_after})(?:\.|\b)',
                    tail,
                    maxsplit=1
                )[0]
                if len(clean_name(city_only).split()) >= 3:
                    return None
                return clean_name(city_only)
    match = re.search(
        r'[А-Я][А-Я\- ]*?\s*\b(?:' + markers + r')\.?\b', address
    )
    if match:
        return clean_name(match.group())
    match = re.search(
        r'\b(?:' + markers + r')\.?\s+[А-Я][А-Я\-]+'
        r'(?:\s+[А-Я][А-Я\-]+)*'
        r'(?=\s*,|\s+(?:' + markers_after + r')\b|$)',
        address,
    )
    return clean_name(match.group(1)) if match else None


def extract_city_by_list(address: str) -> str | None:
    all_markers_after = frozenset(
        STREET_MARKERS + HOUSE_MARKERS + BUILDING_MARKERS + APARTMENT_MARKERS
        )
    words = re.findall(r'[А-Я0-9\-]+', address)
    for start in range(len(words)):
        if start > 0 and words[start - 1] in all_markers_after:
            continue
        for n in range(min(MAX_CITY_WORDS, len(words) - start), 0, -1):
            candidate = ' '.join(words[start:start + n])
            if candidate in KNOWN_CITIES_SET:
                return candidate
    return None


def extract_street(address: str) -> str | None:
    markers = '|'.join(STREET_MARKERS)
    markers_after = '|'.join(HOUSE_MARKERS + BUILDING_MARKERS + APARTMENT_MARKERS)
    for part in split_address(address):
        for marker in STREET_MARKERS:
            match = re.search(rf'\b{marker}(?:\.|\b)\s*(?=[А-Я0-9])', part)
            if match:
                tail = part[match.start():]
                street_only = re.split(
                    rf'\s+\d[\d\-/А-Я]*(?=\s+(?:{markers_after})\b|$)'
                    rf'|\s+(?:{markers_after})(?:\.|\b)',
                    tail,
                    maxsplit=1
                )[0]
                result = clean_name(street_only)
                if result in STREET_MARKERS_SET:
                    return None
                if len(result.split()) >= 5:
                    return None
                return result
    match = re.search(
        r'[А-Я0-9][А-Я0-9\- ]*?\s*\b(?:' + markers + r')\.?\b', address
    )
    if match:
        result = clean_name(match.group())
        return result if check_street(result) else None
    match = re.search(
        r'\b(?:' + markers + r')\.?\s+'
        r'([А-Я][А-Я\- ]*?)'
        r'(?=\s+\d|\s+(?:' + markers_after + r')\b|$)',
        address,
    )
    if match:
        result = clean_name(match.group())
        return result if check_street(result) else None
    return None


def check_street(street: str) -> str | None:
    if street in STREET_MARKERS_SET:
        return None
    if len(street.split()) > 3:
        return None
    if street and '/' in street:
        return None
    return street


def extract_house(address: str) -> str | None:
    markers = '|'.join(HOUSE_MARKERS)
    markers_after = '|'.join(BUILDING_MARKERS + APARTMENT_MARKERS)
    for part in split_address(address):
        for marker in HOUSE_MARKERS:
            match = re.search(rf'\b{marker}(?:\.|\b)\s*(?=[0-9])', part)
            if match:
                tail = part[match.start():]
                house_only = re.split(
                    rf'\s+(?:{markers_after})(?:\.|\b)',
                    tail,
                    maxsplit=1
                )[0]
                return clean_name(house_only)
    match = re.search(
        r'[0-9][А-Я0-9\-/]*?\s*(?:' + markers + r')\.?\b', address
    )
    if match:
        return clean_name(match.group())
    match = re.search(
        r'\b(?:' + markers + r')\.?\s+'
        r'([0-9][А-Я0-9\-/]*?)'
        r'(?=\s+(?:' + markers_after + r')\b|\s*,|$)',
        address,
    )
    if match:
        return clean_name(match.group())
    match = re.search(
        r'(?<=[А-Я,])\s+(\d[\d\-/А-Я]*)'
        r'(?=\s+(?:' + markers_after + r')\b|\s*,|$)',
        address,
    )
    return clean_name(match.group()) if match else None


def extract_building(address: str) -> str | None:
    markers = '|'.join(BUILDING_MARKERS)
    markers_after = '|'.join(APARTMENT_MARKERS)
    for part in split_address(address):
        for marker in BUILDING_MARKERS:
            match = re.search(rf'\b{marker}(?:\.|\b)\s*(?=[0-9])', part)
            if match:
                tail = part[match.start():]
                house_only = re.split(
                    rf'\s+(?:{markers_after})(?:\.|\b)',
                    tail,
                    maxsplit=1
                )[0]
                return clean_name(house_only)
    match = re.search(
        r'\b(?:' + markers + r')\.?\s+'
        r'([0-9][А-Я0-9\-/]*?)'
        r'(?=\s+(?:' + markers_after + r')\b|\s*,|$)',
        address,
    )
    return clean_name(match.group()) if match else None


def extract_apartment(address: str) -> str | None:
    markers = '|'.join(APARTMENT_MARKERS)
    for part in split_address(address):
        for marker in APARTMENT_MARKERS:
            match = re.search(rf'\b{marker}(?:\.|\b)\s*(?=[0-9])', part)
            if match:
                tail = part[match.start():]
                if re.search(r'\d[А-Я]{3,}', tail):
                    return 'ERROR'
                return clean_name(tail)
    match = re.search(
        r'\b(?:' + markers + r')\.?\s+'
        r'([0-9][А-Я0-9\-/]*?)',
        address,
    )

    return clean_name(match.group()) if match else None


def parse_address(address: str) -> dict:
    if not isinstance(address, str) or not address:
        result = AddressResult(
            source='' if address is None else str(address),
            status='ERROR',
            comment='ПУСТО ИЛИ НЕКОРРЕКТНЫЙ',
        )
        return asdict(result)

    normalized = normalize_address(address)
    used_WARNING = False
    comment_WARNING = []

    if check_latin(normalized):
        used_WARNING = True
        comment_WARNING.append('ЛАТИНИЦА')

    postal_code = extract_postal_code(normalized) or ''
    city = extract_city(normalized)
    street = extract_street(normalized)
    house = extract_house(normalized)
    building = extract_building(normalized)
    apartment = extract_apartment(normalized)
    if city is None:
        city = extract_city_by_list(normalized)
    if street and re.search(rf'{re.escape(street)}\s+\d', normalized):
        used_WARNING = True
        comment_WARNING.append('УЛИЦА И ДОМ ОПРЕДЕЛЕНЫ ЭВРИСТИЧЕСКИ')

    missing = []
    if not city:
        missing.append('город')
    if not street:
        missing.append('улица')
    if not house:
        missing.append('дом')
    if apartment == 'ERROR':
        missing.append('квартира')

    if missing:
        status = 'ERROR'
        city = normalized
        street = ''
        house = ''
        building = ''
        apartment = ''
        comment = 'АДРЕС: НЕ РАСПОЗНАН'
    elif used_WARNING:
        status = 'WARNING'
        comment = '; '.join(comment_WARNING)
    else:
        status = 'GOOD'
        comment = ''

    result = AddressResult(
        source=address,
        normalized=normalized,
        country='РОССИЯ',
        postal_code=postal_code,
        city=city or '',
        street=street or '',
        house=house or '',
        building=building or '',
        apartment=apartment or '',
        status=status,
        comment=comment,
    )

    return asdict(result)



if __name__ == "__main__":
    test_addresses = [
        "СПБ, Московское шоссе 16 корпус 1, квартира 70",
        "Г. Барнаул.Советской Армии 50 а к/2 КВ 69",
        "Краснодарский край, г. Тихорецк, ул. К. Либкнехта, 29",
        "Республика Башкортостан, Зианчуринский район, С. Ишемгул, во. Чекмарёва д. 43",
        "Г. Тамбов узловой проезд дом 1",
        "Москва, Балаклавский пр. 4к1, 65",
        "г. Солнечногорск, парковый бульвар, д.2 корп 2, кВ. 376МОСКВА",
        "Москва, Огородный проезд 21акб кв22Москва",
        "454084, Россия, Челябинск, ул. Братьев Кашириных, 129.",
        "Московская область г. Голубое Парковый бульвар, д.2 кВ. 376В",
        "Самарская область Волжский район мкр Южный город Алабина 30 кВ 142",
        "Воронеж Москвоский пр-кт 130к1",
        "Иваново, мкр 30, д 19, кв 137",
        "Москва Дмитровское шоссе 75/77 кв211",
        "Ростов-на-Дону бульвар Комарова 12/2 а кВ 91",
        "Воронеж московский пр-кт 130к1",
        "Московская обл. Раменский р-н г. Раменское Спортивный пр-д д. 6 КВ. 178",
        "Москва Дмитровское шоссе 75/77 кв211",
    ]

    for addr in test_addresses:
        parsed = parse_address(addr)
        print(f"{'─' * 70}")
        print(f"ВХОД:     {addr}")
        print(f"НОРМ:     {parsed['normalized']}")
        print(f"ИНДЕКС:   {parsed['postal_code']}")
        print(f"ГОРОД:    {parsed['city']}")
        print(f"УЛИЦА:    {parsed['street']}")
        print(f"ДОМ:      {parsed['house']}")
        print(f"КОРПУС:   {parsed['building']}")
        print(f"КВАРТИРА: {parsed['apartment']}")
        print(f"status: {parsed['status']}")
        print(f"comment: {parsed['comment']}")
        print(f"{'_' * 70}")
