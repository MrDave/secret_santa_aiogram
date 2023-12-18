import asyncio

from aiogram import Router, F
from aiogram.filters import StateFilter, CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state, State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from santa_bot.bot.keyboards import confirm_bt
from santa_bot.bot.LEXICON import *

from santa_bot.models import Game, Player

storage = MemoryStorage()
router = Router()


class FSMUserForm(StatesGroup):
    user_name = State()
    email = State()
    wishlist = State()
    check_data = State()
    game = State()


@router.message(Command(commands='cancel'), StateFilter(default_state))
async def process_cancel_command(message: Message):
    await message.answer(
        text='Отменять нечего. Вы вне машины состояний\n\n'
    )
    await message.answer(text="Нажми /start для начала работы")


@router.message(Command(commands='cancel'), ~StateFilter(default_state))
async def process_cancel_command_state(message: Message, state: FSMContext):
    await message.answer(
        text='Вы вышли из машины состояний\n\n'
    )
    await state.clear()
    await message.answer(text="Нажми /start для начала работы")


@router.message(Command(commands=['user']), StateFilter(default_state))
async def start_user(message: Message, state: FSMContext):
    try:
        game_id = int(message.text.split(" ")[-1])
    except ValueError as e:
        await message.answer("неверный аргумент команды")
        raise e

    try:
        game = Game.objects.get(id=game_id)
        await state.update_data(game=game)
    except Game.DoesNotExist:
        await message.answer("Нет игры с таким ID")

    text_message = LEXICON['game'].format(game.name, game.start_date, game.end_date, game.description)
    await message.answer(text=text_message)
    await asyncio.sleep(1)
    await message.answer(text=LEXICON['user_name'])
    await state.set_state(FSMUserForm.user_name)


@router.message(StateFilter(FSMUserForm.user_name))
async def get_description_group(message: Message, state: FSMContext):
    await state.update_data(user_name=message.text)
    message_text = LEXICON['email']
    await message.answer(text=message_text)
    await state.set_state(FSMUserForm.email)


@router.message(StateFilter(FSMUserForm.email))
async def get_description_group(message: Message, state: FSMContext):
    await state.update_data(email=message.text)
    message_text = LEXICON['wishlist']
    await message.answer(text=message_text)
    await state.set_state(FSMUserForm.wishlist)


@router.message(StateFilter(FSMUserForm.wishlist))
async def get_description_group(message: Message, state: FSMContext):
    await state.update_data(wishlist=message.text)
    answer = await state.get_data()
    message_text = LEXICON['check_data'].format(answer['user_name'], answer['email'], answer['wishlist'])
    await message.answer(text=message_text, reply_markup=confirm_bt())

    await state.set_state(FSMUserForm.check_data)


@router.callback_query(StateFilter(FSMUserForm.check_data), F.data.in_([LEXICON['ok'], LEXICON['mistake']]))
async def get_description_group(callback: CallbackQuery, state: FSMContext):
    if callback.data == LEXICON['ok']:
        answer = await state.get_data()
        game = answer['game']
        message_text = LEXICON['in_game'].format(game.end_date)
        participation = Player.objects.create(
            telegram_id=callback.from_user.id,
            game=game,
            name=answer['user_name'],
            email=answer['email'],
            wishlist=answer['wishlist']
        )
        await callback.message.answer(text=message_text)
        await callback.answer()

    elif callback.data == LEXICON['mistake']:
        message_text = LEXICON['not_in_game']
        await callback.message.answer(text=message_text)
        await callback.answer()
