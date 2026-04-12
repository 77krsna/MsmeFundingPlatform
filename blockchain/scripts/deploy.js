const hre = require("hardhat");
const fs = require("fs");
const path = require("path");

async function main() {
    console.log("Deploying MSME Finance Contracts...\n");
    
    const [deployer] = await hre.ethers.getSigners();
    console.log("Deploying with account:", deployer.address);
    
    // Fixed for ethers v6
    const balance = await hre.ethers.provider.getBalance(deployer.address);
    console.log("Account balance:", hre.ethers.formatEther(balance), "ETH\n");

    // Deploy MSMERegistration
    console.log("Deploying MSMERegistration...");
    const MSMERegistration = await hre.ethers.getContractFactory("MSMERegistration");
    const msmeRegistration = await MSMERegistration.deploy();
    await msmeRegistration.waitForDeployment(); // Changed from .deployed()
    const msmeAddress = await msmeRegistration.getAddress(); // v6 syntax
    console.log("✅ MSMERegistration deployed to:", msmeAddress);

    // Deploy FundingRequest
    console.log("\nDeploying FundingRequest...");
    const FundingRequest = await hre.ethers.getContractFactory("FundingRequest");
    const fundingRequest = await FundingRequest.deploy();
    await fundingRequest.waitForDeployment();
    const fundingAddress = await fundingRequest.getAddress();
    console.log("✅ FundingRequest deployed to:", fundingAddress);

    // Deploy RepaymentManager
    console.log("\nDeploying RepaymentManager...");
    const RepaymentManager = await hre.ethers.getContractFactory("RepaymentManager");
    const repaymentManager = await RepaymentManager.deploy();
    await repaymentManager.waitForDeployment();
    const repaymentAddress = await repaymentManager.getAddress();
    console.log("✅ RepaymentManager deployed to:", repaymentAddress);

    console.log("\n✅ All contracts deployed successfully!\n");

    // Save deployment info
    const network = await hre.ethers.provider.getNetwork();
    const deploymentInfo = {
        network: hre.network.name,
        chainId: network.chainId.toString(),
        contracts: {
            MSMERegistration: msmeAddress,
            FundingRequest: fundingAddress,
            RepaymentManager: repaymentAddress
        },
        deployer: deployer.address,
        timestamp: new Date().toISOString()
    };

    // Create deployments directory if it doesn't exist
    const deploymentsDir = path.join(__dirname, "..", "deployments");
    if (!fs.existsSync(deploymentsDir)) {
        fs.mkdirSync(deploymentsDir);
    }

    // Save to file
    const deploymentPath = path.join(deploymentsDir, `${hre.network.name}.json`);
    fs.writeFileSync(deploymentPath, JSON.stringify(deploymentInfo, null, 2));
    console.log("Deployment info saved to:", deploymentPath);

    // Also save ABIs for frontend
    const abisDir = path.join(__dirname, "..", "deployments", "abis");
    if (!fs.existsSync(abisDir)) {
        fs.mkdirSync(abisDir, { recursive: true });
    }

    const msmeABI = JSON.parse(fs.readFileSync(
        path.join(__dirname, "..", "artifacts", "contracts", "MSMERegistration.sol", "MSMERegistration.json")
    ));
    fs.writeFileSync(
        path.join(abisDir, "MSMERegistration.json"),
        JSON.stringify(msmeABI.abi, null, 2)
    );

    const fundingABI = JSON.parse(fs.readFileSync(
        path.join(__dirname, "..", "artifacts", "contracts", "FundingRequest.sol", "FundingRequest.json")
    ));
    fs.writeFileSync(
        path.join(abisDir, "FundingRequest.json"),
        JSON.stringify(fundingABI.abi, null, 2)
    );

    const repaymentABI = JSON.parse(fs.readFileSync(
        path.join(__dirname, "..", "artifacts", "contracts", "RepaymentManager.sol", "RepaymentManager.json")
    ));
    fs.writeFileSync(
        path.join(abisDir, "RepaymentManager.json"),
        JSON.stringify(repaymentABI.abi, null, 2)
    );

    console.log("✅ ABIs saved to deployments/abis/\n");
}

main()
    .then(() => process.exit(0))
    .catch((error) => {
        console.error(error);
        process.exit(1);
    });