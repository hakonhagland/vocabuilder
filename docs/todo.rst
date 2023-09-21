TODO (further work)
===================

* Finish Firebase implementation
* Implement view button. It should open a view of the local database content.
* Implement delete button. It should enable the user to delete a term from the
  database.
* Fix edit config option. Currently the app will not quit until the editor has exited.
  The implementation of a daemon process will be necessary, and implementation will be
  different on different platforms.
* Fix docker image such that it will run under x11docker.
* Add locking mechanism. The user should not be able to open more than one instance
  of the app editing the same database at the same time.
* Add documentation for Python source code. Transfer this to sphinx docs.
* Add feature: Improve the usability of the app by adding a tag field to each data item.
  Currently all items implicitly have the tag “Translation”. But the user may choose to
  tag an item as “conjugation” for example. And it will allow the user to add items
  representing the conjugations of a word and later limit the practice session to all
  items with a given tag, e.g. “conjugation”. The app may also choose to present a different
  layout of the gui for practicing “conjugations” compared to practicing “translations”..
* Tooltip with translation at mouse hover in the list of terms that appears when
  selecting a new term to add to the database.
