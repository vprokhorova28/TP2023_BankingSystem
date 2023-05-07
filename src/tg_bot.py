from bank_system import Client, Address, Passport, DebitAccount, Deposit, \
    CreditAccount, Transfer
from exceptions import OperationFailed, Unidentified
import time
import bot_config
import nest_asyncio
from aiogram import Bot
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, Message, \
    ReplyKeyboardRemove
from aiogram.dispatcher import Dispatcher, FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
import pickle

nest_asyncio.apply()

with open("src/token.txt", "r") as f:
    TOKEN = f.read()

bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


def load_list_bank():
    with open("src/banks.pickle", "rb") as file:
        return pickle.load(file)


def save_data(list_bank):
    with open("src/banks.pickle", "wb") as file:
        pickle.dump(list_bank, file)


list_banks = load_list_bank()

button_banks = KeyboardButton('Выбрать банк')
start_markup = ReplyKeyboardMarkup(resize_keyboard=True).add(button_banks)


@dp.message_handler(commands=['start'])
async def process_start_command(msg: Message):
    await bot.send_message(msg.from_user.id, bot_config.START_MSG, reply_markup=start_markup)


@dp.message_handler(commands=['help'])
async def process_help_command(msg: Message):
    await bot.send_message(msg.from_user.id, bot_config.HELP_MSG)


class Authorization(StatesGroup):
    bank = State()
    name = State()
    surname = State()
    password = State()


class Registration(StatesGroup):
    name = State()
    surname = State()
    password = State()
    city = State()
    street = State()
    house = State()
    flat = State()
    series = State()
    number = State()
    issued_by = State()
    when_issued = State()


bank_choose_markup = ReplyKeyboardMarkup(resize_keyboard=True)
for bank in list_banks.values():
    bank_choose_markup.insert(KeyboardButton(bank.name))


@dp.message_handler(Text("Выбрать банк"))
async def choose_bank(msg: Message):
    await bot.send_message(msg.from_user.id, bot_config.CHOOSE_BANK,
                           reply_markup=bank_choose_markup)
    await Authorization.bank.set()


action_choose_markup = ReplyKeyboardMarkup(resize_keyboard=True)
action_choose_markup.insert(KeyboardButton("Открыть счет"))
action_choose_markup.insert(KeyboardButton("Мои счета"))
action_choose_markup.insert(KeyboardButton("Перевод"))

personal_account = ReplyKeyboardMarkup(resize_keyboard=True)
personal_account.add(KeyboardButton("Вход"))
personal_account.add(KeyboardButton("Регистрация"))


@dp.message_handler(Text([bank for bank in list_banks.keys()]),
                    state=Authorization.bank)
async def bank_selected(msg: Message, state: FSMContext):
    await state.update_data(bank=msg.text)
    await bot.send_message(msg.from_user.id, bot_config.SIGNUP_OR_LOGIN,
                           reply_markup=personal_account)


@dp.message_handler(Text("Вход"), state=Authorization.bank)
async def login(msg: Message):
    await bot.send_message(msg.from_user.id, bot_config.ENTER_NAME,
                           reply_markup=ReplyKeyboardRemove())
    await Authorization.name.set()


@dp.message_handler(state=Authorization.name)
async def process_name(msg: Message, state: FSMContext):
    await state.update_data(name=msg.text)
    await bot.send_message(msg.from_user.id, bot_config.ENTER_SURNAME)
    await Authorization.surname.set()


@dp.message_handler(state=Authorization.surname)
async def process_surname(msg: Message, state: FSMContext):
    await state.update_data(surname=msg.text)
    await bot.send_message(msg.from_user.id, bot_config.ENTER_PASSWORD)
    await Authorization.password.set()


@dp.message_handler(state=Authorization.password)
async def process_password(msg: Message, state: FSMContext):
    await state.update_data(password=msg.text)
    data = await state.get_data()
    if (data['name'], data['surname']) in \
            list_banks[data['bank']].get_clients() and \
            data['password'] == list_banks[data['bank']].get_clients()[
        (data['name'], data['surname'])].get_password():
        await bot.send_message(msg.from_user.id, bot_config.AUTHORIZATION_SUCCEEDED,
                               reply_markup=action_choose_markup)
        await state.reset_state(with_data=False)
    else:
        await bot.send_message(msg.from_user.id, bot_config.AUTHORIZATION_FAILED,
                               reply_markup=personal_account)
        await Authorization.bank.set()


