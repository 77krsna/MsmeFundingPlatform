// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";
import "./OrderContract.sol";

contract OrderFactory is Ownable {
    
    address public oracleAddress;
    uint256 public interestRateBps;
    uint256 public platformFeeBps;
    
    address[] public allOrders;
    mapping(string => address) public orderByGemId;
    mapping(address => bool) public isValidOrder;
    
    event OrderCreated(
        address indexed orderAddress,
        string gemOrderId,
        uint256 orderAmount,
        uint256 deliveryDeadline
    );
    
    event OracleUpdated(address oldOracle, address newOracle);
    
    error OrderAlreadyExists(string gemOrderId);
    error OnlyOracle();
    
    modifier onlyOracle() {
        if (msg.sender != oracleAddress) revert OnlyOracle();
        _;
    }
    
    constructor(address _oracle, uint256 _interestRateBps, uint256 _platformFeeBps)
        Ownable(msg.sender)
    {
        oracleAddress = _oracle;
        interestRateBps = _interestRateBps;
        platformFeeBps = _platformFeeBps;
    }
    
    function createOrder(
        string memory _gemOrderId,
        uint256 _orderAmount,
        uint256 _deliveryDeadline
    ) external onlyOracle returns (address) {
        if (orderByGemId[_gemOrderId] != address(0)) {
            revert OrderAlreadyExists(_gemOrderId);
        }
        
        OrderContract newOrder = new OrderContract(
            _gemOrderId,
            _orderAmount,
            _deliveryDeadline,
            oracleAddress,
            interestRateBps,
            platformFeeBps
        );
        
        address orderAddress = address(newOrder);
        
        allOrders.push(orderAddress);
        orderByGemId[_gemOrderId] = orderAddress;
        isValidOrder[orderAddress] = true;
        
        emit OrderCreated(orderAddress, _gemOrderId, _orderAmount, _deliveryDeadline);
        
        return orderAddress;
    }
    
    function updateOracle(address _newOracle) external onlyOwner {
        address oldOracle = oracleAddress;
        oracleAddress = _newOracle;
        emit OracleUpdated(oldOracle, _newOracle);
    }
    
    function getOrderCount() external view returns (uint256) {
        return allOrders.length;
    }
    
    function getOrderByGemId(string memory _gemOrderId) external view returns (address) {
        return orderByGemId[_gemOrderId];
    }
}