import io

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from babytilly2.celery import app


@app.task()
def import_price(import_id: int) -> None:
    from commercial.models import ImportPrice
    from commercial.functions import do_import_price
    import_price: ImportPrice = ImportPrice.objects.get(id=import_id)

    in_memory_file = io.StringIO()
    with import_price.file.open(mode='rb') as import_file:
        in_memory_file.writelines([l.decode('utf-8-sig') for l in import_file.readlines()])
        in_memory_file.seek(0)

    do_import_price(
        csv_file=in_memory_file,
        country=import_price.departament.country
    )


@app.task()
def import_novelty(import_id: int) -> None:
    from commercial.models import ImportNew
    from commercial.functions import do_import_novelty
    import_price: ImportNew = ImportNew.objects.get(id=import_id)

    in_memory_file = io.StringIO()
    with import_price.file.open(mode='rb') as import_file:
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
    with import_special.file.open(mode='rb') as import_file:
        in_memory_file.writelines([l.decode('utf-8-sig') for l in import_file.readlines()])
        in_memory_file.seek(0)

    do_import_special(
        csv_file=in_memory_file,
        departament_id=import_special.departament_id
    )


@app.task()
def import_debs(import_id: int):
    from commercial.models import ImportDebs
    from commercial.functions import do_import_debs
    import_debs = ImportDebs.objects.get(id=import_id)

    in_memory_file = io.StringIO()
    with import_debs.file.open(mode='rb') as import_file:
        in_memory_file.writelines([l.decode('utf-8-sig') for l in import_file.readlines()])
        in_memory_file.seek(0)

    do_import_debs(csv_file=in_memory_file)


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
    html_body = str(render_to_string('commercial/order_mail.html', context))
    text_body = str(render_to_string('commercial/order_mail_text.html', context))
    stuff_email = Departament.objects.get(id=order.user.profile.departament_id).email
    to_emails = [settings.DEFAULT_FROM_EMAIL, stuff_email]
    if order.user.email:
        to_emails.append(order.user.email)
    additional_emails = filter(bool, [e.strip() for e in order.user.profile.additional_emails.split(',')])
    if additional_emails:
        to_emails += additional_emails
    msg = EmailMultiAlternatives(
        subject='Order {} {}'.format(order, order.user),
        body=text_body,
        to=to_emails,
        reply_to=['order.carrello@gmail.com']
    )
    msg.attach_alternative(html_body, 'text/html')
    for company, csv_file in export_to_csv(order):
        msg.attach(f'order{order.pk} {company}.csv', csv_file, 'text/csv')
    msg.send()


@app.task()
def send_message_mail(user_id: int, message_id: int):
    from commercial.models import Message
    user = get_user_model().objects.select_related('profile').get(pk=user_id)
    message = Message.objects.select_related('complaint').get(pk=message_id)

    context = {
        'user': user,
        'message': message,
    }

    html_body = str(render_to_string('commercial/complaint_mail.html', context))
    to_emails = []
    if user.email:
        to_emails.append(user.email)
    additional_emails = filter(bool, [e.strip() for e in user.profile.additional_emails.split(',')])
    if additional_emails:
        to_emails += additional_emails
    msg = EmailMultiAlternatives(
        subject=f'Complaint {message.complaint} {message.complaint.user} {message.complaint.product_name()}',
        body=str(strip_tags(html_body)),
        to=to_emails,
        reply_to=['complaints.carrello@gmail.com']
    )
    msg.attach_alternative(html_body, 'text/html')
    msg.send()
