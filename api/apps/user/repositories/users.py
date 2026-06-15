from apps.user.models import User
from common.repositories import BaseRepository


class UserRepository(BaseRepository[User]):
    """Data access for user accounts."""

    model = User
