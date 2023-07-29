import vocabuilder.vocabuilder

# from .conftest import config_object, config_dir_path


class TestGeneral:
    def test_construct(self) -> None:
        name = vocabuilder.vocabuilder.select_vocabulary()
        assert name == "english-korean"
