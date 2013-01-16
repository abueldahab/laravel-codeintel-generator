#Laravel Code-intelignece Helper Script Generator

Code-intelligence helper script generator for the Laravel framework version 4.x

Copyright 2013 Max Ehsan [http://laravelbook.com/](http://laravelbook.com/)

###Requirements

- Python 2.6
- Laravel 4 source code

###Instructions

Run `laragen` from your Laravel 4 application root directory:

	$ ./laragen

If you have placed the Laravel framework 4 source code in another location, specify the path in the argument:

	$ ./laragen /path/to/laravel/

To generate IDE helper script for a single Laravel source file, provide the filename in the argument:

	$ ./laragen /path/to/Artisan.php

`_ide_helper.php` will be generated in the current directory. Copy the file to your Laravel 4 `app/` folder.