@dp.message_handler(Text("Регистрация"), state=Authorization.bank)
async def registration(msg: Message):
    await bot.send_message(msg.from_user.id, bot_config.ENTER_NAME,
                           reply_markup=ReplyKeyboardRemove())
    await Registration.name.set()


@dp.message_handler(state=Registration.name)
async def registration_name(msg: Message, state: FSMContext):
    await state.update_data(name=msg.text)
    await bot.send_message(msg.from_user.id, bot_config.ENTER_SURNAME)
    await Registration.surname.set()


@dp.message_handler(state=Registration.surname)
async def registration_surname(msg: Message, state: FSMContext):
    await state.update_data(surname=msg.text)
    data = await state.get_data()
    Client(list_banks[data['bank']], data['name'], data['surname'])
    await bot.send_message(msg.from_user.id, bot_config.SET_PASSWORD)
    await Registration.password.set()


address_password_markup = ReplyKeyboardMarkup(resize_keyboard=True)
address_password_markup.add(KeyboardButton("Добавить адрес"))
address_password_markup.add(KeyboardButton("Добавить паспорт"))
address_password_markup.add(KeyboardButton("Закончить регистрацию"))


@dp.message_handler(state=Registration.password)
async def registration_password(msg: Message, state: FSMContext):
    await state.update_data(password=msg.text)
    data = await state.get_data()
    list_banks[data['bank']].get_clients()[(
        data['name'], data['surname'])].set_password(msg.text)
    save_data(list_banks)
    await bot.send_message(msg.from_user.id, bot_config.VERIFY_IDENTITY,
                           reply_markup=address_password_markup)
    await state.reset_state(with_data=False)


@dp.message_handler(Text("Добавить адрес"))
async def registration_address(msg: Message, state: FSMContext):
    data = await state.get_data()
    if list_banks[data['bank']].get_clients()[
        (data['name'], data['surname'])].is_address_set():
        await bot.send_message(msg.from_user.id, bot_config.ADDRESS_ALREADY_ADDED)
    else:
        await bot.send_message(msg.from_user.id, bot_config.ENTER_CITY,
                               reply_markup=ReplyKeyboardRemove())
        await Registration.city.set()


@dp.message_handler(state=Registration.city)
async def registration_city(msg: Message, state: FSMContext):
    await state.update_data(city=msg.text)
    await bot.send_message(msg.from_user.id, bot_config.ENTER_STREET)
    await Registration.street.set()


@dp.message_handler(state=Registration.street)
async def registration_street(msg: Message, state: FSMContext):
    await state.update_data(street=msg.text)
    await bot.send_message(msg.from_user.id, bot_config.ENTER_HOUSE)
    await Registration.house.set()


@dp.message_handler(state=Registration.house)
async def registration_house(msg: Message, state: FSMContext):
    await state.update_data(house=msg.text)
    await bot.send_message(msg.from_user.id, bot_config.ENTER_FLAT)
    await Registration.flat.set()


@dp.message_handler(state=Registration.flat)
async def registration_flat(msg: Message, state: FSMContext):
    await state.update_data(flat=msg.text)
    data = await state.get_data()
    list_banks[data['bank']].get_clients()[
        (data['name'], data['surname'])].add_address(
        Address(data['city'], data['street'], data['house'], data['flat']))
    save_data(list_banks)
    if list_banks[data['bank']].get_clients()[
        (data['name'], data['surname'])].is_identified:
        await bot.send_message(msg.from_user.id,
                               bot_config.ADDRESS_ADDED + bot_config.STATUS_IDENTIFIED,
                               reply_markup=action_choose_markup)
    else:
        await bot.send_message(msg.from_user.id, bot_config.ADDRESS_ADDED,
                               reply_markup=address_password_markup)
    await state.reset_state(with_data=False)


