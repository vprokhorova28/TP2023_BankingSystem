import pickle
from bank_system import *

Sberbank = Bank("Sberbank", 20000, 5000, 5, 3)
Tinkoff = Bank("Tinkoff", 25000, 5000, 5.5, 2)
VTB = Bank("VTB", 10000, 5000, 4.5, 4)
AlfaBank = Bank("AlfaBank", 15000, 7000, 4.5, 4.5)
SovkomBank = Bank("SovkomBank", 20000, 7000, 4, 3)
list_banks = {"Sberbank": Sberbank, "Tinkoff": Tinkoff, "VTB": VTB,
              "AlfaBank": AlfaBank, "SovkomBank": SovkomBank}

with open("src/banks.pickle", "wb") as file:
    pickle.dump(list_banks, file)
    