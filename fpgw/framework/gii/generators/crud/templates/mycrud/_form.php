<?php
/**
 * The following variables are available in this template:
 * - $this: the CrudCode object
 */
?>


<div class="form">
<?php
	$mdl=new $this->modelClass;
	$relations = $mdl->relations();
?>
	
<?php echo "<?php \$form=\$this->beginWidget('CActiveForm', array(
	'id'=>'".$this->class2id($this->modelClass)."-form',
	'enableAjaxValidation'=>false,
)); ?>\n"; ?>

<div class="row buttons">
	<?php echo "<?php \n" ?>
		$this->widget('zii.widgets.jui.CJuiButton',array(
		    'name'=>'button',
		    'caption'=>$model->isNewRecord ? 'Create' : 'Save',
		    'buttonType'=>'button',
		    'htmlOptions'=>array('class'=>'redButton'),
		    'options'=>array(
		    	'icons'=>array('primary'=>'ui-icon-check'),			    	
		    ),
		    'onclick'=>'function(){this.form.submit()}'
		));
		$this->widget('zii.widgets.jui.CJuiButton',array(
		    'name'=>'cancel',
		    'caption'=>'Cancel',
		    'buttonType'=>'button',
		    'htmlOptions'=>array('class'=>'normalButton'),
		    'options'=>array(
		    	'icons'=>array('primary'=>'ui-icon-closethick'),			    	
		    ),
		    'onclick'=>'function(){location.href="'.bu().'/<?php echo $this->modelClass?>/'.($model->isNewRecord ? 'index':'view/'.$model->id).'"; this.blur(); return false;}',
		));
	<?php echo "?>\n" ?>
</div>
<div class="clear"></div>

<?php echo "<?php \n" ?>
	$this->beginWidget('zii.widgets.CPortlet', array(
		'title'=>'<?php echo $this->class2name($this->modelClass)?>',
	));
<?php echo "?>\n" ?>

	<p class="note">Fields with <span class="required">*</span> are required.</p>

	<?php echo "<?php echo \$form->errorSummary(\$model); ?>\n"; ?>

<?php
foreach($this->tableSchema->columns as $column)
{
	if($column->autoIncrement)
		continue;
	else if((stripos($column->name,'date')!==false || $column->dbType == 'date'|| $column->dbType == 'datetime')
		&& $column->name!='created_at' )
	{
		echo "\t<div class=\"row grid_4\">\n";
		echo "\t<?php echo ".$this->generateActiveLabel($this->modelClass,$column)."; ?>\n"; 
		echo "\t<?php \$this->widget('zii.widgets.jui.CJuiDatePicker', 
				array(
					'model'=>\$model,
					'attribute'=>'{$column->name}',
					'options'=>array(
						'showAnim'=>'fold',
						'dateFormat'=>'yy-mm-dd',
						'changeMonth'=>true,
						'changeYear'=>true,
						'duration'=>'fast',
						'showAnim' =>'scale',
						'yearRange'=>'-50',
					),
					'htmlOptions'=>array('style'=>'height:16px;','id'=>'{$column->name}'),
			));
		?>\n";
		echo "\t<?php echo \$form->error(\$model,'{$column->name}'); ?>\n"; 
		echo "\t</div>\n";
		continue;
	}
	else if($column->dbType == 'text')
	{
		echo "\t<div class=\"row grid_8\">\n";
		echo "\t<?php echo ".$this->generateActiveLabel($this->modelClass,$column)."; ?>\n"; 
		echo "\t<?php echo \$form->textArea(\$model,'{$column->name}', array('cols'=>50, 'rows'=>5)); ?>\n"; 
		echo "\t<?php echo \$form->error(\$model,'{$column->name}'); ?>\n"; 
		echo "\t</div>\n";
		continue;		
	}
	else if(array_key_exists($column->name, $this->tableSchema->foreignKeys) && $column->name != 'created_by_id')
	{
		//print_r($this->tableSchema->foreignKeys[$column->name]);
		$foreignKey = $this->tableSchema->foreignKeys[$column->name] ;
		$foreignTable = $foreignKey[0];
		//$foreignModel = str_replace(' ','',ucwords(str_replace('_',' ',$foreignTable) ));
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
				$foreignModel = $rel[1];
				break;						
			}
		}
		
		
		echo "\t<div class=\"row grid_4\">\n";
		echo "\t<?php echo ".$this->generateActiveLabel($this->modelClass,$column)."; ?>\n"; 
		echo "\t<?php /*echo \$form->dropDownlist(\$model,'{$column->name}', \n
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
		echo "\t<?php echo \$form->hiddenField(\$model,'{$column->name}'); ?>\n"; 
		echo "\t<?php 
		\$this->widget('zii.widgets.jui.CJuiAutoComplete', array(
		'name'=>'{$this->modelClass}_{$relname}',
		'source'=>'js: function( request, response ) {
				$.getJSON( \"".Yii::app()->createUrl( "{$foreignModel}/autocomplete") . "\", {
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
		'htmlOptions'=>array('size'=>'30')
		));
		?>\n";	
		echo "\t<?php echo \$form->error(\$model,'{$column->name}'); ?>\n"; 
		echo "\t</div>\n";
		continue;
	}
	else if($column->name=='created_at' || $column->name=='created_by_id')
	{		
		echo "\t<?php echo \$form->hiddenField(\$model,'{$column->name}'); ?>\n"; 
		continue;
	}
