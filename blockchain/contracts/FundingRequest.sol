// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

contract FundingRequest {
    
    enum FundingStatus { 
        Pending,    // 0
        Approved,   // 1
        Funded,     // 2
        Repaying,   // 3
        Completed,  // 4
        Defaulted,  // 5
        Rejected    // 6
    }
    
    struct FundRequest {
        uint256 id;
        uint256 msmeId;
        address msmeOwner;
        uint256 amountRequired;
        uint256 amountFunded;
        uint256 interestRate;
        uint256 tenure;
        string purpose;
        string documentHash;
        FundingStatus status;
        uint256 createdAt;
        uint256 fundedAt;
    }
    
    struct Investment {
        address investor;
        uint256 amount;
        uint256 timestamp;
        bool isRepaid;
    }
    
    mapping(uint256 => FundRequest) public fundRequests;
    mapping(uint256 => Investment[]) public requestInvestments;
    mapping(address => uint256[]) public investorPortfolio;
    uint256 public requestCount;
    address public admin;
    
    event FundingRequested(uint256 indexed id, uint256 msmeId, uint256 amount);
    event FundingApproved(uint256 indexed id);
    event FundingRejected(uint256 indexed id);
    event InvestmentMade(uint256 indexed requestId, address investor, uint256 amount);
    event FundsDisbursed(uint256 indexed requestId, address msmeOwner, uint256 amount);
    event RepaymentMade(uint256 indexed requestId, uint256 amount);
    event StatusChanged(uint256 indexed requestId, FundingStatus newStatus);
    
    modifier onlyAdmin() {
        require(msg.sender == admin, "Only admin");
        _;
    }
    
    constructor() {
        admin = msg.sender;
    }
    
    function createFundingRequest(
        uint256 _msmeId,
        uint256 _amountRequired,
        uint256 _interestRate,
        uint256 _tenure,
        string memory _purpose,
        string memory _documentHash
    ) public {
        require(_amountRequired > 0, "Amount must be > 0");
        require(_interestRate > 0, "Interest rate required");
        require(_tenure > 0, "Tenure required");
        require(bytes(_purpose).length > 0, "Purpose required");
        
        requestCount++;
        fundRequests[requestCount] = FundRequest(
            requestCount,
            _msmeId,
            msg.sender,
            _amountRequired,
            0,
            _interestRate,
            _tenure,
            _purpose,
            _documentHash,
            FundingStatus.Pending,
            block.timestamp,
            0
        );
        
        emit FundingRequested(requestCount, _msmeId, _amountRequired);
    }
    
    function approveFundingRequest(uint256 _requestId) public onlyAdmin {
        FundRequest storage request = fundRequests[_requestId];
        require(request.status == FundingStatus.Pending, "Not pending");
        request.status = FundingStatus.Approved;
        emit FundingApproved(_requestId);
        emit StatusChanged(_requestId, FundingStatus.Approved);
    }
    
    function rejectFundingRequest(uint256 _requestId) public onlyAdmin {
        FundRequest storage request = fundRequests[_requestId];
        require(request.status == FundingStatus.Pending, "Not pending");
        request.status = FundingStatus.Rejected;
        emit FundingRejected(_requestId);
        emit StatusChanged(_requestId, FundingStatus.Rejected);
    }
    
    function invest(uint256 _requestId) public payable {
        FundRequest storage request = fundRequests[_requestId];
        require(request.status == FundingStatus.Approved, "Not approved for funding");
        require(msg.value > 0, "Investment amount must be > 0");
        require(
            request.amountFunded + msg.value <= request.amountRequired,
            "Exceeds required amount"
        );
        
        request.amountFunded += msg.value;
        
        requestInvestments[_requestId].push(Investment(
            msg.sender,
            msg.value,
            block.timestamp,
            false
        ));
        
        investorPortfolio[msg.sender].push(_requestId);
        
        if (request.amountFunded >= request.amountRequired) {
            request.status = FundingStatus.Funded;
            request.fundedAt = block.timestamp;
            emit StatusChanged(_requestId, FundingStatus.Funded);
        }
        
        emit InvestmentMade(_requestId, msg.sender, msg.value);
    }
    
    function disburseFunds(uint256 _requestId) public onlyAdmin {
        FundRequest storage request = fundRequests[_requestId];
        require(request.status == FundingStatus.Funded, "Not fully funded");
        
        request.status = FundingStatus.Repaying;
        payable(request.msmeOwner).transfer(request.amountFunded);
        
        emit FundsDisbursed(_requestId, request.msmeOwner, request.amountFunded);
        emit StatusChanged(_requestId, FundingStatus.Repaying);
    }
    
    function makeRepayment(uint256 _requestId) public payable {
        FundRequest storage request = fundRequests[_requestId];
        require(msg.sender == request.msmeOwner, "Only MSME owner");
        require(request.status == FundingStatus.Repaying, "Not in repayment phase");
        require(msg.value > 0, "Repayment amount must be > 0");
        
        emit RepaymentMade(_requestId, msg.value);
    }
    
    function getFundRequest(uint256 _id) public view returns (FundRequest memory) {
        return fundRequests[_id];
    }
    
    function getInvestments(uint256 _requestId) public view returns (Investment[] memory) {
        return requestInvestments[_requestId];
    }
    
    function getInvestorPortfolio(address _investor) public view returns (uint256[] memory) {
        return investorPortfolio[_investor];
    }
}