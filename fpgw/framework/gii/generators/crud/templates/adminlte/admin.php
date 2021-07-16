<section class="content-header">
  <h1>
    Manage <?php echo $this->pluralize($this->class2name($this->modelClass)); ?>
  </h1>
  <ol class="breadcrumb">
    <li><a href="#"><i class="fa fa-dashboard"></i> Home</a></li>
    <li><?php echo $this->modelClass;?></li>
    <li class="active">Manage <?php echo $this->pluralize($this->class2name($this->modelClass)); ?></li>
  </ol>
</section>

<section class="content">
	<div class="row">
		<div class="col-lg-12 col-xs-12">
			<div class="box box-primary">
				<div class="box-body">
					<a class="btn btn-success" href="<?php echo '<?php echo'?> Yii::app()->createUrl('<?php echo strtolower($this->modelClass);?>/create');?>"><span class="glyphicon glyphicon-plus"></span> Buat <?php echo strtolower($this->modelClass);?> baru</a>

					<?php echo "<?php"; ?> $this->widget('zii.widgets.grid.CGridView', array(
						'id'=>'<?php echo $this->class2id($this->modelClass); ?>-grid',
						'dataProvider'=>$model->search(),
						'itemsCssClass'=>'table table-striped table-hover',
						'filter'=>$model,
						'columns'=>array(
					<?php
					$count=0;
					foreach($this->tableSchema->columns as $column)
					{
						if(++$count==7)
							echo "\t\t/*\n";
						echo "\t\t'".$column->name."',\n";
					}
					if($count>=7)
						echo "\t\t*/\n";
					?>
							array(
								'class'=>'JButtonColumn',
							),
						),
					)); ?>
				</div>
			</div>
		</div>
	</div>
</section>
