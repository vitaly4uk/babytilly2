import codecs

from django.core.management import BaseCommand

from commercial.functions import do_import_price


class Command(BaseCommand):
    help = "Import data from .csv file"

    def add_arguments(self, parser):
        parser.add_argument('file_name')
        parser.add_argument('country')

    def handle(self, *args, **options):
        with codecs.open(options['file_name'], 'r', encoding='utf-8-sig') as csv_file:
            do_import_price(csv_file, options['country'])
