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
	\$model->{$nameColumn}=>array('view','id'=>\$model->{$this->tableSchema->primaryKey}),
	'Update',
);\n";
?>

$this->menu=array(
	array('label'=>'List <?php echo $this->modelClass; ?>', 'url'=>array('index')),
	array('label'=>'Create <?php echo $this->modelClass; ?>', 'url'=>array('create')),
	array('label'=>'View <?php echo $this->modelClass; ?>', 'url'=>array('view', 'id'=>$model-><?php echo $this->tableSchema->primaryKey; ?>)),
	//array('label'=>'Manage <?php echo $this->modelClass; ?>', 'url'=>array('admin')),
);
$this->menu2=array(
	<?php foreach ($relations as $relname => $rel):?>
	<?php if($relname != 'createdBy'):?>
	array('label'=>'List <?php echo $this->pluralize($this->class2name($rel[1])); ?>', 'url'=>array('//<?php echo $rel[1]?>')),
	<?php endif;?>
	<?php endforeach;?>
);
?>

<h1>Update <?php echo $this->pluralize($this->class2name($this->modelClass)).": <?php echo \$model->name; ?>"; ?></h1>

<?php echo "<?php echo \$this->renderPartial('_form', array('model'=>\$model)); ?>"; ?>