import os
from aiogram import Bot, Router, types
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

from controllers import user_controller


router = Router(
    name="comands",
)

class InstructionState(StatesGroup):
    waiting_for_instruction = State()

@router.message(CommandStart())
async def start_handler(message: Message):
    user_data = message.from_user

    user = await user_controller.get_user_by_tg_id(user_data.id)

    if user:
        user.first_name = user_data.first_name
        user.last_name = user_data.last_name
        await user_controller.update_user(user)
        greeting = f"Привіт, {user.first_name}! Ти як?"
    else:
        user = user_controller.User(
            tg_id=user_data.id,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
        )
        await user_controller.create_user(user)
        greeting = f"Привіт, {user.first_name}! Ти новий користувач. Як справи?"

    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📝 Розкажи про себе")],
            [KeyboardButton(text="📚 Додати прочитану книгу")]
        ],
        resize_keyboard=True
    )

    await message.answer(greeting, reply_markup=keyboard)


@router.message(lambda m: m.text == "📝 Розкажи про себе")
async def ask_for_instruction(message: types.Message, state: FSMContext):
    message_text = (
        "📝 Розкажи про себе, щоб я могла краще тобі допомагати.\n\n"
        "Це твої особисті інструкції для мене. Напиши все, що вважаєш важливим:\n\n"
        "— Як ти хочеш, щоб я до тебе зверталась?\n"
        "— Які жанри або теми тобі цікаві?\n"
        "— Які книжки ти прочитав нещодавно?\n"
        "— Чого ти очікуєш від наших розмов?\n\n"
        "Це допоможе мені краще підлаштуватися під тебе 📚✨\n"
        "Просто надішли свою інструкцію, і я її запам’ятаю 💡"
    )

    your_instruction = "Ось твоя інструкція: \n\n"

    markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="❌ Скасувати", callback_data="cancel_instruction")]
        ]
    )

    user = await user_controller.get_user_by_tg_id(message.from_user.id)
    if user and getattr(user, "custom_instruction", None):
        your_instruction += f"{user.custom_instruction}\n"
        markup.inline_keyboard.append(
            [InlineKeyboardButton(text="🗑️ Видалити інструкцію", callback_data="delete_instruction")]
        )

        await message.answer(message_text)
        await message.answer(your_instruction, reply_markup=markup)
    else:
        await message.answer(message_text, reply_markup=markup)

    await state.set_state(InstructionState.waiting_for_instruction)


@router.callback_query(
    lambda c: c.data == "cancel_instruction",
    InstructionState.waiting_for_instruction
)
async def cancel_instruction(callback_query: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback_query.message.edit_reply_markup(reply_markup=None)
    await callback_query.message.answer("❌ Інструкцію скасовано.")


@router.callback_query(
    lambda c: c.data == "delete_instruction",
    InstructionState.waiting_for_instruction
)
async def delete_instruction(callback_query: types.CallbackQuery, state: FSMContext):
    user = await user_controller.get_user_by_tg_id(callback_query.from_user.id)
    if user and getattr(user, "custom_instruction", None):
        user.custom_instruction = None
        await user_controller.update_user(user)

        await state.clear()
        await callback_query.message.edit_reply_markup(reply_markup=None)
        await callback_query.message.delete()
        await callback_query.message.answer("🗑️ Інструкцію видалено.")


@router.message(InstructionState.waiting_for_instruction)
async def save_instruction(message: types.Message, state: FSMContext):
    new_instruction = message.text
    user = await user_controller.get_user_by_tg_id(message.from_user.id)

    if not user:
        await message.answer("Користувача не знайдено.")
        await state.clear()
        return

    user.custom_instruction = new_instruction
    await user.save()

    await message.answer("✅ Інструкція збережена.")
    await state.clear()
