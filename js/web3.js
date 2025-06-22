// Web3 Integration
let web3;
let account;

const connectWallet = async () => {
    if(window.ethereum) {
        try {
            // Request account access
            const accounts = await window.ethereum.request({ 
                method: 'eth_requestAccounts' 
            });
            
            account = accounts[0];
            web3 = new Web3(window.ethereum);
            
            // Update UI
            updateWalletStatus();
            
            // Initialize contract interactions
            initContract();
            
        } catch(error) {
            console.error("User denied account access:", error);
        }
    } else {
        // Fallback for non-MetaMask users
        alert('Please install MetaMask or use a Web3-enabled browser');
    }
};

const initContract = async () => {
    // Load contract ABI and address
    const response = await fetch('config/web3-config.json');
    const config = await response.json();
    
    // Initialize contract
    const contract = new web3.eth.Contract(
        config.abi,
        config.contractAddress
    );
    
    return contract;
};

document.getElementById('connectWalletBtn').addEventListener('click', connectWallet);
