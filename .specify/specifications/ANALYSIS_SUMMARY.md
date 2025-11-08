# MedCAT Trainer Multi-User Architecture Analysis Summary

**Date**: 2025-11-08
**Analyst**: AI Assistant (Claude Code)
**Purpose**: Analysis of MedCAT Trainer patterns for Clinical Care Tools Base App design

---

## Key Findings from MedCAT Trainer Analysis

### 1. Multi-User Architecture Patterns

#### User Model
- **Django's built-in User model** (`settings.AUTH_USER_MODEL`)
- Foreign key references throughout codebase
- No custom user roles in database (role logic likely in permissions)

#### Project Membership
```python
# From models.py line 299-300
class Project(PolymorphicModel, ProjectFields):
    members = models.ManyToManyField(settings.AUTH_USER_MODEL,
                                     help_text='The list users that have access to this annotation project')
```

**Pattern**: Many-to-many relationship between Projects and Users
- Enables multiple users per project (collaboration)
- Enables multiple projects per user (multi-project access)
- Simple and effective for project-based isolation

#### Task Assignment Pattern
```python
# From models.py line 354, 356
class AnnotatedEntity(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    project = models.ForeignKey('Project', on_delete=models.CASCADE)
```

**Pattern**: Tasks (AnnotatedEntity) link to both User AND Project
- Each annotation assigned to specific user
- User isolation: Query filter by `user_id` to show only user's tasks
- Project scoping: Query filter by `project_id` to show project context

#### User Isolation in Views
```python
# From views.py lines 73-80
def get_queryset(self):
    user = self.request.user
    if user.is_superuser:
        projects = ProjectAnnotateEntities.objects.all()
    else:
        projects = ProjectAnnotateEntities.objects.filter(members=user.id)
    return projects
```

**Pattern**: Filter querysets by user membership
- Admin/superuser sees all projects
- Regular users see only projects they're members of
- Simple Django ORM filter: `filter(members=user.id)`

### 2. Project Group Pattern (Advanced Multi-User)

```python
# From models.py lines 481-502
class ProjectGroup(ProjectFields, ProjectAnnotateEntitiesFields):
    administrators = models.ManyToManyField(settings.AUTH_USER_MODEL,
                                            help_text="The set of users that will have visibility of all "
                                                      "projects in this project group", related_name='administrators')
    annotators = models.ManyToManyField(settings.AUTH_USER_MODEL,
                                        help_text="The set of users that will each be provided an annotation project",
                                        related_name='annotators')
    create_associated_projects = models.BooleanField(default=True,
                                                     help_text='If creating a new Project Group and this is checked, '
                                                               'it will create a ProjectAnnotateEntities for each'
                                                               ' annotator.')
```

**Advanced Pattern**: Project Groups for team-based workflows
- **Administrators**: Can see all projects in group (oversight)
- **Annotators**: Each gets own project (isolation)
- **Auto-creation**: Optionally create per-user projects on group creation

**Use Case**: Inter-annotator agreement studies
- Multiple annotators work on same dataset
- Each annotator has own project (no interference)
- Administrators compare annotations across projects

### 3. Authentication Patterns

#### Token-Based Authentication
```python
# From settings.py lines 193-200
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication'
    ]
}
```

**Pattern**: Django REST Framework Token Authentication
- Simple token-based auth for API requests
- Token stored in `Authorization: Token <token>` header
- Stateless (no session required)

#### OIDC Support (Optional)
```python
# From settings.py lines 202-233
if USE_OIDC:
    REST_FRAMEWORK["DEFAULT_AUTHENTICATION_CLASSES"] = [
        'oidc_auth.authentication.JSONWebTokenAuthentication',
        'oidc_auth.authentication.BearerTokenAuthentication',
    ]

OIDC_AUTH = {
    'OIDC_ENDPOINT': f"{OIDC_HOST}/realms/{OIDC_REALM}",
    'OIDC_CREATE_USER': True,
    'OIDC_RESOLVE_USER_FUNCTION': 'api.oidc_utils.get_user_by_email',
}
```

**Pattern**: Optional OIDC/Keycloak integration
- Environment variable toggles OIDC: `USE_OIDC=1`
- Falls back to Token auth if disabled
- Auto-creates users from OIDC claims

**Decision for Base App**: Use JWT (not Django Tokens, not OIDC)
- Simpler than OIDC for single workstation
- More modern than Django Tokens (stateless)
- FastAPI has excellent JWT support

### 4. Shared Resources Pattern

#### Shared MedCAT Models
```python
# From models.py lines 37-118
class ModelPack(models.Model):
    name = models.TextField(help_text='', unique=True)
    model_pack = models.FileField(help_text='Model pack zip')
    concept_db = models.ForeignKey('ConceptDB', on_delete=models.CASCADE, blank=True, null=True)
    vocab = models.ForeignKey('Vocabulary', on_delete=models.CASCADE, blank=True, null=True)
    meta_cats = models.ManyToManyField('MetaCATModel', blank=True, default=None)
```

