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

Creating a firebase database
----------------------------

* Go to https://firebase.google.com/
* Create a new project

.. image:: images/firebase_create_project.png
   :width: 600px


* Go to the database section
* Create a new database

.. image:: images/firebase_create_database.png
   :width: 600px

* Select "Start in test mode"
* Go to the "Rules" tab
* Replace the content of the text box with the following:

.. code-block:: json

    {
      "rules": {
        ".read": true,
        ".write": true
      }
    }

* Click on "Enable"

Downloading the firebase credentials
------------------------------------

* Go to the settings of your firebase project
* Go to the "Service accounts" tab
* Click on "Generate new private key"
* Save the json file somewhere on your computer
* In the :doc:`vocabuilder config file <configuration>`, set the path to the json file in the "Firebase" section:

.. code-block:: yaml

    [Firebase]
    credentials = /path/to/credentials.json

Saving the database URL
-----------------------

* Go to the realtime database section of your firebase project
* Go to the data tab
* Copy the URL of your database
* In the :doc:`vocabuilder config file <configuration>`, insert the URL in the "Firebase" section:

.. code-block:: yaml

    [Firebase]
    databaseURL = https://your-project.firebasedatabase.app
