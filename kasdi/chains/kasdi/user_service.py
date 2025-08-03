from databases.models.kasdi import User
from controllers import readed_book_controller


class UserContextService:
    """Service for preparing user-related context data."""

    @staticmethod
    async def prepare_readed_books(user: User) -> str:
        """Prepare user's read books information."""
        readed_books = await readed_book_controller.get_readed_books_by_user_id(user.id)

        if not readed_books:
            return "The user does not provide any read books."

        book_info = [
            f"Title: {book.title}\nAuthor: {book.author or 'Unknown'}\nUser Notes: {book.notes or 'No notes'}"
            for book in readed_books
        ]

        return "\n\n".join(book_info)

    @staticmethod
    async def prepare_user_instructions(user: User) -> str:
        """Prepare user's custom instructions."""
        if not user.custom_instruction:
            return "The user has no specific instructions."

        return user.custom_instruction

    @staticmethod
    async def prepare_memory(user: User) -> str:
        """Prepare user's memory items."""
        if user.memory_enabled is False:
            return "Memory is disabled for this user."

        if not user.memory:
            return "We do not have any memory for this user."

        memory_items = [
            "- " + item.content + f" (created at {item.created_at.strftime('%Y-%m-%d')})"
            for item in user.memory if item.content
        ]

        return "\n".join(memory_items)

    @classmethod
    async def prepare_user_context(cls, user: User) -> dict:
        """Prepare all user context data."""
        user_name = f"{user.first_name} {user.last_name or ''}".strip()
        users_books = await cls.prepare_readed_books(user)
        user_instructions = await cls.prepare_user_instructions(user)
        memory = await cls.prepare_memory(user)

        return {
            "user_name": user_name,
            "users_books": users_books,
            "user_instructions": user_instructions,
            "memory": memory,
        }
