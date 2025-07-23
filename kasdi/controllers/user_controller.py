from typing import Optional
from databases.models.kasdi import User


async def get_user_by_id(user_id: str) -> Optional[User]:
    """
    Fetch a user by their ID from the database.

    :param user_id: The ID of the user to fetch.
    :return: The User object if found, otherwise None.
    """
    return await User.get(user_id) if user_id else None


async def get_user_by_tg_id(tg_id: int) -> Optional[User]:
    """
    Fetch a user by their Telegram ID from the database.

    :param tg_id: The Telegram ID of the user to fetch.
    :return: The User object if found, otherwise None.
    """
    return await User.find_one(User.tg_id == tg_id) if tg_id else None


async def create_user(user: User) -> User:
    """
    Create a new user in the database.
    """
    await user.save()
    return user


async def update_user(user: User) -> User:
    """
    Update an existing user in the database.

    :param user: The User object with updated information.
    :return: The updated User object.
    """
    await user.save()
    return user
