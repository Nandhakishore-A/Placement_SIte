import json
import re
import os
from datetime import datetime
from copy import deepcopy

class MockCursor:
    def __init__(self, items):
        self.items = items
        self._sort_key = None
        self._sort_dir = 1
        self._skip = 0
        self._limit = None

    def sort(self, key_or_list, direction=1):
        if isinstance(key_or_list, list):
            self._sort_key = key_or_list[0][0]
            self._sort_dir = key_or_list[0][1]
        else:
            self._sort_key = key_or_list
            self._sort_dir = direction
        return self

    def skip(self, n):
        self._skip = n
        return self

    def limit(self, n):
        self._limit = n
        return self

    def _execute(self):
        res = list(self.items)
        if self._sort_key:
            rev = (self._sort_dir == -1 or self._sort_dir == "desc")
            res.sort(key=lambda x: (x.get(self._sort_key) is None, x.get(self._sort_key)), reverse=rev)
        if self._skip:
            res = res[self._skip:]
        if self._limit is not None:
            res = res[:self._limit]
        return [deepcopy(x) for x in res]

    def __iter__(self):
        return iter(self._execute())

    def __list__(self):
        return self._execute()

class MockCollection:
    def __init__(self, name, parent_db):
        self.name = name
        self.parent_db = parent_db
        self.docs = []

    def create_index(self, keys, **kwargs):
        pass

    def _matches(self, doc, query):
        if not query:
            return True
        for k, v in query.items():
            if k == "$or":
                if not any(self._matches(doc, cond) for cond in v):
                    return False
            elif isinstance(v, dict):
                doc_val = doc.get(k)
                for op, op_val in v.items():
                    if op == "$regex":
                        flags = re.IGNORECASE if v.get("$options") == "i" else 0
                        if doc_val is None or not re.search(op_val, str(doc_val), flags):
                            return False
                    elif op == "$gte":
                        if doc_val is None or doc_val < op_val:
                            return False
                    elif op == "$lte":
                        if doc_val is None or doc_val > op_val:
                            return False
                    elif op == "$ne":
                        if doc_val == op_val:
                            return False
                    elif op == "$in":
                        if doc_val not in op_val:
                            return False
            else:
                if doc.get(k) != v:
                    return False
        return True

    def find(self, query=None, projection=None):
        query = query or {}
        matched = [d for d in self.docs if self._matches(d, query)]
        return MockCursor(matched)

    def find_one(self, query=None, projection=None):
        query = query or {}
        for d in self.docs:
            if self._matches(d, query):
                return deepcopy(d)
        return None

    def count_documents(self, query=None):
        query = query or {}
        return sum(1 for d in self.docs if self._matches(d, query))

    def insert_one(self, doc):
        d = deepcopy(doc)
        if "_id" not in d:
            d["_id"] = str(len(self.docs) + 1)
        self.docs.append(d)
        self.parent_db.save_to_disk()
        return type("Result", (), {"inserted_id": d["_id"]})

    def insert_many(self, docs):
        ids = []
        for doc in docs:
            d = deepcopy(doc)
            if "_id" not in d:
                d["_id"] = str(len(self.docs) + 1)
            self.docs.append(d)
            ids.append(d["_id"])
        self.parent_db.save_to_disk()
        return type("Result", (), {"inserted_ids": ids})

    def update_one(self, query, update, upsert=False):
        matched = False
        set_vals = update.get("$set", {})
        inc_vals = update.get("$inc", {})
        for d in self.docs:
            if self._matches(d, query):
                for k, v in set_vals.items():
                    d[k] = v
                for k, v in inc_vals.items():
                    d[k] = d.get(k, 0) + v
                matched = True
                break
        if not matched and upsert:
            new_doc = deepcopy(query)
            for k, v in set_vals.items():
                new_doc[k] = v
            self.insert_one(new_doc)
        self.parent_db.save_to_disk()
        return type("Result", (), {"modified_count": 1 if matched else 0})

    def find_one_and_update(self, query, update, return_document=True, upsert=True):
        doc = self.find_one(query)
        if not doc and upsert:
            new_doc = deepcopy(query)
            if "$set" in update:
                new_doc.update(update["$set"])
            if "$inc" in update:
                for k, v in update["$inc"].items():
                    new_doc[k] = v
            self.insert_one(new_doc)
            return self.find_one(query)
        elif doc:
            self.update_one(query, update)
            return self.find_one(query)
        return None

    def delete_one(self, query):
        for i, d in enumerate(self.docs):
            if self._matches(d, query):
                del self.docs[i]
                self.parent_db.save_to_disk()
                return type("Result", (), {"deleted_count": 1})
        return type("Result", (), {"deleted_count": 0})

    def aggregate(self, pipeline):
        current_docs = deepcopy(self.docs)
        for stage in pipeline:
            if "$match" in stage:
                current_docs = [d for d in current_docs if self._matches(d, stage["$match"])]
            elif "$group" in stage:
                group_spec = stage["$group"]
                group_id_expr = group_spec.get("_id")
                groups = {}
                for doc in current_docs:
                    if group_id_expr is None:
                        gid = None
                    elif isinstance(group_id_expr, str) and group_id_expr.startswith("$"):
                        gid = doc.get(group_id_expr[1:])
                    else:
                        gid = str(group_id_expr)
                    
                    if gid not in groups:
                        groups[gid] = []
                    groups[gid].append(doc)
                
                result_docs = []
                for gid, doc_list in groups.items():
                    res = {"_id": gid}
                    for field, acc in group_spec.items():
                        if field == "_id":
                            continue
                        if "$sum" in acc:
                            sum_expr = acc["$sum"]
                            if sum_expr == 1:
                                res[field] = len(doc_list)
                            elif isinstance(sum_expr, dict) and "$cond" in sum_expr:
                                cond_list = sum_expr["$cond"]
                                count = 0
                                for d in doc_list:
                                    eq_args = cond_list[0].get("$eq", [])
                                    val = d.get(eq_args[0][1:]) if eq_args[0].startswith("$") else eq_args[0]
                                    if val == eq_args[1]:
                                        count += cond_list[1]
                                    else:
                                        count += cond_list[2]
                                res[field] = count
                            elif isinstance(sum_expr, (int, float)):
                                res[field] = sum_expr * len(doc_list)
                            elif isinstance(sum_expr, str) and sum_expr.startswith("$"):
                                res[field] = sum(d.get(sum_expr[1:], 0) for d in doc_list if isinstance(d.get(sum_expr[1:]), (int, float)))
                        elif "$max" in acc:
                            max_field = acc["$max"][1:] if acc["$max"].startswith("$") else acc["$max"]
                            vals = [d.get(max_field) for d in doc_list if d.get(max_field) is not None]
                            res[field] = max(vals) if vals else 0
                        elif "$avg" in acc:
                            avg_field = acc["$avg"][1:] if acc["$avg"].startswith("$") else acc["$avg"]
                            vals = [d.get(avg_field) for d in doc_list if d.get(avg_field) is not None]
                            res[field] = sum(vals)/len(vals) if vals else 0
                    result_docs.append(res)
                current_docs = result_docs
        return current_docs

