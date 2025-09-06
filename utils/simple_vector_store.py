import os
import hashlib
import json
import pickle
from datetime import datetime
from sentence_transformers import SentenceTransformer
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

class SimpleVectorStore:
    def __init__(self):
        self.data_file = os.path.join(os.path.dirname(__file__), "..", "vector_data.json")
        self.embeddings_file = os.path.join(os.path.dirname(__file__), "..", "embeddings.pkl")
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.load_data()
    
    def load_data(self):
        """Load existing data and embeddings"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    self.documents = json.load(f)
            else:
                self.documents = []
            
            if os.path.exists(self.embeddings_file):
                with open(self.embeddings_file, 'rb') as f:
                    self.embeddings = pickle.load(f)
            else:
                self.embeddings = []
        except Exception as e:
            print(f"Error loading data: {e}")
            self.documents = []
            self.embeddings = []
    
    def save_data(self):
        """Save data and embeddings to files"""
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.documents, f, indent=2, ensure_ascii=False)
            
            with open(self.embeddings_file, 'wb') as f:
                pickle.dump(self.embeddings, f)
        except Exception as e:
            print(f"Error saving data: {e}")
    
    def _generate_doc_id(self, job_description, interview_level):
        """Generate a unique document ID"""
        content = f"{job_description.strip().lower()}_{interview_level}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def add_document(self, job_description, qa_content, interview_level):
        """Add a document to the vector store"""
        try:
            doc_id = self._generate_doc_id(job_description, interview_level)
            
            # Check if document already exists
            for i, doc in enumerate(self.documents):
                if doc.get('doc_id') == doc_id:
                    # Update existing document
                    self.documents[i] = {
                        'doc_id': doc_id,
                        'job_description': job_description,
                        'qa_content': qa_content,
                        'interview_level': interview_level,
                        'timestamp': datetime.now().isoformat()
                    }
                    # Update embedding
                    embedding = self.model.encode([job_description])
                    self.embeddings[i] = embedding[0]
                    self.save_data()
                    return True
            
            # Add new document
            document = {
                'doc_id': doc_id,
                'job_description': job_description,
                'qa_content': qa_content,
                'interview_level': interview_level,
                'timestamp': datetime.now().isoformat()
            }
            
            # Generate embedding
            embedding = self.model.encode([job_description])
            
            self.documents.append(document)
            self.embeddings.append(embedding[0])
            
            self.save_data()
            return True
        except Exception as e:
            print(f"Error adding document: {e}")
            return False
    
    def search_similar(self, job_description, interview_level, similarity_threshold=0.8):
        """Search for similar documents"""
        try:
            if not self.documents or not self.embeddings:
                return None
            
            # Filter by interview level
            level_filtered_docs = []
            level_filtered_embeddings = []
            
            for i, doc in enumerate(self.documents):
                if doc.get('interview_level') == interview_level:
                    level_filtered_docs.append(doc)
                    level_filtered_embeddings.append(self.embeddings[i])
            
            if not level_filtered_docs:
                return None
            
            # Generate embedding for query
            query_embedding = self.model.encode([job_description])
            
            # Calculate similarities
            similarities = cosine_similarity(query_embedding, level_filtered_embeddings)[0]
            
            # Find best match
            max_similarity_idx = np.argmax(similarities)
            max_similarity = similarities[max_similarity_idx]
            
            if max_similarity >= similarity_threshold:
                return level_filtered_docs[max_similarity_idx]['qa_content']
            
            return None
        except Exception as e:
            print(f"Error searching documents: {e}")
            return None