?>
	<div class="row grid_4">
		<?php echo "<?php echo ".$this->generateActiveLabel($this->modelClass,$column)."; ?>\n"; ?>
		<?php echo "<?php echo ".$this->generateActiveField($this->modelClass,$column)."; ?>\n"; ?>
		<?php echo "<?php echo \$form->error(\$model,'{$column->name}'); ?>\n"; ?>
	</div>

<?php
}
?>
<div class="clear"></div>


<?php echo "<?php \$this->endWidget(); ?>\n"; // master portlet ?>

<?php echo "<?php \n" ?>
	$this->beginWidget('zii.widgets.CPortlet', array(
		'title'=>'Details',
	));
<?php echo "?>\n" ?>


<?php
/********************************
generate table grid for detail input 
**********************************/
foreach($relations as $relname => $rel): //foreach reated models
if($rel[0]=='CHasManyRelation'):
	$modelName=$rel[1];
	$detailForeignKey=$rel[2];
?>

<?php echo "\n<?php \n" ?>
//detail records : <?php echo $relname  ?>

ob_start(); 
<?php echo "?> \n" ?>
<table width="100%" id="detail<?php echo $modelName  ?>">
<?php
	$mdlDetail=new $modelName;
	$relationsDetail = $mdlDetail->relations();
	$count=0;
?>

	<tr>
<?php
	foreach($mdlDetail->tableSchema->columns as $column)
	{
		if(++$count==7)
			echo "\t\t<!--\n";
			
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
						echo "\t\t<th>\n";
						echo "\t\t<?php echo CHtml::label('{$foreignModel}', '{$modelName}s_'.\$d->id.'_{$column->name}') ?>\n";  
						echo "\t\t</th>\n";
					}
				}
			}
			else
			{
				echo "\t\t<th>\n";
				echo "\t\t<?php echo CHtml::label('{$column->name}','{$modelName}s_'.\$d->id.'_{$column->name}' ) ?> \n";
				echo "\t\t</th>\n";				
			}
		}
	}
	if($count>=7)
		echo "\t\t-->\n";
?>
		<th>
			Actions
		</th>
	</tr>

<?php $count=0; ?>
<?php echo "<?php " ?> 
foreach ($model-><?php echo $relname?> as $d):?>
	<tr id="<?php echo $modelName.'<?php echo $d->id?>'?>">
<?php 
	foreach($mdlDetail->tableSchema->columns as $column)
	{
		if(++$count==7)
			echo "\t\t<!--\n";
			
		if($column->name=='id' or $column->name=='ID' or $column->name=='created_at' or $column->name=='created_by_id')
			continue;
		else if($column->name == $detailForeignKey)
			continue;
		else if($column->dbType=='date' || $column->dbType=='datetime')
		{
			echo "\t\t<td>\n";
			echo "\t\t<?php \$this->widget('zii.widgets.jui.CJuiDatePicker', 
					array(
						'name'=>'{$modelName}s['.\$d->id.'][{$column->name}]',
						'value'=>\$d->{$column->name},
						'options'=>array(
							'showAnim'=>'fold',
							'dateFormat'=>'yy-mm-dd',
							'changeMonth'=>true,
							'changeYear'=>true,
							'duration'=>'fast',
							'showAnim' =>'scale',
							'yearRange'=>'-50',
						),
						'htmlOptions'=>array('style'=>'height:16px;','id'=>'{$column->name}'),
				));
			?>\n";
			echo "\t\t</td>\n";
			continue;
		}

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
						echo "\t\t";
						echo "<td><?php echo CHtml::dropDownList('{$modelName}s['.\$d->id.'][{$column->name}]', 
							\$d->{$relnameDetail}->id,
							CHtml::listData({$foreignModel}::model()->findAll(),'id','name'))?>\n";
						echo "\t\t</td>\n";
					}
				}
			}
			else if($column->dbType==='boolean'||$column->dbType==='tinyint(1)')
			{
				echo "\t\t";
				echo "<td><input type='checkbox' name='{$modelName}s['.\$d->id.'][{$column->name}]' checked='<?php echo \$d->{$column->name}==1?\"chekced\":\"\" ?>'></td>\n";
			}
			else
			{	
				echo "\t\t";
				echo "<td><?php echo CHtml::textField('{$modelName}s['.\$d->id.'][{$column->name}]', \$d->{$column->name}); ?></td>\n";			
			}
		}
	}
	if($count>=7)
		echo "\t\t-->\n";