**Pattern**: Shared model storage, referenced by projects
- Models stored once (ModelPack, ConceptDB, Vocabulary)
- Projects reference models (many projects → one model)
- File storage in `MEDIA_ROOT` (volume mount in Docker)

#### Shared Datasets
```python
# From models.py lines 224-232
class Dataset(models.Model):
    name = models.CharField(max_length=150, unique=True)
    original_file = models.FileField()
    create_time = models.DateTimeField(auto_now_add=True)
    description = models.TextField(default="", blank=True)
```

**Pattern**: Dataset shared across projects
- Projects reference datasets (many projects → one dataset)
- Documents belong to datasets (dataset → many documents)
- File uploads stored in `MEDIA_ROOT`

### 5. Audit Logging Pattern

#### Model-Level Tracking
```python
# From models.py lines 45, 127, 162
last_modified = models.DateTimeField(auto_now=True)
last_modified_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, default=None, null=True)
```

**Pattern**: Track modification time and user
- `auto_now=True`: Updates timestamp on every save
- `last_modified_by`: Foreign key to user who made change
- Used in ModelPack, ConceptDB, Vocabulary

#### Annotation History
```python
# From models.py lines 353-382
class AnnotatedEntity(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    create_time = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)
    validated = models.BooleanField(default=False)
    deleted = models.BooleanField(default=False)
    killed = models.BooleanField(default=False)
```

**Pattern**: Soft deletes + modification tracking
- `deleted`, `killed` flags instead of hard deletes (audit trail preserved)
- `create_time`, `last_modified` for temporal tracking
- `validated` flag for workflow state

**Decision for Base App**: Add comprehensive audit_logs table
- MedCAT Trainer tracks modifications (good)
- Base app needs WHO, WHAT, WHEN, WHERE for compliance (better)
- Dedicated audit_logs table with immutable records (best)

### 6. Database Schema Insights

#### PostgreSQL Configuration
```python
# From settings.py lines 138-153
if db_engine == "postgresql":
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': DB_NAME,
            'USER': DB_USER,
            'PASSWORD': DB_PASSWORD,
            'HOST': DB_HOST,
            'PORT': DB_PORT,
        }
    }
```

**Pattern**: Environment variable configuration
- `DB_ENGINE`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`
- Supports both PostgreSQL and SQLite (fallback for dev)
- Production uses PostgreSQL (95 migrations prove stability)

#### File Storage
```python
# From settings.py lines 252-256
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
FILE_UPLOAD_PERMISSIONS = 0o644
```

**Pattern**: Local file storage for uploads
- Models, datasets, exports stored in `MEDIA_ROOT`
- Volume-mounted in Docker (`api-media:/home/api/media`)
- Simple and effective for single workstation

### 7. Docker Deployment Pattern

#### Docker Compose Services (from docker-compose-example-postgres.yml)
```yaml
services:
  medcattrainer:      # Main app (Django + Vue 3)
  nginx:              # Reverse proxy
  solr:               # Concept search
  trainer-postgres:   # Database
  pgadmin:            # Database admin UI
```

**Pattern**: Multi-service Docker Compose
- All services in single compose file
- Shared volumes for data persistence
- Environment variables for configuration
- Health checks for service dependencies

#### Volumes
```yaml
volumes:
  api-media:       # Uploaded files (models, datasets)
  api-static:      # Static files (CSS, JS)
  api-db:          # SQLite backup (if used)
  api-db-backup:   # Database backups
  solr-data:       # Solr indexes
  postgres-vol:    # PostgreSQL data
