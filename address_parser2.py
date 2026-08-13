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
        "Адрес_регистрации_str: Город Сочи адлерский р-он с. Казачий брод ул краснофлотская дом 26 «снт Солнышко»",
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
