import pymongo
import certifi
from bson.objectid import ObjectId

class MongoSession():
    def __init__(self):
        self.mongoURI = 'mongodb+srv://dhiwakar:mongodb@cluster0.p7j2bx2.mongodb.net/'
        self.client = pymongo.MongoClient(self.mongoURI,tlsCAFile=certifi.where())
        self.WDC_db = self.client["WDC"]
        self.results_col = self.WDC_db["results"]
        self.emptyDocId = None
    
    def createDoc(self):
        emptyDoc = self.results_col.insert_one({})
        self.emptyDocId = emptyDoc.inserted_id
        return self.emptyDocId
    
    def docIsEmpty(self, _id):
        doc = self.results_col.find_one(ObjectId(_id))
        return len(doc)==1
    
    def getDoc(self, _id):
        doc = self.results_col.find_one(ObjectId(_id))
        doc.pop('_id')
        return doc

    def updateDoc(self,query,data):
        return self.results_col.update_one(query, data)
        
    def clearSession(self):
        self.emptyDocId = None
