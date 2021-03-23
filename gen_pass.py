from random import randint


# Generate a 4 digit number pass
def credit_pass():
    password = ""
    while len(password) < 4:
        password += str(randint(0,9))
    return password


# Generate a card number
def card_number():
    card = [4]
    while len(card) != 16:
        card.append(randint(0,9))
        if len(card) == 16:
            if luhn(card) == True:
                card = ''.join([str(c) for c in card])
                return card
            else:
                card = [4]


# Check the valid of a credit card by the algorithm Luhn
def luhn(card):
    # Keep thee last digit
    last_digit = card[-1]

    #Copy the card variable
    copy_card = card.copy()
    # Remove it
    copy_card.pop()

    # Reverse card
    copy_card = card[::-1]
    # Multiply odd position by 2 and remove 9 if greater than 9
    for i in range(0, len(copy_card)):
        if (i+1) % 2 != 0:
            copy_card[i] = copy_card[i] * 2
        if copy_card[i] > 9:
            copy_card[i] = copy_card[i] - 9
    # sum all the numbers
    sum_ = sum(copy_card)
    # Check the last digit with mod 10 of the sum
    if last_digit == (sum_ % 10):
        # Return True
        return True
    # Return false and generate another credit number
    return False


# Generate the back code of the credit card
def cc_code():
    code = ""
    while len(code) < 3:
        code += str(randint(0,9))
    return code


