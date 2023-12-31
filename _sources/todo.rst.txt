TODO (further work)
===================

* Other apps: Anki, Glossika, HelloTalk: https://youtu.be/U_SAcVGFpag
* Add feature: integration with Google Translate. Speak the word with correct pronunciation.
* Make the items in the view window selectable and copyable. CTRL-C should copy the
  selected item to the clipboard.
* View window: Update list of terms when the database is updated.
* Finish Firebase implementation. Firebase is only synchronized at the start
  of the program. We need to update continuously. We also need to implement a way to
  clean up duplicated and deleted entries in the Firebase database like we do for the local
  database.
* If an item is renamed, the item is not deleted from Firebase?
* If several devices (e.g. android, iPad, laptop) are used at the same time, we
  must continuously check Firebase for updates (on each device).
* Implement delete button. It should enable the user to delete a term from the
  database.
* Fix docker image such that it will run under x11docker.
* Add locking mechanism. The user should not be able to open more than one instance
  of the app editing the same database at the same time.
* Add documentation for Python source code. Transfer this to sphinx docs.
* Add feature: Improve the usability of the app by adding a tag field to each data item.
  Currently, all items implicitly have the tag “Translation”. But the user may choose to
  tag an item as “conjugation” for example. And it will allow the user to add items
  representing the conjugations of a word and later limit the practice session to all
  items with a given tag, e.g. “conjugation”. The app may also choose to present a different
  layout of the GUI for practicing “conjugations” compared to practicing “translations”..
* Tooltip with translation at mouse hover in the list of terms that appears when
  selecting a new term to add to the database.
* Add an icon for the app. Start with Linux. Then add icon for Windows and Mac.
* When practicing from list (not random) add option to override "practice delay" when selecting terms
  from the list