?>
		<td>
			<a onclick='deleteRow("<?php echo $modelName.'<?php echo $d->id?>'?>")' >
				<img src="<?php echo "<?php echo bu().'/images/icon/delete.png'?>"?>"/>
			</a>
		</td>
	</tr>
<?php echo "<?php " ?> endforeach; // end foreach record detail ?>
</table>



<div class="row grid_16 buttons">
	<button type="button" id="add<?php echo "{$modelName}"?>">Add new <?php echo "{$modelName}"?></button>
</div>
<div class="clear"></div>

<?php echo "<?php " ?> 
$detailContent['<?php echo $modelName ?>'] = ob_get_contents();
ob_end_clean();

cs()->registerScript("<?php echo $modelName ?>","

$(\"#add<?php echo $modelName?>\").click(function() {
	newId<?php echo $modelName  ?>++;
	jsContent<?php echo $modelName  ?> = jsContent<?php echo $modelName  ?>.replace(/new(\d+)/g, 'new'+newId<?php echo $modelName  ?>);
	$(\"#detail<?php echo $modelName  ?>\").append( jsContent<?php echo $modelName  ?> );
});
");
<?php echo "?>" ?>

<?php endif; //if relation has many?>
<?php endforeach; // each related detail models?>





<?php
/********************************
generate new record input
**********************************/
foreach($relations as $relname => $rel): //foreach reated models
if($rel[0]=='CHasManyRelation'):
	$modelName=$rel[1];
	$detailForeignKey=$rel[2];
?>
<script type="text/javascript">
var jsContent<?php echo $modelName  ?>='<tr id="<?php echo $modelName  ?>new000">';
var newId<?php echo $modelName  ?> = 0;
</script>

<?php
	$mdlDetail=new $modelName;
	$relationsDetail = $mdlDetail->relations();
	$count=0;
	foreach($mdlDetail->tableSchema->columns as $column)
	{
		if(++$count==7)
			echo "\t\t<!--\n";
			
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
?>
		<script>
			jsContent<?php echo $modelName  ?> = jsContent<?php echo $modelName  ?> + '<td>'+
			'<?php echo '<?php echo str_replace("\n","",CHtml::dropDownList("'.$modelName.'s[new000]['.$column->name.']", "",CHtml::listData('.$foreignModel.'::model()->findAll(),"id","name"))) ?>'; ?>' +
			'</td>'

		</script>
<?
					}
				}
			}
			else if($column->dbType==='boolean'||$column->dbType==='tinyint(1)')
			{
?>
		<script type="text/javascript">
			jsContent<?php echo $modelName  ?> = jsContent<?php echo $modelName  ?> + '<td>'+
			'<?php echo '<?php echo CHtml::checkbox("'.$modelName.'s[new000]['.$column->name.']", "")?>'; ?>' +
			'</td>'

		</script>
<?
			}
			else
			{	
?>
		<script type="text/javascript">
			jsContent<?php echo $modelName  ?> = jsContent<?php echo $modelName  ?> + '<td>'+
			'<?php echo '<?php echo CHtml::textField("'.$modelName.'s[new000]['.$column->name.']", "")?>'; ?>' +
			'</td>'

		</script>
<?
			}
		}
	}//end column	
	if($count>=7)
		echo "\t\t-->\n";
?>

	<script type="text/javascript">
		jsContent<?php echo $modelName  ?> = jsContent<?php echo $modelName  ?> + '<td>'+
		'<a onclick=deleteRow("<?php echo $modelName?>new000") >' +
		'	<img src="<?php echo "<?php echo bu().'/images/icon/delete.png'?>"?>"/>'+
		'</a>' +
		'</td>'
	</script>

<?php endif; //if relation has many?>
<?php endforeach; // each related detail models?>



<?php
/********************************
generate tabs that display the table grids above for detail input
**********************************/
?>
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


<?php echo "<?php \$this->endWidget(); ?>\n"; // detail portlet?>


<?php echo "<?php \$this->endWidget(); ?>\n"; // form?>

</div><!-- form -->


<?php echo "<?php \n"?>
if($detailContent):
?>
<script>
function deleteRow(id)
{
	$("#"+id).remove();
}
</script>
<?php echo "<?php \n"?>
endif;
?>
