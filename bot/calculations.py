import math


def calc_amount_out(amount_in, reserve_in, reserve_out):
    amount_in_with_fee = amount_in * 997
    numerator = amount_in_with_fee * reserve_out
    denominator = reserve_in * 1000 + amount_in_with_fee
    return int(numerator / denominator)


def calc_amount_in(amount_out, reserve_in, reserve_out):
    return int((amount_out * reserve_in * 1000) / ((reserve_out - amount_out) * 997))


def calc_revenue(attacker_amount_in, victim_amount_in, attacker_amount_out, victim_amount_out, reserve_in, reserve_out):
    resulting_reserve_in = reserve_in + attacker_amount_in + victim_amount_in
    resulting_reserve_out = reserve_out - attacker_amount_out - victim_amount_out
    print(attacker_amount_in, victim_amount_in, attacker_amount_out, victim_amount_out, reserve_in, reserve_out)
    print(resulting_reserve_in)
    print(resulting_reserve_out)
    return int(calc_amount_out(attacker_amount_out, resulting_reserve_out, resulting_reserve_in))


# ((reserve_out - attacker_amount_in * 0.997 * reserve_out / (reserve_in + attacker_amount_in * 0.997)) *
# victim_amount_in * 0.997) / (reserve_in + victim_amount_in * 0.997 + attacker_amount_in * 0.997)

# (1.00301 * victim_amount_in * reserve_out * reserve_in) / (victim_amount_in * attacker_amount_in + 1.00301 *
# victim_amount_in * reserve_in + attacker_amount_in * attacker_amount_in + 2.00602 * attacker_amount_in * reserve_in
# + 1.0063 * reserve_in * reserve_in)
def calc_attack_amount_in(victim_amount_in, victim_amount_out, reserve_in, reserve_out):
    attacker_amount_in = (-(victim_amount_out * victim_amount_in + 2.00602 * victim_amount_out * reserve_in) + math.sqrt(math.pow(victim_amount_out*victim_amount_in + 2.00602 * victim_amount_out * reserve_in, 2) - 4 * victim_amount_out * (1.00301 * victim_amount_out * victim_amount_in * reserve_in + 1.00603 * victim_amount_out * reserve_in * reserve_in - 1.00301 * victim_amount_in * reserve_out * reserve_in))) / (2 * victim_amount_out)
    return int(attacker_amount_in)


def calc_attack_amount_out(victim_amount_in, victim_amount_out, reserve_in, reserve_out):
    attacker_amount_out = ((-victim_amount_in * victim_amount_out + 2 * victim_amount_in * reserve_out + 0.00301808 * reserve_in * victim_amount_out) - math.sqrt(math.pow(victim_amount_in * victim_amount_out - 2 * victim_amount_in * reserve_out - 0.00301808 * reserve_in * victim_amount_out, 2) - 4 * victim_amount_in * (victim_amount_in * reserve_out * reserve_out - 1.00301 * reserve_in * victim_amount_out * reserve_out - victim_amount_in * victim_amount_out * reserve_out))) / (2 * victim_amount_in)
    return int(attacker_amount_out)
