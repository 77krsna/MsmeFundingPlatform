const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("OrderFactory & OrderContract", function () {
  let factory;
  let owner, oracle, msme, investor1, investor2;

  beforeEach(async function () {
    [owner, oracle, msme, investor1, investor2] = await ethers.getSigners();

    const Factory = await ethers.getContractFactory("OrderFactory");
    factory = await Factory.deploy(oracle.address, 1000, 150);
    await factory.waitForDeployment();
  });

  describe("Factory", function () {
    it("Should deploy with correct settings", async function () {
      expect(await factory.oracleAddress()).to.equal(oracle.address);
      expect(await factory.interestRateBps()).to.equal(1000);
      expect(await factory.platformFeeBps()).to.equal(150);
    });

    it("Should create order contract", async function () {
      const deadline = Math.floor(Date.now() / 1000) + 86400 * 90;
      const amount = ethers.parseEther("10");

      await factory.connect(oracle).createOrder("GEM12345", amount, deadline);

      expect(await factory.getOrderCount()).to.equal(1);

      const orderAddress = await factory.getOrderByGemId("GEM12345");
      expect(orderAddress).to.not.equal(ethers.ZeroAddress);
      expect(await factory.isValidOrder(orderAddress)).to.be.true;
    });

    it("Should prevent duplicate orders", async function () {
      const deadline = Math.floor(Date.now() / 1000) + 86400 * 90;
      const amount = ethers.parseEther("10");

      await factory.connect(oracle).createOrder("GEM12345", amount, deadline);
      await expect(
        factory.connect(oracle).createOrder("GEM12345", amount, deadline)
      ).to.be.revertedWithCustomError(factory, "OrderAlreadyExists");
    });

    it("Should only allow oracle to create orders", async function () {
      const deadline = Math.floor(Date.now() / 1000) + 86400 * 90;
      await expect(
        factory.connect(msme).createOrder("GEM99999", ethers.parseEther("5"), deadline)
      ).to.be.revertedWithCustomError(factory, "OnlyOracle");
    });
  });

  describe("OrderContract", function () {
    let order;

    beforeEach(async function () {
      const deadline = Math.floor(Date.now() / 1000) + 86400 * 90;
      const amount = ethers.parseEther("10");

      await factory.connect(oracle).createOrder("GEM12345", amount, deadline);
      const orderAddress = await factory.getOrderByGemId("GEM12345");
      order = await ethers.getContractAt("OrderContract", orderAddress);
    });

    it("Should have correct initial state", async function () {
      expect(await order.gemOrderId()).to.equal("GEM12345");
      expect(await order.orderAmount()).to.equal(ethers.parseEther("10"));
      expect(await order.currentState()).to.equal(0);
    });

    it("Should allow MSME to claim order", async function () {
      await order.connect(msme).claimOrder("27AABCU9603R1ZM");
      expect(await order.msmeAddress()).to.equal(msme.address);
      expect(await order.currentState()).to.equal(1);
    });

    it("Should prevent double claim", async function () {
      await order.connect(msme).claimOrder("27AABCU9603R1ZM");
      await expect(
        order.connect(investor1).claimOrder("OTHER_GSTN")
      ).to.be.revertedWithCustomError(order, "InvalidState");
    });

    it("Should accept investments", async function () {
      await order.connect(msme).claimOrder("27AABCU9603R1ZM");

      await order.connect(investor1).invest({ value: ethers.parseEther("2") });

      expect(await order.investments(investor1.address)).to.equal(ethers.parseEther("2"));
      expect(await order.totalFunded()).to.equal(ethers.parseEther("2"));
      expect(await order.getInvestorCount()).to.equal(1);
    });

    it("Should reject tiny investments", async function () {
      await order.connect(msme).claimOrder("27AABCU9603R1ZM");

      await expect(
        order.connect(investor1).invest({ value: ethers.parseEther("0.0001") })
      ).to.be.revertedWithCustomError(order, "InvestmentTooLow");
    });

    it("Should transition to FUNDED_T1 when fully funded", async function () {
      await order.connect(msme).claimOrder("27AABCU9603R1ZM");
      await order.connect(investor1).invest({ value: ethers.parseEther("4") });

      expect(await order.currentState()).to.equal(2);
    });

    it("Should allow oracle to release tranche", async function () {
      await order.connect(msme).claimOrder("27AABCU9603R1ZM");
      await order.connect(investor1).invest({ value: ethers.parseEther("4") });

      const before = await ethers.provider.getBalance(msme.address);
      await order.connect(oracle).releaseTranche(1);
      const after = await ethers.provider.getBalance(msme.address);

      expect(after).to.be.gt(before);
      expect(await order.currentState()).to.equal(4);
    });

    it("Should return correct tranche info", async function () {
      const [amount1, released1] = await order.getTrancheInfo(1);
      const [amount2, released2] = await order.getTrancheInfo(2);
      const [amount3, released3] = await order.getTrancheInfo(3);

      expect(amount1).to.equal(ethers.parseEther("4"));
      expect(amount2).to.equal(ethers.parseEther("3"));
      expect(amount3).to.equal(ethers.parseEther("3"));
      expect(released1).to.be.false;
      expect(released2).to.be.false;
      expect(released3).to.be.false;
    });
  });

  describe("Full Lifecycle", function () {
    it("Should complete full order lifecycle", async function () {
      const deadline = Math.floor(Date.now() / 1000) + 86400 * 90;
      const amount = ethers.parseEther("10");

      // 1. Create order
      await factory.connect(oracle).createOrder("GEM_FULL", amount, deadline);
      const orderAddress = await factory.getOrderByGemId("GEM_FULL");
      const order = await ethers.getContractAt("OrderContract", orderAddress);

      // 2. MSME claims
      await order.connect(msme).claimOrder("27AABCU9603R1ZM");
      expect(await order.currentState()).to.equal(1);

      // 3. Fund tranche 1
      await order.connect(investor1).invest({ value: ethers.parseEther("4") });
      expect(await order.currentState()).to.equal(2);

      // 4. Release tranche 1
      await order.connect(oracle).releaseTranche(1);
      expect(await order.currentState()).to.equal(4);

      console.log("    ✅ Order created and funded");
      console.log("    ✅ Tranche 1 released to MSME");
      console.log("    ✅ Full lifecycle working!");
    });
  });
});