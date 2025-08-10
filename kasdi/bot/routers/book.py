from aiogram import Router, types, Bot
from aiogram.types import Message, LinkPreviewOptions
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

from bot.filters.book import (
    ShowReadedBooksFilter,
    DeleteReadedBookCallback,
    AddReadedBookCallback,
    SaveAllReadedBooksCallback,
    CancelAllReadedBooksCallback,
    CancelAddingBooksCallback,
)

from bot.types import BookCreateMessage
from bot.parsers.book_parser import BookMessagesParser

from core.configs import get_config
from controllers import (
    user_controller,
    readed_book_controller,
)

from core.logger import create_scoped_logger


router = Router(
    name="book",
)

logger = create_scoped_logger("kasdi.bot.routers.book")

READED_BOOKS_LIMIT = 15

async def is_readed_books_limit_reached(user_id: str) -> bool:
    readed_books = await readed_book_controller.get_readed_books_by_user_id(user_id)
    return len(readed_books) >= READED_BOOKS_LIMIT


class BookInput(StatesGroup):
    collecting = State()


book_session_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="✅ Зберегти всі",
                callback_data="save_all_books"
            ),
            InlineKeyboardButton(
                text="❌ Скасувати всі",
                callback_data="cancel_all_books"
            ),
        ]
    ]
)


@router.message(ShowReadedBooksFilter())
async def readed_books_handler(message: types.Message):
    logger.info(f"Read books requested: user_tg_id={message.from_user.id}")
    user = await user_controller.get_user_by_tg_id(message.from_user.id)

    if not user:
        logger.warning("User not found for read books view")
        await message.answer("Користувача не знайдено.")
        return

    books = await readed_book_controller.get_readed_books_by_user_id(user.id, attach_ksd_info=True)

    if not books:
        logger.info("No read books found for user")
        await message.answer("📚 У тебе ще немає прочитаних книг.")

    else:
        await message.answer("<b>📚 Ось список твоїх прочитаних книг:</b>", parse_mode="HTML")

    for readed_book, ksd_book in books:
        logger.debug(f"Rendering read book: id={readed_book.id}")
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="❌ Видалити",
                    callback_data=f"delete_book:{str(readed_book.id)}"
                ),
                # TODO: ADD EDIT BOOK CALLBACK
                # InlineKeyboardButton(
                #     text="✏️ Редагувати",
                #     callback_data=f"edit_book:{str(book.id)}"
                # ),
            ]
        ])
        text = f"📖 <b>{readed_book.title}</b>"

        if readed_book.author:
            text += f"\n👤 <i>{readed_book.author}</i>"

        if readed_book.notes:
            text += f"\n📝 {readed_book.notes}"

        if ksd_book:
            text += f"\n🔗 <a href=\"{ksd_book.url}\">Перейти до книги</a>"
            text += f"\n📚 <i>Жанр: {ksd_book.genre}</i>" if ksd_book.genre else ""
            text += f"\n🏢 <i>Видавництво: {ksd_book.publisher}</i>" if ksd_book.publisher else ""
            text += f"\n📆 <i>Рік видання: {ksd_book.publish_year}</i>" if ksd_book.publish_year else ""
            text += f"\n📖 <i>ISBN: {ksd_book.isbn}</i>" if ksd_book.isbn else ""

        await message.answer(text.strip(), reply_markup=kb, parse_mode="HTML", link_preview_options=LinkPreviewOptions(is_disabled=True))

    if await is_readed_books_limit_reached(user.id):
        logger.info("Read books limit reached; notifying user")
        await message.answer(
            f"A... іще - ти досяг ліміту в {READED_BOOKS_LIMIT} прочитаних книг, поки твоя поличка забита. 📚"
        )
        return

    await message.answer(
        "➕ Щоб додати нову/нові книги, просто натисни кнопку:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="📚 Додати книгу/книги", callback_data="add_book")
            ]
        ]))


