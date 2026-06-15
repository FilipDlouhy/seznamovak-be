from django.db.models import Model


class BaseRepository[T: Model]:
    """Generic data access for a Django model; the only place that talks to Model.objects."""

    model: type[T]

    def get_by_id(self, pk) -> T | None:
        return self.model.objects.filter(pk=pk).first()

    def get_by_id_for_update(self, pk) -> T | None:
        return self.model.objects.select_for_update().filter(pk=pk).first()

    def get_all(self) -> list[T]:
        return list(self.model.objects.all())

    def count(self) -> int:
        return self.model.objects.count()

    def save(self, instance: T, *, update_fields: list[str] | None = None, validate: bool = True) -> T:
        if validate:
            instance.full_clean()
        instance.save(update_fields=update_fields)
        return instance

    def delete(self, instance: T) -> None:
        instance.delete()
