import argparse
import os
import re
from openai import OpenAI

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

PROMPT_TEMPLATE = """
You are an expert Solidity developer focused on security. Generate minimal, secure Solidity code for the following natural language requirement: "{user_input}".

**Security Guidelines:**
- Use Solidity ^0.8.0 with modern best practices.
- Include necessary access control (e.g., restrict minting to authorized addresses).
- Avoid insecure patterns (e.g., public mint functions, reentrancy risks, integer overflows).
- Use modifiers for access control where applicable.
- Include inline comments for clarity.
- Use OpenZeppelin contracts for standard functionality like ERC-20.
- If the request is unclear or insecure, respond with an error message instead of code.

**Output Format:**
1. Solidity code in a code block (```solidity\n...\n```).
2. A brief explanation of key security considerations in a separate section.

**Example Input**: "Create an ERC-20 token with minting restricted to addresses in an allowlist"
**Example Output**:
```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract AllowlistToken is ERC20, Ownable {
    mapping(address => bool) private _allowlist;

    constructor(string memory name, string memory symbol) ERC20(name, symbol) Ownable(msg.sender) {}

    modifier onlyAllowlisted() {
        require(_allowlist[msg.sender], "Not allowlisted");
        _;
    }

    function mint(address to, uint256 amount) external onlyAllowlisted {
        _mint(to, amount);
    }

    function addToAllowlist(address account) external onlyOwner {
        _allowlist[account] = true;
    }
}
```
**Security Considerations**:
- Utilized OpenZeppelin's ERC-20 and Ownable for secure, widely-used implementations.
- Minting restricted to only allowlisted addresses using a modifier.
- Only the contract owner can manage the allowlist.
- Solidity ^0.8.0 automatically checks for overflow/underflow issues.
"""

def generate_solidity_code(user_input):
    try:
        prompt = PROMPT_TEMPLATE.format(user_input=user_input)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a secure Solidity code generator."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            max_tokens=1000
        )
        output = response.choices[0].message.content.strip()
        if "```solidity" not in output or "**Security Considerations**" not in output:
            return "Error: Generated output doesn't follow the required format."
        if re.search(r"public\s+mint", output, re.IGNORECASE):
            return "Error: Detected insecure pattern (public mint function)."
        if "import \"@openzeppelin" not in output:
            return "Error: ERC-20 must be implemented using OpenZeppelin contracts."
        return output
    except Exception as e:
        return f"Error: Failed to generate code. Details: {str(e)}"

def main():
    parser = argparse.ArgumentParser(description="Convert natural language to secure Solidity code.")
    parser.add_argument("input", type=str, help="Natural language description of the smart contract")
    args = parser.parse_args()
    result = generate_solidity_code(args.input)
    print(result)

if __name__ == "__main__":
    main()
