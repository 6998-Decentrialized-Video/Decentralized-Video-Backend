const hre = require("hardhat");

async function main() {
  const VideoPlatform = await hre.ethers.getContractFactory("DecentralizedVideoPlatform");
  const videoPlatform = await VideoPlatform.deploy();

  await videoPlatform.deployed();

  console.log("DecentralizedVideoPlatform deployed to:", videoPlatform.address);
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
