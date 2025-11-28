import json
import logging
import os
import re
import zipfile
import tempfile
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import pandas as pd
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Q

from core.settings import MEDIA_ROOT
from .models import *
from .utils import env_str_to_bool
from .regex_extractors import extract_all_fields

_MAX_DATASET_SIZE_DEFAULT = 10000
_dt_fmt = '%Y-%m-%d %H:%M:%S.%f'

logger = logging.getLogger(__name__)


def rtf_to_text(rtf_content: str) -> str:
    """
    Convert RTF content to plain text.

    Uses a simple regex-based approach that handles common RTF formatting.
    For more complex RTF files, consider installing striprtf package.

    Args:
        rtf_content: RTF file content as string

    Returns:
        Plain text extracted from RTF
    """
    try:
        # Try using striprtf if available (more robust)
        from striprtf.striprtf import rtf_to_text as striprtf_convert
        return striprtf_convert(rtf_content)
    except ImportError:
        # Fallback to simple regex-based conversion
        pass

    text = rtf_content

    # Remove RTF header
    text = re.sub(r'^\{\\rtf1.*?\\viewkind\d*', '', text, flags=re.DOTALL)

    # Handle common RTF control words
    replacements = [
        (r'\\par\s*', '\n'),           # Paragraph breaks
        (r'\\line\s*', '\n'),          # Line breaks
        (r'\\tab\s*', '\t'),           # Tabs
        (r'\\pard\s*', ''),            # Paragraph reset
        (r'\\plain\s*', ''),           # Plain text reset
        (r'\\b0?\s*', ''),             # Bold
        (r'\\i0?\s*', ''),             # Italic
        (r'\\ul0?\s*', ''),            # Underline
        (r'\\fs\d+\s*', ''),           # Font size
        (r'\\f\d+\s*', ''),            # Font
        (r'\\cf\d+\s*', ''),           # Color
        (r'\\highlight\d+\s*', ''),    # Highlight
        (r'\\lang\d+\s*', ''),         # Language
        (r'\\ltrch\s*', ''),           # Left-to-right
        (r'\\rtlch\s*', ''),           # Right-to-left
        (r'\\qj\s*', ''),              # Justify
        (r'\\ql\s*', ''),              # Left align
        (r'\\qr\s*', ''),              # Right align
        (r'\\qc\s*', ''),              # Center align
        (r'\\fi-?\d+\s*', ''),         # First line indent
        (r'\\li\d+\s*', ''),           # Left indent
        (r'\\ri\d+\s*', ''),           # Right indent
        (r'\\sl-?\d+\s*', ''),         # Line spacing
        (r'\\sa\d+\s*', ''),           # Space after
        (r'\\sb\d+\s*', ''),           # Space before
        (r"\\\'([0-9a-fA-F]{2})", lambda m: chr(int(m.group(1), 16))),  # Hex characters
        (r'\\u(\d+)\??', lambda m: chr(int(m.group(1)))),  # Unicode characters
        (r'\\\*\\[a-z]+\s*', ''),      # Ignorable destinations
        (r'\\[a-z]+\d*\s*', ''),       # Other control words
        (r'\{[^{}]*\}', ''),           # Nested groups (simplified)
        (r'[\{\}]', ''),               # Remaining braces
    ]

    for pattern, replacement in replacements:
        if callable(replacement):
            text = re.sub(pattern, replacement, text)
        else:
            text = re.sub(pattern, replacement, text)

    # Clean up
    text = re.sub(r'\n{3,}', '\n\n', text)  # Reduce multiple newlines
    text = text.strip()

    return text


def parse_rtf_file(file_path: str) -> Tuple[str, str]:
    """
    Parse a single RTF file and extract text.

    Args:
        file_path: Path to RTF file

    Returns:
        Tuple of (document_name, text_content)
    """
    doc_name = os.path.splitext(os.path.basename(file_path))[0]

    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        rtf_content = f.read()

    text = rtf_to_text(rtf_content)
    return doc_name, text


