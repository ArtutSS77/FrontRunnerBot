from calculations import *

amountIn = 100
reserveIn = 1000
reserveOut = 2000
amountOut = 100

print(calc_amount_out(amountIn, reserveIn, reserveOut))
print(calc_amount_in(amountOut, reserveIn, reserveOut))
print(calc_revenue(amountIn, amountIn, amountIn, amountIn, reserveIn, reserveOut))
print(calc_attack_amount_in(100, 150, 1000, 2000))
print(calc_attack_amount_out(150, 181, 100000000000000000000, 900000000000000000000000000000000))