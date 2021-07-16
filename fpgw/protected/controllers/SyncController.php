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
		$criteria->limit = "1000";
		
		$model = TrnAbsent::model()->findAll($criteria);

		$totaldata = count($model);

		$result = array();

		$time_start = microtime(true);

		foreach($model as $m){

			$userid  = $m->UserID;
			$tgl     = gmdate('Y-m-d H:i:s', strtotime($m->Tgl));
			$idmesin = $m->IDMesin;
			$tgl2    = $m->Tgl2;
			$bulan   = $m->Bulan;
			$tahun   = $m->Tahun;
			$status  = $m->Status;
			$telat   = $m->Telat;

			/*send to odoo via xmlrpc*/
			/*$params = array(
				array(
					'absen_id'=>$userid,
		        	'no_mesin'=>$idmesin,
		           	'tanggal'=>$tgl2,
		           	'date'=>$tgl,
		           	'bulan'=>$bulan,
		           	'tahun'=>$tahun,
		           	'status'=>$status,
		           	'telat'=>$telat
	           )
			);

			$result_post = xmlrpc_request('hr.attendance.finger', 'create', $params);*/


			/*send to odoo via inject to database postgre*/
			$fingerOdoo 			= new HrAttendanceFinger;
			$fingerOdoo->status 	= $status;
			$fingerOdoo->create_uid = 1;
			$fingerOdoo->create_date= gmdate('Y-m-d H:i:s');
			$fingerOdoo->absen_id 	= $userid;
			$fingerOdoo->telat 		= intval($telat);
			$fingerOdoo->write_uid 	= 1;
			$fingerOdoo->bulan 		= $bulan;
			$fingerOdoo->tahun 		= $tahun;
			$fingerOdoo->no_mesin 	= $idmesin;
			$fingerOdoo->tanggal 	= $tgl2;
			$fingerOdoo->write_date = gmdate('Y-m-d H:i:s');
			$fingerOdoo->date 		= $tgl;
			
			if($fingerOdoo->save()){
				$m->is_read = 1;
				$m->save();
			}
		}

		$time_end = microtime(true);

		$time = $time_end - $time_start;

	    echo "Send {$totaldata} data with total time {$time} second";
	}
}