def parse_rtf_zip(zip_path: str) -> List[Tuple[str, str]]:
    """
    Parse a ZIP file containing RTF files.

    Args:
        zip_path: Path to ZIP file

    Returns:
        List of (document_name, text_content) tuples
    """
    documents = []

    with zipfile.ZipFile(zip_path, 'r') as zf:
        for file_info in zf.infolist():
            if file_info.filename.lower().endswith('.rtf') and not file_info.is_dir():
                doc_name = os.path.splitext(os.path.basename(file_info.filename))[0]

                with zf.open(file_info) as f:
                    rtf_content = f.read().decode('utf-8', errors='ignore')
                    text = rtf_to_text(rtf_content)
                    documents.append((doc_name, text))

    return documents


class InvalidParameterError(Exception):
    """Exception raised when invalid parameters are provided"""
    pass


def dataset_from_file(dataset: Dataset, extract_regex_fields: bool = True):
    """
    Create Document objects from a dataset file.

    Supports CSV, XLSX, RTF, and ZIP (containing RTF files).

    Args:
        dataset: Dataset model instance with original_file attached
        extract_regex_fields: If True, extract NHS number, consultant, specialty via regex
    """
    file_path = dataset.original_file.path
    file_name = file_path.lower()
    max_dataset_size = int(os.environ.get('MAX_DATASET_SIZE', _MAX_DATASET_SIZE_DEFAULT))

    # Determine file type and parse accordingly
    if file_name.endswith('.csv'):
        df = pd.read_csv(file_path, on_bad_lines='error')
        df.columns = [c.lower() for c in df.columns]
        source_type = 'csv'
        _validate_dataframe(df, max_dataset_size)
        documents_data = [(row['name'], row['text']) for _, row in df.iterrows()]

    elif file_name.endswith('.xlsx'):
        df = pd.read_excel(file_path)
        df.columns = [c.lower() for c in df.columns]
        source_type = 'xlsx'
        _validate_dataframe(df, max_dataset_size)
        documents_data = [(row['name'], row['text']) for _, row in df.iterrows()]

    elif file_name.endswith('.rtf'):
        source_type = 'rtf'
        doc_name, text = parse_rtf_file(file_path)
        documents_data = [(doc_name, text)]

    elif file_name.endswith('.zip'):
        source_type = 'zip'
        documents_data = parse_rtf_zip(file_path)
        if len(documents_data) > max_dataset_size:
            raise Exception(f'ZIP contains {len(documents_data)} RTF files. Max dataset size is {max_dataset_size}.')
        if len(documents_data) == 0:
            raise Exception('ZIP file contains no RTF files.')

    else:
        raise Exception("Please make sure the file is .csv, .xlsx, .rtf, or .zip (containing RTF files)")

    # Validate unique names
    if env_str_to_bool('UNIQUE_DOC_NAMES_IN_DATASETS', True):
        names = [d[0] for d in documents_data]
        if len(set(names)) != len(names):
            raise Exception('Document names must be unique')

    # Create Document objects
    with transaction.atomic():
        for doc_name, text in documents_data:
            text = sanitise_input(str(text))

            document = Document()
            document.name = str(doc_name)
            document.text = text
            document.dataset = dataset
            document.source_file_type = source_type

            # Extract regex fields if enabled
            if extract_regex_fields and text:
                extracted = extract_all_fields(text)
                document.nhs_number = extracted.get('nhs_number')
                document.consultant = extracted.get('consultant')
                document.specialty = extracted.get('specialty')

            document.save()

    logger.info(f'Created {len(documents_data)} documents from {source_type} file for dataset {dataset.name}')


def _validate_dataframe(df: pd.DataFrame, max_dataset_size: int):
    """Validate a dataframe for document creation."""
    if 'text' not in df.columns or 'name' not in df.columns:
        raise Exception(
            "Please make sure the uploaded file has two columns: 'name', 'text'. "
            "The 'name' column are document IDs, and the 'text' column is the text you're "
            "collecting annotations for"
        )

    if df.shape[0] > max_dataset_size:
        raise Exception(
            f'Attempting to upload a dataset with {df.shape[0]} rows. '
            f'The Max dataset size is set to {max_dataset_size}, please reduce the number of rows '
            f'or contact the MedCATTrainer administrator to increase the env var value: MAX_DATASET_SIZE'
        )

    if df['name'].nunique() != df.shape[0] and env_str_to_bool('UNIQUE_DOC_NAMES_IN_DATASETS', True):
        raise Exception('name column entries must be unique')


