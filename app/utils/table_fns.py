from typing import Iterable

from loguru import logger


def delete_fields(
    fields, *, rows: Iterable[dict] | None = None, row: dict | None = None
):
    if not (rows or row):
        msg = "Either rows or row must be provided"
        raise ValueError(msg)

    if row:
        single_row = True
        rows = [row]
    else:
        single_row = False
        rows = list(rows)

    for row in rows:
        logger.debug(f"Deleting fields {fields} from row {row}")
        for field in fields:
            if field in row:
                del row[field]

    if single_row:
        return row

    logger.debug(f"Deleted fields {fields} from rows {rows}")
    return rows
