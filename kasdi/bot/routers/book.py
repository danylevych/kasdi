from aiogram import Router, types, Bot
from aiogram.types import Message
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
from bot.utils import BookMessagesParser

from core.configs import get_config
from controllers import (
    user_controller,
    readed_book_controller,
)


router = Router(
    name="book",
)


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
    user = await user_controller.get_user_by_tg_id(message.from_user.id)

    if not user:
        await message.answer("Користувача не знайдено.")
        return

    books = await readed_book_controller.get_readed_books_by_user_id(user.id)

    if not books:
        await message.answer("📚 У тебе ще немає прочитаних книг.")


    for book in books:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="❌ Видалити",
                    callback_data=f"delete_book:{str(book.id)}"
                ),
                # TODO: ADD EDIT BOOK CALLBACK
                # InlineKeyboardButton(
                #     text="✏️ Редагувати",
                #     callback_data=f"edit_book:{str(book.id)}"
                # ),
            ]
        ])
        text = f"📖 <b>{book.title}</b>"

        if book.notes:
            text += f"\n📝 {book.notes}"

        # TODO: FIND RELEVANT INFO ABOUT BOOK IN KDS DATABASE
        await message.answer(text, reply_markup=kb, parse_mode="HTML")

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
    user = await user_controller.get_user_by_tg_id(callback.from_user.id)

    if not user:
        await callback.answer("Користувача не знайдено.")
        return

    result = await readed_book_controller.delete_readed_book(user_id=user.id, book_id=book_id)

    if result:
        await callback.message.edit_reply_markup(reply_markup=None)
        await callback.message.edit_text("✅ Ми видалили книгу з твоїх прочитаних.")
    else:
        await callback.answer("❌ Помилка при видаленні книги.", show_alert=True)


@router.callback_query(AddReadedBookCallback())
async def start_book_session(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.delete()

    await state.set_state(BookInput.collecting)
    await state.update_data(entries=[], last_prompt_id=None)

    prompt = await callback.message.answer(
        "📚 Надішли мені записи про прочитані книги. Коли завершиш — просто збережи, я опрацюю їх )",
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
    await state.clear()
    await callback.message.edit_reply_markup(None)
    await callback.message.answer("❌ Добренько, додаси пізніше 😅")
    await callback.answer()


@router.message(BookInput.collecting)
async def collect_entries(message: Message, state: FSMContext):
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
        "📚 Запис додано. Надішли ще одну книгу або натисни кнопку, щоб зберегти всі записи.",
        reply_markup=book_session_keyboard
    )

    await state.update_data(last_prompt_id=prompt.message_id)


@router.callback_query(SaveAllReadedBooksCallback(), BookInput.collecting)
async def save_all_books(callback: types.CallbackQuery, state: FSMContext):
    user = await user_controller.get_user_by_tg_id(callback.from_user.id)

    if not user:
        await callback.answer("Користувача не знайдено.", show_alert=True)
        await state.clear()
        return

    readed_books = await readed_book_controller.get_readed_books_by_user_id(user.id)

    data = await state.get_data()
    entries = data.get("entries", [])

    readed_books = await BookMessagesParser(callback.message.bot, get_config().OPENAI_API_KEY).parse(
        messages=entries,
        actual_readed_books=readed_books
    )

    created = await readed_book_controller.create_readed_books(readed_books, user.id)

    await callback.message.edit_reply_markup(None)
    await callback.message.answer(f"✅ Збережено {len(created)} записів.")
    await state.clear()
    await callback.answer()


@router.callback_query(CancelAllReadedBooksCallback(), BookInput.collecting)
async def cancel_all_books(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_reply_markup(None)
    await callback.message.answer("❌ Ого, ми скасували всі твої записи. Якщо захочеш, можеш спробувати ще раз пізніше.")
    await callback.answer()
