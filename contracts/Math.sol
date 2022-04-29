pragma solidity ^0.8.0;

contract Math {

    function sqrt(int256 a) public view returns (int256) {
        int256 c = (a + 1) / 2;
        int256 b = a;
        while (c < b) {
            b = c;
            c = (a / c + c) / 2;
        }
        return b;
    }

    function calcAmountOut(uint amountIn, uint reserveIn, uint reserveOut) public view returns(uint256) {
        uint amountInWithFee = amountIn * 997;
        uint numerator = amountInWithFee * reserveOut;
        uint denominator = reserveIn * 1000 + amountInWithFee;
        return numerator / denominator;
    }

    function calcAmountIn(uint amountOut, uint reserveIn, uint reserveOut) public view returns(uint256) {
        uint numerator = amountOut * reserveIn * 1000;
        uint denominator = (reserveOut - amountOut) * 997;
        return numerator / denominator;
    }

    function calcRevenue(uint attackerAmountIn, uint victimAmountIn, uint attackerAmountOut, uint victimAmountOut, uint reserveIn, uint reserveOut) public view returns(uint256) {
        uint resultingReserveIn = reserveIn + attackerAmountIn + victimAmountIn;
        uint resultingReserveOut = reserveOut - attackerAmountOut - victimAmountOut;
        return calcAmountOut(attackerAmountOut, resultingReserveOut, resultingReserveIn);
    }

    function calcAttackAmountIn(int256 victimAmountIn, int256 victimAmountOut, int256 reserveIn, int256 reserveOut) public view returns (int256) {
        int256 b = victimAmountOut * victimAmountIn + 200602 * victimAmountOut * reserveIn / 100000;
        int256 a = victimAmountOut;
        int256 c = 100301 * victimAmountOut * victimAmountIn * reserveIn / 100000 + 100603 * victimAmountOut * reserveIn * reserveIn / 100000 - 100301 * victimAmountIn * reserveOut * reserveIn / 100000;
        int256 solution = (sqrt(b * b - 4 * a * c) - b) / (2 * a);
        return solution;
    }

    function calcAttackAmountOut(int256 victimAmountIn, int256 victimAmountOut, int256 reserveIn, int256 reserveOut) public view returns (int256) {
        int256 b = 2 * victimAmountIn * reserveOut + 301808 * reserveIn * victimAmountOut / 100000000 - victimAmountIn * victimAmountOut;
        int256 a = victimAmountIn;
        int256 c = victimAmountIn * reserveOut * reserveOut - 100301 * reserveIn * victimAmountOut * reserveOut / 100000 - victimAmountIn * victimAmountOut * reserveOut;
        int256 solution = (b - sqrt(b * b - 4 * a * c))/(2 * a);
        return solution;
    }

}