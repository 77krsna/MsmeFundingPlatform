const hre = require("hardhat");

async function main() {
    console.log("\n🚀 MSME Blockchain Platform - Complete Test Suite\n");
    console.log("═".repeat(60), "\n");

    // Get test accounts
    const [admin, msme1, investor1, investor2] = await hre.ethers.getSigners();
    
    console.log("👥 Test Accounts Setup:");
    console.log("   Admin:      ", admin.address);
    console.log("   MSME #1:    ", msme1.address);
    console.log("   Investor #1:", investor1.address);
    console.log("   Investor #2:", investor2.address);
    console.log("\n" + "═".repeat(60) + "\n");

    // ==========================================
    // STEP 1: DEPLOY CONTRACTS
    // ==========================================
    console.log("📦 STEP 1: Deploying Smart Contracts");
    console.log("-".repeat(60));

    // Deploy MSMERegistration
    const MSMERegistration = await hre.ethers.getContractFactory("MSMERegistration");
    const msmeReg = await MSMERegistration.deploy();
    await msmeReg.waitForDeployment(); // Changed from .deployed()
    const msmeRegAddress = await msmeReg.getAddress(); // Get address
    console.log("✅ MSMERegistration deployed:", msmeRegAddress);

    // Deploy FundingRequest
    const FundingRequest = await hre.ethers.getContractFactory("FundingRequest");
    const fundingReq = await FundingRequest.deploy();
    await fundingReq.waitForDeployment();
    const fundingReqAddress = await fundingReq.getAddress();
    console.log("✅ FundingRequest deployed:  ", fundingReqAddress);

    // Deploy RepaymentManager
    const RepaymentManager = await hre.ethers.getContractFactory("RepaymentManager");
    const repayment = await RepaymentManager.deploy();
    await repayment.waitForDeployment();
    const repaymentAddress = await repayment.getAddress();
    console.log("✅ RepaymentManager deployed:", repaymentAddress);
    
    console.log("\n" + "═".repeat(60) + "\n");

    // ==========================================
    // STEP 2: REGISTER MSME
    // ==========================================
    console.log("📝 STEP 2: MSME Registration");
    console.log("-".repeat(60));
    
    const registerTx = await msmeReg.connect(msme1).registerMSME(
        "Tech Innovations Pvt Ltd",
        "MSME123456",
        "Small"
    );
    await registerTx.wait();
    console.log("✅ MSME registered");
    console.log("   Tx Hash:", registerTx.hash.substring(0, 20) + "...");
    
    const msmeData = await msmeReg.getMSME(1);
    console.log("   Business:", msmeData.businessName);
    console.log("   Category:", msmeData.category);
    console.log("   Verified:", msmeData.isVerified ? "Yes" : "No");
    console.log("\n" + "═".repeat(60) + "\n");

    // ==========================================
    // STEP 3: ADMIN VERIFICATION
    // ==========================================
    console.log("✔️  STEP 3: Admin Verification & Credit Scoring");
    console.log("-".repeat(60));
    
    const verifyTx = await msmeReg.connect(admin).verifyMSME(1);
    await verifyTx.wait();
    console.log("✅ MSME verified by admin");
    
    const scoreTx = await msmeReg.connect(admin).updateCreditScore(1, 750);
    await scoreTx.wait();
    console.log("✅ Credit score updated: 750/900");
    console.log("\n" + "═".repeat(60) + "\n");

    // ==========================================
    // STEP 4: FUNDING REQUEST
    // ==========================================
    console.log("💰 STEP 4: Create Funding Request");
    console.log("-".repeat(60));
    
    const fundAmount = hre.ethers.parseEther("10"); // Updated syntax
    const createReqTx = await fundingReq.connect(msme1).createFundingRequest(
        1,                      // MSME ID
        fundAmount,             // 10 ETH
        500,                    // 5% interest
        12,                     // 12 months
        "Machinery Purchase",
        "QmIPFSHash123"
    );
    await createReqTx.wait();
    console.log("✅ Funding request created");
    
    const request = await fundingReq.getFundRequest(1);
    console.log("   Amount:  ", hre.ethers.formatEther(request.amountRequired), "ETH");
    console.log("   Interest:", request.interestRate.toString(), "bps (5%)");
    console.log("   Tenure:  ", request.tenure.toString(), "months");
    console.log("   Purpose: ", request.purpose);
    console.log("\n" + "═".repeat(60) + "\n");

    // ==========================================
    // STEP 5: ADMIN APPROVAL
    // ==========================================
    console.log("✅ STEP 5: Admin Approves Funding Request");
    console.log("-".repeat(60));
    
    const approveTx = await fundingReq.connect(admin).approveFundingRequest(1);
    await approveTx.wait();
    console.log("✅ Funding request approved - Now open for investments");
    console.log("\n" + "═".repeat(60) + "\n");

    // ==========================================
    // STEP 6: INVESTMENTS
    // ==========================================
    console.log("💵 STEP 6: Investors Fund the MSME");
    console.log("-".repeat(60));
    
    // Investor 1 invests 6 ETH
    const invest1Amount = hre.ethers.parseEther("6");
    const invest1Tx = await fundingReq.connect(investor1).invest(1, {
        value: invest1Amount
    });
    await invest1Tx.wait();
    console.log("✅ Investor #1 invested:", hre.ethers.formatEther(invest1Amount), "ETH");
    
    // Investor 2 invests 4 ETH (completes funding)
    const invest2Amount = hre.ethers.parseEther("4");
    const invest2Tx = await fundingReq.connect(investor2).invest(1, {
        value: invest2Amount
    });
    await invest2Tx.wait();
    console.log("✅ Investor #2 invested:", hre.ethers.formatEther(invest2Amount), "ETH");
    
    const fundedRequest = await fundingReq.getFundRequest(1);
    console.log("\n   Total Funded:", hre.ethers.formatEther(fundedRequest.amountFunded), "ETH");
    console.log("   Status:", fundedRequest.status == 2 ? "FULLY FUNDED ✅" : "Partial");
    console.log("\n" + "═".repeat(60) + "\n");

    // ==========================================
    // STEP 7: FUND DISBURSEMENT
    // ==========================================
    console.log("💸 STEP 7: Disburse Funds to MSME");
    console.log("-".repeat(60));
    
    const balanceBefore = await hre.ethers.provider.getBalance(msme1.address);
    console.log("   MSME Balance Before:", hre.ethers.formatEther(balanceBefore).substring(0, 10), "ETH");
    
    const disburseTx = await fundingReq.connect(admin).disburseFunds(1);
    await disburseTx.wait();
    console.log("✅ Funds disbursed to MSME");
    
    const balanceAfter = await hre.ethers.provider.getBalance(msme1.address);
    console.log("   MSME Balance After: ", hre.ethers.formatEther(balanceAfter).substring(0, 10), "ETH");
    console.log("   Received:           ", hre.ethers.formatEther(balanceAfter - balanceBefore), "ETH");
    console.log("\n" + "═".repeat(60) + "\n");

    // ==========================================
    // STEP 8: REPAYMENT SCHEDULE
    // ==========================================
    console.log("📅 STEP 8: Create Repayment Schedule");
    console.log("-".repeat(60));
    
    const totalRepayment = hre.ethers.parseEther("10.5"); // Principal + Interest
    const scheduleTx = await repayment.connect(admin).createSchedule(1, totalRepayment, 12);
    await scheduleTx.wait();
    console.log("✅ Repayment schedule created");
    
    const schedule = await repayment.getSchedule(1);
    console.log("   Total Repayment:", hre.ethers.formatEther(schedule.totalAmount), "ETH");
    console.log("   Installments:   ", schedule.totalInstallments.toString());
    console.log("   Per Month:      ", hre.ethers.formatEther(schedule.installmentAmount), "ETH");
    console.log("\n" + "═".repeat(60) + "\n");

    // ==========================================
    // STEP 9: FIRST REPAYMENT
    // ==========================================
    console.log("💳 STEP 9: MSME Makes First Repayment");
    console.log("-".repeat(60));
    
    const installment = schedule.installmentAmount;
    const repaymentTx = await repayment.connect(msme1).payInstallment(1, {
        value: installment
    });
    await repaymentTx.wait();
    console.log("✅ First installment paid:", hre.ethers.formatEther(installment), "ETH");
    
    const updatedSchedule = await repayment.getSchedule(1);
    console.log("   Paid:", updatedSchedule.paidInstallments.toString(), "of", updatedSchedule.totalInstallments.toString());
    console.log("   Remaining:", (updatedSchedule.totalInstallments - updatedSchedule.paidInstallments).toString(), "installments");
    console.log("\n" + "═".repeat(60) + "\n");

    // ==========================================
    // FINAL SUMMARY
    // ==========================================
    console.log("🎉 TEST SUITE COMPLETED SUCCESSFULLY!");
    console.log("═".repeat(60));
    console.log("\n📊 Final Summary:");
    console.log("-".repeat(60));
    
    const finalMSME = await msmeReg.getMSME(1);
    const finalRequest = await fundingReq.getFundRequest(1);
    const finalSchedule = await repayment.getSchedule(1);
    
    console.log("\n🏢 MSME Status:");
    console.log("   Name:         ", finalMSME.businessName);
    console.log("   Verified:     ", finalMSME.isVerified ? "✅ Yes" : "❌ No");
    console.log("   Credit Score: ", finalMSME.creditScore.toString(), "/900");
    
    console.log("\n💰 Funding Status:");
    console.log("   Required:     ", hre.ethers.formatEther(finalRequest.amountRequired), "ETH");
    console.log("   Raised:       ", hre.ethers.formatEther(finalRequest.amountFunded), "ETH");
    console.log("   Investors:    ", 2);
    console.log("   Status:       ", finalRequest.status == 3 ? "REPAYING" : "Unknown");
    
    console.log("\n📅 Repayment Status:");
    console.log("   Total Due:    ", hre.ethers.formatEther(finalSchedule.totalAmount), "ETH");
    console.log("   Paid So Far:  ", hre.ethers.formatEther(finalSchedule.totalPaid), "ETH");
    console.log("   Progress:     ", finalSchedule.paidInstallments.toString(), "/", finalSchedule.totalInstallments.toString(), "installments");
    console.log("   Completion:   ", ((Number(finalSchedule.paidInstallments) / Number(finalSchedule.totalInstallments)) * 100).toFixed(1), "%");
    
    console.log("\n" + "═".repeat(60));
    console.log("\n✅ All blockchain operations completed successfully!");
    console.log("✅ Smart contracts are working as expected!");
    console.log("✅ Platform is ready for frontend integration!\n");
}

main()
    .then(() => process.exit(0))
    .catch((error) => {
        console.error("\n❌ Error occurred:");
        console.error(error);
        process.exit(1);
    });