<?php
/**
 * The following variables are available in this template:
 * - $this: the CrudCode object
 */
?>
<div class="wide form">

<?php echo "<?php \$form=\$this->beginWidget('CActiveForm', array(
	'action'=>Yii::app()->createUrl(\$this->route),
	'method'=>'get',
)); ?>\n"; ?>
<?php
$mdl=new $this->modelClass;
$relations = $mdl->relations();
?>
<?php foreach($this->tableSchema->columns as $column): ?>
<?php
	$field=$this->generateInputField($this->modelClass,$column);
	if(strpos($field,'password')!==false)
		continue;
		
	else if(array_key_exists($column->name, $this->tableSchema->foreignKeys) && $column->name != 'created_by_id')
	{
		//print_r($this->tableSchema->foreignKeys[$column->name]);
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
				$value = "\$model->$relname->$foreignValue";
				break;						
			}
		}
		
		
		echo "<div class=\"row\">\n";
		echo "<?php echo ".$this->generateActiveLabel($this->modelClass,$column)."; ?>\n"; 
		echo "<?php /*echo \$form->dropDownlist(\$model,'{$column->name}', \n
			(CHtml::listData($foreignModel::model()->findAll(),'{$foreignField}','{$foreignValue}')),
			array(
			'empty'=>'--Choose one--',
			//'ajax' => array(
			//	'type'=>'POST', 
			///	'url'=>CController::createUrl('dataPokok/ambilkotan'), 
			//	'data' => 'js:{nasabah:$(this).val()}',
			//	'update'=>'#DataPokok_id_city', 
			//	)
			));*/ ?>\n";
		echo "</div>\n";

		echo "\t<div class=\"row\">\n";
		echo "\t<?php echo \$form->hiddenField(\$model,'{$column->name}'); ?>\n"; 
		echo "\t<?php 
		\$this->widget('zii.widgets.jui.CJuiAutoComplete', array(
		'name'=>'{$this->modelClass}_{$foreignTable}',
		'source'=>'js: function( request, response ) {
				$.getJSON( \"".Yii::app()->createUrl( "{$foreignTable}/autocomplete") . "\", {
					term: request.term,
				}, response );
			}',
		'value'=>{$value},	
		'options'=>array(
	        'max'=>10,
			'minChars'=>2, 
			'delay'=>300,
			'matchCase'=>true,
	        'minLength'=>'2',
			'search'=>\"js: function(event, ui) {
				\$('#{$this->modelClass}_{$column->name}').val('');
			}\",		        
			'select'=>\"js: function(event, ui) {
				\$('#{$this->modelClass}_{$column->name}').val(ui.item.id);
			}\"
		),
		'htmlOptions'=>array('size'=>'60')
		));
		?>\n";	
		echo "\t<?php echo \$form->error(\$model,'{$column->name}'); ?>\n"; 
		echo "\t</div>\n";
		continue;
	}
	else if($column->name=='created_at' || $column->name=='created_by_id')
	{		
		echo "<?php echo \$form->hiddenField(\$model,'{$column->name}'); ?>\n"; 
		continue;
	}
?>
	<div class="row">
		<?php echo "<?php echo \$form->label(\$model,'{$column->name}'); ?>\n"; ?>
		<?php echo "<?php echo ".$this->generateActiveField($this->modelClass,$column)."; ?>\n"; ?>
	</div>

<?php endforeach; ?>
	<div class="row buttons">
		<?php echo "<?php echo CHtml::submitButton('Search'); ?>\n"; ?>
	</div>

<?php echo "<?php \$this->endWidget(); ?>\n"; ?>

</div><!-- search-form -->