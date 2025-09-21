# documents/models.py
import os
import uuid
from django.db import models
from django.conf import settings
from accounts.models import User

# import rag helpers (relative import - adjust path as needed)
from rag_components.vector_store_update import add_file_to_vector_db, delete_document_vectors_by_doc_id

def document_upload_path(instance, filename):
    ext = filename.split('.')[-1]
    return os.path.join('documents', f"{uuid.uuid4()}.{ext}")

class Document(models.Model):
    title = models.CharField(max_length=255, blank=True)
    file = models.FileField(upload_to=document_upload_path)
    summary = models.TextField(blank=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='uploaded_documents')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title or os.path.basename(self.file.name)

    def save(self, *args, **kwargs):
        # If new file upload or file changed, we'll add/replace in vector DB after saving
        is_new = self.pk is None
        old_path = None
        if not is_new:
            try:
                old = Document.objects.get(pk=self.pk)
                old_path = old.file.path if old.file and old.file.name != self.file.name else None
            except Document.DoesNotExist:
                old_path = None

        super().save(*args, **kwargs)

        # Add or update vectors for this document file
        try:
            add_file_to_vector_db(self.file.path, doc_id=str(self.pk), source_name=self.title or os.path.basename(self.file.name))
        except Exception as e:
            # Log as appropriate in your project
            print(f"Failed to update vector DB for doc {self.pk}: {e}")

        # Optionally delete vectors for previously replaced file if path changed
        # (we key vectors by doc_id so this is usually not necessary)

    def delete(self, *args, **kwargs):
        doc_id = str(self.pk)
        # delete vectors first
        try:
            delete_document_vectors_by_doc_id(doc_id)
        except Exception as e:
            print(f"Failed to delete vectors for doc {doc_id}: {e}")
        # then delete model instance and file
        if self.file:
            try:
                self.file.delete(save=False)
            except Exception:
                pass
        super().delete(*args, **kwargs)
