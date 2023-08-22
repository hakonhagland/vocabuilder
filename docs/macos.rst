MacOS
=====

Keyboard shortcuts
------------------

Most buttons have :doc:`keyboard shortcuts <shortcuts>` but these are disabled by default on MacOS,
see the `QT documentation <https://doc.qt.io/qt-6/qshortcut.html#details>`_.

By setting the :doc:`config value <configuration>` ``MacOS.EnableAmpersandShortcut``
to ``true`` you can enable these shortcuts.

However, because mnemonic shortcuts do not fit in with
`Aqua's <https://en.wikipedia.org/wiki/Aqua_(user_interface)>`_ guidelines,
Qt will not show the shortcut character as underlined, see the
`QT documentation <https://doc.qt.io/qt-6/qshortcut.html#details>`_ for more information.
