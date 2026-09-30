from django.contrib.auth import get_user_model
from django.db.models.signals import pre_delete
from django.dispatch import receiver

from companies.models import Company


@receiver(pre_delete, sender=Company)
def reset_owner_flag(sender, instance, **kwargs):
    '''Снимает флаг с владельца до удаления компании.
    Связь user.company обнуляется через on_delete=SET_NULL.
    Флаг нужно сбросить отдельно, иначе сработает проверка:
    "владелец должен быть привязан к компании".'''

    User = get_user_model()
    User.objects.filter(company_id=instance.pk, is_company_owner=True).update(
        is_company_owner=False,
    )