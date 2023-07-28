Installing XOA Chimera Core
===========================

XOA Chimera Core is available to install via the `Python Package Index <https://pypi.org/>`_. You can also install from the source file.

Prerequisites
-------------

Before installing XOA Chimera Core, please make sure your environment has installed:
    
* `Python`_
* `pip`_

Python
^^^^^^

XOA Chimera Core requires that you `install Python <https://realpython.com/installing-python/>`_  on your system.

.. note:: 

    XOA Chimera Core requires Python >= 3.8.

``pip``
^^^^^^^^

Make sure ``pip`` is installed on your system. ``pip`` is the `package installer for Python <https://packaging.python.org/guides/tool-recommendations/>`_ . You can use it to install packages from the `Python Package Index <https://pypi.org/>`_  and other indexes.

Usually, ``pip`` is automatically installed if you are:

* working in a `virtual Python environment <https://packaging.python.org/en/latest/tutorials/installing-packages/#creating-and-using-virtual-environments>`_ (`virtualenv <https://virtualenv.pypa.io/en/latest/#>`_ or `venv <https://docs.python.org/3/library/venv.html>`_ ). It is not necessary to use ``sudo pip`` inside a virtual Python environment.
* using Python downloaded from `python.org <https://www.python.org/>`_ 

If you don't have ``pip`` installed, you can:

* Download the script, from https://bootstrap.pypa.io/get-pip.py.
* Open a terminal/command prompt, ``cd`` to the folder containing the ``get-pip.py`` file and run:

.. tab:: Windows

    .. code-block:: doscon
        :caption: Install pip in Windows environment.

        > py get-pip.py

.. tab:: macOS/Linux

    .. code-block:: console
        :caption: Install pip in macOS/Linux environment.

        $ python3 get-pip.py

.. seealso::

    Read more details about this script in `pypa/get-pip <https://github.com/pypa/get-pip>`_.

    Read more about installation of ``pip`` in `pip installation <https://pip.pypa.io/en/stable/installation/>`_.


Installing From PyPI Using ``pip``
----------------------------------

``pip`` is the recommended installer for XOA Chimera Core. The most common usage of ``pip`` is to install from the `Python Package Index <https://pypi.org/>`_ using `Requirement Specifiers <https://pip.pypa.io/en/stable/cli/pip_install/#requirement-specifiers>`_.

.. note::
    
    If you install XOA Chimera Core using ``pip install chimera-core``, XOA Python API (PyPI package name `xoa_driver <https://pypi.org/project/xoa-python-api/>`_) will be automatically installed.


.. _install_core_global:

Install to Global Namespace
^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. tab:: Windows
    :new-set:

    .. code-block:: doscon
        :caption: Install XOA Chimera Core in Windows environment from PyPI.

        > pip install chimera-core            # latest version
        > pip install chimera-core==1.0.7     # specific version
        > pip install chimera-core>=1.0.7     # minimum version

.. tab:: macOS/Linux

    .. code-block:: console
        :caption: Install XOA Chimera Core in macOS/Linux environment from PyPI.

        $ pip install chimera-core            # latest version
        $ pip install chimera-core==1.0.7     # specific version
        $ pip install chimera-core>=1.0.7     # minimum version


.. _install_core_venv:

Install in Virtual Environment
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Install XOA Chimera Core in a virtual environment, so it does not pollute your global namespace. 

For example, your project folder is called ``/my_xoa_project``.

.. tab:: Windows

    .. code-block:: doscon
        :caption: Install XOA Chimera Core in a virtual environment in Windows from PyPI.

        [my_xoa_project]> python -m venv ./env
        [my_xoa_project]> source ./env/bin/activate

        (env) [my_xoa_project]> pip install chimera-core         # latest version
        (env) [my_xoa_project]> pip install chimera-core==1.0.7  # specific version
        (env) [my_xoa_project]> pip install chimera-core>=1.0.7  # minimum version

.. tab:: macOS/Linux

    .. code-block:: console
        :caption: Install XOA Chimera Core in a virtual environment in macOS/Linux from PyPI.

        [my_xoa_project]$ python3 -m venv ./env
        [my_xoa_project]$ source ./env/bin/activate

        (env) [my_xoa_project]$ pip install chimera-core         # latest version
        (env) [my_xoa_project]$ pip install chimera-core==1.0.7  # specific version
        (env) [my_xoa_project]$ pip install chimera-core>=1.0.7 # minimum version

Afterwards, your project folder will be:

