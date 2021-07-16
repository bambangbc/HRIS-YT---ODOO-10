<?php

/**
 * This is the model class for table "hr_attendance_finger".
 *
 * The followings are the available columns in table 'hr_attendance_finger':
 * @property integer $id
 * @property string $status
 * @property integer $create_uid
 * @property integer $employee_id
 * @property string $create_date
 * @property string $absen_id
 * @property integer $telat
 * @property integer $write_uid
 * @property string $bulan
 * @property string $tahun
 * @property string $no_mesin
 * @property string $tanggal
 * @property string $write_date
 * @property string $date
 *
 * The followings are the available model relations:
 * @property ResUsers $writeU
 * @property HrEmployee $employee
 * @property ResUsers $createU
 */
class HrAttendanceFinger extends CActiveRecord
{
	/**
	 * @return string the associated database table name
	 */
	public function tableName()
	{
		return 'hr_attendance_finger';
	}

	/**
	 * @return array validation rules for model attributes.
	 */
	public function rules()
	{
		// NOTE: you should only define rules for those attributes that
		// will receive user inputs.
		return array(
			array('create_uid, employee_id, telat, write_uid', 'numerical', 'integerOnly'=>true),
			array('status, create_date, absen_id, bulan, tahun, no_mesin, tanggal, write_date, date', 'safe'),
			// The following rule is used by search().
			// @todo Please remove those attributes that should not be searched.
			array('id, status, create_uid, employee_id, create_date, absen_id, telat, write_uid, bulan, tahun, no_mesin, tanggal, write_date, date', 'safe', 'on'=>'search'),
		);
	}

	/**
	 * @return array relational rules.
	 */
	public function relations()
	{
		// NOTE: you may need to adjust the relation name and the related
		// class name for the relations automatically generated below.
		return array(
			/*'writeU' => array(self::BELONGS_TO, 'ResUsers', 'write_uid'),
			'employee' => array(self::BELONGS_TO, 'HrEmployee', 'employee_id'),
			'createU' => array(self::BELONGS_TO, 'ResUsers', 'create_uid'),*/
		);
	}

	/**
	 * @return array customized attribute labels (name=>label)
	 */
	public function attributeLabels()
	{
		return array(
			'id' => 'ID',
			'status' => 'Status',
			'create_uid' => 'Create Uid',
			'employee_id' => 'Employee',
			'create_date' => 'Create Date',
			'absen_id' => 'Absen',
			'telat' => 'Telat',
			'write_uid' => 'Write Uid',
			'bulan' => 'Bulan',
			'tahun' => 'Tahun',
			'no_mesin' => 'No Mesin',
			'tanggal' => 'Tanggal',
			'write_date' => 'Write Date',
			'date' => 'Date',
		);
	}

	/**
	 * Retrieves a list of models based on the current search/filter conditions.
	 *
	 * Typical usecase:
	 * - Initialize the model fields with values from filter form.
	 * - Execute this method to get CActiveDataProvider instance which will filter
	 * models according to data in model fields.
	 * - Pass data provider to CGridView, CListView or any similar widget.
	 *
	 * @return CActiveDataProvider the data provider that can return the models
	 * based on the search/filter conditions.
	 */
	public function search()
	{
		// @todo Please modify the following code to remove attributes that should not be searched.

		$criteria=new CDbCriteria;

		$criteria->compare('id',$this->id);
		$criteria->compare('status',$this->status,true);
		$criteria->compare('create_uid',$this->create_uid);
		$criteria->compare('employee_id',$this->employee_id);
		$criteria->compare('create_date',$this->create_date,true);
		$criteria->compare('absen_id',$this->absen_id,true);
		$criteria->compare('telat',$this->telat);
		$criteria->compare('write_uid',$this->write_uid);
		$criteria->compare('bulan',$this->bulan,true);
		$criteria->compare('tahun',$this->tahun,true);
		$criteria->compare('no_mesin',$this->no_mesin,true);
		$criteria->compare('tanggal',$this->tanggal,true);
		$criteria->compare('write_date',$this->write_date,true);
		$criteria->compare('date',$this->date,true);

		return new CActiveDataProvider($this, array(
			'criteria'=>$criteria,
		));
	}

	/**
	 * @return CDbConnection the database connection used for this class
	 */
	public function getDbConnection()
	{
		return Yii::app()->db2;
	}

	/**
	 * Returns the static model of the specified AR class.
	 * Please note that you should have this exact method in all your CActiveRecord descendants!
	 * @param string $className active record class name.
	 * @return HrAttendanceFinger the static model class
	 */
	public static function model($className=__CLASS__)
	{
		return parent::model($className);
	}
}
