from beanie.operators import Eq
from beanie import Link
from typing import List, Optional, Tuple, Union

from bson import ObjectId
from database.models.kasdi import ReadedBook, User
from database.models.ksd import Book as KSDItem
from controllers import user_controller


async def get_readed_books_by_user_id(
    user_id: str,
    attach_ksd_info: bool = False
) -> Union[List[ReadedBook], List[Tuple[ReadedBook, KSDItem]]]:
    """
    Get all read books for a specific user.

    :param user_id: The ID of the user whose read books are to be fetched.
    :return: A list of ReadedBook objects if found, otherwise None.
    """

    books = await ReadedBook.find(ReadedBook.user.id == user_id).to_list()

    if attach_ksd_info:
        fully_book_data = []

        for book in books:
            ksd_book = await KSDItem.get(book.ksd_book_id) if book.ksd_book_id else None
            fully_book_data.append((book, ksd_book))

        return fully_book_data

    return books


async def tie_readed_books_to_ksd_item(readed_books: List[ReadedBook]) -> None:
    """
    Tie read books to a KSD item.

    :param readed_books: The list of read books to be tied.
    :param ksd_item_id: The ID of the KSD item to tie the books to.
    """
    from chains.tools import SearchBooksTool

    search_tool = SearchBooksTool()

    for readed_book in readed_books:
        ksd_book = await search_tool.find(
            title=readed_book.title,
            author_name=readed_book.author,
            limit=1,
        )

        if ksd_book:
            readed_book.ksd_book_id = ksd_book[0]['_id']
            readed_book.author = ksd_book[0].get('author', readed_book.author)
            readed_book.title = ksd_book[0].get('title', readed_book.title)

        await readed_book.save()


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


async def create_readed_books(readed_books: List[ReadedBook], user: User) -> List[ReadedBook]:
    """
    Create multiple read book entries in the database.

    :param readed_books: List of ReadedBook objects to be created.
    :param user_id: The ID of the user who owns these read books.
    :return: List of created ReadedBook objects.
    """
    for book in readed_books:
        existing_books = await ReadedBook.find(
            Eq(ReadedBook.user.id, user.id),
            Eq(ReadedBook.title, book.title)
        ).to_list()

        if existing_books:
            continue

        book.user = user
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
