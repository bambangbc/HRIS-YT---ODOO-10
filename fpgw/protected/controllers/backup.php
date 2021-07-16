<?php

Yii::import('application.vendor.ripcord-master.*');

class SyncController extends Controller
{
	private function checkArray($userid, $tgl, $idmesin, $array)
	{
		$result = true;

		foreach($array as $a){
			if(($a[0]==$userid) && ($a[1]==$tgl) && ($a[2]==$idmesin)){
				$result = false;
				break;
			}
		}

		return $result;
	}

	public function actionIndex()
	{
		$criteria = new CDbCriteria;
		$criteria->condition = "is_read=0";
		$criteria->order = "Tgl2 ASC";
		
		$model = TrnAbsent::model()->findAll($criteria);

		$result = array();

		foreach($model as $m){

			$userid  = $m->UserID;
			$tgl     = gmdate('Y-m-d H:i:s', strtotime($m->Tgl));
			$idmesin = $m->IDMesin;
			$tgl2    = $m->Tgl2;
			$bulan   = $m->Bulan;
			$tahun   = $m->Tahun;
			$status  = $m->Status;
			$telat   = $m->Telat;

			if($this->checkArray($userid, $tgl, $idmesin, $result)){
				$result[] = array(
					$userid,
					$tgl,
					$idmesin,
					$tgl2,
					$bulan,
					$tahun,
					$status,
					$telat,
				);

				/*send to odoo*/
				$params = array(
					0,
					$userid,
		        	$idmesin,
		           	$tgl,
		           	$tgl2,
		           	$bulan,
		           	$tahun,
		           	$status,
		           	$telat,
				);

				/*echo "<pre/>";
				var_dump(array($params, $params));die;*/

				$result_post = xmlrpc_request('hr.attendance', 'check_attendance', $params);
				echo "<pre/>";
				var_dump($result_post);
				echo "<br/>";
			}

			
			/*$m->is_read = 1;
			$m->save();*/
		}
	}
}