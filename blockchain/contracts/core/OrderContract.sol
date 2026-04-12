// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import "@openzeppelin/contracts/utils/Pausable.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "../libraries/StateMachine.sol";
import "../libraries/TrancheLogic.sol";

/**
 * @title OrderContract
 * @notice Individual contract for each GeM order
 */
contract OrderContract is ReentrancyGuard, Pausable, Ownable {
    using StateMachine for StateMachine.State;
    using TrancheLogic for TrancheLogic.TrancheState;
    
    // ============================================
    // STATE VARIABLES
    // ============================================
    
    string public gemOrderId;
    uint256 public orderAmount;
    uint256 public deliveryDeadline;
    address public msmeAddress;
    string public gstnNumber;
    
    StateMachine.State public currentState;
    TrancheLogic.TrancheState public trancheState;
    
    mapping(address => uint256) public investments;  // investor => amount
    address[] public investors;
    uint256 public totalFunded;
    
    uint256 public interestRateBps;  // Basis points (e.g., 1000 = 10%)
    uint256 public platformFeeBps;   // Basis points (e.g., 150 = 1.5%)
    
    address public factoryAddress;
    address public oracleAddress;
    
    // ============================================
    // EVENTS
    // ============================================
    
    event StateChanged(StateMachine.State oldState, StateMachine.State newState);
    event MSMEClaimed(address indexed msme, string gstn);
    event InvestmentReceived(address indexed investor, uint256 amount);
    event TrancheReleased(uint8 indexed trancheNumber, uint256 amount);
    event DeliveryConfirmed(bytes32 invoiceHash, uint256 timestamp);
    event PaymentReceived(uint256 amount, string paymentRef);
    event InvestorRepaid(address indexed investor, uint256 principal, uint256 interest);
    
    // ============================================
    // ERRORS
    // ============================================
    
    error OnlyOracle();
    error OnlyMSME();
    error InvalidState();
    error OrderAlreadyClaimed();
    error InvestmentTooLow();
    error DeadlinePassed();
    
    // ============================================
    // MODIFIERS
    // ============================================
    
    modifier onlyOracle() {
        if (msg.sender != oracleAddress) revert OnlyOracle();
        _;
    }
    
    modifier onlyMSME() {
        if (msg.sender != msmeAddress) revert OnlyMSME();
        _;
    }
    
    modifier inState(StateMachine.State _state) {
        if (currentState != _state) revert InvalidState();
        _;
    }
    
    // ============================================
    // CONSTRUCTOR
    // ============================================
    
    constructor(
        string memory _gemOrderId,
        uint256 _orderAmount,
        uint256 _deliveryDeadline,
        address _oracle,
        uint256 _interestRateBps,
        uint256 _platformFeeBps
    ) Ownable(msg.sender) {
        gemOrderId = _gemOrderId;
        orderAmount = _orderAmount;
        deliveryDeadline = _deliveryDeadline;
        oracleAddress = _oracle;
        factoryAddress = msg.sender;
        interestRateBps = _interestRateBps;
        platformFeeBps = _platformFeeBps;
        
        currentState = StateMachine.State.PENDING_VERIFICATION;
        
        // Initialize tranches (40%, 30%, 30%)
        TrancheLogic.TrancheConfig memory config = TrancheLogic.TrancheConfig({
            tranche1Percent: 40,
            tranche2Percent: 30,
            tranche3Percent: 30
        });
        
        trancheState = TrancheLogic.initializeTranches(_orderAmount, config);
    }
    
    // ============================================
    // MSME FUNCTIONS
    // ============================================
    
    /**
     * @notice MSME claims ownership of this order
     * @param _gstn GSTN number for verification
     */
    function claimOrder(string memory _gstn) 
        external 
        inState(StateMachine.State.PENDING_VERIFICATION) 
    {
        if (msmeAddress != address(0)) revert OrderAlreadyClaimed();
        
        msmeAddress = msg.sender;
        gstnNumber = _gstn;
        
        _transitionState(StateMachine.State.OPEN_FOR_FUNDING);
        
        emit MSMEClaimed(msg.sender, _gstn);
    }
    
    // ============================================
    // INVESTOR FUNCTIONS
    // ============================================
    
    /**
     * @notice Invest in this order
     */
    function invest() 
        external 
        payable 
        nonReentrant 
        whenNotPaused 
    {
        // Can invest in states where funding is needed
        if (currentState != StateMachine.State.OPEN_FOR_FUNDING &&
            currentState != StateMachine.State.PRODUCTION &&
            currentState != StateMachine.State.AWAITING_DELIVERY) {
            revert InvalidState();
        }
        
        if (msg.value < 0.01 ether) revert InvestmentTooLow();
        
        if (investments[msg.sender] == 0) {
            investors.push(msg.sender);
        }
        
        investments[msg.sender] += msg.value;
        totalFunded += msg.value;
        
        emit InvestmentReceived(msg.sender, msg.value);
        
        // Auto-transition if tranche is fully funded
        _checkAndTransitionAfterFunding();
    }
    
    // ============================================
    // ORACLE FUNCTIONS
    // ============================================
    
    /**
     * @notice Confirm delivery (called by oracle)
     * @param invoiceHash Hash of delivery invoice
     */
    function confirmDelivery(bytes32 invoiceHash) 
        external 
        onlyOracle 
        inState(StateMachine.State.AWAITING_DELIVERY) 
    {
        _transitionState(StateMachine.State.DELIVERED);
        emit DeliveryConfirmed(invoiceHash, block.timestamp);
    }
    
    /**
     * @notice Confirm payment received (called by oracle)
     * @param amount Amount received
     * @param paymentRef Bank paymentRef
     */
    function confirmPayment(uint256 amount, string memory paymentRef) 
        external 
        onlyOracle 
    {
        if (currentState != StateMachine.State.DISBURSED_T3 && 
            currentState != StateMachine.State.DELIVERED) {
            revert InvalidState();
        }
        
        _transitionState(StateMachine.State.PAYMENT_RECEIVED);
        emit PaymentReceived(amount, paymentRef);
        
        // Auto-trigger repayment
        _repayInvestors();
    }
    
    /**
     * @notice Mark order as defaulted (called by oracle after deadline)
     */
    function markDefaulted() 
        external 
        onlyOracle 
    {
        if (block.timestamp <= deliveryDeadline) revert DeadlinePassed();
        
        StateMachine.State oldState = currentState;
        currentState = StateMachine.State.DEFAULTED;
        
        emit StateChanged(oldState, currentState);
    }
    
    // ============================================
    // ADMIN FUNCTIONS (TRANCHE RELEASE)
    // ============================================
    
    /**
     * @notice Release tranche to MSME
     * @param trancheNumber Which tranche to release (1, 2, or 3)
     */
    function releaseTranche(uint8 trancheNumber) 
        external 
        onlyOracle 
        nonReentrant 
    {
        if (!TrancheLogic.canReleaseTranche(trancheState, trancheNumber)) {
            revert TrancheLogic.TrancheAlreadyReleased(trancheNumber);
        }
        
        uint256 amount = TrancheLogic.getTrancheAmount(trancheState, trancheNumber);
        
        if (address(this).balance < amount) {
            revert TrancheLogic.InsufficientFunds();
        }
        
        TrancheLogic.markTrancheReleased(trancheState, trancheNumber);
        
        // Transfer to MSME
        (bool success, ) = msmeAddress.call{value: amount}("");
        require(success, "Transfer failed");
        
        emit TrancheReleased(trancheNumber, amount);
        
        // Update state based on tranche
        if (trancheNumber == 1) {
            _transitionState(StateMachine.State.DISBURSED_T1);
            _transitionState(StateMachine.State.PRODUCTION);
        } else if (trancheNumber == 2) {
            _transitionState(StateMachine.State.DISBURSED_T2);
            _transitionState(StateMachine.State.AWAITING_DELIVERY);
        } else if (trancheNumber == 3) {
            _transitionState(StateMachine.State.DISBURSED_T3);
        }
    }
    
    // ============================================
    // INTERNAL FUNCTIONS
    // ============================================
    
    function _transitionState(StateMachine.State newState) private {
        StateMachine.State oldState = currentState;
        StateMachine.validateTransition(oldState, newState);
        currentState = newState;
        emit StateChanged(oldState, newState);
    }
    
    function _checkAndTransitionAfterFunding() private {
        uint8 currentTranche = StateMachine.getCurrentTranche(currentState);
        uint256 requiredAmount = TrancheLogic.getTrancheAmount(trancheState, currentTranche);
        
        if (totalFunded >= requiredAmount) {
            if (currentState == StateMachine.State.OPEN_FOR_FUNDING) {
                _transitionState(StateMachine.State.FUNDED_T1);
            } else if (currentState == StateMachine.State.PRODUCTION) {
                _transitionState(StateMachine.State.FUNDED_T2);
            } else if (currentState == StateMachine.State.AWAITING_DELIVERY) {
                _transitionState(StateMachine.State.FUNDED_T3);
            }
        }
    }
    
    function _repayInvestors() private {
        for (uint256 i = 0; i < investors.length; i++) {
            address investor = investors[i];
            uint256 principal = investments[investor];
            
            if (principal > 0) {
                // Calculate interest (simple interest)
                uint256 interest = (principal * interestRateBps) / 10000;
                uint256 totalReturn = principal + interest;
                
                // Transfer
                (bool success, ) = investor.call{value: totalReturn}("");
                require(success, "Repayment failed");
                
                emit InvestorRepaid(investor, principal, interest);
                
                investments[investor] = 0;
            }
        }
        
        _transitionState(StateMachine.State.REPAID);
    }
    
    // ============================================
    // VIEW FUNCTIONS
    // ============================================
    
    function getInvestorCount() external view returns (uint256) {
        return investors.length;
    }
    
    function getTrancheInfo(uint8 trancheNumber) external view returns (
        uint256 amount,
        bool released
    ) {
        amount = TrancheLogic.getTrancheAmount(trancheState, trancheNumber);
        
        if (trancheNumber == 1) released = trancheState.tranche1Released;
        else if (trancheNumber == 2) released = trancheState.tranche2Released;
        else if (trancheNumber == 3) released = trancheState.tranche3Released;
    }
    
    function isFullyFunded() external view returns (bool) {
        return totalFunded >= orderAmount;
    }
}