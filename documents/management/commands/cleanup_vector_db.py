"""
Management command to clean up orphaned vectors in ChromaDB
Usage: python manage.py cleanup_vector_db
"""
from django.core.management.base import BaseCommand
from documents.models import Document
from rag_components.vector_store_update import get_vector_store, delete_document_vectors_by_doc_id


class Command(BaseCommand):
    help = 'Clean up orphaned vectors in ChromaDB for deleted documents'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        self.stdout.write(self.style.SUCCESS('🔍 Scanning for orphaned vectors...'))
        
        # Get all existing document IDs
        existing_doc_ids = set(str(doc.pk) for doc in Document.objects.all())
        self.stdout.write(f"   Found {len(existing_doc_ids)} documents in database")
        
        # Get all doc_ids in vector store
        vs = get_vector_store()
        collection = vs._collection
        all_vectors = collection.get()
        
        vector_doc_ids = set()
        if all_vectors['metadatas']:
            for metadata in all_vectors['metadatas']:
                doc_id = metadata.get('doc_id')
                if doc_id:
                    vector_doc_ids.add(doc_id)
        
        self.stdout.write(f"   Found {len(vector_doc_ids)} unique doc_ids in vector DB")
        
        # Find orphans
        orphaned_doc_ids = vector_doc_ids - existing_doc_ids
        
        if not orphaned_doc_ids:
            self.stdout.write(self.style.SUCCESS('✅ No orphaned vectors found! Vector DB is clean.'))
            return
        
        self.stdout.write(self.style.WARNING(f'⚠️  Found {len(orphaned_doc_ids)} orphaned document(s):'))
        for doc_id in sorted(orphaned_doc_ids):
            # Count chunks for this doc_id
            chunk_count = sum(1 for m in all_vectors['metadatas'] if m.get('doc_id') == doc_id)
            self.stdout.write(f'   - doc_id={doc_id} ({chunk_count} chunks)')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('\n🔍 DRY RUN: No deletions performed'))
            self.stdout.write('   Run without --dry-run to actually clean up')
        else:
            self.stdout.write(self.style.WARNING('\n🗑️  Deleting orphaned vectors...'))
            deleted_count = 0
            for doc_id in orphaned_doc_ids:
                try:
                    delete_document_vectors_by_doc_id(doc_id)
                    deleted_count += 1
                    self.stdout.write(self.style.SUCCESS(f'   ✓ Deleted vectors for doc_id={doc_id}'))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'   ✗ Failed to delete doc_id={doc_id}: {e}'))
            
            self.stdout.write(self.style.SUCCESS(f'\n✅ Cleaned up {deleted_count} orphaned document(s)'))