class FastDatabase:
    def __init__(self, filepath="placement_local_db.json"):
        self.filepath = filepath
        self._collections = {}
        self._counters = {}
        self.load_from_disk()

    def __getattr__(self, name):
        if name not in self._collections:
            self._collections[name] = MockCollection(name, self)
        return self._collections[name]

    def __getitem__(self, name):
        return self.__getattr__(name)

    def list_collection_names(self):
        return list(self._collections.keys())

    def save_to_disk(self):
        try:
            data = {}
            for name, col in self._collections.items():
                data[name] = []
                for d in col.docs:
                    if isinstance(d, dict):
                        c_doc = dict(d)
                        for k, v in c_doc.items():
                            if isinstance(v, datetime):
                                c_doc[k] = v.isoformat()
                        data[name].append(c_doc)
            data["counters"] = self._counters
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, default=str, indent=2)
        except Exception as e:
            pass

    def load_from_disk(self):
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for name, docs in data.items():
                        if name == "counters" and isinstance(docs, dict):
                            self._counters = docs
                            # Also populate counters collection for find_one_and_update compatibility
                            col = MockCollection("counters", self)
                            for k, v in docs.items():
                                col.docs.append({"_id": k, "sequence_value": v})
                            self._collections["counters"] = col
                            continue
                            
                        if isinstance(docs, list):
                            col = MockCollection(name, self)
                            for d in docs:
                                if isinstance(d, dict):
                                    for k in ["created_at", "date", "interview_date"]:
                                        if k in d and isinstance(d[k], str) and "T" in d[k]:
                                            try:
                                                d[k] = datetime.fromisoformat(d[k])
                                            except Exception:
                                                pass
                                    col.docs.append(d)
                            self._collections[name] = col
            except Exception:
                pass
