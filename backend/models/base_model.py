from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class TimestampedModel(BaseModel):
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

class MongoModel(TimestampedModel):
    @property
    def collection_name(self) -> str:
        raise NotImplementedError
        
    async def save(self):
        from database import Database
        collection = await Database.get_collection(self.collection_name)
        result = await Database.execute_with_retry(
            collection, 
            'insert_one', 
            self.model_dump(exclude={'id'})
        )
        return result.inserted_id
