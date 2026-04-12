const hre = require("hardhat");
const fs = require("fs");
const path = require("path");

async function main() {
    console.log("🧪 Testing MSME Blockchain Deployment\n");
    console.log("═".repeat(50), "\n");

    // Load deployment addresses
    const deploymentPath = path.join(__dirname, "..", "deployments", "localhost.json");
    const deployment = JSON.parse(fs.readFileSync(deploymentPath));
    
    console.log("📋 Deployment Info:");
    console.log("Network:", deployment.network);
    console.log("Chain ID:", deployment.chainId);
    console.log("Deployer:", deployment.deployer);
    console.log("\n");

    // Get signers (test accounts)
    const [admin, msme1, investor1, investor2] = await hre.ethers.getSigners();
    
    console.log("👥 Test Accounts:");
    console.log("Admin:", admin.address);
    console.log("MSME 1:", msme1.address);
    console.log("Investor 1:", investor1.address);
    console.log("Investor 2:", investor2.address);
    console.log("\n" + "═".repeat(50) + "\n");

    // Get contract instances
    const MSMERegistration = await hre.ethers.getContractFactory("MSMERegistration");
    const msmeReg = MSMERegistration.attach(deployment.contracts.MSMERegistration);

    const FundingRequest = await hre.ethers.getContractFactory("FundingRequest");
    const fundingReq = FundingRequest.attach(deployment.contracts.FundingRequest);

    const RepaymentManager = await hre.ethers.getContractFactory("RepaymentManager");
    const repayment = RepaymentManager.attach(deployment.contracts.RepaymentManager);

    // ==========================================
    // TEST 1: Register MSME
    // ==========================================
    console.log("📝 TEST 1: Register MSME");
    console.log("-".repeat(50));
    
    try {
        const tx1 = await msmeReg.connect(msme1).registerMSME(
            "Tech Innovations Pvt Ltd",
            "MSME123456",
            "Small"
        );
        await tx1.wait();
        console.log("✅ MSME registered successfully");
        console.log("   Transaction Hash:", tx1.hash);
        
        // Get MSME details
        const msmeData = await msmeReg.getMSME(1);
        console.log("   Business Name:", msmeData.businessName);
        console.log("   Category:", msmeData.category);
        console.log("   Is Verified:", msmeData.isVerified);
        console.log("   Owner:", msmeData.owner);
    } catch (error) {
        console.log("❌ Error:", error.message);
    }
    console.log("\n");

    // ==========================================
    // TEST 2: Verify MSME (Admin)
    // ==========================================
    console.log("✔️  TEST 2: Verify MSME by Admin");
    console.log("-".repeat(50));
    
    try {
        const tx2 = await msmeReg.connect(admin).verifyMSME(1);
        await tx2.wait();
        console.log("✅ MSME verified successfully");
        console.log("   Transaction Hash:", tx2.hash);
        
        const msmeData = await msmeReg.getMSME(1);
        console.log("   Is Verified:", msmeData.isVerified);
    } catch (error) {
        console.log("❌ Error:", error.message);
    }
    console.log("\n");

    // ==========================================
    // TEST 3: Update Credit Score
    // ==========================================
    console.log("📊 TEST 3: Update Credit Score");
    console.log("-".repeat(50));
    
    try {
        const tx3 = await msmeReg.connect(admin).updateCreditScore(1, 750);
        await tx3.wait();
        console.log("✅ Credit score updated");
        
        const msmeData = await msmeReg.getMSME(1);
        console.log("   Credit Score:", msmeData.creditScore.toString());
    } catch (error) {
        console.log("❌ Error:", error.message);
    }
    console.log("\n");

    // ==========================================
    // TEST 4: Create Funding Request
    // ==========================================
    console.log("💰 TEST 4: Create Funding Request");
    console.log("-".repeat(50));
    
    try {
        const amount = hre.ethers.utils.parseEther("10"); // 10 ETH
        const tx4 = await fundingReq.connect(msme1).createFundingRequest(
            1, // MSME ID
            amount,
            500, // 5% interest (500 basis points)
            12, // 12 months tenure
            "Machinery Purchase",
            "QmHash123" // IPFS hash (dummy)
        );
        await tx4.wait();
        console.log("✅ Funding request created");
        console.log("   Transaction Hash:", tx4.hash);
        
        const request = await fundingReq.getFundRequest(1);
        console.log("   Amount Required:", hre.ethers.utils.formatEther(request.amountRequired), "ETH");
        console.log("   Interest Rate:", request.interestRate.toString(), "basis points");
        console.log("   Tenure:", request.tenure.toString(), "months");
        console.log("   Status:", request.status);
    } catch (error) {
        console.log("❌ Error:", error.message);
    }
    console.log("\n");

    // ==========================================
    // TEST 5: Approve Funding Request
    // ==========================================
    console.log("✅ TEST 5: Approve Funding Request");
    console.log("-".repeat(50));
    
    try {
        const tx5 = await fundingReq.connect(admin).approveFundingRequest(1);
        await tx5.wait();
        console.log("✅ Funding request approved");
        
        const request = await fundingReq.getFundRequest(1);
        console.log("   Status:", request.status);
    } catch (error) {
        console.log("❌ Error:", error.message);
    }
    console.log("\n");

    // ==========================================
    // TEST 6: Investor 1 Invests
    // ==========================================
    console.log("💵 TEST 6: Investor 1 Makes Investment");
    console.log("-".repeat(50));
    
    try {
        const investAmount1 = hre.ethers.utils.parseEther("6"); // 6 ETH
        const tx6 = await fundingReq.connect(investor1).invest(1, {
            value: investAmount1
        });
        await tx6.wait();
        console.log("✅ Investment successful");
        console.log("   Amount:", hre.ethers.utils.formatEther(investAmount1), "ETH");
        console.log("   Transaction Hash:", tx6.hash);
        
        const request = await fundingReq.getFundRequest(1);
        console.log("   Total Funded:", hre.ethers.utils.formatEther(request.amountFunded), "ETH");
        console.log("   Status:", request.status);
    } catch (error) {
        console.log("❌ Error:", error.message);
    }
    console.log("\n");

    // ==========================================
    // TEST 7: Investor 2 Invests (Complete Funding)
    // ==========================================
    console.log("💵 TEST 7: Investor 2 Completes Funding");
    console.log("-".repeat(50));
    
    try {
        const investAmount2 = hre.ethers.utils.parseEther("4"); // 4 ETH
        const tx7 = await fundingReq.connect(investor2).invest(1, {
            value: investAmount2
        });
        await tx7.wait();
        console.log("✅ Investment successful");
        console.log("   Amount:", hre.ethers.utils.formatEther(investAmount2), "ETH");
        
        const request = await fundingReq.getFundRequest(1);
        console.log("   Total Funded:", hre.ethers.utils.formatEther(request.amountFunded), "ETH");
        console.log("   Status:", request.status);
        
        // Get all investments
        const investments = await fundingReq.getInvestments(1);
        console.log("   Total Investors:", investments.length);
    } catch (error) {
        console.log("❌ Error:", error.message);
    }
    console.log("\n");

    // ==========================================
    // TEST 8: Disburse Funds
    // ==========================================
    console.log("💸 TEST 8: Disburse Funds to MSME");
    console.log("-".repeat(50));
    
    try {
        const balanceBefore = await msme1.getBalance();
        console.log("   MSME Balance Before:", hre.ethers.utils.formatEther(balanceBefore), "ETH");
        
        const tx8 = await fundingReq.connect(admin).disburseFunds(1);
        await tx8.wait();
        console.log("✅ Funds disbursed");
        
        const balanceAfter = await msme1.getBalance();
        console.log("   MSME Balance After:", hre.ethers.utils.formatEther(balanceAfter), "ETH");
        
        const request = await fundingReq.getFundRequest(1);
        console.log("   Status:", request.status);
    } catch (error) {
        console.log("❌ Error:", error.message);
    }
    console.log("\n");

    // ==========================================
    // TEST 9: Create Repayment Schedule
    // ==========================================
    console.log("📅 TEST 9: Create Repayment Schedule");
    console.log("-".repeat(50));
    
    try {
        const totalRepayment = hre.ethers.utils.parseEther("10.5"); // 10 ETH + 5% interest
        const tx9 = await repayment.connect(admin).createSchedule(
            1, // Request ID
            totalRepayment,
            12 // 12 installments
        );
        await tx9.wait();
        console.log("✅ Repayment schedule created");
        
        const schedule = await repayment.getSchedule(1);
        console.log("   Total Amount:", hre.ethers.utils.formatEther(schedule.totalAmount), "ETH");
        console.log("   Installments:", schedule.totalInstallments.toString());
        console.log("   Per Installment:", hre.ethers.utils.formatEther(schedule.installmentAmount), "ETH");
    } catch (error) {
        console.log("❌ Error:", error.message);
    }
    console.log("\n");

    // ==========================================
    // TEST 10: Make First Repayment
    // ==========================================
    console.log("💳 TEST 10: MSME Makes First Repayment");
    console.log("-".repeat(50));
    
    try {
        const schedule = await repayment.getSchedule(1);
        const installmentAmount = schedule.installmentAmount;
        
        const tx10 = await repayment.connect(msme1).payInstallment(1, {
            value: installmentAmount
        });
        await tx10.wait();
        console.log("✅ Repayment successful");
        console.log("   Amount Paid:", hre.ethers.utils.formatEther(installmentAmount), "ETH");
        
        const updatedSchedule = await repayment.getSchedule(1);
        console.log("   Paid Installments:", updatedSchedule.paidInstallments.toString());
        console.log("   Total Paid:", hre.ethers.utils.formatEther(updatedSchedule.totalPaid), "ETH");
        console.log("   Remaining:", updatedSchedule.totalInstallments - updatedSchedule.paidInstallments);
    } catch (error) {
        console.log("❌ Error:", error.message);
    }
    console.log("\n");

    // ==========================================
    // FINAL SUMMARY
    // ==========================================
    console.log("═".repeat(50));
    console.log("🎉 ALL TESTS COMPLETED!");
    console.log("═".repeat(50));
    console.log("\n📊 Final State:");
    console.log("-".repeat(50));
    
    const finalMSME = await msmeReg.getMSME(1);
    const finalRequest = await fundingReq.getFundRequest(1);
    const finalSchedule = await repayment.getSchedule(1);
    
    console.log("MSME:");
    console.log("  Business:", finalMSME.businessName);
    console.log("  Verified:", finalMSME.isVerified);
    console.log("  Credit Score:", finalMSME.creditScore.toString());
    
    console.log("\nFunding Request:");
    console.log("  Required:", hre.ethers.utils.formatEther(finalRequest.amountRequired), "ETH");
    console.log("  Funded:", hre.ethers.utils.formatEther(finalRequest.amountFunded), "ETH");
    console.log("  Status:", finalRequest.status);
    
    console.log("\nRepayment:");
    console.log("  Total:", hre.ethers.utils.formatEther(finalSchedule.totalAmount), "ETH");
    console.log("  Paid:", finalSchedule.paidInstallments.toString(), "/", finalSchedule.totalInstallments.toString());
    console.log("  Amount Paid:", hre.ethers.utils.formatEther(finalSchedule.totalPaid), "ETH");
    
    console.log("\n" + "═".repeat(50));
}

main()
    .then(() => process.exit(0))
    .catch((error) => {
        console.error(error);
        process.exit(1);
    });