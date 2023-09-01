Suggesting changes to the code
==============================

Suggestions for improvements are very welcome. Please use the
`GitHub issue tracker <https://github.com/hakonhagland/vocabuilder/issues>`_ or submit
a pull request!

Pull request
------------

To set up an environment for developing and submitting a pull request, you could:

* Install pyenv
* Install the python versions listed in
  `.python_version <https://github.com/hakonhagland/vocabuilder/blob/main/.python-version>`_ with pyenv
* On Linux and MacOs:
   * Install poetry : Run : ``curl -sSL https://install.python-poetry.org | python3 -``
   * On macOS: update PATH environment variable in your `~/.zshrc` init file:
     ``export PATH="/Users/username/.local/bin:$PATH"`` such that zsh can find the ``poetry`` command
* On Windows (powershell):
   * Install poetry :
     ``(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | py -``
   * update ``PATH`` to include the install folder, e.g.
     ``C:\Users\username\AppData\Roaming\Python\Scripts``

* Then, from the root directory of this repository:
   * run ``poetry install`` to install dependencies into a virtual environment
   * run ``poetry install --all-extras`` to install the sphinx extras for documentation
   * run ``poetry shell`` to activate the virtual environment
   * run ``pytest`` to run the test suite
   * run ``pre-commit install`` to install the pre-commit hooks
   * run ``make coverage`` to run unit tests and generate coverage report
   * run ``make docker-image`` to build docker image
   * run ``make run-docker-image`` to run the docker image
