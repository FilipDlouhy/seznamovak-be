from common.exceptions import NotFoundError


class UserService:
    """User account retrieval."""

    def __init__(self, *, user_repository):
        self.user_repository = user_repository

    def get_by_id(self, *, user_id):
        user = self.user_repository.get_by_id(user_id)
        if user is None:
            raise NotFoundError("User not found.")
        return user
