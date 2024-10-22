from abc import ABC, abstractmethod

from domain.entities.user import User


class UsersPort(ABC):

    @abstractmethod
    def retrieve_user(self, username: str) -> User:
        pass

    @abstractmethod
    def update_user(self, user: User) -> None:
        pass