<?php
    Class MyActiveRecord extends CActiveRecord {

        private static $db2 = null;

        protected static function getAdvertDbConnection()
        {
            if (self::$db2 !== null)
                return self::$db2;
            else
            {
                self::$db2 = Yii::app()->db2;
                if (self::$db2 instanceof CDbConnection)
                {
                    self::$db2->setActive(true);
                    return self::$db2;
                }
                else
                    throw new CDbException(Yii::t('yii','Active Record requires a "db" CDbConnection application component.'));
            }
        }
    }
?>