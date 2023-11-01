from __future__ import annotations
import csv

from pathlib import Path
from types import TracebackType
from typing import Literal, Optional
from vocabuilder.exceptions import CsvFileException
from vocabuilder.type_aliases import DatabaseRow, DatabaseValue


class CsvDatabaseHeader:
    """
    * status        : 0 = The item has been deleted, 1, 2, 3,.. the item is not deleted
    * term1         : "From" term
    * term2         : "To" term (translation of Term1)
    * test_delay    : Number of days to next possible test, 0 or negative means no delay
    * last_test     : timestamp (epoch) of last time this term was practiced
    * last_modified : timestamp (epoch) of last time any of the previous was modified
    """

    status = "Status"
    term1 = "Term1"
    term2 = "Term2"
    test_delay = "TestDelay"
    last_test = "LastTest"
    last_modified = "LastModified"
    header = [status, term1, term2, test_delay, last_test, last_modified]
    types = {
        status: int,
        term1: str,
        term2: str,
        test_delay: int,  # NOTE: unit is days
        # NOTE: epoch value: when an item is added, last_test is set to "now"
        last_test: int,
        last_modified: int,  # NOTE: epoch value
    }


class CSVwrapper:
    def __init__(self, dbname: Path):
        self.quotechar = '"'
        self.delimiter = ","
        self.filename = str(dbname)
        self.header = CsvDatabaseHeader()

    def append_line(self, row_dict: DatabaseRow) -> None:
        row = self.dict_to_row(row_dict)
        self.append_row(row)

    def append_row(self, row: list[DatabaseValue]) -> None:
        with open(self.filename, "a", newline="", encoding="utf_8") as fp:
            csvwriter = csv.writer(
                fp,
                delimiter=self.delimiter,
                quotechar=self.quotechar,
                quoting=csv.QUOTE_MINIMAL,
            )
            csvwriter.writerow(row)

    def dict_to_row(self, row_dict: DatabaseRow) -> list[DatabaseValue]:
        row = []
        for key in self.header.header:
            row.append(row_dict[key])
        return row

    def open_for_read(self, header: CsvDatabaseHeader) -> "CSVwrapperReader":
        return CSVwrapperReader(self, self.filename, header)

    def open_for_write(self) -> "CSVwrapperWriter":
        return CSVwrapperWriter(self, self.filename)


class CSVwrapperReader:
    """Context manager for reading lines from the database csv file"""

    def __init__(self, parent: CSVwrapper, filename: str, header: CsvDatabaseHeader):
        self.parent = parent
        self.header = header
        self.fp = open(filename, "r", encoding="utf_8")
        self.csvh = csv.DictReader(
            self.fp,
            delimiter=self.parent.delimiter,
            quotechar=self.parent.quotechar,
        )

    def __enter__(self) -> CSVwrapperReader:
        return self

    def __exit__(
        self,
        type: Optional[type[BaseException]],
        value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> Literal[False]:
        self.fp.close()
        return False  # TODO: handle exceptions

    def __iter__(self, start: int = 0) -> CSVwrapperReader:
        return self

    def __next__(self) -> dict[str, DatabaseValue]:
        try:
            row = next(self.csvh)
        except StopIteration as e:
            raise e
        self.fixup_datatypes(row)
        return row

    def fixup_datatypes(self, row: dict[str, str]) -> None:
        """NOTE: this method modifies the input argument 'row'"""
        for key in row:
            try:
                row[key] = self.header.types[key](
                    row[key]
                )  # cast the element to the correct type
            except TypeError as exc:
                raise CsvFileException("Bad type found in CSV file") from exc


class CSVwrapperWriter:
    """Context manager for writing lines to the database csv file"""

    def __init__(self, parent: CSVwrapper, filename: str):
        self.parent = parent
        self.fp = open(filename, "w", newline="", encoding="utf_8")
        self.csvwriter = csv.writer(
            self.fp,
            delimiter=self.parent.delimiter,
            quotechar=self.parent.quotechar,
            quoting=csv.QUOTE_MINIMAL,
        )

    def __enter__(self) -> CSVwrapperWriter:
        return self

    def __exit__(
        self,
        type: Optional[type[BaseException]],
        value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> Literal[False]:
        self.fp.close()
        return False  # TODO: handle exceptions

    def writerow(self, row: list[DatabaseValue]) -> None:
        self.csvwriter.writerow(row)

    def writeline(self, row_dict: DatabaseRow) -> None:
        row = self.parent.dict_to_row(row_dict)
        self.csvwriter.writerow(row)
