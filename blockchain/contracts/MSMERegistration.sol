// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

contract MSMERegistration {
    
    struct MSME {
        uint256 id;
        address owner;
        string businessName;
        string registrationNumber;
        string category; // Micro, Small, Medium
        bool isVerified;
        bool isActive;
        uint256 creditScore;
        uint256 registeredAt;
    }
    
    mapping(uint256 => MSME) public msmes;
    mapping(address => uint256) public addressToMSME;
    uint256 public msmeCount;
    address public admin;
    
    event MSMERegistered(uint256 indexed id, string businessName, address owner);
    event MSMEVerified(uint256 indexed id, address verifiedBy);
    event CreditScoreUpdated(uint256 indexed id, uint256 newScore);
    
    modifier onlyAdmin() {
        require(msg.sender == admin, "Only admin can perform this");
        _;
    }
    
    modifier onlyMSMEOwner(uint256 _id) {
        require(msmes[_id].owner == msg.sender, "Not the MSME owner");
        _;
    }
    
    constructor() {
        admin = msg.sender;
    }
    
    function registerMSME(
        string memory _businessName,
        string memory _registrationNumber,
        string memory _category
    ) public {
        require(addressToMSME[msg.sender] == 0, "Already registered");
        require(bytes(_businessName).length > 0, "Business name required");
        require(bytes(_registrationNumber).length > 0, "Registration number required");
        
        msmeCount++;
        msmes[msmeCount] = MSME(
            msmeCount,
            msg.sender,
            _businessName,
            _registrationNumber,
            _category,
            false,
            true,
            0,
            block.timestamp
        );
        
        addressToMSME[msg.sender] = msmeCount;
        emit MSMERegistered(msmeCount, _businessName, msg.sender);
    }
    
    function verifyMSME(uint256 _id) public onlyAdmin {
        require(msmes[_id].isActive, "MSME not found");
        require(!msmes[_id].isVerified, "Already verified");
        msmes[_id].isVerified = true;
        emit MSMEVerified(_id, msg.sender);
    }
    
    function updateCreditScore(uint256 _id, uint256 _score) public onlyAdmin {
        require(msmes[_id].isActive, "MSME not found");
        require(_score <= 900, "Score must be <= 900");
        msmes[_id].creditScore = _score;
        emit CreditScoreUpdated(_id, _score);
    }
    
    function getMSME(uint256 _id) public view returns (MSME memory) {
        require(msmes[_id].isActive, "MSME not found");
        return msmes[_id];
    }
    
    function getMyMSME() public view returns (MSME memory) {
        uint256 id = addressToMSME[msg.sender];
        require(id > 0, "No MSME registered");
        return msmes[id];
    }
}