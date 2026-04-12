const fs = require("fs");
const path = require("path");

function readJSON(p) {
  return JSON.parse(fs.readFileSync(p, "utf8"));
}

function upsertEnv(envPath, key, value) {
  let content = fs.existsSync(envPath) ? fs.readFileSync(envPath, "utf8") : "";
  // normalize CRLF
  content = content.replace(/\r\n/g, "\n");

  const line = `${key}=${value}`;
  const re = new RegExp(`^${key}=.*$`, "m");
  if (re.test(content)) content = content.replace(re, line);
  else content = content.trimEnd() + (content.endsWith("\n") || content.length === 0 ? "" : "\n") + line + "\n";

  fs.writeFileSync(envPath, content, "utf8");
}

function main() {
  const root = path.resolve(__dirname, "..");
  const frontendEnv = path.join(root, "frontend", ".env");

  // Prefer deployed-addresses.json (your repo has it)
  const deployed1 = path.join(root, "blockchain", "deployed-addresses.json");
  const deployed2 = path.join(root, "blockchain", "deployments", "localhost.json");

  let deployedPath = null;
  if (fs.existsSync(deployed1)) deployedPath = deployed1;
  else if (fs.existsSync(deployed2)) deployedPath = deployed2;

  if (!deployedPath) {
    console.error("No deployed addresses file found.");
    process.exit(1);
  }

  const data = readJSON(deployedPath);

  // Try multiple shapes safely
  const addr = (k) => {
    const v = data[k];
    if (typeof v === "string") return v;
    if (v && typeof v.address === "string") return v.address;
    return null;
  };

  const msme = addr("MSMERegistration") || addr("msme") || addr("MSME");
  const funding = addr("FundingRequest") || addr("funding") || addr("FUNDING");
  const repay = addr("RepaymentManager") || addr("repayment") || addr("REPAYMENT");

  // Basic runtime URLs
  upsertEnv(frontendEnv, "VITE_API_URL", "http://127.0.0.1:8001");
  upsertEnv(frontendEnv, "VITE_API_BASE_URL", "http://127.0.0.1:8001/api");
  upsertEnv(frontendEnv, "VITE_RPC_URL", "http://127.0.0.1:8545");

  if (msme) upsertEnv(frontendEnv, "VITE_MSME_CONTRACT", msme);
  if (funding) upsertEnv(frontendEnv, "VITE_FUNDING_CONTRACT", funding);
  if (repay) upsertEnv(frontendEnv, "VITE_REPAYMENT_CONTRACT", repay);

  console.log("Updated frontend/.env using:", deployedPath);
  console.log("MSME:", msme);
  console.log("FUNDING:", funding);
  console.log("REPAY:", repay);
}

main();
