from datetime import datetime, timezone
from uuid import uuid4

class InMemoryRepository:
    def __init__(self): self.records = {}
    async def connect(self): return None
    async def create(self, record): self.records[record["analysis_id"]] = record; return record
    async def get(self, key): return self.records.get(key)
    async def list_recent(self, limit=20): return list(self.records.values())[-limit:][::-1]
    async def delete(self, key): return self.records.pop(key, None) is not None
    def close(self): pass

class MongoRepository:
    def __init__(self, uri, database):
        from motor.motor_asyncio import AsyncIOMotorClient
        self.client = AsyncIOMotorClient(uri, serverSelectionTimeoutMS=1500, connectTimeoutMS=1500); self.collection = self.client[database]["analyses"]
    async def connect(self):
        await self.client.admin.command("ping")
        await self.collection.create_index("analysis_id", unique=True); await self.collection.create_index("created_at"); await self.collection.create_index("file_hash")
    async def create(self, record): await self.collection.insert_one(record); return record
    async def get(self, key): return await self.collection.find_one({"analysis_id": key}, {"_id": 0})
    async def list_recent(self, limit=20): return await self.collection.find({}, {"_id": 0}).sort("created_at", -1).to_list(limit)
    async def delete(self, key): return (await self.collection.delete_one({"analysis_id": key})).deleted_count > 0
    def close(self): self.client.close()
