from contact.models import Newsletter, Subscriber
from django.core.management.base import BaseCommand
from django.db.transaction import set_autocommit, commit
from eucs_platform.logger import log_message


class Command(BaseCommand):
    label = 'Send all newsletters with status Ready'

    def add_arguments(self, parser):
        parser.add_argument('-i', '--id', type=int, help='Newsletter ID')
        parser.add_argument('-m', '--mass', type=bool, help='Mass')

    def handle(self, *args, **options):
        if options['id']:
            dset = Newsletter.objects.filter(id=options['id'])
        else:
            dset = Newsletter.objects.filter(status=Newsletter.READY)

        set_autocommit(False)
        for newsletter in dset:
            newsletter.status = Newsletter.QUEUED
            newsletter.save()
            commit()
            print('Iniciando envio')
            if options['mass']:
                subscribers = Subscriber.objects.filter(opt_out=False).exclude(last_newsletter=newsletter)
            else:
                subscribers = Subscriber.objects.filter(opt_out=False).exclude(last_newsletter=newsletter)[0:10]

            count = 0
            try:
                for subscriber in subscribers:
                    newsletter.send(subscriber)
                    subscriber.last_newsletter = newsletter
                    subscriber.save()
                    count += 1
                    print(subscriber.email)

                newsletter.status = Newsletter.SENT
                newsletter.sent_count += count
                newsletter.save()
                log_message(newsletter, 'Sent')
                commit()
                print(f'Envio realizado para {count} contatos')

            except Exception as e:
                newsletter.status = Newsletter.ERROR
                newsletter.sent_count += count
                newsletter.save()
                log_message(newsletter, str(e))
                commit()
