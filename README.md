apache2gelf
===========

A set of python scripts to deliver Apache and PHP log files to graylog2. Scripts support the following log files:
* standard Apache 2.2 error log (errorlog2gelf.py);
* custom (but quite close to standard 'combined') Apache access log (accesslog2gelf.py);
* standard PHP error log (phplog2gelf.py).

Requirements:
* python-argparse
* python-graypy

Usage example
-------------

For Apache with mod_php:

    <VirtualHost *:80>
      ServerName example.com
      DocumentRoot /var/www/example.com

      ErrorLog "| /path/to/errorlog2gelf.py --vhost example.com > /var/log/apache/error.log"
      CustomLog "|| /path/to/accesslog2gelf.py --vhost example.com" "%V %h %u \"%r\" %>s %b \"%{Referer}i\""
      php_admin_value error_log "/var/log/php/example.com.php.log"
    </VirtualHost>

phplog2gelf.py basically does 'tail -F', so it should be executed separately:
    /path/to/phplog2gelf.py --vhost example.com /var/log/php/example.com.php.log

Command line parameters
-----------------------

All scripts understand the following command line parameters:
* `--host` to specify graylog2 server
* `--port` to specify graylog2 GELF port
* `--facility` to specify log facility
* `--vhost` to add an extra 'term' to all log messages. This allows you to configure per-virtualhost log handlers (on the expense of running N additional processes, of course) and then filter logs in graylog2 accordingly.

accesslog2gelf.py
-----------------

The script has log format hard-coded into it, so if you would like to change the CustomLog fields or resulting log messages, just hack it.

errorlog2gelf.py
----------------

The script outputs all messages to stdout. This allows you to have a local log file as well (you can only have one ErrorLog parameter in Apache configuration)

phplog2gelf.py
--------------

This script is somewhat different from the previous two. Because there is no way to get log messages from php via pipe, we have to 'tail -F' the log file. The script supports multiline PHP error log messages as well.

You should launch `phplog2gelf.py` separately - just stick it into your rc.local file. If you have a Debian/Ubuntu system you can also use the following *monit* configuration:

    check process phplog2gelf_example with pidfile /var/run/phplog2gelf_example.pid
        start program = "/sbin/start-stop-daemon --start --pidfile /var/run/phplog2gelf_example.pid --user www-data --chuid www-data --background --make-pidfile --exec /usr/local/sbin/phplog2gelf.py -- --vhost example.com /var/log/php/example.com.php.log"
        stop program = "/sbin/start-stop-daemon --stop --pidfile /var/run/phplog2gelf_example.pid --verbose"

Credits
=======

Copyright (c) 2012, Anton Tolchanov
The scripts are licensed under MIT license.

