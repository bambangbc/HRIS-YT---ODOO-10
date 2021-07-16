<?php

// This is the database connection configuration.
return array(
	// uncomment the following lines to use a MySQL database
	'connectionString' => 'pgsql:host=localhost;port=5432;dbname=training',
	//'emulatePrepare' => true,
	'username' => 'openpg',
	'password' => 'openpgpwd',
	'charset' => 'utf8',
	//'enableParamLogging'=>true,
	'class' => 'CDbConnection'	
);