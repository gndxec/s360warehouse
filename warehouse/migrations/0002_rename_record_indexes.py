from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("warehouse", "0001_initial"),
    ]

    operations = [
        migrations.RenameIndex(
            model_name="warehouserecord",
            new_name="wh_rec_resource_active_idx",
            old_name="warehouse_w_resource_b38f9c_idx",
        ),
        migrations.RenameIndex(
            model_name="warehouserecord",
            new_name="wh_rec_kind_active_idx",
            old_name="warehouse_w_resource_49f112_idx",
        ),
    ]
