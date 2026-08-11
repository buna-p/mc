import re
from datetime import datetime

from address_parser import parse_address


def safe_str(val) -> str:
    if val is None:
        return ''
    if isinstance(val, float) and val != val:
        return ''
    return str(val).strip().upper()


def del_prefix(data: str, prefix: str) -> str:
    data = data.strip()
    data = data.removeprefix(prefix.upper())
    data = data.strip()
    return data


def format_date(val: str) -> str:
    try:
        return datetime.strptime(val[:10], '%Y-%m-%d').strftime('%d.%m.%Y')
    except ValueError:
        return ''


def extract_fio(data: str) -> tuple[str, str, str, str]:
    data = del_prefix(data, 'ФИО_str: ')
    patronymics = ["ОГЛЫ", "ОГЛУ", "УУЛУ", "УЛЫ", "КЫЗЫ", "КЫЗЫСЫ", "ГЫЗЫ",]
    if not data:
        return '', '', '', 'ФИО: ПУСТО'
    parts = [p for p in data.split() if p]
    if len(parts) > 3:
        if parts[3] in patronymics:
            return parts[0], parts[1], parts[2] + parts[3], ''
        return data, '', '', 'ФИО: НЕ РАСПОЗНАНЫ'
    elif len(parts) == 3:
        return parts[0], parts[1], parts[2], ''
    elif len(parts) == 2:
        return parts[0], parts[1], '', ''
    return data, '', '', 'ФИО: НЕ РАСПОЗНАНЫ'


def extract_passport_details(data: str) -> tuple[str, str, str]:
    passport_data = del_prefix(data, 'Seriya_i_nomer_pasporta_str: ')
    if not passport_data:
        return '', '', 'ПД: ПУСТО'
    passport_data = re.sub(r'\D', '', passport_data)
    if len(passport_data) == 10:
        series, number = passport_data[:4], passport_data[4:]
    else:
        return passport_data, '', 'ПД: НЕ РАСПОЗНАНЫ'
    return series, number, ''


def extract_passport_date(data: str) -> tuple[str, str]:
    passport_date = del_prefix(data, 'Data_vydachi_pasporta_str: ')
    if not passport_date:
        return '', 'ДАТА ВЫДАЧИ ПАСПОРТА: ПУСТО'
    passport_date = format_date(passport_date)
    if not passport_date:
        return data, 'ДАТА ВЫДАЧИ ПАСПОРТА: НЕ РАСПОЗНАНА'
    return passport_date, ''


def extract_passport_code(data: str) -> tuple[str, str]:
    passport_code = del_prefix(data, 'Kod_podrazdeleniya_str: ')
    if not passport_code:
        return '', 'КП: ПУСТО'
    digits = re.sub(r'\D', '', passport_code)
    if len(digits) == 6:
        return f'{digits[:3]}-{digits[3:]}', ''
    return passport_code, 'КП: НЕ РАСПОЗНАН'


def extract_issued_by(data: str) -> tuple[str, str]:
    issued_by = del_prefix(data, 'Кем_выдан_str: ')
    if not issued_by:
        return '', 'КЕМ ВЫДАН: ПУСТО'
    return issued_by, ''


def extract_birth_date(data: str) -> tuple[str, str]:
    birth_date = del_prefix(data, 'Дата_рождения_date: ')
    if not birth_date:
        return '', 'ДР: ПУСТО'
    birth_date = format_date(birth_date)
    if not birth_date:
        return data, 'ДР: НЕ РАСПОЗНАНА'
    return birth_date, ''


def extract_place_of_birth(data: str) -> tuple[str, str]:
    place_of_birth = del_prefix(data, 'Место_рождения_str: ')
    if not place_of_birth:
        return '', 'МЕСТО РОЖДЕНИЯ: ПУСТО'
    return place_of_birth, ''


def extract_gender(data: str) -> tuple[str, str]:
    gender = del_prefix(data, 'Пол_str: ')
    if not gender:
        return '', 'ПОЛ: ПУСТО'
    if len(gender) != 1:
        gender = gender[:1]
    if gender not in {'М', 'Ж'}:
        return gender, 'ПОЛ: НЕ РАСПОЗНАН'
    return gender, ''


def extract_quantity(data: str) -> str:
    quantity = del_prefix(data, 'Количество_номеров_str: ')
    if not quantity:
        return '1'
    return quantity


def extract_email(data: str, email_prefix: str) -> str:
    email = del_prefix(data, email_prefix)
    if not email:
        return ''
    return email


def extract_city(data: str) -> tuple[str, str]:
    city = del_prefix(data, 'Gorod_podklyucheniya_str: ')
    if not city:
        return city, 'ГОРОД ПОДКЛЮЧЕНИЯ: ПУСТО'
    return city, ''