@dp.message_handler(Text("Добавить паспорт"))
async def registration_passport(msg: Message, state: FSMContext):
    data = await state.get_data()
    if list_banks[data['bank']].get_clients()[
        (data['name'], data['surname'])].is_passport_set():
        await bot.send_message(msg.from_user.id, bot_config.PASSPORT_ALREADY_ADDED)
    else:
        await bot.send_message(msg.from_user.id, bot_config.ENTER_PASSPORT_SERIES,
                               reply_markup=ReplyKeyboardRemove())
        await Registration.series.set()


@dp.message_handler(state=Registration.series)
async def registration_series(msg: Message, state: FSMContext):
    await state.update_data(series=msg.text)
    await bot.send_message(msg.from_user.id, bot_config.ENTER_PASSPORT_NUMBER)
    await Registration.number.set()


@dp.message_handler(state=Registration.number)
async def registration_number(msg: Message, state: FSMContext):
    await state.update_data(number=msg.text)
    await bot.send_message(msg.from_user.id, bot_config.PASSPORT_ISSUED_BY)
    await Registration.issued_by.set()


@dp.message_handler(state=Registration.issued_by)
async def registration_issued_by(msg: Message, state: FSMContext):
    await state.update_data(issued_by=msg.text)
    await bot.send_message(msg.from_user.id, bot_config.WHEN_PASSPORT_ISSUED)
    await Registration.when_issued.set()


@dp.message_handler(state=Registration.when_issued)
async def registration_when_issued(msg: Message, state: FSMContext):
    await state.update_data(when_issued=msg.text)
    data = await state.get_data()
    list_banks[data['bank']].get_clients()[
        (data['name'], data['surname'])].add_passport(
        Passport(data['series'], data['number'], data['issued_by'],
                 data['when_issued']))
    save_data(list_banks)
    if list_banks[data['bank']].get_clients()[
        (data['name'], data['surname'])].is_identified:
        await bot.send_message(msg.from_user.id,
                               bot_config.PASSPORT_ADDED + bot_config.STATUS_IDENTIFIED,
                               reply_markup=action_choose_markup)
    else:
        await bot.send_message(msg.from_user.id, bot_config.PASSPORT_ADDED,
                               reply_markup=address_password_markup)
    await state.reset_state(with_data=False)


@dp.message_handler(Text("Закончить регистрацию"))
async def registration_end(msg: Message, state: FSMContext):
    await bot.send_message(msg.from_user.id, bot_config.CHOOSE_ACTION,
                           reply_markup=action_choose_markup)


account_selection_markup = ReplyKeyboardMarkup(resize_keyboard=True)
account_selection_markup.add(KeyboardButton("Дебетовый счет"))
account_selection_markup.add(KeyboardButton("Депозит"))
account_selection_markup.add(KeyboardButton("Кредитный счет"))
account_selection_markup.add(KeyboardButton("Назад"))


@dp.message_handler(Text("Открыть счет"))
async def open_account(msg: Message, state: FSMContext):
    await bot.send_message(msg.from_user.id, bot_config.CHOOSE_ACCOUNT_TYPE,
                           reply_markup=account_selection_markup)


replenishment_markup = ReplyKeyboardMarkup(resize_keyboard=True)
replenishment_markup.add(KeyboardButton("Пополнить"))
replenishment_markup.add(KeyboardButton("Назад"))


@dp.message_handler(Text("Дебетовый счет"))
async def open_debit_account(msg: Message, state: FSMContext):
    data = await state.get_data()
    account = DebitAccount(list_banks[data['bank']],
                           list_banks[data['bank']].get_clients()[
                               (data['name'], data['surname'])])
    save_data(list_banks)
    await bot.send_message(msg.from_user.id,
                           bot_config.DEBIT_ACCOUNT_OPENED + f'{account.id}',
                           reply_markup=action_choose_markup)
    await state.update_data(account_to=account.id)
    await bot.send_message(msg.from_user.id, bot_config.REPLENISH_INFO,
                           reply_markup=replenishment_markup)


