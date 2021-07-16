<section class="content-header">
  <h1>
    <?php echo $this->modelClass;?> Detail
  </h1>
  <ol class="breadcrumb">
    <li><a href="#"><i class="fa fa-dashboard"></i> Home</a></li>
    <li><?php echo $this->modelClass;?></li>
    <li class="active"><?php echo $this->modelClass;?> Detail</li>
  </ol>
</section>
<section class="content">
	<div class="row">
		<div class="col-lg-12 col-xs-12">
			<div class="box box-primary">
				<div class="box-body">
			<?php echo "<?php"; ?> $this->widget('zii.widgets.CDetailView', array(
				'data'=>$model,
				'htmlOptions'=>array('class'=>'table table-striped table-hover'),
				'attributes'=>array(
			<?php
			foreach($this->tableSchema->columns as $column)
				echo "\t\t'".$column->name."',\n";
			?>
				),
			)); ?>
					<a class="btn btn-primary" href="<?php echo '<?php echo'?> Yii::app()->createUrl('<?php echo strtolower($this->modelClass);?>/index');?>"><span class="glyphicon glyphicon-chevron-left"></span> Kembali ke <?php echo strtolower($this->modelClass);?> list</a>
					<a class="btn btn-success" href="<?php echo '<?php echo'?> Yii::app()->createUrl('<?php echo strtolower($this->modelClass);?>/update',array('id'=>$model-><?php echo $this->tableSchema->primaryKey; ?>));?>"><span class="glyphicon glyphicon-pencil"></span> Update <?php echo strtolower($this->modelClass);?></a>
				</div>
			</div>
		</div>
	</div>
</section>
