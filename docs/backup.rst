Creating backup
===============

Your database is backed up to a local git repository when you start the app
or when you click the ``Backup`` button. From the backup repository you may
recovery any earlier state of your vocabulary database.

The git backup repository is located in ``user_data_dir`` as defined by the
`platformdirs <https://pypi.org/project/platformdirs/>`_ package

Extension to `firebase <https://firebase.google.com/>`_ cloud backup is planned.