@dp.message_handler(Text("Депозит"))
async def open_deposit(msg: Message, state: FSMContext):
    data = await state.get_data()
    account = Deposit(list_banks[data['bank']],
                      list_banks[data['bank']].get_clients()[
                          (data['name'], data['surname'])])
    save_data(list_banks)
    await bot.send_message(msg.from_user.id,
                           bot_config.DEBIT_ACCOUNT_OPENED + f'{account.id}',
                           reply_markup=action_choose_markup)
    await state.update_data(account_to=account.id)
    await bot.send_message(msg.from_user.id, bot_config.REPLENISH_INFO,
                           reply_markup=replenishment_markup)


@dp.message_handler(Text("Кредитный счет"))
async def open_credit_account(msg: Message, state: FSMContext):
    data = await state.get_data()
    account = CreditAccount(list_banks[data['bank']],
                            list_banks[data['bank']].get_clients()[
                                (data['name'], data['surname'])])
    save_data(list_banks)
    await bot.send_message(msg.from_user.id,
                           bot_config.DEBIT_ACCOUNT_OPENED + f'{account.id}'
                           f'\nкредитный лимит:\n{account.bank.credit_limit} '
                           f'рублей\nкомиссия при минусе:\n'
                           f'{account.bank.commission}%',
                           reply_markup=ReplyKeyboardRemove())
    await state.update_data(account_to=account.id)
    await bot.send_message(msg.from_user.id, bot_config.REPLENISH_INFO,
                           reply_markup=replenishment_markup)


@dp.message_handler(Text("Назад"))
async def open_back_to_menu(msg: Message, state: FSMContext):
    await bot.send_message(msg.from_user.id, bot_config.CHOOSE_ACTION,
                           reply_markup=action_choose_markup)


class ReplenishmentStates(StatesGroup):
    account_from = State()
    amount = State()


@dp.message_handler(Text("Пополнить"))
async def replenishment(msg: Message, state: FSMContext):
    await bot.send_message(msg.from_user.id, bot_config.ENTER_ACCOUNT_FROM_ID,
                           reply_markup=ReplyKeyboardRemove())
    await ReplenishmentStates.account_from.set()


@dp.message_handler(state=ReplenishmentStates.account_from)
async def replenishment_account_from(msg: Message, state: FSMContext):
    data = await state.get_data()
    if msg.text not in list_banks[data['bank']].get_clients()[
        (data['name'], data['surname'])].get_accounts().keys():
        await bot.send_message(msg.from_user.id, bot_config.NO_SUCH_ID,
                               reply_markup=replenishment_markup)
        await state.reset_state(with_data=False)
    else:
        await state.update_data(account_from=msg.text)
        await bot.send_message(msg.from_user.id, bot_config.ENTER_SUM)
        await ReplenishmentStates.amount.set()


class DepositStates(StatesGroup):
    period = State()


@dp.message_handler(state=ReplenishmentStates.amount)
async def replenishment_amount(msg: Message, state: FSMContext):
    data = await state.get_data()
    transfer = Transfer(list_banks[data['bank']],
                        list_banks[data['bank']], data['account_from'],
                        data['account_to'], int(msg.text))
    try:
        transfer.execute()
    except OperationFailed as error:
        await bot.send_message(msg.from_user.id, error,
                               reply_markup=replenishment_markup)
        await state.reset_state(with_data=False)
    except Unidentified:
        pass
    else:
        save_data(list_banks)
        account = list_banks[data['bank']].get_clients()[
            (data['name'], data['surname'])].get_accounts()[data["account_to"]]
        await bot.send_message(msg.from_user.id, bot_config.OPERATION_SUCCEEDED,
                               reply_markup=action_choose_markup)
        await state.reset_state(with_data=False)
        if isinstance(account, Deposit):
            await bot.send_message(msg.from_user.id, bot_config.DEPOSIT_RATE +
                                   f'{list_banks[data["bank"]].deposit_rate}%' +
                                   bot_config.ENTER_MONTH_NUMBER,
                                   reply_markup=ReplyKeyboardRemove())
            await DepositStates.period.set()


