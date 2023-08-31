Usage
=====

Installation
------------

To install the vocabuilder script:

* Ensure that you have Python version 3.10 or higher
* Download the git source:

.. code-block:: bash

    $ git clone --depth=1 https://github.com/hakonhagland/vocabuilder.git
    $ cd vocabuilder
    $ python -m venv .venv  # optionally create venv
    $ source .venv/bin/activate
    $ pip install .

.. note::
    On Windows (powershell) type ``.\.venv\Scripts\Activate.ps1`` to activate the venv


Running
-------

In the terminal window type:

.. code-block:: bash

    $ vocabuilder

This will present you with a dialog window to enter the name of the new vocabulary to create.
For example, if you are an english speaking person and plan to learn korean you could call
it "english-korean".

An alternative is to provide the name on the command line:

.. code-block:: bash

    $ vocabuilder english-korean

If you exit the app, it will remember the last used vocabulary name, so you do not have to
specify it on the command line the next time.

If you want to work on more than one vocabulary, you can create a new one by specifying a
different name on the command line.
