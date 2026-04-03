# Mock in-memory database for development when MongoDB is unavailable
# Data is stored in-memory only (resets on server restart)

_mock_users_storage = {}
_mock_files_storage = {}
_mock_jobs_storage = {}

class MockCollection:
    """Mock MongoDB collection using dictionaries"""
    
    def __init__(self, storage_dict):
        self.storage = storage_dict
    
    def insert_one(self, document):
        """Insert a document"""
        from bson import ObjectId
        doc_id = ObjectId()
        doc = {**document, "_id": doc_id}
        self.storage[str(doc_id)] = doc
        # Return object with inserted_id property
        class Result:
            def __init__(self, id):
                self.inserted_id = id
        return Result(doc_id)
    
    def find_one(self, query):
        """Find one document by query"""
        for doc in self.storage.values():
            match = True
            for key, value in query.items():
                if doc.get(key) != value:
                    match = False
                    break
            if match:
                return doc
        return None
    
    def find(self, query=None):
        """Find multiple documents"""
        if query is None:
            return list(self.storage.values())
        results = []
        for doc in self.storage.values():
            match = True
            if query:
                for key, value in query.items():
                    if doc.get(key) != value:
                        match = False
                        break
            if match:
                results.append(doc)
        return results
    
    def update_one(self, query, update_data):
        """Update one document"""
        doc = self.find_one(query)
        if doc:
            doc_id = str(doc["_id"])
            if "$set" in update_data:
                doc.update(update_data["$set"])
            else:
                doc.update(update_data)
            self.storage[doc_id] = doc
            return {"modified_count": 1}
        return {"modified_count": 0}
    
    def delete_one(self, query):
        """Delete one document"""
        doc = self.find_one(query)
        if doc:
            del self.storage[str(doc["_id"])]
            return {"deleted_count": 1}
        return {"deleted_count": 0}

class MockDB:
    """Mock MongoDB database"""
    
    def __init__(self):
        self.users = MockCollection(_mock_users_storage)
        self.files = MockCollection(_mock_files_storage)
        self.jobs = MockCollection(_mock_jobs_storage)
    
    def __getitem__(self, collection_name):
        """Access collections by name"""
        if collection_name == "users":
            return self.users
        elif collection_name == "files":
            return self.files
        elif collection_name == "jobs":
            return self.jobs
        else:
            return MockCollection({})

# Create mock database instance
mock_db = MockDB()
