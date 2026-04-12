// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title TrancheLogic
 * @notice Calculates tranche amounts and validates releases
 */
library TrancheLogic {
    
    struct TrancheConfig {
        uint8 tranche1Percent;  // e.g., 40 for 40%
        uint8 tranche2Percent;  // e.g., 30 for 30%
        uint8 tranche3Percent;  // e.g., 30 for 30%
    }
    
    struct TrancheState {
        uint256 tranche1Amount;
        uint256 tranche2Amount;
        uint256 tranche3Amount;
        bool tranche1Released;
        bool tranche2Released;
        bool tranche3Released;
    }
    
    error InvalidTranchePercentages();
    error TrancheAlreadyReleased(uint8 tranche);
    error InsufficientFunds();
    
    /**
     * @notice Initialize tranches based on total amount
     */
    function initializeTranches(
        uint256 totalAmount,
        TrancheConfig memory config
    ) internal pure returns (TrancheState memory) {
        // Validate percentages sum to 100
        if (config.tranche1Percent + config.tranche2Percent + config.tranche3Percent != 100) {
            revert InvalidTranchePercentages();
        }
        
        TrancheState memory state;
        state.tranche1Amount = (totalAmount * config.tranche1Percent) / 100;
        state.tranche2Amount = (totalAmount * config.tranche2Percent) / 100;
        state.tranche3Amount = totalAmount - state.tranche1Amount - state.tranche2Amount; // Remaining to avoid rounding issues
        
        return state;
    }
    
    /**
     * @notice Calculate amount for specific tranche
     */
    function getTrancheAmount(
        TrancheState memory state,
        uint8 trancheNumber
    ) internal pure returns (uint256) {
        if (trancheNumber == 1) return state.tranche1Amount;
        if (trancheNumber == 2) return state.tranche2Amount;
        if (trancheNumber == 3) return state.tranche3Amount;
        return 0;
    }
    
    /**
     * @notice Check if tranche can be released
     */
    function canReleaseTranche(
        TrancheState memory state,
        uint8 trancheNumber
    ) internal pure returns (bool) {
        if (trancheNumber == 1) return !state.tranche1Released;
        if (trancheNumber == 2) return state.tranche1Released && !state.tranche2Released;
        if (trancheNumber == 3) return state.tranche2Released && !state.tranche3Released;
        return false;
    }
    
    /**
     * @notice Mark tranche as released
     */
    function markTrancheReleased(
        TrancheState storage state,
        uint8 trancheNumber
    ) internal {
        if (trancheNumber == 1) {
            if (state.tranche1Released) revert TrancheAlreadyReleased(1);
            state.tranche1Released = true;
        } else if (trancheNumber == 2) {
            if (state.tranche2Released) revert TrancheAlreadyReleased(2);
            state.tranche2Released = true;
        } else if (trancheNumber == 3) {
            if (state.tranche3Released) revert TrancheAlreadyReleased(3);
            state.tranche3Released = true;
        }
    }
}