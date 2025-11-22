# Clinical Care Tools Documentation

Complete documentation for the Clinical Care Tools application.

## 📚 Documentation Index

### Getting Started
- **[SETUP.md](SETUP.md)** - Development environment setup and local development
- **[Quick Start Guide](../README.md#-quick-start)** - 5-minute quick start

### Deployment & Operations
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Production deployment, scaling, and operations
- **[SECURITY.md](SECURITY.md)** - Security model, compliance requirements, audit logging
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - System design, component interactions, data flows

### Development
- **[API.md](API.md)** - RESTful API documentation, endpoints, authentication
- **[backend/README.md](../backend/README.md)** - Backend development guide
- **[frontend/README.md](../frontend/README.md)** - Frontend development guide

### Clinical & User
- **[USER_GUIDE.md](USER_GUIDE.md)** - Clinician and end-user guide
- **[FAQ.md](FAQ.md)** - Frequently asked questions

## 🎯 Documentation by Role

### For Clinicians
Start with: [USER_GUIDE.md](USER_GUIDE.md)
- Patient search workflows
- Document upload process
- Timeline interpretation
- Data export options

### For Developers
Start with: [SETUP.md](SETUP.md) → [ARCHITECTURE.md](ARCHITECTURE.md) → [API.md](API.md)
- Development environment
- System architecture
- API reference
- Backend: [backend/README.md](../backend/README.md)
- Frontend: [frontend/README.md](../frontend/README.md)

### For DevOps/System Administrators
Start with: [DEPLOYMENT.md](DEPLOYMENT.md) → [SECURITY.md](SECURITY.md)
- Production deployment
- Scaling and monitoring
- Backup and recovery
- Security and compliance
- Health checks and troubleshooting

### For Security/Compliance Officers
Start with: [SECURITY.md](SECURITY.md)
- Encryption and TLS
- Authentication & authorization
- Audit logging
- HIPAA/GDPR/21 CFR Part 11 compliance
- Data retention policies

## 🚀 Quick Navigation

### Installation & Setup
1. [SETUP.md](SETUP.md) - Get development environment running
2. [Docker Compose Configuration](../docker-compose.yml) - Container orchestration

### Understanding the System
1. [ARCHITECTURE.md](ARCHITECTURE.md) - System design overview
2. [API.md](API.md) - REST API endpoints and schemas
3. [backend/README.md](../backend/README.md) - Backend implementation details

### Building & Deploying
1. [DEPLOYMENT.md](DEPLOYMENT.md) - Production deployment
2. [SECURITY.md](SECURITY.md) - Security hardening
3. [scripts/](../scripts/) - Automated deployment and operational scripts

### Using the Application
1. [USER_GUIDE.md](USER_GUIDE.md) - End-user workflows
2. [API.md](API.md) - For programmatic access
3. [FAQ.md](FAQ.md) - Common questions and troubleshooting

## 📄 Document Structure

Each documentation file follows a consistent structure:

```
# Document Title

## Overview/Summary

## Table of Contents

## Main Content
- Organized by logical sections
- Code examples where applicable
- Diagrams for complex concepts

## Examples
- Real-world usage scenarios
- Configuration examples
- Command examples

## Troubleshooting
- Common issues
- Solutions and workarounds

## References
- External links
- Related documents
- Additional resources
```

## 🔍 Key Topics

### Authentication & Access Control
- JWT token-based authentication
- Role-based access control (RBAC)
- User management
- Session management

**Documents**: [API.md](API.md#authentication), [SECURITY.md](SECURITY.md#authentication)

### Data Security
- Encryption at rest (AES-256)
- Encryption in transit (TLS 1.3)
- Key management
- Data retention policies

**Documents**: [SECURITY.md](SECURITY.md#encryption-and-key-management)

### Compliance
- HIPAA requirements
- GDPR compliance
- FDA 21 CFR Part 11
- Audit logging requirements

**Documents**: [SECURITY.md](SECURITY.md#compliance-frameworks)

### NLP & Clinical Features
- Medical concept extraction
- Meta-annotation filtering
- Confidence scoring
- Temporal relationship extraction

**Documents**: [ARCHITECTURE.md](ARCHITECTURE.md#nlp-service), [USER_GUIDE.md](USER_GUIDE.md#clinical-features)

### Performance & Scaling
- Caching strategy
- Database optimization
- Horizontal scaling
- Load testing

**Documents**: [DEPLOYMENT.md](DEPLOYMENT.md#performance-tuning), [scripts/load-test.sh](../scripts/load-test.sh)

## 🆘 Troubleshooting Guide

### Quick Help by Issue

| Issue | Reference |
|-------|-----------|
| Can't connect to database | [DEPLOYMENT.md#troubleshooting](DEPLOYMENT.md#troubleshooting) |
| NLP service not responding | [ARCHITECTURE.md#nlp-service](ARCHITECTURE.md#nlp-service) |
| Frontend not loading API | [API.md#cors](API.md#cross-origin-requests) |
| Health checks failing | [DEPLOYMENT.md#health-checks](DEPLOYMENT.md#health-checks) |
| Performance degradation | [DEPLOYMENT.md#performance-tuning](DEPLOYMENT.md#performance-tuning) |
| Backup/restore issues | [DEPLOYMENT.md#backup-and-recovery](DEPLOYMENT.md#backup-and-recovery) |

## 📊 Documentation Statistics

| Type | Count | Purpose |
|------|-------|---------|
| Setup & Installation | 1 | Development environment |
| Deployment Guides | 1 | Production operations |
| API Documentation | 1 | Developer reference |
| Architecture | 1 | System design |
| Security & Compliance | 1 | Regulatory requirements |
| User Guides | 1 | Clinical users |
| Component READMEs | 3 | Backend, Frontend, Scripts |

## 🔄 Contributing to Documentation

When updating documentation:

1. **Maintain consistency**: Follow the structure and style of existing docs
2. **Include examples**: Real-world code and configuration examples
3. **Cross-reference**: Link related sections and documents
4. **Update TOC**: Keep table of contents current
5. **Review**: Have technical and non-technical reviewers
6. **Version**: Update version number and last updated date

## 📦 Documentation Tools

### Available Scripts
- `./scripts/generate-api-docs.sh` - Generate API documentation from code
- `./scripts/generate-schema-diagrams.sh` - Generate database schema diagrams

### External Tools
- API testing: Postman collection (see [API.md](API.md#postman-collection))
- Load testing: [load-test.sh](../scripts/load-test.sh) with Locust
- Health monitoring: [health-check.sh](../scripts/health-check.sh)

## 📞 Getting Help

1. **Search this documentation** - Most answers are in the docs
2. **Check [FAQ.md](FAQ.md)** - Common questions answered
3. **Review logs** - Container logs often have error details
4. **Open an issue** - Report bugs with full context
5. **Ask in discussions** - Community support channel

## 🎓 Learning Resources

### Internal
- Source code examples in each component
- Test files for usage patterns
- Postman collection for API testing

### External
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Vue 3 Guide](https://vuejs.org/guide/)
- [PostgreSQL Manual](https://www.postgresql.org/docs/)
- [MedCAT GitHub](https://github.com/CogStack/MedCAT)

## 📋 Latest Updates

### Version 1.0.0 (2025-01-08)
- Initial comprehensive documentation
- Complete API reference
- Deployment and security guides
- User and developer guides
- Setup and troubleshooting

---

**Last Updated**: 2025-01-08
**Maintainers**: Clinical Care Tools Development Team
**Feedback**: Open issues or pull requests with documentation improvements
