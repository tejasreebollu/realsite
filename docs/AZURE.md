# Azure evaluation deployment

Updated: 11 October 2026.

The included Azure path hosts the same Docker stack on one Ubuntu VM with Caddy providing domain-based HTTPS. It is an evaluation topology. No Azure resources have been created by this work.

## Included files

- `infra/main.bicep`: VM, SSD OS disk, static public IP, virtual network, NIC, and NSG.
- `infra/cloud-init.yml`: install Docker Engine and Compose from Docker's Ubuntu apt repository.
- `infra/compose.azure.yml`: remove the local web binding, add Caddy on ports 80/443, enable secure session cookies, disable known demo-account creation/login and existing demo sessions.
- `infra/Caddyfile`: HTTPS reverse proxy and HTTP redirect.
- `infra/deploy.ps1`: create resources, package/upload source, generate a database password, start the stack.

Only HTTPS/HTTP and administrator-restricted SSH are permitted by the NSG. PostgreSQL, Redis, and FastAPI remain on the Docker network. VM size and region are parameters; availability and pricing must be checked for your subscription.

## Deployment

Requires Azure CLI with Bicep, OpenSSH/scp, tar, a signed-in Azure subscription, an SSH key pair, a public domain, and control over its DNS. Running the script creates billable resources.

```powershell
az login
az account set --subscription '<subscription-id>'

.\infra\deploy.ps1 `
  -ResourceGroup 'rg-realsite-india-eval' `
  -Location 'centralindia' `
  -Domain 'homes.your-domain.example' `
  -AdminCidr '<your-public-ip>/32' `
  -SshPublicKeyPath '<path-to-key.pub>' `
  -SshPrivateKeyPath '<path-to-private-key>'
```

The script prints the static VM IP. Point the domain A record to that IP. The SSH client requests host fingerprint verification on its first connection. DNS propagation and outbound access to the certificate issuer must succeed before HTTPS is available.

The deployment environment is stored in ignored `artifacts/azure.env` and uploaded as `~/portal/.env` with mode 600. It is preserved across reruns to avoid breaking the PostgreSQL credentials. Use a separate artifact directory/environment per deployment; do not reuse this file for a different VM or domain. The script is designed for a fresh evaluation VM and does not import local development database volumes.

## Validate the templates without deploying

```powershell
az bicep build --file infra/main.bicep --outfile artifacts/main.json
$env:PORTAL_DOMAIN = 'portal.example.com'
docker compose -f compose.yml -f infra/compose.azure.yml config --quiet
```

## After deployment

```bash
cd ~/portal
sudo docker compose -f compose.yml -f infra/compose.azure.yml ps
sudo docker compose -f compose.yml -f infra/compose.azure.yml logs --tail 100 api caddy
```

Use `https://<domain>/api/health` to check readiness. Do not use this evaluation stack for production user data until the production work below is completed.

## Production progression

Move PostgreSQL to Azure Database for PostgreSQL Flexible Server, Redis to an appropriate managed Redis service, hosted images to Azure Blob Storage/CDN, and credentials to Key Vault. Run web/API containers on Container Apps or another chosen Azure compute service. Add migration jobs, managed identity, Application Insights, database backups/restore drills, and deployment automation.

Configure SMTP email-change delivery, add registration verification/password reset, moderation, data retention, and a full security/accessibility review. Configure trusted proxy client IP forwarding for per-client rate limits when Caddy sits in front of nginx. Supply live authorised inventory and decide demo data removal before public launch.

Sources: [Azure Linux VM CLI quickstart](https://learn.microsoft.com/en-us/azure/virtual-machines/linux/quick-create-cli), [Docker Engine on Ubuntu](https://docs.docker.com/engine/install/ubuntu/).

Property images persist in the property_images volume inherited from base Compose. Back it up alongside PostgreSQL; managed Azure Blob storage is not configured by this VM template.

## Verification email

The Azure overlay forces `ACCOUNT_EMAIL_MODE=smtp`, secure cookies and disabled demo logins. Configure a verified sender and SMTP secrets in the VM environment before demonstrating email changes; unconfigured delivery returns 503 and does not change the account email. Azure Communication Services Email is the recommended Azure provider. See [user management](USER-MANAGEMENT.md) for TLS ports and configuration. No mail resource is provisioned by the deployment script; real SMTP delivery and Azure runtime remain unverified.

## Updating this release

The release adds user profile/active fields and agent_profiles/email_changes/account_audit tables with additive startup migration. It also includes advanced listing metadata, price/room filters and drawn-area search. Existing databases receive nullable `features` JSON and `previous_price` columns through the compatibility migration; polygon and return-location criteria stay in existing saved-search JSON. Startup preserves existing inventory and account activity. Back up PostgreSQL and the image volume before upgrading an existing evaluation VM. A frontend-only cursor/layout change can use `docker compose -f compose.yml -f infra/compose.azure.yml up -d --build --no-deps web`. Follow [handoff](HANDOFF.md) for data preservation and [testing](TESTING.md) for checks. These changes have been exercised locally; Azure runtime remains unverified.

## Final frontend refinements

The same frontend includes visible filtered pins throughout drawing and a thin cyan hover glow on the pin matching a result card. These changes require only a web rebuild, with no database migration. They were validated against the local Docker stack; deploying the templates to Azure and real email delivery are separate operations. See [verification](VERIFICATION.md) and [handoff](HANDOFF.md) for release evidence and update commands.
