# Information about the source code

For those interested, the project was created by poetry:
```
$ poetry new --src myproject
```

Since I wanted to be able to execute the `main()` function in the `vocabuilder.py` module as a
separate CLI script called `vocabuilder` after installing the project,
I added the following section to the `pyproject.toml` file:

```
[tool.poetry.scripts]
vocabuilder = "vocabuilder.vocabuilder:main"
```

Then, using `poetry add ...` I added some dependencies to the project resulting in the following being added to `pyproject.toml`:

```
[tool.poetry.dependencies]
python = "^3.9"
platformdirs = "^3.8.0"
pyqt6 = "^6.5.1"
configparser = "^5.3.0"
pathlib = "^1.0.1"
gitpython = "^3.1.31"
```

Then, pytest was added as a development dependency using `poetry add --group=dev pytest`.

I added a licence and a repository to the `tool.poetry` section of `pyproject.toml`.

To install the dependencies and the `vocabuilder` script into a virtual env I ran:

```
$ poetry install
```

Then entered the virtual env with

```
$ poetry shell
```

To run the tests from here:

```
(vocabuilder-py3.10) $ pytest
```

and to run the script:

```
(vocabuilder-py3.10) $ vocabuilder
```

To install the script globally on my computer (in development mode), exit the venv:

```
(vocabuilder-py3.10) $ exit
```

Then run `pip install` from the project root:

```
$ pip install -e .
```
