Configuration
=============

The configuration file is named ``config.ini`` and is located in ``user_config_dir`` as defined
by the `platformdirs <https://pypi.org/project/platformdirs/>`_ package.

The language used in the file should follow the syntax described by the
`configparser <https://docs.python.org/3/library/configparser.html>`_ module
in the Python standard library.

By adding values to the config file you can change things like:

* window and dialog sizes,
* font sizes,
* font colors,
* other platform specific behaviors.

See the source code for
`read_config() <https://github.com/hakonhagland/vocabuilder/blob/10e95f4b12fd4038545caea2b879e75a9ef11333/src/vocabuilder/vocabuilder.py#L393>`_
for the currently supported options and their default values.