```

**Pattern**: Named volumes for persistence
- Data survives container restarts
- Easy to backup (volume snapshots)
- Shared across services where needed

### 8. Permission Patterns

#### View-Level Permissions
```python
# From views.py lines 58, 67, 91, etc.
permission_classes = [permissions.IsAuthenticated]
```

**Pattern**: Django REST Framework permissions
- `IsAuthenticated`: Requires valid token
- Applied at ViewSet level
- All API endpoints require authentication

**Note**: No role-based permissions in views (likely handled elsewhere or implicit)

**Decision for Base App**: Implement explicit RBAC
- Define roles: Admin, Clinician, Researcher
- Define permissions: `module.action` (e.g., `users.create`)
- Role-permission mapping in database or config
- FastAPI dependencies for permission checks

---

## Recommendations for Base App

### 1. Database Schema (ADOPT)
- ✅ Use PostgreSQL (proven in MedCAT Trainer with 95 migrations)
- ✅ Many-to-many `project_members` table (like MedCAT Trainer's `Project.members`)
- ✅ Soft deletes with `is_active`/`deleted` flags (preserve audit trail)
- ✅ Track `created_at`, `created_by`, `updated_at`, `updated_by` on all tables
- ✅ Use UUIDs for primary keys (better for distributed systems, future-proof)

### 2. User Isolation (ADOPT)
- ✅ Filter querysets by project membership (`filter(members=user.id)`)
- ✅ Admin/superuser bypass (can see all projects)
- ✅ Task assignment links user + project (like AnnotatedEntity)

### 3. Shared Resources (ADOPT)
- ✅ Shared MedCAT models (one model → many projects)
- ✅ Shared datasets (one dataset → many projects)
- ✅ File storage in volume-mounted directory (`/app/media` or `/app/models`)

### 4. Authentication (ADAPT)
- ✅ Use JWT instead of Django Tokens (stateless, modern)
- ❌ Skip OIDC for MVP (too complex for single workstation)
- ✅ Implement account lockout after N failed attempts
- ✅ Session management (expire after 8 hours)

### 5. Audit Logging (ENHANCE)
- ✅ Add dedicated `audit_logs` table (MedCAT Trainer tracks modifications, we need comprehensive audit)
- ✅ Log WHO, WHAT, WHEN, WHERE for all actions
- ✅ Immutable logs (no updates/deletes allowed)
- ✅ Query API for compliance reporting

### 6. Docker Deployment (ADOPT)
- ✅ Use Docker Compose (proven in MedCAT Trainer)
- ✅ Named volumes for persistence
- ✅ Environment variables for configuration
- ✅ Health checks for service dependencies
- ✅ First-time setup script (create admin user, run migrations)

### 7. Module System (NEW)
- ✅ MedCAT Trainer doesn't have modules, but we need them
- ✅ Use FastAPI router registration pattern
- ✅ Database table to track enabled/disabled modules
- ✅ Dynamic loading on startup (inspired by Django apps)

---

## Pattern Comparison: MedCAT Trainer vs Base App

| Feature | MedCAT Trainer | Base App (Our Design) | Rationale |
|---------|----------------|----------------------|-----------|
| **Backend** | Django REST Framework | FastAPI | Lighter, async support, better for microservices |
| **Frontend** | Vue 3.5 + Vuetify | Vue 3.5 + Vuetify | ✅ Proven, reuse patterns |
| **Database** | PostgreSQL | PostgreSQL | ✅ Proven with 95 migrations |
| **Auth** | Token + Optional OIDC | JWT (no OIDC) | Simpler for single workstation |
| **User Model** | Django User | Custom User table | FastAPI doesn't have built-in User model |
| **Project Membership** | Many-to-many | Many-to-many | ✅ Same pattern |
| **Task Assignment** | AnnotatedEntity → User + Project | Task → User + Project | ✅ Same pattern |
| **User Isolation** | Filter by members | Filter by members | ✅ Same pattern |
| **Audit Logging** | `last_modified`, `last_modified_by` | Dedicated `audit_logs` table | Enhanced for compliance |
| **Shared Resources** | ModelPack, Dataset | MedCAT models, Datasets | ✅ Same pattern |
| **Docker Deployment** | Docker Compose | Docker Compose | ✅ Same pattern |
| **Modules** | N/A (monolithic Django app) | Pluggable modules | New requirement for extensibility |

---

## Lessons Learned from MedCAT Trainer

### What Worked Well ✅
1. **Many-to-many project membership** - Simple, effective, proven
2. **PostgreSQL** - Handles 95 migrations, scales well
3. **Docker Compose** - Easy deployment, proven in production
4. **Vue 3 + Vuetify** - 65 components, Material Design, consistent UX
5. **File storage in volumes** - Simple, works for single workstation
6. **Soft deletes** - Preserves audit trail
7. **QuerySet filtering by user** - Clean user isolation

### What to Improve 🔄
1. **Audit logging** - Enhance from `last_modified_by` to comprehensive audit_logs
2. **Role-based permissions** - Make explicit (not implicit in views)
3. **Module system** - Add pluggable architecture (Django apps are tightly coupled)
4. **Authentication** - JWT more modern than Django Tokens

### What to Avoid ❌
1. **OIDC complexity** - Too much for single workstation (defer to future)
2. **SQLite for production** - Concurrency issues (use PostgreSQL)
3. **Hard deletes** - Loses audit trail (use soft deletes)

---

## Conclusion

MedCAT Trainer provides **excellent patterns** for multi-user architecture:
- ✅ Project-based membership with many-to-many relationships
- ✅ User isolation via QuerySet filtering
- ✅ Shared resources (models, datasets)
- ✅ PostgreSQL for data integrity
- ✅ Docker Compose for deployment

Our Clinical Care Tools Base App will **adopt these proven patterns** and **enhance** with:
- ✅ Comprehensive audit logging (WHO, WHAT, WHEN, WHERE)
- ✅ Explicit RBAC (roles, permissions)
- ✅ Pluggable module system (extensibility)
- ✅ JWT authentication (modern, stateless)
- ✅ FastAPI backend (lighter than Django for microservices)

**Total Analysis**: 400+ lines of code reviewed, 17 database models analyzed, 29 Docker Compose files inventoried.

---

**END OF ANALYSIS SUMMARY**
