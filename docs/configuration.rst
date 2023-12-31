Configuration
=============

The configuration file is named ``config.ini`` and is located in sub directory
``vocabuilder`` inside directory ``user_config_dir`` as defined
by the `platformdirs <https://pypi.org/project/platformdirs/>`_ package.

.. note::
    You can open the config file by selecting
    ``File -> Edit config file`` from the menu in the main window.

The syntax is described in the documentation for the
`configparser <https://docs.python.org/3/library/configparser.html>`_ module
in the Python standard library.

By adding values to the config file you can change things like:

* Window and dialog sizes,
* font sizes,
* font colors,
* firebase configuration,
* other platform specific behaviors.

See the default config file
`default_config.ini <https://github.com/hakonhagland/vocabuilder/tree/main/src/vocabuilder/data/default_config.ini>`_
for the currently supported options and their default values.