.. code-block::
    :caption: After creating Python virtual environment

    /my_xoa_project
        |
        |- env

.. seealso::

    * `Virtual Python environment <https://packaging.python.org/en/latest/tutorials/installing-packages/#creating-and-using-virtual-environments>`_
    * `virtualenv <https://virtualenv.pypa.io/en/latest/#>`_
    * `venv <https://docs.python.org/3/library/venv.html>`_


Upgrading From PyPI Using ``pip``
---------------------------------

To upgrade XOA Chimera Core package from PyPI:

.. tab:: Windows
    :new-set:
    
    .. code-block:: doscon
        :caption: Upgrade XOA Chimera Core in Windows environment from PyPI.

        > pip install chimera-core --upgrade

.. tab:: macOS/Linux

    .. code-block:: console
        :caption: Upgrade XOA Chimera Core in macOS/Linux environment from PyPI.

        $ pip install chimera-core --upgrade


.. note::
    
    If you upgrade XOA Chimera Core using ``pip install --upgrade chimera-core``, XOA Python API (PyPI package name `xoa_driver <https://pypi.org/project/xoa-python-api/>`_) will be automatically upgraded.


Installing Manually From Source
-------------------------------

If for some reason you need to install XOA Chimera Core manually from source, the steps are:

**Step 1**, make sure Python packages `wheel <https://wheel.readthedocs.io/en/stable/>`_ and  `setuptools <https://setuptools.pypa.io/en/latest/index.html>`_ are installed on your system. Install ``wheel`` and ``setuptools`` using ``pip``:

.. tab:: Windows
    :new-set:

    .. code-block:: doscon
        :caption: Install ``wheel`` and ``setuptools`` in Windows environment.

        > pip install wheel setuptools

.. tab:: macOS/Linux

    .. code-block:: console
        :caption: Install ``wheel`` and ``setuptools`` in macOS/Linux environment.

        $ pip install wheel setuptools

**Step 2**, download the XOA Chimera Core source distribution from `XOA Chimera Core Releases <https://github.com/xenanetworks/open-automation-core/releases>`_. Unzip the archive and run the ``setup.py`` script to install the package:

.. tab:: Windows
    :new-set:

    .. code-block:: doscon
        :caption: Install XOA Chimera Core in Windows environment from source.

        [xoa_core]> python setup.py install

.. tab:: macOS/Linux

    .. code-block:: console
        :caption: Install XOA Chimera Core in macOS/Linux environment from source.

        [xoa_core]$ python3 setup.py install


**Step 3**, if you want to distribute, you can build ``.whl`` file for distribution from the source:

.. tab:: Windows
    :new-set:

    .. code-block:: doscon
        :caption: Build XOA Chimera Core wheel in Windows environment for distribution.

        [xoa_core]> python setup.py bdist_wheel

.. tab:: macOS/Linux

    .. code-block:: console
        :caption: Build XOA Chimera Core wheel in macOS/Linux environment for distribution.

        [xoa_core]$ python3 setup.py bdist_wheel

.. important::

    If you install XOA Chimera Core from the source code, you need to install XOA Python API (PyPI package name `xoa_driver <https://pypi.org/project/xoa-python-api/>`_) separately. This is because XOA Python API is treated as a 3rd-party dependency of XOA Chimera Core. You can go to `XOA Python API <https://github.com/xenanetworks/open-automation-python-api>`_ repository to learn how to install it.


Uninstall and Remove Unused Dependencies
----------------------------------------

``pip uninstall chimera-core`` can uninstall the package itself but not its dependencies. Leaving the package's dependencies in your environment can later create conflicting dependencies problem.

We recommend install and use the `pip-autoremove <https://github.com/invl/pip-autoremove>`_ utility to remove a package plus unused dependencies.

.. tab:: Windows
    :new-set:

    .. code-block:: doscon
        :caption: Uninstall XOA Chimera Core in Windows environment.

        > pip install pip-autoremove
        > pip-autoremove chimera-core -y

.. tab:: macOS/Linux

    .. code-block:: console
        :caption: Uninstall XOA Chimera Core in macOS/Linux environment.

        $ pip install pip-autoremove
        $ pip-autoremove chimera-core -y

.. seealso::

    See the `pip uninstall <https://pip.pypa.io/en/stable/cli/pip_uninstall/#pip-uninstall>`_ reference.

    See `pip-autoremove <https://github.com/invl/pip-autoremove>`_ usage.



