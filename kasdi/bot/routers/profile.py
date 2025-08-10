from aiogram import Router, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

from ..filters.profile import (
    ShowProfileFilter,
    AddInstructionCallback,
    EditInstructionCallback,
    DeleteInstructionCallback,
    CancelInstructionCallback,
)

from controllers import (
    user_controller,
)

from core.logger import create_scoped_logger

router = Router(
    name="profile",
)

logger = create_scoped_logger("kasdi.bot.routers.profile")

class InstructionState(StatesGroup):
    waiting_for_instruction = State()


user_instruction_prompt = (
    "📝 Розкажи про себе, щоб я могла краще тобі допомагати.\n\n"
    "Це твої особисті інструкції для мене. Напиши все, що вважаєш важливим:\n\n"
    "— Як ти хочеш, щоб я до тебе зверталась?\n"
    "— Які жанри або теми тобі цікаві?\n"
    "— Які книжки ти прочитав нещодавно?\n"
    "— Чого ти очікуєш від наших розмов?\n\n"
    "Це допоможе мені краще підлаштуватися під тебе 📚✨\n"
    "Просто надішли свою інструкцію, і я її запам’ятаю 💡"
)


@router.message(ShowProfileFilter())
async def profile_handler(message: types.Message):
    logger.info(f"Profile view requested: user_tg_id={message.from_user.id}")
    user = await user_controller.get_user_by_tg_id(message.from_user.id)

    await message.answer(
        "📝 Тут ти можеш додати або змінити свою інструкцію «Про мене».\n"
        "💡 Це допоможе мені краще розуміти твої потреби і надавати більш персоналізовану допомогу.",
    )

    if user and user.custom_instruction:
        logger.debug("User has custom instruction; presenting edit/delete options")
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✏️ Змінити інструкцію",
                    callback_data="edit_instruction"
                ),
                InlineKeyboardButton(
                    text="🗑️ Видалити інструкцію",
                    callback_data="delete_instruction"
                ),
            ]
        ])
        await message.answer(
            f"📝 <b>Твоя інструкція «Про мене»</b>:\n\n"
            f"{user.custom_instruction}",
            parse_mode="HTML",
            reply_markup=kb
        )
    else:
        logger.debug("User has no custom instruction; presenting add option")
        await message.answer(
            "У тебе ще немає інструкції «Про мене». Можеш додати її зараз.",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[[
                        InlineKeyboardButton(
                            text="➕ Додати інструкцію",
                            callback_data="add_instruction"
                        )
                    ]]
            )
        )

@router.callback_query(AddInstructionCallback())
async def request_user_instruction(callback: types.CallbackQuery, state: FSMContext):
    logger.info(f"Add instruction requested: user_tg_id={callback.from_user.id}")
    await callback.message.delete()

    your_instruction = "Ось твоя інструкція: \n\n"

    markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="❌ Скасувати",
                callback_data="cancel_instruction"
            )]
        ]
    )

    user = await user_controller.get_user_by_tg_id(callback.from_user.id)
    if user and getattr(user, "custom_instruction", None):
        your_instruction += f"{user.custom_instruction}\n"
        markup.inline_keyboard.append(
            [InlineKeyboardButton(
                text="🗑️ Видалити інструкцію",
                callback_data="delete_instruction"
            )]
        )

        await callback.message.answer(user_instruction_prompt)
        await callback.message.answer(your_instruction, reply_markup=markup)
    else:
        await callback.message.answer(user_instruction_prompt, reply_markup=markup)

    await state.set_state(InstructionState.waiting_for_instruction)


@router.callback_query(EditInstructionCallback())
async def edit_instruction(callback: types.CallbackQuery, state: FSMContext):
    logger.info(f"Edit instruction requested: user_tg_id={callback.from_user.id}")
    await callback.message.delete()

    user = await user_controller.get_user_by_tg_id(callback.from_user.id)

    if not user or not user.custom_instruction:
        await callback.answer("❌ У тебе немає інструкції для редагування.", show_alert=True)
        return

    markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="❌ Скасувати",
                callback_data="cancel_instruction"
            )]
        ]
    )

    await callback.message.answer(user_instruction_prompt, reply_markup=markup)
    await state.set_state(InstructionState.waiting_for_instruction)


@router.callback_query(
    CancelInstructionCallback(),
    InstructionState.waiting_for_instruction
)
async def cancel_instruction(callback: types.CallbackQuery, state: FSMContext):
    logger.info(f"Cancel instruction flow: user_tg_id={callback.from_user.id}")
    await state.clear()
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer("❌ Ми все скасували. Якщо захочеш, можеш спробувати ще раз пізніше.")


@router.callback_query(
    DeleteInstructionCallback(),
    InstructionState.waiting_for_instruction
)
async def delete_instruction(callback: types.CallbackQuery, state: FSMContext):
    logger.info(f"Delete instruction requested: user_tg_id={callback.from_user.id}")
    user = await user_controller.get_user_by_tg_id(callback.from_user.id)

    if user and getattr(user, "custom_instruction", None):
        user.custom_instruction = None
        await user_controller.update_user(user)

        await state.clear()
        await callback.message.edit_reply_markup(reply_markup=None)
        await callback.message.delete()
        await callback.message.answer("🗑️ Ми видалили твою інструкцію.\nP.S. Можеш додати нову в будь-який час 😉")


@router.message(InstructionState.waiting_for_instruction)
async def save_instruction(message: types.Message, state: FSMContext):
    logger.info(f"Save instruction message received: user_tg_id={message.from_user.id}")
    new_instruction = message.text
    user = await user_controller.get_user_by_tg_id(message.from_user.id)

    if not user:
        await message.answer("Користувача не знайдено.")
        await state.clear()
        return

    user.custom_instruction = new_instruction
    await user.save()

    await message.answer("✅ Ура! Твою інструкцію збережено.")
    await state.clear()
