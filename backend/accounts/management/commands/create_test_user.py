from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Ustvari test uporabnika mihaelv / corelite'

    def handle(self, *args, **options):
        email = 'mihael.veber@gmail.com'
        username = 'mihaelv'
        password = 'corelite'

        if User.objects.filter(username=username).exists():
            self.stdout.write(
                self.style.WARNING(f'Uporabnik {username} že obstaja')
            )
            return

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'✅ Test uporabnik uspešno ustvarjen!\n'
                f'   Username: {username}\n'
                f'   Email: {email}\n'
                f'   Password: {password}'
            )
        )
