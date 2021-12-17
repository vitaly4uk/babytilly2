import io

from babytilly2.celery import app


@app.task()
def import_price(import_id: int):
    from commercial.models import ImportPrice
    from commercial.functions import do_import_price
    import_price = ImportPrice.objects.get(id=import_id)

    in_memory_file = io.StringIO()
    with import_price.file.open(mode='r') as import_file:
        in_memory_file.writelines([l.decode('cp1251') for l in import_file.readlines()])
        in_memory_file.seek(0)

    do_import_price(
        csv_file=in_memory_file,
        country=import_price.departament.country
    )


@app.task()
def import_novelty(import_id: int):
    from commercial.models import ImportNew
    from commercial.functions import do_import_novelty
    import_price = ImportNew.objects.get(id=import_id)

    in_memory_file = io.StringIO()
    with import_price.file.open(mode='r') as import_file:
        in_memory_file.writelines([l.decode('cp1251') for l in import_file.readlines()])
        in_memory_file.seek(0)

    do_import_novelty(
        csv_file=in_memory_file,
        departament_id=import_price.departament_id
    )


@app.task()
def import_special(import_id: int):
    from commercial.models import ImportSpecial
    from commercial.functions import do_import_special
    import_special = ImportSpecial.objects.get(id=import_id)

    in_memory_file = io.StringIO()
    with import_special.file.open(mode='r') as import_file:
        in_memory_file.writelines([l.decode('cp1251') for l in import_file.readlines()])
        in_memory_file.seek(0)

    do_import_special(
        csv_file=in_memory_file,
        departament_id=import_special.departament_id
    )
