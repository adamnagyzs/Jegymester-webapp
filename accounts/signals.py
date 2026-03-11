from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings

from .models import User


@receiver(post_save, sender=User)
def send_welcome_email(sender, instance, created, **kwargs):
    """Send a welcome email when a new user registers."""
    if created and instance.email:
        try:
            send_mail(
                subject='Üdvözlünk a Cinema platformon! 🎬',
                message=(
                    f'Kedves {instance.username}!\n\n'
                    f'Köszönjük, hogy regisztráltál a Cinema - Online Mozijegy Platformra!\n\n'
                    f'Most már böngészhetsz a filmek között, foglalhatsz jegyeket,\n'
                    f'és nyomon követheted a vetítéseket.\n\n'
                    f'Jó szórakozást kívánunk!\n\n'
                    f'Üdvözlettel,\n'
                    f'A Cinema csapata'
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[instance.email],
                fail_silently=True,
            )
        except Exception:
            pass
