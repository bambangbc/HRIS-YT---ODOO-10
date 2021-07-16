<?php
	function xmlrpc_request($object, $method, $params, $params2=null){
		$url 		= "http://localhost:8069";
		$db  		= "training";
		$username 	= "training@vitraining.com";
		$password 	= "1";

		/*$url 		= "http://localhost:8069";
		$db  		= "yt_u";
		$username 	= "admin";
		$password 	= "1";*/

		/* login */
		$common = ripcord::client("$url/xmlrpc/2/common");
		$uid = $common->authenticate($db, $username, $password, array());

		/* create $models object*/
		$models = ripcord::client("$url/xmlrpc/2/object");

        
        if($params2!=null){
            $result = $models->execute_kw($db, $uid, $password, $object, $method, $params, $params2);
        }else{
            $result = $models->execute_kw($db, $uid, $password, $object, $method, $params);
        }

        return $result;
    }
?>