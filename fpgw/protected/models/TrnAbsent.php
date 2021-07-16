<?php

/**
 * This is the model class for table "TrnAbsent".
 *
 * The followings are the available columns in table 'TrnAbsent':
 * @property integer $UserID
 * @property string $Tgl
 * @property string $IDMesin
 * @property integer $Tgl2
 * @property integer $Bulan
 * @property integer $Tahun
 * @property string $Status
 * @property integer $Telat
 * @property integer $is_read
 */
class TrnAbsent extends CActiveRecord
{
	/**
	 * @return string the associated database table name
	 */
	public function tableName()
	{
		return 'TrnAbsent';
	}

	/**
	 * @return array validation rules for model attributes.
	 */
	public function rules()
	{
		// NOTE: you should only define rules for those attributes that
		// will receive user inputs.
		return array(
			array('UserID', 'required'),
			array('UserID, Tgl2, Bulan, Tahun, Telat, is_read', 'numerical', 'integerOnly'=>true),
			array('IDMesin', 'length', 'max'=>5),
			array('Status', 'length', 'max'=>2),
			// The following rule is used by search().
			// @todo Please remove those attributes that should not be searched.
			array('UserID, Tgl, IDMesin, Tgl2, Bulan, Tahun, Status, Telat, is_read', 'safe', 'on'=>'search'),
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
		);
	}

	/**
	 * @return array customized attribute labels (name=>label)
	 */
	public function attributeLabels()
	{
		return array(
			'UserID' => 'User',
			'Tgl' => 'Tgl',
			'IDMesin' => 'Idmesin',
			'Tgl2' => 'Tgl2',
			'Bulan' => 'Bulan',
			'Tahun' => 'Tahun',
			'Status' => 'Status',
			'Telat' => 'Telat',
			'is_read' => 'Is Read',
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

		$criteria->compare('UserID',$this->UserID);
		$criteria->compare('Tgl',$this->Tgl,true);
		$criteria->compare('IDMesin',$this->IDMesin,true);
		$criteria->compare('Tgl2',$this->Tgl2);
		$criteria->compare('Bulan',$this->Bulan);
		$criteria->compare('Tahun',$this->Tahun);
		$criteria->compare('Status',$this->Status,true);
		$criteria->compare('Telat',$this->Telat);
		$criteria->compare('is_read',$this->is_read);

		return new CActiveDataProvider($this, array(
			'criteria'=>$criteria,
		));
	}

	/**
	 * Returns the static model of the specified AR class.
	 * Please note that you should have this exact method in all your CActiveRecord descendants!
	 * @param string $className active record class name.
	 * @return TrnAbsent the static model class
	 */
	public static function model($className=__CLASS__)
	{
		return parent::model($className);
	}

	public function beforeSave(){
		unset($this->Tgl2);
		unset($this->Bulan);
		unset($this->Tahun);
		
		return parent::beforeSave();
	}
}
