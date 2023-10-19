TODO (further work)
===================

* Refactor firebase database structure. Instead of using the same logic as for
  the local database where we push new entries at the end of the file and clean up duplicates
  later when needed, we should use the term as the key and use the update() or transaction()
  method to update an existing entry directly. This will make it easier to keep the local
  and firebase databases in sync and make it simpler to delete entries from the database.

* Finish Firebase implementation. Firebase is only synchronized at the start
  of the program. We need to update continuously. We also need to implement a way to
  clean up duplicated and deleted entries in the firebase database like we do for the local
  database.
* If several devices (e.g. android, iPad, laptop) are used at the same time, we
  must continuously check firebase for updates (on each device).
* Implement view button. It should open a view of the local database content. This window
  could be non-blocking, so the user could keep this window open while also running
  a practice session from the test window.
* Implement delete button. It should enable the user to delete a term from the
  database.
* Fix edit config option. Currently, the app will not quit until the editor has exited.
  The implementation of a daemon process will be necessary, and implementation will be
  different on different platforms.
* Fix docker image such that it will run under x11docker.
* Add locking mechanism. The user should not be able to open more than one instance
  of the app editing the same database at the same time.
* Add documentation for Python source code. Transfer this to sphinx docs.
* Add feature: Improve the usability of the app by adding a tag field to each data item.
  Currently, all items implicitly have the tag “Translation”. But the user may choose to
  tag an item as “conjugation” for example. And it will allow the user to add items
  representing the conjugations of a word and later limit the practice session to all
  items with a given tag, e.g. “conjugation”. The app may also choose to present a different
  layout of the gui for practicing “conjugations” compared to practicing “translations”..
* Tooltip with translation at mouse hover in the list of terms that appears when
  selecting a new term to add to the database.
* Add an icon for the app. Start with Linux. The add icon for Windows and Mac.
* When practicing from list (not random) add option to override delay when selecting terms
  from the list
* Add documentation for standard keyboard shortcuts in ``LineEdit`` and ``TextEdit`` widgets.
  ``Ctrl+Backspace`` deletes the word to the left of the cursor. ``Ctrl+Delete`` deletes the
  word to the right of the cursor. ``Ctrl+Left`` moves the cursor to the beginning of the
  word to the left of the cursor. ``Ctrl+Right`` moves the cursor to the end of the word to
  the right of the cursor. ``Ctrl+Shift+Left`` selects the word to the left of the cursor.
  ``Ctrl+Shift+Right`` selects the word to the right of the cursor. ``Ctrl+Shift+Home``
  selects all text from the cursor to the beginning of the line. ``Ctrl+Shift+End`` selects
  all text from the cursor to the end of the line. ``Ctrl+Shift+Up`` selects all text from
  the cursor to the beginning of the document. ``Ctrl+Shift+Down`` selects all text from
  the cursor to the end of the document. ``Ctrl+Shift+Backspace`` deletes all text from the
  cursor to the beginning of the line. ``Ctrl+Shift+Delete`` deletes all text from the
  cursor to the end of the line.
