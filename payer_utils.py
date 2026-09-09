import re
import pandas as pd


def _normalize_key(value) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if text.lower() == "nan":
        return ""
    text = re.sub(r'\s+', ' ', value)
    text = re.sub(r'\.0$', '', value)
    return text.upper()


def build_reference_dict(ref_df: pd.DataFrame) -> dict:
    for col in ('INN', 'market', 'Payer BAN'):
        if col not in ref_df.columns:
            raise ValueError(f'В справочнике отсутствует колонка: {col}')

    reference_dict = {}
    for _, ref_row in ref_df.iterrows():
        raw_inn = ref_row['INN']
        if pd.notna(raw_inn):
            if isinstance(raw_inn, float):
                raw_inn = str(int(raw_inn))
            else:
                raw_inn = str(raw_inn)
            key_inn = _normalize_key(raw_inn)
        else:
            key_inn = ''

        key_market = _normalize_key(str(ref_row['market'])) if pd.notna(ref_row['market']) else ''
        val_ban = str(ref_row['Payer BAN']).strip() if pd.notna(ref_row['Payer BAN']) else ''

        if key_inn and key_market:
            reference_dict[(key_inn, key_market)] = val_ban
    return reference_dict