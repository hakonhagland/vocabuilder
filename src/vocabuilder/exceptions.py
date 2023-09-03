class CommandLineException(Exception):
    def __init__(self, value: str):
        self.value = value

    def __str__(self) -> str:
        return f"Command line exception: {self.value}"


class ConfigException(Exception):
    def __init__(self, value: str):
        self.value = value

    def __str__(self) -> str:
        return f"Config exception: {self.value}"


class CsvFileException(Exception):
    def __init__(self, value: str):
        self.value = value

    def __str__(self) -> str:
        return f"CSV file exception: {self.value}"


class DatabaseException(Exception):
    def __init__(self, value: str):
        self.value = value

    def __str__(self) -> str:
        return f"Database exception: {self.value}"


class SelectVocabularyException(Exception):
    def __init__(self, value: str):
        self.value = value

    def __str__(self) -> str:
        return f"Select vocabulary exception: {self.value}"
