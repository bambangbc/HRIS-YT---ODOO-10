<?php
/**
 * This is the template for generating a controller class file for CRUD feature.
 * The following variables are available in this template:
 * - $this: the CrudCode object
 */
?>
<?php echo "<?php\n"; ?>

class <?php echo $this->controllerClass; ?> extends <?php echo $this->baseControllerClass."\n"; ?>
{
	/**
	 * @var string the default layout for the views. Defaults to '//layouts/column2', meaning
	 * using two-column layout. See 'protected/views/layouts/column2.php'.
	 */
	public $layout='//layouts/column2';
	public $menu2=array();
	public $menu2Title=null;

	/**
	 * @return array action filters
	 */
	public function filters()
	{
		return array(
			'accessControl', // perform access control for CRUD operations
		);
	}

	/**
	 * Specifies the access control rules.
	 * This method is used by the 'accessControl' filter.
	 * @return array access control rules
	 */
	public function accessRules()
	{
		return array(
			array('allow',  // allow all users to perform 'index' and 'view' actions
				'actions'=>array('index','view', 'autocomplete' ,'simpletree','simpleupdate'),
				'users'=>array('*'),
			),
			array('allow', // allow authenticated user to perform 'create' and 'update' actions
				'actions'=>array('create','update'),
				'users'=>array('@'),
			),
			array('allow', // allow admin user to perform 'admin' and 'delete' actions
				'actions'=>array('admin','delete'),
				'users'=>array('admin'),
			),
			array('deny',  // deny all users
				'users'=>array('*'),
			),
		);
	}

	/**
	 * Displays a particular model.
	 * @param integer $id the ID of the model to be displayed
	 */
	public function actionView($id)
	{
		$this->layout='//layouts/column1';
		$this->render('view',array(
			'model'=>$this->loadModel($id),
		));
	}

	/**
	 * Creates a new model.
	 * If creation is successful, the browser will be redirected to the 'view' page.
	 */
	public function actionCreate()
	{
		$this->layout='//layouts/column1';
		$model=new <?php echo $this->modelClass; ?>;

		// Uncomment the following line if AJAX validation is needed
		// $this->performAjaxValidation($model);

		if(isset($_POST['<?php echo $this->modelClass; ?>']))
		{
			$model->attributes=$_POST['<?php echo $this->modelClass; ?>'];
			if($model->save())
			{
				$this->saveRelatedDetails($model);
				//$this->redirect(array('view','id'=>$model-><?php echo $this->tableSchema->primaryKey; ?>));
				$this->redirect(array('index'));
			}
		}

		$this->render('create',array(
			'model'=>$model,
		));
	}

	/**
	 * Updates a particular model.
	 * If update is successful, the browser will be redirected to the 'view' page.
	 * @param integer $id the ID of the model to be updated
	 */
	public function actionUpdate($id)
	{
		$this->layout='//layouts/column1';
		$model=$this->loadModel($id);

		// Uncomment the following line if AJAX validation is needed
		// $this->performAjaxValidation($model);

		if(isset($_POST['<?php echo $this->modelClass; ?>']))
		{
			$model->attributes=$_POST['<?php echo $this->modelClass; ?>'];
			if($model->save())
			{
				$this->saveRelatedDetails($model);
				$this->redirect(array('view','id'=>$model-><?php echo $this->tableSchema->primaryKey; ?>));
			}
		}

		$this->render('update',array(
			'model'=>$model,
		));
	}

	/**
	 * Deletes a particular model.
	 * If deletion is successful, the browser will be redirected to the 'admin' page.
	 * @param integer $id the ID of the model to be deleted
	 */
	public function actionDelete($id)
	{
		if(Yii::app()->request->isPostRequest)
		{
			// we only allow deletion via POST request
			$this->loadModel($id)->delete();

			// if AJAX request (triggered by deletion via admin grid view), we should not redirect the browser
			if(!isset($_GET['ajax']))
				$this->redirect(isset($_POST['returnUrl']) ? $_POST['returnUrl'] : array('admin'));
		}
		else
			throw new CHttpException(400,'Invalid request. Please do not repeat this request again.');
	}

	/**
	 * Lists all models.
	 */
	public function actionIndex()
	{
		/*
		$dataProvider=new CActiveDataProvider('<?php echo $this->modelClass; ?>');
		$this->render('index-tree',array(
			'dataProvider'=>$dataProvider,
		));
		*/
		
		$model=new <?php echo $this->modelClass; ?>('search');
		$model->unsetAttributes();  // clear any default values
		if(isset($_GET['<?php echo $this->modelClass; ?>']))
			$model->attributes=$_GET['<?php echo $this->modelClass; ?>'];

		$this->render('admin',array(
			'model'=>$model,
		));		
	}

