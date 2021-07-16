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
$nameColumn=$this->guessNameColumn($this->tableSchema->columns);
$label=$this->pluralize($this->class2name($this->modelClass));
echo "\$this->breadcrumbs=array(
	'$label'=>array('index'),
	\$model->{$nameColumn},
);\n";
?>

$this->menu=array(
	array('label'=>'List <?php echo $this->pluralize($this->class2name($this->modelClass)); ?>', 'url'=>array('index')),
	array('label'=>'Create <?php echo $this->pluralize($this->class2name($this->modelClass)); ?>', 'url'=>array('create')),
	array('label'=>'Update <?php echo $this->pluralize($this->class2name($this->modelClass)); ?>', 'url'=>array('update', 'id'=>$model-><?php echo $this->tableSchema->primaryKey; ?>)),
	array('label'=>'Delete <?php echo $this->pluralize($this->class2name($this->modelClass)); ?>', 'url'=>'#', 'linkOptions'=>array('submit'=>array('delete','id'=>$model-><?php echo $this->tableSchema->primaryKey; ?>),'confirm'=>'Are you sure you want to delete this item?')),
	/*array('label'=>'Manage <?php echo $this->modelClass; ?>', 'url'=>array('admin')),*/

);
$this->menu2=array(
	<?php foreach ($relations as $relname => $rel):?>
	<?php if($relname != 'createdBy'):?>
	array('label'=>'List <?php echo $this->pluralize($this->class2name($rel[1])); ?>', 'url'=>array('//<?php echo $rel[1]?>')),
	<?php endif;?>
	<?php endforeach;?>
);
?>
<h1>View <?php echo $this->modelClass.": <?php echo \$model->name; ?>"; ?></h1>
<?php
$mdl=new $this->modelClass;
$relations = $mdl->relations();
?>

<?php echo "<?php \n" ?>
	$this->beginWidget('zii.widgets.CPortlet', array(
		'title'=>'<?php echo $this->pluralize($this->class2name($this->modelClass))?>',
	));
<?php echo "?>\n" ?>

<?php echo "<?php"; ?> $this->widget('zii.widgets.CDetailView', array(
	'data'=>$model,
	'attributes'=>array(
<?php
foreach($this->tableSchema->columns as $column)
{

	if(array_key_exists($column->name, $this->tableSchema->foreignKeys))
	{
		$foreignKey = $this->tableSchema->foreignKeys[$column->name] ;
		$foreignTable = $foreignKey[0];
		$foreignModel = ucwords($foreignTable);
		$foreignField = $foreignKey[1];
		if($foreignTable=='user')
			$foreignValue ='username';
		else
			$foreignValue ='name';
			
		foreach($relations as $relname => $rel)
		{
			if($rel[0]=='CBelongsToRelation' && $rel[2]==$column->name)
			{
				echo "\t\tarray('value'=>\$model->{$relname}?\$model->{$relname}->{$foreignValue}:'','name'=>'{$relname}'),\n";						
			}
		}
	}	
	else if($column->dbType==='boolean'||$column->dbType==='tinyint(1)')
	{
		echo "\t\t";
		echo "array('name'=>'{$column->name}', 'value'=>\$model->{$column->name}?\"True\":\"False\")";
		echo ",\n";			
	}
	else
		echo "\t\t'".$column->name."',\n";
}
?>
	),
)); ?>
<?php echo "<?php \$this->endWidget(); ?>\n"; // master portlet ?>

<?php echo "<?php \n" ?>
	$this->beginWidget('zii.widgets.CPortlet', array(
		'title'=>'Details',
	));
<?php echo "?>\n" ?>


<?php
foreach($relations as $relname => $rel):
if($rel[0]=='CHasManyRelation'):
	$modelName=$rel[1];
	$detailForeignKey=$rel[2];
?>
<?php echo "<?php \n" ?>
//detail records : <?php echo $relname  ?>

$detail = new <?php echo $rel[1]?>('search');
$detail->attributes = array('<?php echo $detailForeignKey?>'=>$model->id);
ob_start();
$this->widget('zii.widgets.grid.CGridView', array(
	'id'=>'<?php echo $modelName ?>-detail-grid',
	'dataProvider'=>$detail->search(),
	'columns'=>array(
<?php
		$mdlDetail=new $modelName;
		$relationsDetail = $mdlDetail->relations();
		$count=0;
		foreach($mdlDetail->tableSchema->columns as $column)
		{
			if(++$count==7)
				echo "\t\t/*\n";
				
			if($column->name=='id' or $column->name=='ID' or $column->name=='created_at' or $column->name=='created_by_id')
				continue;
			else if($column->name == $detailForeignKey)
				continue;
			else
			{
				if(array_key_exists($column->name, $mdlDetail->tableSchema->foreignKeys))
				{
					$foreignKey = $mdlDetail->tableSchema->foreignKeys[$column->name] ;
					$foreignTable = $foreignKey[0];
					$foreignModel = str_replace(' ','',ucwords(str_replace('_',' ',$foreignTable) ));
					$foreignField = $foreignKey[1];
					if($foreignTable=='user')
						$foreignValue ='username';
					else
						$foreignValue ='name';
						
					foreach($relationsDetail as $relnameDetail => $relDetail)
					{
						if($relDetail[0]=='CBelongsToRelation' && $relDetail[2]==$column->name)
						{
							echo "\t\tarray('name'=>'{$column->name}','value'=>'\$data->{$relnameDetail}?\$data->{$relnameDetail}->{$foreignValue}:\"\"'),\n";	
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
			
	),
));
$detailContent['<?php echo $modelName ?>'] = ob_get_contents();
ob_end_clean();

<?php echo "?>" ?>
<?php endif;?>
<?php endforeach;?>


<?php echo "<?php \n"?>
if($detailContent):
$this->widget('zii.widgets.jui.CJuiTabs', array(
    'tabs'=>$detailContent,
    'options'=>array(
        'collapsible'=>true,
        'selected'=>0,
    ),
    'htmlOptions'=>array(
        'style'=>'width:100%;'
    ),
));
endif;
<?php echo "?>\n" ?>

<?php echo "<?php \$this->endWidget(); ?>\n"; // detail portlet ?>
