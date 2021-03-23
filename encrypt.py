import string
from random import randint

def encrypt_pass(password):
    characters = character_list()
    encrypt = ""
    n = 2
    # Generate a new password of len 60
    while len(encrypt) != 60 :
        # Encrypt a random value
        if len(encrypt) < 60 - len(password):
            encrypt += characters[randint(0, len(characters) - 1)]
        else:
            # Encrypting the password
            for p in password:
                for c in range(0, len(characters)):
                    if p == characters[c]:
                        if c + n >= len(characters):
                            index = len(characters) * int((c + n) / len(characters))
                            encrypt += characters[(c + n) - index]
                            break
                        else:
                            encrypt += characters[c + n]
                            break
                n += 2

    return encrypt


# Decrypting algorithm
def decrypt_pass(encrypt, p):
    characters = character_list()
    decrypt = ""
    n = 2
    for e in range(60 - p, 60):
        for c in range(0, len(characters)):
            if encrypt[e] == characters[c]:
                if c - n < 0:
                    index = len(characters) + (c - n)
                    decrypt += characters[index]
                    break
                else:
                    decrypt += characters[c - n]
                    break
        n += 2

    return decrypt


# Generate a list of all caracters
def character_list():

    # Generating a list of numbers
    numbers = ""
    for i in range(0, 10):
        numbers += str(i)
    return string.ascii_lowercase + string.ascii_uppercase +"#@" + numbers