def process_row(row) -> dict:
    errors = []
    case_type = safe_str(row.get('Case_Type_3', ''))
    CASE_ID = safe_str(row.get('CASE_ID', ''))
    column_1 = safe_str(row.get('column_1', ''))  # колво или номер
    column_2 = safe_str(row.get('column_2', ''))  # ФИО
    column_3 = safe_str(row.get('column_3', ''))  # серия номер паспорта
    column_4 = safe_str(row.get('column_4', ''))  # дата выдачи паспорта
    column_5 = safe_str(row.get('column_5', ''))  # код подразделения
    column_6 = safe_str(row.get('column_6', ''))  # кем выдан
    column_7 = safe_str(row.get('column_7', ''))  # др
    column_8 = safe_str(row.get('column_8', ''))  # место рождения
    column_9 = safe_str(row.get('column_9', ''))  # адрес регистрации
    column_10 = safe_str(row.get('column_10', ''))  # пол
    column_13 = safe_str(row.get('column_13', ''))
    # column_14 = safe_str(row.get('column_14', '')) конт тлф
    column_15 = safe_str(row.get('column_15', ''))
    column_16 = safe_str(row.get('column_16', ''))
    if case_type == 'МК.Новое включение Лендинг промо':
        quantity = extract_quantity(column_1)
        gorod_podkl, gorod_podkl_error = extract_city(column_16)
        if gorod_podkl_error:
            errors.append(gorod_podkl_error)
        email_prefix = 'E_mail_str: '
        contact_email = extract_email(column_13, email_prefix)
        delivery_email = ''
    elif case_type == 'МК.MNP. Нет временного номера':
        quantity = 1
        gorod_podkl, gorod_podkl_error = extract_city(column_15)
        if gorod_podkl_error:
            errors.append(gorod_podkl_error)
        email_prefix = 'Контактный_e_mail_CRQ453539_str: '
        contact_email = extract_email(column_13, email_prefix)
        delivery_email = extract_email(column_13, email_prefix)
    surname, name, patronymic, fio_error = extract_fio(column_2)
    if fio_error:
        errors.append(fio_error)
    series, number, passport_error = extract_passport_details(column_3)
    if passport_error:
        errors.append(passport_error)
    passport_date, passport_date_error = extract_passport_date(column_4)
    if passport_date_error:
        errors.append(passport_date_error)
    passport_code, passport_code_errors = extract_passport_code(column_5)
    if passport_code_errors:
        errors.append(passport_code_errors)
    issued_by, issued_by_errors = extract_issued_by(column_6)
    if issued_by_errors:
        errors.append(issued_by_errors)
    birth_date, birth_date_error = extract_birth_date(column_7)
    if birth_date_error:
        errors.append(birth_date_error)
    place_of_birth, place_of_birth_errors = extract_place_of_birth(column_8)
    if place_of_birth_errors:
        errors.append(place_of_birth_errors)
    gender, gender_errors = extract_gender(column_10)
    if gender_errors:
        errors.append(gender_errors)
    parsed_address = parse_address(column_9)
    address_status = parsed_address.get('status', 'ERROR')
    address_comments = parsed_address.get('comment', '')
    if address_status in ('MANUAL', 'ERROR'):
        errors.append(f'АДРЕС: {address_comments}' if address_comments
                      else f'АДРЕС: {address_status}')
    return {
        'КОЛ_ВО': quantity,
        'Комментарий': CASE_ID,
        'Маркет код': gorod_podkl,
        'Фамилия': surname,
        'Имя': name,
        'Отчество': patronymic,
        'ДатаРождения': birth_date,
        'СерияДокумента': series,
        'НомерДокумента': number,
        'КемВыданДокумент': issued_by,
        'ДатаВыдачиДокумента': passport_date,
        'КодПодразделения': passport_code,
        'Пол': gender,
        'МестоРождения': place_of_birth,
        'ИндексРГ': parsed_address.get('postal_code') or '',
        'ГородРГ': parsed_address.get('city') or '',
        'УлицаРГ': parsed_address.get('street') or '',
        'ДомРГ': parsed_address.get('house') or '',
        'КорпусРГ': parsed_address.get('building') or '',
        'КвартираРГ': parsed_address.get('apartment') or '',
        'ИндексПР':  parsed_address.get('postal_code') or '',
        'ГородПР': parsed_address.get('city') or '',
        'УлицаПР': parsed_address.get('street') or '',
        'ДомПР': parsed_address.get('house') or '',
        'КорпусПР': parsed_address.get('building') or '',
        'КвартираПР': parsed_address.get('apartment') or '',
        'Email (ДляКонтактов)': contact_email,
        'Email (ДляДоставкиСчетов)': delivery_email,
        'СТАТУС': 'ERROR' if errors else address_status,
        'ОШИБКИ': '; '.join(errors),
    }