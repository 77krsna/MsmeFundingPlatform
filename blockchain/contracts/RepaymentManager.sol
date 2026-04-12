// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

contract RepaymentManager {
    
    struct Repayment {
        uint256 requestId;
        address msmeOwner;
        uint256 amount;
        uint256 installmentNumber;
        uint256 timestamp;
        bool isOnTime;
    }
    
    struct RepaymentSchedule {
        uint256 requestId;
        uint256 totalAmount;
        uint256 totalInstallments;
        uint256 installmentAmount;
        uint256 paidInstallments;
        uint256 totalPaid;
        bool isCompleted;
    }
    
    mapping(uint256 => RepaymentSchedule) public schedules;
    mapping(uint256 => Repayment[]) public repaymentHistory;
    address public admin;
    
    event ScheduleCreated(uint256 requestId, uint256 totalAmount, uint256 installments);
    event InstallmentPaid(uint256 requestId, uint256 installment, uint256 amount);
    event LoanCompleted(uint256 requestId);
    
    modifier onlyAdmin() {
        require(msg.sender == admin, "Only admin");
        _;
    }
    
    constructor() {
        admin = msg.sender;
    }
    
    function createSchedule(
        uint256 _requestId,
        uint256 _totalAmount,
        uint256 _totalInstallments
    ) public onlyAdmin {
        require(_totalAmount > 0, "Total amount must be > 0");
        require(_totalInstallments > 0, "Installments must be > 0");
        require(schedules[_requestId].requestId == 0, "Schedule already exists");
        
        schedules[_requestId] = RepaymentSchedule(
            _requestId,
            _totalAmount,
            _totalInstallments,
            _totalAmount / _totalInstallments,
            0,
            0,
            false
        );
        
        emit ScheduleCreated(_requestId, _totalAmount, _totalInstallments);
    }
    
    function payInstallment(uint256 _requestId) public payable {
        RepaymentSchedule storage schedule = schedules[_requestId];
        require(schedule.requestId != 0, "Schedule not found");
        require(!schedule.isCompleted, "Loan already completed");
        require(msg.value >= schedule.installmentAmount, "Insufficient amount");
        
        schedule.paidInstallments++;
        schedule.totalPaid += msg.value;
        
        repaymentHistory[_requestId].push(Repayment(
            _requestId,
            msg.sender,
            msg.value,
            schedule.paidInstallments,
            block.timestamp,
            true
        ));
        
        if (schedule.paidInstallments >= schedule.totalInstallments) {
            schedule.isCompleted = true;
            emit LoanCompleted(_requestId);
        }
        
        emit InstallmentPaid(_requestId, schedule.paidInstallments, msg.value);
    }
    
    function getSchedule(uint256 _requestId) public view returns (RepaymentSchedule memory) {
        return schedules[_requestId];
    }
    
    function getRepaymentHistory(uint256 _requestId) public view returns (Repayment[] memory) {
        return repaymentHistory[_requestId];
    }
    
    function getRemainingAmount(uint256 _requestId) public view returns (uint256) {
        RepaymentSchedule memory schedule = schedules[_requestId];
        return schedule.totalAmount - schedule.totalPaid;
    }
    
    function getRemainingInstallments(uint256 _requestId) public view returns (uint256) {
        RepaymentSchedule memory schedule = schedules[_requestId];
        return schedule.totalInstallments - schedule.paidInstallments;
    }
}