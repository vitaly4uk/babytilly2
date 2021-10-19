import codecs

from django.core.management import BaseCommand

from commercial.functions import do_import_csv


class Command(BaseCommand):
    help = "Import data from .csv file"

    def add_arguments(self, parser):
        parser.add_argument('file_name')
        parser.add_argument('country')

    def handle(self, *args, **options):
        with codecs.open(options['file_name'], 'r', encoding='cp1251') as csv_file:
            do_import_csv(csv_file, options['country'])
