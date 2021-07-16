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
	'Create',
);\n";
?>

$this->menu=array(
	array('label'=>'List <?php echo $this->modelClass; ?>', 'url'=>array('index')),
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

<h1>Create <?php echo $this->pluralize($this->class2name($this->modelClass)); ?></h1>

<?php echo "<?php echo \$this->renderPartial('_form', array('model'=>\$model)); ?>"; ?>