def sanitise_input(text: str):
    tags = [('<br>', '\n'), ('</?p>', '\n'), ('<span(?:.*?)?>', ''),
            ('</span>', ''), ('<div (?:.*?)?>', '\n'), ('</div>', '\n'),
            ('</?html>', ''), ('</?body>', ''), ('</?head>', '')]
    for tag, repl in tags:
        text = re.sub(tag, repl, text)
    return text


def delete_orphan_docs(dataset: Dataset):
    Document.objects.filter(dataset__id=dataset.id).delete()


def upload_projects_export(
    medcat_export: Dict,
    cdb_id: str,
    vocab_id: str,
    modelpack_id: str,
    project_name_suffix: str = ' IMPORTED',
    cdb_search_filter_id: str = None,
    members: List[str] = None,
    import_project_name_suffix: str = ' IMPORTED',
    set_validated_docs: bool = False
):
    for proj in medcat_export['projects']:
        if len(proj['documents']) == 0:
            # don't add projects with no documents
            continue
        p = ProjectAnnotateEntities()
        p.name = f"{proj['name']}{project_name_suffix}"
        if len(proj['cuis']) > 1000:
            # store large CUI lists in a json file.
            cuis_file_name = MEDIA_ROOT + '/' + re.sub('/|\.', '_', p.name + '_cuis_file') + '.json'
            json.dump(proj["cuis"].split(','), open(cuis_file_name, 'w'))
            p.cuis = ""
            p.cuis_file.name = cuis_file_name
        else:
            p.cuis = proj['cuis']

        if cdb_id is not None and vocab_id is not None:
            p.concept_db = ConceptDB.objects.get(id=cdb_id)
            p.vocab = Vocabulary.objects.get(id=vocab_id)
        elif modelpack_id is not None:
            p.model_pack = ModelPack.objects.get(id=modelpack_id)
        else:
            raise InvalidParameterError("No cdb, vocab, or modelpack provided")

        # ensure current deployment has the neccessary - Entity, MetaTak, Relation, and warn on not present User objects.
        ent_labels, meta_tasks, rels, unavailable_users, available_users = set(), defaultdict(set), set(), set(), dict()
        for doc in proj['documents']:
            for anno in doc['annotations']:
                ent_labels.add(anno['cui'])
                for meta_anno in anno['meta_anns'].values():
                    meta_tasks[meta_anno['name']].add(meta_anno['value'])
                user_obj = User.objects.filter(username=anno['user']).first()
                if user_obj is None:
                    unavailable_users.add(anno['user'])
                elif anno['user'] not in available_users:
                    available_users[anno['user']] = user_obj
            for rel in doc.get('relations', []):
                rels.add(rel['relation'])
        # escape - filename
        ds_file_name = MEDIA_ROOT + '/' + re.sub('/|\.', '_', p.name + '_dataset') + '.csv'
        names = [doc['name'] for doc in proj['documents']]
        if len(set(names)) != len(names):  # ensure names are unique for docs
            names = [f'{i} - {names[i]}' for i in range(len(names))]
        pd.DataFrame({'name': names,
                      'text': [doc['text'] for doc in proj['documents']]}).to_csv(ds_file_name)
        ds_mod = Dataset()
        ds_mod.name = p.name + '_dataset'
        ds_mod.original_file.name = ds_file_name
        ds_mod.save()
        p.dataset = ds_mod
        p.save()

        if cdb_search_filter_id is not None:
            p.cdb_search_filter.set([ConceptDB.objects.get(id=cdb_search_filter_id)])

        if members is not None:
            p.members.set(members)

        # create django ORM model instances that are referenced in the upload if they don't exist.
        for u in unavailable_users:
            logger.warning(f'Username: {u} - not present in this trainer deployment.')
        for ent_lab in ent_labels:
            ent = Entity.objects.filter(label=ent_lab).first()
            if ent is None:
                ent = Entity()
                ent.label = ent_lab
                ent.save()
        for task in meta_tasks:
            if MetaTask.objects.filter(name=task).first() is None:
                m_task = MetaTask()
                m_task.name = task
                m_task.save()
                # create the MetaTask Values.
            for task_val in meta_tasks[task]:
                if MetaTaskValue.objects.filter(name=task_val).first() is None:
                    mt_value = MetaTaskValue()
                    mt_value.name = task_val
                    mt_value.save()
            m_task = MetaTask.objects.filter(name=task).first()
            curr_vals = m_task.values.all()
            task_vals = [MetaTaskValue.objects.filter(name=m_t).first() for m_t in meta_tasks[task]]
            m_task.values.set(set(list(curr_vals) + task_vals))

        for rel in rels:
            if Relation.objects.filter(label=rel).first() is None:
                r = Relation()
                r.label = rel
                r.save()

        if set_validated_docs:
            p.validated_documents.set(list(Document.objects.filter(dataset=ds_mod)))
        else:
            p.validated_documents.clear()


        for doc in proj['documents']:
            doc_mod = Document.objects.filter(Q(dataset=ds_mod) & Q(text=doc['text'])).first()
            annos = []
            for anno in doc['annotations']:
                a = AnnotatedEntity()
                a.user = available_users[anno['user']]
                a.project = p
                a.document = doc_mod
                e = Entity.objects.get(label=anno['cui'])
                a.entity = e
                a.value = anno['value']
                a.start_ind = anno['start']
                a.end_ind = anno['end']
                a.validated = anno['validated']
                a.correct = anno['correct']
                a.deleted = anno['deleted']
                a.alternative = anno['alternative']
                a.killed = anno['killed']
                a.irrelevant = anno.get('irrelevant', False)  # Added later - so False by default for compatibility
                if anno.get('last_modified') is not None:
                    try:
                        a.last_modified = datetime.strptime(anno['last_modified'], _dt_fmt)
                    except ValueError:
                        a.last_modified = datetime.now()
                if anno.get('create_time') is not None:
                    try:
                        a.create_time = datetime.strptime(anno['create_time'], _dt_fmt)
                    except ValueError:
                        a.create_time = datetime.now()
                a.comment = anno.get('comment')
                a.manually_created = anno['manually_created']

                a.acc = anno['acc']
                a.save()
                annos.append(a)
                for task_name, meta_anno in anno['meta_anns'].items():
                    m_a = MetaAnnotation()
                    m_a.annotated_entity = a
                    # there will be at least one or more of these available.
                    m_a.meta_task = MetaTask.objects.filter(name=task_name).first()
                    m_a.validated = meta_anno['validated']
                    m_a.acc = meta_anno['acc']
                    m_a.meta_task_value = MetaTaskValue.objects.filter(name=meta_anno['value']).first()
                    m_a.save()
                    # missing acc on the model
            anno_to_doc_ind = {a.start_ind: a for a in annos}

            for relation in doc.get('relations', []):
                er = EntityRelation()
                er.user = available_users[relation['user']]
                er.project = p
                er.document = doc_mod
                # there will be at least one or more of these available.
                er.relation = Relation.objects.filter(label=relation['relation']).first()
                er.validated = er.validated
                # link relations with start and end anno ents
                er.start_entity = anno_to_doc_ind[relation['start_entity_start_idx']]
                er.end_entity = anno_to_doc_ind[relation['end_entity_start_idx']]
                if relation.get('create_time') is not None:
                    er.create_time = datetime.strptime(relation['create_time'], _dt_fmt)
                else:
                    er.create_time = datetime.now()
                if relation.get('last_modified_time') is not None:
                    er.last_modified = datetime.strptime(relation['last_modified_time'], _dt_fmt)
                else:
                    er.last_modified = datetime.now()
                er.save()
        logger.info(f"Finished annotation import for project {proj['name']}")
    logger.info('Finished importing all projects')
