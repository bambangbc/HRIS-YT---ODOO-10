<?php
/**
 * The following variables are available in this template:
 * - $this: the CrudCode object
 */
?>
<?php
$mdl=new $this->modelClass;
$relations = $mdl->relations();
?>
<?php
echo "<?php\n";
$label=$this->pluralize($this->class2name($this->modelClass));
echo "\$this->breadcrumbs=array(
	'$label'=>array('index'),
	'Manage',
);\n";
?>

$this->menu=array(
	array('label'=>'List <?php echo $this->pluralize($this->class2name($this->modelClass)); ?>', 'url'=>array('index')),
	array('label'=>'Create <?php echo $this->pluralize($this->class2name($this->modelClass)); ?>', 'url'=>array('create')),
);
$this->menu2=array(
	<?php foreach ($relations as $relname => $rel):?>
	<?php if($relname != 'createdBy'):?>
	array('label'=>'List <?php echo $this->pluralize($this->class2name($rel[1])); ?>', 'url'=>array('//<?php echo $rel[1]?>')),
	<?php endif;?>
	<?php endforeach;?>
);
Yii::app()->clientScript->registerScript('search', "
$('.search-button').click(function(){
	$('.search-form').toggle();
	return false;
});
$('.search-form form').submit(function(){
	$.fn.yiiGridView.update('<?php echo $this->class2id($this->modelClass); ?>-grid', {
		data: $(this).serialize()
	});
	return false;
});
");
?>

<h1>Manage <?php echo $this->pluralize($this->class2name($this->modelClass)); ?></h1>

<p>
You may optionally enter a comparison operator (<b>&lt;</b>, <b>&lt;=</b>, <b>&gt;</b>, <b>&gt;=</b>, <b>&lt;&gt;</b>
or <b>=</b>) at the beginning of each of your search values to specify how the comparison should be done.
</p>

<?php echo "<?php echo CHtml::link('Advanced Search','#',array('class'=>'search-button')); ?>"; ?>

<div class="search-form" style="display:none">
<?php echo "<?php \$this->renderPartial('_search',array(
	'model'=>\$model,
)); ?>\n"; ?>
</div><!-- search-form -->
<?php
$mdl=new $this->modelClass;
$relations = $mdl->relations();
//print_r($relations);
?>
<?php echo "<?php"; ?> $this->widget('zii.widgets.grid.CGridView', array(
	'id'=>'<?php echo $this->class2id($this->modelClass); ?>-grid',
	'dataProvider'=>$model->search(),
	'filter'=>$model,
	'columns'=>array(
<?php
$count=0;
foreach($this->tableSchema->columns as $column)
{
	if(++$count==7)
		echo "\t\t/*\n";
		
	if($column->name=='id' or $column->name=='ID')
		echo "\t\t". "array('name'=>'".$column->name."', 'filter'=>false),\n";
	else if ($column->name=='created_at' || $column->name=='created_by_id')
		continue;
	else
	{
		if(array_key_exists($column->name, $this->tableSchema->foreignKeys))
		{
			$foreignKey = $this->tableSchema->foreignKeys[$column->name] ;
			$foreignTable = $foreignKey[0];
			$foreignModel = str_replace(' ','',ucwords(str_replace('_',' ',$foreignTable) ));
			$foreignField = $foreignKey[1];
			if($foreignTable=='user')
				$foreignValue ='username';
			else
				$foreignValue ='name';
				
			foreach($relations as $relname => $rel)
			{
				if($rel[0]=='CBelongsToRelation' && $rel[2]==$column->name)
				{
					echo "\t\tarray('name'=>'{$column->name}','value'=>'\$data->{$relname}?\$data->{$relname}->{$foreignValue}:\"\"','filter'=>CHtml::listData({$rel[1]}::model()->findAll(), '{$foreignField}', '{$foreignValue}')),\n";	
				}
			}

		}
		else if($column->dbType==='boolean'||$column->dbType==='tinyint(1)')
		{
			echo "\t\t";
			echo "array('name'=>'{$column->name}', 'value'=>'\$data->{$column->name}?\"True\":\"False\"', 'filter'=>array(0=>\"False\", 1=>\"True\"))";
			echo ",\n";			
		}
		else
			echo "\t\t'".$column->name."',\n";		
	}
}
if($count>=7)
	echo "\t\t*/\n";
?>
		array(
			'class'=>'CButtonColumn',
		),
		/*
		array
		(
		    'class'=>'CButtonColumn',
		    'template'=>'{email}{down}{delete}',
		    'buttons'=>array
		    (
		        'email' => array
		        (
		            'label'=>'Send an e-mail to this user',
		            'imageUrl'=>Yii::app()->request->baseUrl.'/images/email.png',
		            'url'=>'Yii::app()->createUrl("users/email", array("id"=>$data->id))',
		        ),
		        'down' => array
		        (
		            'label'=>'[-]',
		            'url'=>'"#"',
		            'visible'=>'$data->score > 0',
		            'click'=>'function(){alert("Going down!");}',
		        ),
		    ),
		),		
		*/
	),
)); ?>
