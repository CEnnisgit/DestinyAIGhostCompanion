---
description: Update deployment docs after infrastructure or config changes
---

# Sync Deployment Docs

Use this workflow after making changes to:
- Cloud Run services or configuration
- GitHub Secrets
- Database instances or schema
- Custom domains or DNS
- Dockerfiles or build process

## Steps

1. **Review current docs**
   - Open `docs/DEPLOYMENT.md`
   - Check if current values match actual configuration

2. **Verify GCP resources**
   ```bash
   # List Cloud Run services
   gcloud run services list --region=us-east1 --project=plumber-apps
   
   # Check service configuration
   gcloud run services describe SERVICE_NAME --region=us-east1 --format="yaml(spec.template.spec.containers[0].env)"
   
   # List Cloud SQL instances
   gcloud sql instances list --project=plumber-apps
   
   # List databases
   gcloud sql databases list --instance=INSTANCE_NAME --project=plumber-apps
   ```

3. **Verify GitHub Secrets**
   - Go to: https://github.com/MarsGetsGitty/Plumbers-CnD-microservices/settings/secrets/actions
   - Compare repository secrets and environment secrets against `docs/DEPLOYMENT.md`

4. **Verify Domain Mappings**
   ```bash
   gcloud run domain-mappings list --region=us-east1 --project=plumber-apps
   ```

5. **Update docs/DEPLOYMENT.md**
   - Update service names if changed
   - Update domain mappings if changed
   - Update GitHub Secrets table if secrets added/removed
   - Update environment variable tables if env vars changed
   - Update troubleshooting section with any new issues encountered

6. **Commit changes**
   ```bash
   git add docs/DEPLOYMENT.md
   git commit -m "docs: sync DEPLOYMENT.md with current infrastructure"
   ```
