#!/usr/bin/env python3

"""
Implementation of Ascon v1.2, an authenticated cipher and hash function
http://ascon.iaik.tugraz.at/
"""


class Ascon:
    def __init__(self, debug=False, debugpermutation=False):
        self.debug = debug
        self.debugpermutation = debugpermutation
    # === Ascon AEAD encryption and decryption ===

    def ascon_encrypt(self, key, nonce, associateddata, plaintext, variant="Ascon-128"):
        """
        Ascon encryption.
        key: a bytes object of size 16 (for Ascon-128, Ascon-128a; 128-bit security) or 20 (for Ascon-80pq; 128-bit security)
        nonce: a bytes object of size 16 (must not repeat for the same key!)
        associateddata: a bytes object of arbitrary length
        plaintext: a bytes object of arbitrary length
        variant: "Ascon-128", "Ascon-128a", or "Ascon-80pq" (specifies key size, rate and number of rounds)
        returns a bytes object of length len(plaintext)+16 containing the ciphertext and tag
        """
        assert variant in ["Ascon-128", "Ascon-128a", "Ascon-80pq"]
        if variant in ["Ascon-128", "Ascon-128a"]:
            assert (len(key) == 16 and len(nonce) == 16)
        if variant == "Ascon-80pq":
            assert (len(key) == 20 and len(nonce) == 16)
        S = [0, 0, 0, 0, 0]
        k = len(key) * 8   # bits
        a = 12   # rounds
        b = 8 if variant == "Ascon-128a" else 6   # rounds
        rate = 16 if variant == "Ascon-128a" else 8   # bytes

        self.ascon_initialize(S, k, rate, a, b, key, nonce)
        # self.ascon_process_associated_data(S, b, rate, associateddata)
        ciphertext = self.ascon_process_plaintext(S, b, rate, plaintext)
        tag = self.ascon_finalize(S, rate, a, key)
        return ciphertext + tag

    def ascon_decrypt(self, key, nonce, associateddata, ciphertext, variant="Ascon-128"):
        """
        Ascon decryption.
        key: a bytes object of size 16 (for Ascon-128, Ascon-128a; 128-bit security) or 20 (for Ascon-80pq; 128-bit security)
        nonce: a bytes object of size 16 (must not repeat for the same key!)
        associateddata: a bytes object of arbitrary length
        ciphertext: a bytes object of arbitrary length (also contains tag)
        variant: "Ascon-128", "Ascon-128a", or "Ascon-80pq" (specifies key size, rate and number of rounds)
        returns a bytes object containing the plaintext or None if verification fails
        """
        assert variant in ["Ascon-128", "Ascon-128a", "Ascon-80pq"]
        if variant in ["Ascon-128", "Ascon-128a"]:
            assert (len(key) == 16 and len(nonce)
                    == 16 and len(ciphertext) >= 16)
        if variant == "Ascon-80pq":
            assert (len(key) == 20 and len(nonce)
                    == 16 and len(ciphertext) >= 16)
        S = [0, 0, 0, 0, 0]
        k = len(key) * 8  # bits
        a = 12  # rounds
        b = 8 if variant == "Ascon-128a" else 6   # rounds
        rate = 16 if variant == "Ascon-128a" else 8   # bytes

        self.ascon_initialize(S, k, rate, a, b, key, nonce)
        # self.ascon_process_associated_data(S, b, rate, associateddata)
        plaintext = self.ascon_process_ciphertext(S, b, rate, ciphertext[:-16])
        tag = self.ascon_finalize(S, rate, a, key)
        if tag == ciphertext[-16:]:
            return plaintext
        else:
            return None

    # === Ascon AEAD building blocks ===

    def ascon_initialize(self, S, k, rate, a, b, key, nonce):
        """
        Ascon initialization phase - internal helper function.
        S: Ascon state, a list of 5 64-bit integers
        k: key size in bits
        rate: block size in bytes (8 for Ascon-128, Ascon-80pq; 16 for Ascon-128a)
        a: number of initialization/finalization rounds for permutation
        b: number of intermediate rounds for permutation
        key: a bytes object of size 16 (for Ascon-128, Ascon-128a; 128-bit security) or 20 (for Ascon-80pq; 128-bit security)
        nonce: a bytes object of size 16
        returns nothing, updates S
        """
        iv_zero_key_nonce = self.to_bytes(
            [k, rate * 8, a, b] + (20-len(key))*[0]) + key + nonce
        S[0], S[1], S[2], S[3], S[4] = self.bytes_to_state(iv_zero_key_nonce)
        if self.debug:
            self.printstate(S, "initial value:")

        self.ascon_permutation(S, a)

        zero_key = self.bytes_to_state(self.zero_bytes(40-len(key)) + key)
        S[0] ^= zero_key[0]
        S[1] ^= zero_key[1]
        S[2] ^= zero_key[2]
        S[3] ^= zero_key[3]
        S[4] ^= zero_key[4]
        if self.debug:
            self.printstate(S, "initialization:")

    def ascon_process_associated_data(self, S, b, rate, associateddata):
        """
        Ascon associated data processing phase - internal helper function.
        S: Ascon state, a list of 5 64-bit integers
        b: number of intermediate rounds for permutation
        rate: block size in bytes (8 for Ascon-128, 16 for Ascon-128a)
        associateddata: a bytes object of arbitrary length
        returns nothing, updates S
        """
        if len(associateddata) > 0:
            a_zeros = rate - (len(associateddata) % rate) - 1
            a_padding = self.to_bytes([0x80] + [0 for i in range(a_zeros)])
            a_padded = associateddata + a_padding

            for block in range(0, len(a_padded), rate):
                S[0] ^= self.bytes_to_int(a_padded[block:block+8])
                if rate == 16:
                    S[1] ^= self.bytes_to_int(a_padded[block+8:block+16])

                self.ascon_permutation(S, b)

        S[4] ^= 1
        if self.debug:
            self.printstate(S, "process associated data:")

    def ascon_process_plaintext(self, S, b, rate, plaintext):
        """
        Ascon plaintext processing phase (during encryption) - internal helper function.
        S: Ascon state, a list of 5 64-bit integers
        b: number of intermediate rounds for permutation
        rate: block size in bytes (8 for Ascon-128, Ascon-80pq; 16 for Ascon-128a)
        plaintext: a bytes object of arbitrary length
        returns the ciphertext (without tag), updates S
        """
        p_lastlen = len(plaintext) % rate
        p_padding = self.to_bytes([0x80] + (rate-p_lastlen-1)*[0x00])
        p_padded = plaintext + p_padding

        # first t-1 blocks
        ciphertext = self.to_bytes([])
        for block in range(0, len(p_padded) - rate, rate):
            if rate == 8:
                S[0] ^= self.bytes_to_int(p_padded[block:block+8])
                ciphertext += self.int_to_bytes(S[0], 8)
            elif rate == 16:
                S[0] ^= self.bytes_to_int(p_padded[block:block+8])
                S[1] ^= self.bytes_to_int(p_padded[block+8:block+16])
                ciphertext += (self.int_to_bytes(S[0],
                               8) + self.int_to_bytes(S[1], 8))

            self.ascon_permutation(S, b)

        # last block t
        block = len(p_padded) - rate
        if rate == 8:
            S[0] ^= self.bytes_to_int(p_padded[block:block+8])
            ciphertext += self.int_to_bytes(S[0], 8)[:p_lastlen]
        elif rate == 16:
            S[0] ^= self.bytes_to_int(p_padded[block:block+8])
            S[1] ^= self.bytes_to_int(p_padded[block+8:block+16])
            ciphertext += (self.int_to_bytes(S[0], 8)[:min(8, p_lastlen)] +
                           self.int_to_bytes(S[1], 8)[:max(0, p_lastlen-8)])
        if self.debug:
            self.printstate(S, "process plaintext:")
        return ciphertext

    def ascon_process_ciphertext(self, S, b, rate, ciphertext):
        """
        Ascon ciphertext processing phase (during decryption) - internal helper function. 
        S: Ascon state, a list of 5 64-bit integers
        b: number of intermediate rounds for permutation
        rate: block size in bytes (8 for Ascon-128, Ascon-80pq; 16 for Ascon-128a)
        ciphertext: a bytes object of arbitrary length
        returns the plaintext, updates S
        """
        c_lastlen = len(ciphertext) % rate
        c_padded = ciphertext + self.zero_bytes(rate - c_lastlen)

        # first t-1 blocks
        plaintext = self.to_bytes([])
        for block in range(0, len(c_padded) - rate, rate):
            if rate == 8:
                Ci = self.bytes_to_int(c_padded[block:block+8])
                plaintext += self.int_to_bytes(S[0] ^ Ci, 8)
                S[0] = Ci
            elif rate == 16:
                Ci = (self.bytes_to_int(
                    c_padded[block:block+8]), self.bytes_to_int(c_padded[block+8:block+16]))
                plaintext += (self.int_to_bytes(S[0] ^ Ci[0],
                              8) + self.int_to_bytes(S[1] ^ Ci[1], 8))
                S[0] = Ci[0]
                S[1] = Ci[1]

            self.ascon_permutation(S, b)

        # last block t
        block = len(c_padded) - rate
        if rate == 8:
            c_padding1 = (0x80 << (rate-c_lastlen-1)*8)
            c_mask = (0xFFFFFFFFFFFFFFFF >> (c_lastlen*8))
            Ci = self.bytes_to_int(c_padded[block:block+8])
            plaintext += self.int_to_bytes(Ci ^ S[0], 8)[:c_lastlen]
            S[0] = Ci ^ (S[0] & c_mask) ^ c_padding1
        elif rate == 16:
            c_lastlen_word = c_lastlen % 8
            c_padding1 = (0x80 << (8-c_lastlen_word-1)*8)
            c_mask = (0xFFFFFFFFFFFFFFFF >> (c_lastlen_word*8))
            Ci = (self.bytes_to_int(
                c_padded[block:block+8]), self.bytes_to_int(c_padded[block+8:block+16]))
            plaintext += (self.int_to_bytes(S[0] ^ Ci[0], 8) +
                          self.int_to_bytes(S[1] ^ Ci[1], 8))[:c_lastlen]
            if c_lastlen < 8:
                S[0] = Ci[0] ^ (S[0] & c_mask) ^ c_padding1
            else:
                S[0] = Ci[0]
                S[1] = Ci[1] ^ (S[1] & c_mask) ^ c_padding1
        if self.debug:
            self.printstate(S, "process ciphertext:")
        return plaintext

    def ascon_finalize(self, S, rate, a, key):
        """
        Ascon finalization phase - internal helper function.
        S: Ascon state, a list of 5 64-bit integers
        rate: block size in bytes (8 for Ascon-128, Ascon-80pq; 16 for Ascon-128a)
        a: number of initialization/finalization rounds for permutation
        key: a bytes object of size 16 (for Ascon-128, Ascon-128a; 128-bit security) or 20 (for Ascon-80pq; 128-bit security)
        returns the tag, updates S
        """
        assert (len(key) in [16, 20])
        S[rate//8+0] ^= self.bytes_to_int(key[0:8])
        S[rate//8+1] ^= self.bytes_to_int(key[8:16])
        S[rate//8+2] ^= self.bytes_to_int(key[16:] +
                                          self.zero_bytes(24-len(key)))

        self.ascon_permutation(S, a)

        S[3] ^= self.bytes_to_int(key[-16:-8])
        S[4] ^= self.bytes_to_int(key[-8:])
        tag = self.int_to_bytes(S[3], 8) + self.int_to_bytes(S[4], 8)
        if self.debug:
            self.printstate(S, "finalization:")
        return tag

    # === Ascon permutation ===

    def ascon_permutation(self, S, rounds=1):
        """
        Ascon core permutation for the sponge construction - internal helper function.
        S: Ascon state, a list of 5 64-bit integers
        rounds: number of rounds to perform
        returns nothing, updates S
        """
        assert (rounds <= 12)
        if self.debugpermutation:
            self.printwords(S, "permutation input:")
        for r in range(12-rounds, 12):
            # --- add round constants ---
            S[2] ^= (0xf0 - r*0x10 + r*0x1)
            if self.debugpermutation:
                self.printwords(S, "round constant addition:")
            # --- substitution layer ---
            S[0] ^= S[4]
            S[4] ^= S[3]
            S[2] ^= S[1]
            T = [(S[i] ^ 0xFFFFFFFFFFFFFFFF) & S[(i+1) % 5] for i in range(5)]
            for i in range(5):
                S[i] ^= T[(i+1) % 5]
            S[1] ^= S[0]
            S[0] ^= S[4]
            S[3] ^= S[2]
            S[2] ^= 0XFFFFFFFFFFFFFFFF
            if self.debugpermutation:
                self.printwords(S, "substitution layer:")
            # --- linear diffusion layer ---
            S[0] ^= self.rotr(S[0], 19) ^ self.rotr(S[0], 28)
            S[1] ^= self.rotr(S[1], 61) ^ self.rotr(S[1], 39)
            S[2] ^= self.rotr(S[2],  1) ^ self.rotr(S[2],  6)
            S[3] ^= self.rotr(S[3], 10) ^ self.rotr(S[3], 17)
            S[4] ^= self.rotr(S[4],  7) ^ self.rotr(S[4], 41)
            if self.debugpermutation:
                self.printwords(S, "linear diffusion layer:")

    # === helper functions ===

    def get_random_bytes(self, num):
        import os
        return self.to_bytes(os.urandom(num))

    def zero_bytes(self, n):
        return n * b"\x00"

    def to_bytes(self, l):  # where l is a list or bytearray or bytes
        return bytes(bytearray(l))

    def bytes_to_int(self, bytes):
        return sum([bi << ((len(bytes) - 1 - i)*8) for i, bi in enumerate(self.to_bytes(bytes))])

    def bytes_to_state(self, bytes):
        return [self.bytes_to_int(bytes[8*w:8*(w+1)]) for w in range(5)]

    def int_to_bytes(self, integer, nbytes):
        return self.to_bytes([(integer >> ((nbytes - 1 - i) * 8)) % 256 for i in range(nbytes)])

    def rotr(self, val, r):
        return (val >> r) | ((val & (1 << r)-1) << (64-r))

    def bytes_to_hex(self, b):
        return b.hex()
        # return "".join(x.encode('hex') for x in b)

    def printstate(self, S, description=""):
        print(" " + description)
        print(" ".join(["{s:016x}".format(s=s) for s in S]))

    def printwords(self, S, description=""):
        print(" " + description)
        print("\n".join(["  x{i}={s:016x}".format(**locals())
              for i, s in enumerate(S)]))

    # === some demo if called directly ===


def demo_print(data, asc):
    maxlen = max([len(text) for (text, val) in data])
    for text, val in data:
        print("{text}:{align} 0x{val} ({length} bytes)".format(text=text, align=(
            (maxlen - len(text)) * " "), val=asc.bytes_to_hex(val), length=len(val)))


def demo_aead(variant, asc):
    assert variant in ["Ascon-128", "Ascon-128a", "Ascon-80pq"]
    keysize = 20 if variant == "Ascon-80pq" else 16
    print("=== demo encryption using {variant} ===".format(variant=variant))

    # choose a cryptographically strong random key and a nonce that never repeats for the same key:
    key = asc.get_random_bytes(keysize)  # zero_bytes(keysize)
    nonce = asc.get_random_bytes(16)      # zero_bytes(16)

    associateddata = b"ASCON"
    plaintext = b"ascon"

    ciphertext = asc.ascon_encrypt(
        key, nonce, associateddata, plaintext,  variant)
    receivedplaintext = asc.ascon_decrypt(
        key, nonce, associateddata, ciphertext, variant)

    if receivedplaintext == None:
        print("verification failed!")

    demo_print([("key", key),
                ("nonce", nonce),
                ("plaintext", plaintext),
                ("ass.data", associateddata),
                ("ciphertext", ciphertext[:-16]),
                ("tag", ciphertext[-16:]),
                ("received", receivedplaintext),
                ], asc)
# demo_aead("Ascon-128")
