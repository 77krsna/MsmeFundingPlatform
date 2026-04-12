console.log("Setup test running...");

require("dotenv").config();

console.log("ENV CHECK:");
console.log("DATABASE_URL:", process.env.DATABASE_URL ? "Loaded" : "Missing");
console.log("PRIVATE_KEY:", process.env.PRIVATE_KEY ? "Loaded" : "Missing");
console.log("POLYGON_RPC_URL:", process.env.POLYGON_RPC_URL ? "Loaded" : "Missing");