	/**
	 * Manages all models.
	 */
	public function actionAdmin()
	{
		$model=new <?php echo $this->modelClass; ?>('search');
		$model->unsetAttributes();  // clear any default values
		if(isset($_GET['<?php echo $this->modelClass; ?>']))
			$model->attributes=$_GET['<?php echo $this->modelClass; ?>'];

		$this->render('admin',array(
			'model'=>$model,
		));
	}

	/**
	 * Returns the data model based on the primary key given in the GET variable.
	 * If the data model is not found, an HTTP exception will be raised.
	 * @param integer the ID of the model to be loaded
	 */
	public function loadModel($id)
	{
		$model=<?php echo $this->modelClass; ?>::model()->findByPk($id);
		if($model===null)
			throw new CHttpException(404,'The requested page does not exist.');
		return $model;
	}

	/**
	 * Performs the AJAX validation.
	 * @param CModel the model to be validated
	 */
	protected function performAjaxValidation($model)
	{
		if(isset($_POST['ajax']) && $_POST['ajax']==='<?php echo $this->class2id($this->modelClass); ?>-form')
		{
			echo CActiveForm::validate($model);
			Yii::app()->end();
		}
	}
	function actionAutocomplete()
	{
		$arr = array();

		if (isset($_GET['term']))
		{
			$term = $_GET['term'];
		
			$crit = new CDbCriteria;
			//static criteria
			//$crit->condition='used_in_cb=1 or used_in_gl=1';
			//dynamic criteria depening on term input, name or code
			$crit->addSearchCondition('name', $term, true, 'AND', 'LIKE' );
			//$crit->addSearchCondition('code', $term, true, 'OR', 'LIKE' );
			$models = <?php echo $this->modelClass; ?>::model()->findAll($crit);
			foreach($models as $model)
			{
				$arr[] = array(
			          'label'=>$model->name,  // label for dropdown list
			          'value'=>$model->name,  // value for input field
			          'id'=>$model->id,       // return value from autocomplete
				);
			}
		}
		echo CJSON::encode($arr);
		Yii::app()->end();
	}

	function saveRelatedDetails($model)
	{
<?php 
		$mdl = new $this->modelClass;
		$relations = $mdl->relations();

		foreach($relations as $relname => $rel)
		{
			if($rel[0]=='CHasManyRelation')
			{
				$modelName=$rel[1];
				$detailForeignKey=$rel[2];

				echo "\t\t\${$relname} = \$_POST['{$modelName}s'];\n";

				echo "\t\tif(\${$relname})
		{
			{$modelName}::model()->deleteAll('$detailForeignKey='.\$model->id);
			foreach (\${$relname} as \$id => \$value) 
			{
				\$d = new $modelName;
				\$d->attributes = \$value;
				\$d->$detailForeignKey = \$model->id;
				if (! \$d->save()) die ('saving $modelName error:'. var_dump(\$d->getErrors()));
			}
		}\n";
			}
		}
?>
	}	

	/*
	simpleTree ajax handler
	syaratnya harus ada field:
	- parent_id
	- sorting
	*/
	public function actionSimpletree()
	{
	    Yii::import('application.extensions.SimpleTreeWidget');    
	    SimpleTreeWidget::performAjax();
	}
	/**
	 * Updates a particular model.
	 * If update is successful, the browser will be redirected to the 'view' page.
	 * @param integer $id the ID of the model to be updated
	 */
	public function actionSimpleupdate($id)
	{
		$this->layout="plain";
		$model=$this->loadModel($id);
		// Uncomment the following line if AJAX validation is needed
		//$this->performAjaxValidation($model);

		if(isset($_POST['<?php echo $this->modelClass; ?>']))
		{
			$model->attributes=$_POST['<?php echo $this->modelClass; ?>'];
			if($model->save())
			{
		        $res = array(
		            'id'=>$model->id,
					'message'=>'Sukses! <?php echo $this->modelClass; ?> berhasil di simpan',
					'success'=>true,
		        );
			}
			else
			{
				$res = array(
					'message'=>'Gagal',
					'success'=>false,					
				);
			}
	        echo CJSON::encode($res);
			Yii::app()->end();
		}

		$this->render('_simpleform',array(
			'model'=>$model,
			'id'=>$id,
		));
	}	
}
