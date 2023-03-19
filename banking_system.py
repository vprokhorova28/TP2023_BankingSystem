from abc import ABCMeta, abstractmethod
import time
import uuid

MONTH = 30
DAY = 24
HOUR = 60
MINUTE = 60

class Bank:
    def __init__(self, name: str, limit: float):
        self.__accounts = {}
        self.__clients = []
        self.name = name
        self.limit = limit

    def get_accounts(self):
        return self.__accounts

    def get_clients(self):
        return self.__clients

class Address:
    def __init__(self, city: str, street: str, house: int, flat: int):
        self.__city = city
        self.__street = street
        self.__house = house
        self.__flat = flat

class Passport:
    def __init__(self, series: str, number: str, issued_by: str, when_issued: str):
        self.__series = series
        self.__number = number
        self.__issued_by = issued_by
        self.__when_issued = when_issued

class Client:
    def __init__(self, bank: Bank, name: str, surname: str):
        self.__bank = bank
        self.__name = ""
        self.__surname = ""
        self.__address = None
        self.__passport = None
        self.is_identified = False

    def add_address(self, address: Address):
        self.__address = address

    def add_passport(self, passport: Passport):
        self.__passport = passport

    def update_status(self):
        if (self.__address != None and self.__passport != None):
            self.is_identified = True

class Builder(metaclass=ABCMeta):
    @abstractmethod
    def add_address(self, city: str, street: str, house: int, flat: int):
        pass

    @abstractmethod
    def add_passport(self, series: str, number: str, issued_by: str, when_issued: str):
        pass

class ClientBuilder(Builder):
    def __init__(self, bank: Bank, name: str, surname: str):
        self.__user = Client(bank, name, surname)

    def add_address(self, city: str, street: str, house: int, flat: int):
        self.__user.add_address(Address(city, street, house, flat))
        self.__user.update_status()

    def add_passport(self, series: str, number: str, issued_by: str, when_issued: str):
        self.__user.add_passport(Passport(series, number, issued_by, when_issued))
        self.__user.update_status()

class Account(metaclass=ABCMeta):
    @abstractmethod
    def __init__(self, bank: Bank, client: Client):
        self.__bank = bank
        self.__client = client
        self.__balance = 0
        self.__id = uuid.uuid4()

    @abstractmethod
    def _update_balance(self, amount: float) -> bool:
        pass

class DebitAccount(Account):
    def __init__(self, bank: Bank, client: Client):
        super().__init__(bank, client)

    def _update_balance(self, amount: float) -> bool:
        if (not (self.__client.is_identified) and amount < 0 and -amount > self.__bank.limit):
            print("Your account has not been identified")
            return False
        if (self.__balance + amount < 0):
            print("Insufficient funds")
            return False
        self.__balance += amount
        return True

class Deposit(Account):
    def __init__(self, bank: Bank, client: Client, period: int):
        super().__init__(bank, client)
        self.__data = time.time() + period * MONTH * DAY * HOUR * MINUTE

    def _update_balance(self, amount: float) -> bool:
        if (self.__data < time.time() and not (self.__client.is_identified) and amount < 0 and -amount > self.__bank.limit):
            print("Your account has not been identified")
            return False
        if (self.__data > time.time() and amount < 0):
            print("It is impossible to withdraw")
            return False
        self.__balance += amount
        return True

class CreditAccount(Account):
    def __init__(self, bank: Bank, client: Client, commission: float, limit: float):
        super().__init__(bank, client)
        self.__commission = commission
        self.limit = limit

    def _update_balance(self, amount: float) -> bool:
        if (not (self.__client.is_identified) and amount < 0 and -amount > self.__bank.limit):
            print("Your account has not been identified")
            return False
        if (self.__balance + amount < -self.limit):
            print("Limit is exceeded")
            return False
        if (self.__balance + amount < 0):
            self.__balance += amount + (self.__balance + amount) * self.__commission
            return False
        self.__balance += amount
        return True

        

class Operation(metaclass=ABCMeta):
    @abstractmethod
    def __init__ (self, bank: Bank, account: str, amount: float):
        self.__bank = bank
        self.__account = account
        self.__amount = amount

    @abstractmethod
    def execute(self):
        pass

class Replenishment(Operation):
    def __init__(self, bank: Bank, account: str, amount: float):
        super().__init__(bank, account, amount)

    def execute(self):
        self.__bank.get_accounts()[self.__account]._update_balance(self.__amount)

class Withdrawal(Operation):
    def __init__(self, bank: Bank, account: str, amount: float):
        super().__init__(bank, account, amount)

    def execute(self):
        self.__bank.get_accounts()[self.__account]._update_balance(-self.__amount)

class Transfer(Operation):
    def __init__(self, bank: Bank, account_from: str, account_to: str, amount: float):
        super().__init__(bank, account_from, amount)
        self.__account_to = account_to

    def execute(self):
        if (self.__bank.get_accounts()[self.__account]._update_balance(-self.__amount)):
            self.__bank.get_accounts()[self.__account_to]._update_balance(self.__amount)
        else:
            print ("Operation failed")

    def cancel(self):
        self.__bank.get_accounts()[self.__account]._update_balance(self.__amount)
        if not(self.__bank.get_accounts()[self.__account_to]._update_balance(-self.__amount)):
            print ("Operation failed")