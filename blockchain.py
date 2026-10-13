import hashlib
import json
import os
from time import time

CHAIN_FILE = "blockchain.json"


class Block:
    def __init__(self, index, votes, timestamp, previous_hash, nonce=0):
        self.index = index
        self.votes = votes
        self.timestamp = timestamp
        self.previous_hash = previous_hash
        self.nonce = nonce
        self.hash = self.calculate_hash()

    def calculate_hash(self):
        data = json.dumps({
            "index": self.index,
            "votes": self.votes,
            "timestamp": self.timestamp,
            "previous_hash": self.previous_hash,
            "nonce": self.nonce
        }, sort_keys=True)
        return hashlib.sha256(data.encode()).hexdigest()

    def mine(self, difficulty=3):
        target = "0" * difficulty
        while self.hash[:difficulty] != target:
            self.nonce += 1
            self.hash = self.calculate_hash()

    def to_dict(self):
        return self.__dict__


class VotingBlockchain:
    def __init__(self, difficulty=3):
        self.difficulty = difficulty
        self.pending_votes = []
        self.voted_ids = set()
        self.chain = []
        self.load_or_create()

    def load_or_create(self):
        if os.path.exists(CHAIN_FILE):
            try:
                with open(CHAIN_FILE) as f:
                    data = json.load(f)
                    self.chain = [self._dict_to_block(b) for b in data["chain"]]
                    self.voted_ids = set(data.get("voted_ids", []))
            except Exception:
                self.create_genesis()
        else:
            self.create_genesis()

    def _dict_to_block(self, d):
        b = Block(d["index"], d["votes"], d["timestamp"],
                  d["previous_hash"], d["nonce"])
        b.hash = d["hash"]
        return b

    def save(self):
        with open(CHAIN_FILE, "w") as f:
            json.dump({
                "chain": [b.to_dict() for b in self.chain],
                "voted_ids": list(self.voted_ids)
            }, f, indent=2)

    def create_genesis(self):
        genesis = Block(0, [], time(), "0")
        genesis.mine(self.difficulty)
        self.chain.append(genesis)
        self.save()

    def add_vote(self, voter_id, candidate):
        if not voter_id or not candidate:
            return False, "❌ Voter ID and candidate required"
        if voter_id in self.voted_ids:
            return False, f"❌ Voter '{voter_id}' has already voted!"
        self.pending_votes.append({
            "voter_id": voter_id,
            "candidate": candidate,
            "timestamp": time()
        })
        self.voted_ids.add(voter_id)
        self.save()
        return True, f"✅ Vote for '{candidate}' recorded (pending)"

    def mine_pending(self):
        if not self.pending_votes:
            return None
        block = Block(
            index=len(self.chain),
            votes=self.pending_votes,
            timestamp=time(),
            previous_hash=self.chain[-1].hash
        )
        block.mine(self.difficulty)
        self.chain.append(block)
        self.pending_votes = []
        self.save()
        return block

    def get_results(self):
        tally = {}
        for block in self.chain:
            for vote in block.votes:
                c = vote["candidate"]
                tally[c] = tally.get(c, 0) + 1
        for vote in self.pending_votes:
            c = vote["candidate"]
            tally[c] = tally.get(c, 0) + 1
        return tally

    def is_valid(self):
        for i in range(1, len(self.chain)):
            curr, prev = self.chain[i], self.chain[i - 1]
            if curr.hash != curr.calculate_hash():
                return False
            if curr.previous_hash != prev.hash:
                return False
            if curr.hash[:self.difficulty] != "0" * self.difficulty:
                return False
        return True

    def reset(self):
        if os.path.exists(CHAIN_FILE):
            os.remove(CHAIN_FILE)
        self.pending_votes = []
        self.voted_ids = set()
        self.chain = []
        self.create_genesis()