# --- shovel ---
# id: gen_wechat_pay_api_v3_key
# title: Generate WeChat Pay APIv3 key
# when_to_use: Need a 32-char alphanumeric WeChat Pay APIv3 key
# runtime: python
# kind: shovel
# requires: stdlib
# side_effects: none
# platforms: macOS,Linux,Windows
# tags: wechat,crypto
# privacy: public
# completeness: 4
# generality: 3
# efficiency: 4
# invoke: python3 fawai_shovels/python/gen-wechat-pay-api-v3-key.py
# depends_shovels: 
# --- end-shovel ---
"""Generate a WeChat Pay APIv3 key (32 alphanumeric characters).

WeChat Pay requires: 32 characters, digits and upper/lower letters only.
Uses secrets for cryptographically strong randomness.
"""

from __future__ import annotations

import secrets
import string

ALPHABET = string.ascii_letters + string.digits  # A-Za-z0-9


def gen_api_v3_key(length: int = 32) -> str:
    if length < 1:
        raise ValueError("length must be >= 1")
    return "".join(secrets.choice(ALPHABET) for _ in range(length))


if __name__ == "__main__":
    LENGTH = 32
    COUNT = 1

    for i in range(COUNT):
        key = gen_api_v3_key(LENGTH)
        print(key)
