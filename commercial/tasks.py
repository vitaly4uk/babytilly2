import io

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

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
        in_memory_file.writelines([l.decode('utf-8-sig') for l in import_file.readlines()])
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
        in_memory_file.writelines([l.decode('utf-8-sig') for l in import_file.readlines()])
        in_memory_file.seek(0)

    do_import_special(
        csv_file=in_memory_file,
        departament_id=import_special.departament_id
    )


@app.task()
def send_order_email(order_id: int):
    from commercial.models import Order, Departament
    from commercial.functions import export_to_csv
    order = Order.objects.get(pk=order_id)

    context = {
        'cart': order.items.all(),
        'order': order,
        'profile': order.user,
    }
    html_body = str(render_to_string('commercial/mail.html', context))
    text_body = str(render_to_string('commercial/mail_text.html', context))
    stuff_email = Departament.objects.get(id=order.user.profile.departament_id).email
    to_emails = [settings.DEFAULT_FROM_EMAIL, stuff_email]
    if order.user.email:
        to_emails.append(order.user.email)
    additional_emails = filter(bool, [e.strip() for e in order.user.profile.additional_emails.split(',')])
    if additional_emails:
        to_emails += additional_emails
    print(f'Sending order #{order_id} to: {to_emails}')
    msg = EmailMultiAlternatives(
        subject='Order {} {}'.format(order, order.user),
        body=text_body,
        to=to_emails,
        reply_to=['order.carrello@gmail.com']
    )
    msg.attach_alternative(html_body, 'text/html')
    for company, csv_file in export_to_csv(order):
        msg.attach(f'zakaz{order.pk} {company}.csv', csv_file, 'text/csv')
    msg.send()
