import io
from babytilly2.celery import app


@app.task()
def import_price(import_id: int):
    from commercial.models import ImportPrice
    from commercial.functions import do_import_csv
    import_price = ImportPrice.objects.get(id=import_id)

    in_memory_file = io.StringIO()
    with import_price.file.open(mode='r') as import_file:
        in_memory_file.writelines([l.decode('cp1251') for l in import_file.readlines()])
        in_memory_file.seek(0)

    do_import_csv(
        csv_file=in_memory_file,
        country=import_price.departament.country
    )
