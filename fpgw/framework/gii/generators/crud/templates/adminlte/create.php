<section class="content-header">
  <h1>
    Buat <?php echo $this->modelClass; ?>
  </h1>
  <ol class="breadcrumb">
    <li><a href="#"><i class="fa fa-dashboard"></i> Home</a></li>
    <li><?php echo $this->modelClass;?></li>
    <li class="active">Buat <?php echo $this->modelClass; ?></li>
  </ol>
</section>

<section class="content">
	<div class="row">
		<div class="col-lg-12 col-xs-12">
			<div class="box box-primary">
				<div class="box-body">
					<?php echo "<?php \$this->renderPartial('_form', array('model'=>\$model)); ?>"; ?>
				</div>
			</div>
		</div>
	</div>
</section>


