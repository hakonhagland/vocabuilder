Firebase
========

Synchronization with firebase
-----------------------------

This feature is under development.

Plan for implementation
-----------------------

* Connect local database with firebase cloud database
* Use a separate script if you want to reset the firebase database to the current local database
* If you use this script from serveral devices with the same firebase database,
   * Data is only synchronized (downloaded) with firebase database at app startup
     or when explicitly requested
   * Data is uploaded continuously (each time something in the database is modified locally)
