Command-line interface
======================

We offer a command-line client for XNAT together with this library.
Many of the commands have arguments for the hostname and login information.
This would make each command have a lot parameters, e.g.::

    $ xnat --hostname https://xnat.example.com --user username list project

To avoid having to give all these arguments for every single call, it
is possible to set the hostname with an environment variable. Furthermore,
you can login once and reuse the session. For example::

    $ XNATPY_HOST=https://xnat.example.com
    $ XNATPY_JSESSION=`xnat login --user username`
    $ xnat list project
    $ xnat logout

Between the login and logout all commands will automatically use the host
and login specified. This avoids the need to login for every single command.

Command-line interface reference
--------------------------------

.. click:: xnat.client:cli
   :prog: xnat
   :nested: full