// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title StateMachine
 * @notice Manages order lifecycle states
 */
library StateMachine {
    
    enum State {
        PENDING_VERIFICATION,  // 0: Contract created, awaiting MSME claim
        OPEN_FOR_FUNDING,      // 1: MSME verified, open to investors
        FUNDED_T1,             // 2: Tranche 1 funded
        DISBURSED_T1,          // 3: Tranche 1 disbursed
        PRODUCTION,            // 4: MSME producing goods
        FUNDED_T2,             // 5: Tranche 2 funded
        DISBURSED_T2,          // 6: Tranche 2 disbursed
        AWAITING_DELIVERY,     // 7: Awaiting delivery confirmation
        DELIVERED,             // 8: Delivery confirmed
        FUNDED_T3,             // 9: Tranche 3 funded
        DISBURSED_T3,          // 10: Tranche 3 disbursed
        PAYMENT_RECEIVED,      // 11: Government paid
        REPAID,                // 12: Investors repaid
        DEFAULTED,             // 13: Order failed
        LIQUIDATED             // 14: Collateral liquidated
    }
    
    error InvalidStateTransition(State from, State to);
    
    /**
     * @notice Check if state transition is valid
     */
    function validateTransition(State from, State to) internal pure {
        bool valid = false;
        
        // Define valid transitions
        if (from == State.PENDING_VERIFICATION && to == State.OPEN_FOR_FUNDING) valid = true;
        else if (from == State.OPEN_FOR_FUNDING && to == State.FUNDED_T1) valid = true;
        else if (from == State.FUNDED_T1 && to == State.DISBURSED_T1) valid = true;
        else if (from == State.DISBURSED_T1 && to == State.PRODUCTION) valid = true;
        else if (from == State.PRODUCTION && to == State.FUNDED_T2) valid = true;
        else if (from == State.FUNDED_T2 && to == State.DISBURSED_T2) valid = true;
        else if (from == State.DISBURSED_T2 && to == State.AWAITING_DELIVERY) valid = true;
        else if (from == State.AWAITING_DELIVERY && to == State.DELIVERED) valid = true;
        else if (from == State.DELIVERED && to == State.FUNDED_T3) valid = true;
        else if (from == State.FUNDED_T3 && to == State.DISBURSED_T3) valid = true;
        else if (from == State.DISBURSED_T3 && to == State.PAYMENT_RECEIVED) valid = true;
        else if (from == State.PAYMENT_RECEIVED && to == State.REPAID) valid = true;
        else if (to == State.DEFAULTED && from >= State.OPEN_FOR_FUNDING && from <= State.AWAITING_DELIVERY) valid = true;
        else if (from == State.DEFAULTED && to == State.LIQUIDATED) valid = true;
        
        if (!valid) revert InvalidStateTransition(from, to);
    }
    
    /**
     * @notice Get tranche number for current state
     */
    function getCurrentTranche(State state) internal pure returns (uint8) {
        if (state <= State.DISBURSED_T1) return 1;
        if (state <= State.DISBURSED_T2) return 2;
        if (state <= State.DISBURSED_T3) return 3;
        return 0;
    }
}