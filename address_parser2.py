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
    address = data.removeprefix('Адрес_регистрации_str: ')
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
                tail = part[match.start():]
                city_only = re.split(
                    rf'\s+(?:{markers_after})(?:\.|\b)',
                    tail,
                    maxsplit=1
                )[0]
                return clean_name(city_only)
    match = re.search(
        r'[А-Я][А-Я\- ]*?\s*(?:' + markers + r')\.?\b', address
    )
    if match:
        return clean_name(match.group())
    match = re.search(
        r'\b(?:' + markers + r')\.?\s+[А-Я][А-Я\-]+'
        r'(?:\s+[А-Я][А-Я\-]+)*'
        r'(?=\s*,|\s+(?:' + markers_after + r')\b|$)',
        address,
    )
    return clean_name(match.group()) if match else None


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
                return clean_name(street_only)
    match = re.search(
        r'[А-Я0-9][А-Я0-9\- ]*?\s*(?:' + markers + r')\.?\b', address
    )
    if match:
        return clean_name(match.group())
    match = re.search(
        r'\b(?:' + markers + r')\.?\s+'
        r'([А-Я][А-Я\- ]*?)'
        r'(?=\s+\d|\s+(?:' + markers_after + r')\b|$)',
        address,
    )
    return clean_name(match.group()) if match else None


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
            comment='АДРЕС: ПУСТО ИЛИ НЕКОРРЕКТНЫЙ',
        )
        return asdict(result)

    normalized = normalize_address(address)
    used_WARNING = False
    comment_WARNING = []

    if check_latin(normalized):
        used_WARNING = True
        comment_WARNING.append('АДРЕС: ЛАТИНИЦА')

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
        comment_WARNING.append('АДРЕС: УЛИЦА И ДОМ ОПРЕДЕЛЕНЫ ЭВРИСТИЧЕСКИ')

    missing = []
    if not city:
        missing.append('город')
    if not street:
        missing.append('улица')
    if not house:
        missing.append('дом')

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
        comment = {"; ".join(comment_WARNING)}
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
        "Адрес_регистрации_str: Московская обл., г. Электросталь, проезд Полярный, д. 5А, кв. 27",
        "Адрес_регистрации_str: Г. САНКТ-ПЕТЕРБУРГ, УЛИЦА ОКТЯБРЬСКАЯ НАБ. Д. 90, К. 6, КВ. 64",
        "Адрес_регистрации_str: Красноярск ул.Матросова д.40 кв.146",
        "Адрес_регистрации_str: г. Новосибирск ул. Фрунзе 20-135",
        "Адрес_регистрации_str: 624250 Российская Федерация, обл Свердловская, г Заречный, ул Ленина, д. 35А, кв. 57",
        "Адрес_регистрации_str: Верхняя салда Карла Либкнехта д.1, кв. 11",
        "Адрес_регистрации_str: г. Новocибирск, ул. Фрунзе 20-135",
        "Адрес_регистрации_str: Республика Башкортостан Татышлинский район село Ялгы-Нарат улица Центральная дом 15",
        "Адрес_регистрации_str: г. Ижевск, ул. Березняковская, д. 2",
        "Адрес_регистрации_str: Республика Башкортостан, г. Ишiмбай, ул. Гагарина, д. 28, кв. 72",
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
