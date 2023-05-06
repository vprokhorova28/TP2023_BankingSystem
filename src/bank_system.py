from abc import ABCMeta, abstractmethod
import time
import uuid
from exceptions import OperationFailed, Unidentified
from globals import MONTH, DAY, HOUR, MINUTE

class Bank:
    def __init__(self, name: str, credit_limit: float, unid_limit: float,
                 deposit_rate: float, commission: float):
        self.__accounts = {}
        self.__clients = {}
        self.name = name
        self.credit_limit = credit_limit
        self.unid_limit = unid_limit
        self.commission = commission
        self.deposit_rate = deposit_rate

    def get_accounts(self) -> dict:
        return self.__accounts

    def get_clients(self) -> dict:
        return self.__clients

class Address:
    def __init__(self, city: str, street: str, house: int, flat: int):
        self.city = city
        self.street = street
        self.house = house
        self.flat = flat

class Passport:
    def __init__(self, series: str, number: str, issued_by: str,
                 when_issued: str):
        self.series = series
        self.number = number
        self.issued_by = issued_by
        self.when_issued = when_issued

class Client:
    def __init__(self, bank: Bank, name: str, surname: str):
        self.bank = bank
        self.name = ""
        self.surname = ""
        self.__address = None
        self.__passport = None
        self.is_identified = False
        self.__password = ""
        self.__accounts = {}
        bank.get_clients()[(name, surname)] = self

    def add_address(self, address: Address):
        self.__address = address
        self.update_status()

    def add_passport(self, passport: Passport):
        self.__passport = passport
        self.update_status()

    def set_password(self, password: str):
        self.__password = password

    def get_password(self) -> str:
        return self.__password
  
    def is_address_set(self) -> bool:
        return self.__address != None
    
    def is_passport_set(self) -> bool:
        return self.__passport != None

    def update_status(self):
        if (self.is_address_set() and self.is_passport_set()):
            self.is_identified = True

    def get_accounts(self) -> dict:
        return self.__accounts

class Account(metaclass=ABCMeta):
    @abstractmethod
    def __init__(self, bank: Bank, client: Client):
        self.bank = bank
        self.client = client
        self.balance = 0
        self.id = str(uuid.uuid4())
        bank.get_accounts()[self.id] = self
        client.get_accounts()[self.id] = self

    @abstractmethod
    def _update_balance(self, amount: float):
        pass

class DebitAccount(Account):
    def __init__(self, bank: Bank, client: Client):
        super().__init__(bank, client)

    def _update_balance(self, amount: float):
        if (not (self.client.is_identified) and amount < 0 and \
            -amount > self.bank.credit_limit):
            raise Unidentified("Ваш аккаунт не идентифицирован")
        if (self.balance + amount < 0):
            raise OperationFailed("Недостаточно средств для снятия")
        self.balance += amount

class Deposit(Account):
    def __init__(self, bank: Bank, client: Client):
        super().__init__(bank, client)
        self.period = 0
        self.start_amount = 0
        self.active = False
        self.end_time = 0

    def _update_balance(self, amount: float):
        self.check_balance()
        if (not (self.active) and not (self.client.is_identified) and \
            amount < 0 and -amount > self.bank.credit_limit):
            raise Unidentified("Ваш аккаунт не идентифицирован")
        if (self.active and amount < 0):
            raise OperationFailed("Снятие с депозитного счета невозможно")
        self.balance += amount 
    
    def start(self, period: int):
        self.period = period
        self.start_amount = self.balance
        self.end_time = time.time() + self.period * MONTH * DAY * HOUR * MINUTE
        self.active = True

    def check_balance(self):
        if (self.end_time < time.time() and self.active):
            self.balance += self.start_amount * \
                (((self.bank.deposit_rate / 12) * self.period) / 100)
            self.active = False

class CreditAccount(Account):
    def __init__(self, bank: Bank, client: Client):
        super().__init__(bank, client)

    def _update_balance(self, amount: float):
        if (not (self.client.is_identified) and amount < 0 and \
            -amount > self.bank.unid_limit):
            raise Unidentified("Ваш аккаунт не идентифицирован")
        if (self.balance + amount < -self.bank.credit_limit):
            raise OperationFailed("Превышен допустимый лимит")
        if (self.balance + amount < 0 and amount < 0):
            self.balance += amount + (self.balance + amount) * \
                (self.bank.commission / 100)
        else:
            self.balance += amount

class Operation(metaclass=ABCMeta):
    @abstractmethod
    def __init__ (self, bank: Bank, account: str, amount: float):
        self.bank= bank
        self.account = account
        self.amount = amount

    @abstractmethod
    def execute(self):
        pass

class Replenishment(Operation):
    def __init__(self, bank: Bank, account: str, amount: float):
        super().__init__(bank, account, amount)

    def execute(self):
        try:
            self.bank.get_accounts()[self.account]._update_balance(self.amount)
        except (OperationFailed, Unidentified):
            raise

class Withdrawal(Operation):
    def __init__(self, bank: Bank, account: str, amount: float):
        super().__init__(bank, account, amount)

    def execute(self):
        try:
            self.bank.get_accounts()[self.account]._update_balance(-self.amount)
        except (OperationFailed, Unidentified):
            raise

class Transfer(Operation):
    def __init__(self, bank_from: Bank, bank_to: Bank, account_from: str,
                 account_to: str, amount: float):
        super().__init__(bank_from, account_from, amount)
        self.account_to = account_to
        self.bank_to = bank_to

    def execute(self):
        if self.amount < 0:
            raise OperationFailed("Сумма перевода не может быть отрицательной")
        try:
            self.bank.get_accounts()[self.account]._update_balance(-self.amount)
        except (OperationFailed, Unidentified):
            raise
        else:
            self.bank_to.get_accounts()[self.account_to]._update_balance(
                self.amount)

    def cancel(self):
        try:
            self.bank.get_accounts()[self.account]._update_balance(self.amount)
            self.bank_to.get_accounts()[self.account_to]._update_balance(
                -self.amount)
        except (OperationFailed, Unidentified):
            raise