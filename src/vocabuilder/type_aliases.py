# from vocabuilder.csv_helpers import CsvDatabaseHeader

# -----------------
#   Type aliases
# ----------------

DatabaseValue = str | int | None
DatabaseRow = dict[str, DatabaseValue]
DatabaseType = dict[str, DatabaseRow]