@router.callback_query(DeleteReadedBookCallback())
async def delete_book(callback: types.CallbackQuery):
    book_id = callback.data.split(":")[1]
    logger.info(f"Delete read book requested: book_id={book_id}, user_tg_id={callback.from_user.id}")
    user = await user_controller.get_user_by_tg_id(callback.from_user.id)

    if not user:
        logger.warning("User not found when deleting read book")
        await callback.answer("Користувача не знайдено.")
        return

    result = await readed_book_controller.delete_readed_book(user_id=user.id, book_id=book_id)

    if result:
        logger.info("Read book deleted successfully")
        await callback.message.edit_reply_markup(reply_markup=None)
        await callback.message.edit_text("✅ Ми видалили книгу з твоїх прочитаних.")
    else:
        logger.error("Failed to delete read book")
        await callback.answer("❌ Помилка при видаленні книги.", show_alert=True)


@router.callback_query(AddReadedBookCallback())
async def start_book_session(callback: types.CallbackQuery, state: FSMContext):
    logger.info(f"Start book session requested: user_tg_id={callback.from_user.id}")
    await callback.message.delete()

    await state.set_state(BookInput.collecting)
    await state.update_data(entries=[], last_prompt_id=None)

    prompt = await callback.message.answer(
        "📚 Надішли мені записи про прочитані книги (фото, текст, аудіо). Коли завершиш — просто збережи, я опрацюю їх )",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="❌ Скасувати",
                        callback_data="cancel_adding_books"
                    )
                ]
            ]
        )
    )
    await state.update_data(last_prompt_id=prompt.message_id)
    await callback.answer()


@router.callback_query(CancelAddingBooksCallback(), BookInput.collecting)
async def cancel_adding_books(callback: types.CallbackQuery, state: FSMContext):
    logger.info(f"Cancel adding books: user_tg_id={callback.from_user.id}")
    await state.clear()
    await callback.message.edit_reply_markup(None)
    await callback.message.answer("❌ Добренько, додаси пізніше 😅")
    await callback.answer()


@router.message(BookInput.collecting)
async def collect_entries(message: Message, state: FSMContext):
    logger.debug("Collecting book entry from message")
    data = await state.get_data()

    last_id = data.get("last_prompt_id")
    if last_id:
        try:
            await message.bot.delete_message(message.chat.id, last_id)
        except:
            pass

    entries = data["entries"]
    entries.append(BookCreateMessage.from_message(message))

    await state.update_data(entries=entries)

    prompt = await message.answer(
        "📚 Запис додано. Надішли ще або натисни кнопку, щоб зберегти всі записи.",
        reply_markup=book_session_keyboard
    )

    await state.update_data(last_prompt_id=prompt.message_id)


@router.callback_query(SaveAllReadedBooksCallback(), BookInput.collecting)
async def save_all_books(callback: types.CallbackQuery, state: FSMContext):
    logger.info(f"Save all read books requested: user_tg_id={callback.from_user.id}")
    user = await user_controller.get_user_by_tg_id(callback.from_user.id)

    if not user:
        logger.warning("User not found while saving read books")
        await callback.answer("Користувача не знайдено.", show_alert=True)
        await state.clear()
        return

    readed_books = await readed_book_controller.get_readed_books_by_user_id(user.id)

    data = await state.get_data()
    entries = data.get("entries", [])

    readed_books = await BookMessagesParser(callback.message.bot, get_config().OPENAI_API_KEY).parse(
        messages=entries,
        user=user,
    )
    logger.debug(f"Parsed entries into read books count={len(readed_books)}")

    created = await readed_book_controller.create_readed_books(readed_books[:READED_BOOKS_LIMIT], user)
    logger.info(f"Created read books count={len(created)}")

    if not created:
        logger.warning("No read books created from session")
        await callback.answer("На жаль, я не зберегла жодної книги")
        await state.clear()
        return

    await readed_book_controller.tie_readed_books_to_ksd_item(created)
    logger.debug("Tied read books to KSD items where possible")

    await callback.message.edit_reply_markup(None)
    await callback.message.answer(f"✅ Збережено {len(created)} записів.")
    await state.clear()
    await callback.answer()


@router.callback_query(CancelAllReadedBooksCallback(), BookInput.collecting)
async def cancel_all_books(callback: types.CallbackQuery, state: FSMContext):
    logger.info(f"Cancel all read books session: user_tg_id={callback.from_user.id}")
    await state.clear()
    await callback.message.edit_reply_markup(None)
    await callback.message.answer("❌ Ого, ми скасували всі твої записи. Якщо захочеш, можеш спробувати ще раз пізніше.")
    await callback.answer()
