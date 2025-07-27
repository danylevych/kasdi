from beanie.operators import Eq
from typing import List, Optional

from bson import ObjectId
from databases.models.kasdi import ReadedBook
from controllers import user_controller


async def get_readed_books_by_user_id(user_id: str) -> List[ReadedBook]:
    """
    Get all read books for a specific user.

    :param user_id: The ID of the user whose read books are to be fetched.
    :return: A list of ReadedBook objects if found, otherwise None.
    """
    return await ReadedBook.find(ReadedBook.user.id == user_id).to_list()


async def get_readed_book_by_user_tg_id(tg_id: int) -> List[ReadedBook]:
    """
    Get all read books for a user by their Telegram ID.

    :param tg_id: The Telegram ID of the user whose read books are to be fetched.
    :return: A list of ReadedBook objects if found, otherwise None.
    """
    user = await user_controller.get_user_by_tg_id(tg_id)

    if not user:
        return []

    return await get_readed_books_by_user_id(user.id)


async def create_readed_book(readed_book: ReadedBook) -> ReadedBook:
    """
    Create a new read book entry in the database.

    :param readed_book: The ReadedBook object to be created.
    :return: The created ReadedBook object.
    """
    await readed_book.save()
    return readed_book


async def create_readed_books(readed_books: List[ReadedBook], user_id: str) -> List[ReadedBook]:
    """
    Create multiple read book entries in the database.

    :param readed_books: List of ReadedBook objects to be created.
    :param user_id: The ID of the user who owns these read books.
    :return: List of created ReadedBook objects.
    """
    for book in readed_books:
        book.user = ObjectId(user_id)
        await book.save()

    return readed_books


async def delete_readed_book(
        user_id: Optional[str] = None,
        user_tg_id: Optional[int] = None,
        book_id: Optional[str] = None
    ) -> bool:
    """
    Delete a read book entry from the database.

    :param user_id: The ID of the user whose read book is to be deleted.
    :param user_tg_id: The Telegram ID of the user whose read book is to be deleted.
    :param book_id: The ID of the book to be deleted.
    """
    if book_id is None:
        return

    if user_id:
        result = await ReadedBook.find(
            Eq(ReadedBook.id, ObjectId(book_id)),
            Eq(ReadedBook.user.id, ObjectId(user_id))
        ).delete()
        return result.deleted_count > 0

    elif user_tg_id:
        user = await user_controller.get_user_by_tg_id(user_tg_id)
        if user:
            result = await ReadedBook.find(
                Eq(ReadedBook.id, ObjectId(book_id)),
                Eq(ReadedBook.user.id, user.id)
            ).delete()

            return result.deleted_count > 0


async def delete_readed_books_by_user_id(user_id: str) -> bool:
    """
    Delete all read books for a specific user.

    :param user_id: The ID of the user whose read books are to be deleted.
    """
    result = await ReadedBook.find(ReadedBook.user.id == user_id).delete()
    return result.deleted_count > 0
