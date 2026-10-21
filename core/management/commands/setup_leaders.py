from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Create or refresh the Club leaders group with club content permissions only.'

    def handle(self, *args, **options):
        group, _ = Group.objects.get_or_create(name='Club leaders')
        permissions = Permission.objects.filter(content_type__app_label__in=['core', 'events'])
        group.permissions.set(permissions)
        self.stdout.write(self.style.SUCCESS('Club leaders group is ready. Assign staff users to this group in admin.'))
