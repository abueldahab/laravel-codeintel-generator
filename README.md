#Laravel Code-intelignece Helper Script Generator

Code-intelligence helper script generator for the Laravel framework version 4.x

Copyright 2013 Max Ehsan [http://laravelbook.com/](http://laravelbook.com/)

###Requirements

- Python 2.6
- Laravel 4 source code

###Instructions

Run `laragen.py` from your Laravel 4 application root directory:

	$ ./laragen.py .

To generate IDE helper script for a single Laravel source file, provide the filename in the argument:

	$ ./laragen.py /path/to/Artisan.php

`_ide_helper.php` will be generated in the current directory. Copy the file to your Laravel 4 `app/` folder.