from typing import Optional
from database.models.kasdi import User, MemoryItem


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


async def add_user_memory(user: User | str, content: str) -> User:
    """
    Add a memory item to the user's memory.

    :param user: The User object to update.
    :param content: The content to store in memory.
    :return: The updated User object with the new memory item.
    """
    if isinstance(user, str):
        user = await get_user_by_id(user)

    if not user:
        raise ValueError("User not found.")

    if not user.memory_enabled:
        raise ValueError("Memory is disabled for this user.")

    if not user.memory:
        user.memory = []

    user.memory.append(MemoryItem(content=content))
    await user.save()
    return user
