import requests
import json

from document import Document
from theExceptions import AQLQueryError

class QueryResult(object) :
	
	def __init__(self, URL, database, rawResults, queryPost, jsonData) :
		"if rawResults = True, will always return the json representation of the results and not a Document object. queryPost contains a dictionnary representation of the initial POST payload sent to the database"

		self.database = database
		self.rawResults = rawResults
		self.queryPost = queryPost

		if jsonData["hasMore"] :
			self.id = jsonData["id"]
			self.URL = "%s/%s" % (URL, self.id)
		else :
			self.id = None
			self.URL = None
		
		self._resetBatch(jsonData)

	def _resetBatch(self, jsonData) :
		"resets the batch according to jsonData"
		self.hasMore = jsonData["hasMore"]
		self.error = jsonData["error"]
		self.code = jsonData["code"]

		try :
			self.count = jsonData["count"]
		except KeyError :
			self.count = None
		
		try :
			self.extra = jsonData["extra"]
		except KeyError :
			self.extra = None

		self.result = jsonData["result"]

		if not self.rawResults :
			self._developed = range(len(self.result))
		else :
			self._developed = None
	
	def _developDoc(self, i) :
		"transform a dict into a Document object"
		raise NotImplemented("Must be implemented in child")

	def nextBatch(self) :
		"become the next batch. raises a StopIteration if there is None"
		if not self.hasMore :
			raise StopIteration("That was the last batch")

		r = requests.put(self.URL)
		data = r.json()
		if r.status_code == 200 and not data['error'] :
			self._resetBatch(data)
		else :
			raise AQLQueryError(data["errorMessage"], self.queryPost["query"], data)

	def delete(self) :
		"kills the cursor"
		requests.delete(self.URL)

	def __getitem__(self, i) :
		"returns a ith result of the query."
		if not self.rawResults and self._developed[i] is not True : self._developDoc(i)
		return self.result[i]

def AQLQueryResult(QueryResult) :
	"AQL queries are attached to a database"
	def __init__(self, URL, database, rawResults, queryPost, jsonData) :
		SimpleQueryResult.__init__(self, URL, database, rawResults, queryPost, jsonData)

	def _developDoc(self, i) :
		docJson = self.result[i]
		try :
			collection = self.database[docJson["_id"].split("/")[0]]
		except KeyError :
			raise CreationError("result %d is not a valid Document. Try setting rawResults to True" % i)

		self.result[i] = Document(collection, docJson)
		self._developed[i] = True

def SimpleQueryResult(QueryResult) :
	"Simple queries are attached to a single collection"
	def __init__(self, URL, collection, rawResults, queryPost, jsonData) :
		SimpleQueryResult.__init__(self, URL, collection.database, rawResults, queryPost, jsonData)
		self.collection = collection

	def _developDoc(self, i) :
		docJson = self.result[i]
		self.result[i] = Document(self.ollection, docJson)
		self._developed[i] = True		