@dp.message_handler(state=DepositStates.period)
async def deposit_period(msg: Message, state: FSMContext):
    data = await state.get_data()
    account = list_banks[data['bank']].get_clients()[
        (data['name'], data['surname'])].get_accounts()[data["account_to"]]
    account.start(int(msg.text))
    await bot.send_message(msg.from_user.id,
                           bot_config.DEPOSIT_OPENED + f'{time.ctime(account.end_time)}',
                           reply_markup=action_choose_markup)
    await state.reset_state(with_data=False)


@dp.message_handler(Text("Мои счета"))
async def my_accounts(msg: Message, state: FSMContext):
    data = await state.get_data()
    accounts = 'Активные счета:'
    num = 0
    for account in list_banks[data['bank']].get_clients()[
        (data['name'], data['surname'])].get_accounts().values():
        num += 1
        if isinstance(account, DebitAccount):
            accounts += f'\n\n{num}. (дебетовый) {account.id}\nбаланс: ' \
                        f'{account.balance} рублей'
        if isinstance(account, Deposit):
            account.check_balance()
            accounts += f'\n\n{num}. (депозит) {account.id}\nбаланс: ' \
                        f'{account.balance} рублей\nставка: {account.bank.deposit_rate}%'
            if account.active:
                accounts += f'\nконец срока: {time.ctime(account.end_time)}'
        if isinstance(account, CreditAccount):
            accounts += f'\n\n{num}. (кредитный) {account.id}\nбаланс: ' \
                        f'{account.balance} рублей'
    await bot.send_message(msg.from_user.id, accounts)


class TransferStates(StatesGroup):
    account_from = State()
    account_to = State()
    amount = State()


@dp.message_handler(Text("Перевод"))
async def my_accounts(msg: Message, state: FSMContext):
    await bot.send_message(msg.from_user.id, bot_config.ENTER_ACCOUNT_FROM_ID,
                           reply_markup=ReplyKeyboardRemove())
    await TransferStates.account_from.set()


@dp.message_handler(state=TransferStates.account_from)
async def transfer_account_from(msg: Message, state: FSMContext):
    data = await state.get_data()
    if msg.text not in list_banks[data['bank']].get_clients()[
        (data['name'], data['surname'])].get_accounts().keys():
        await bot.send_message(msg.from_user.id, bot_config.NO_SUCH_ID,
                               reply_markup=action_choose_markup)
        await state.reset_state(with_data=False)
    else:
        await state.update_data(account_from=msg.text)
        await bot.send_message(msg.from_user.id, bot_config.ENTER_ACCOUNT_TO_ID)
        await TransferStates.account_to.set()


@dp.message_handler(state=TransferStates.account_to)
async def transfer_account_to(msg: Message, state: FSMContext):
    is_existing = False
    for bank in list_banks.values():
        if msg.text in bank.get_accounts().keys():
            await state.update_data(bank_to=bank.name)
            is_existing = True
    if not is_existing:
        await bot.send_message(msg.from_user.id, bot_config.NO_SUCH_ID,
                               reply_markup=action_choose_markup)
        await state.reset_state(with_data=False)
    else:
        await state.update_data(account_to=msg.text)
        await bot.send_message(msg.from_user.id, bot_config.ENTER_SUM)
        await TransferStates.amount.set()


@dp.message_handler(state=TransferStates.amount)
async def transfer_amount(msg: Message, state: FSMContext):
    data = await state.get_data()
    transfer = Transfer(list_banks[data['bank']],
                        list_banks[data['bank_to']], data['account_from'],
                        data['account_to'], int(msg.text))
    try:
        transfer.execute()
    except OperationFailed as error:
        await bot.send_message(msg.from_user.id, error,
                               reply_markup=action_choose_markup)
        await state.reset_state(with_data=False)
    except Unidentified as error:
        await bot.send_message(msg.from_user.id,
                               str(error) + bot_config.ENTER_MISSING_ID_DATA,
                               reply_markup=address_password_markup)
        await state.reset_state(with_data=False)
    else:
        save_data(list_banks)
        await bot.send_message(msg.from_user.id, bot_config.OPERATION_SUCCEEDED,
                               reply_markup=action_choose_markup)
        await state.reset_state(with_data=False)
