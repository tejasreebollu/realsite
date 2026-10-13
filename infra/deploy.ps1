# Evaluation deployment. Running this script creates billable Azure resources.
[CmdletBinding()]
param(
    [Parameter(Mandatory)][ValidatePattern('^[a-zA-Z0-9_-]+$')][string]$ResourceGroup,
    [string]$Location = 'centralindia',
    [ValidatePattern('^[a-zA-Z0-9-]{1,50}$')][string]$VmName = 'realsite-india-vm',
    [string]$VmSize = 'Standard_B2s',
    [Parameter(Mandatory)][ValidatePattern('^([a-zA-Z0-9](?:[a-zA-Z0-9-]*[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$')][string]$Domain,
    [Parameter(Mandatory)][string]$AdminCidr,
    [Parameter(Mandatory)][string]$SshPublicKeyPath,
    [Parameter(Mandatory)][string]$SshPrivateKeyPath
)
$ErrorActionPreference = 'Stop'
$repoPath = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$publicKeyPath = (Resolve-Path -LiteralPath $SshPublicKeyPath).Path
$privateKeyPath = (Resolve-Path -LiteralPath $SshPrivateKeyPath).Path
$adminParts = $AdminCidr.Split('/')
$adminAddress = $null
if ($adminParts.Length -ne 2 -or -not [System.Net.IPAddress]::TryParse($adminParts[0], [ref]$adminAddress) -or $adminAddress.AddressFamily -ne [System.Net.Sockets.AddressFamily]::InterNetwork -or [int]$adminParts[1] -lt 24 -or [int]$adminParts[1] -gt 32) {
    throw 'AdminCidr must be a restricted IPv4 CIDR with a prefix between /24 and /32.'
}
foreach ($name in 'az', 'ssh', 'scp', 'tar') { if (-not (Get-Command $name -ErrorAction SilentlyContinue)) { throw "Missing command: $name" } }
function Assert-Native([string]$Action) { if ($LASTEXITCODE -ne 0) { throw "$Action failed (exit $LASTEXITCODE)." } }
$account = az account show --query id -o tsv
Assert-Native 'Azure sign-in check'
Write-Host "Creating evaluation resources in subscription $account, resource group $ResourceGroup."
az group create --name $ResourceGroup --location $Location --output none
Assert-Native 'Resource group creation'
$publicKey = (Get-Content -LiteralPath $publicKeyPath -Raw).Trim()
$parameters = @{ location = @{ value = $Location }; vmName = @{ value = $VmName }; vmSize = @{ value = $VmSize }; sshPublicKey = @{ value = $publicKey }; adminCidr = @{ value = $AdminCidr } }
$artifactPath = Join-Path $repoPath 'artifacts'
New-Item -ItemType Directory -Path $artifactPath -Force | Out-Null
$parametersPath = Join-Path $artifactPath 'azure.parameters.json'
@{ '$schema' = 'https://schema.management.azure.com/schemas/2019-04-01/deploymentParameters.json#'; contentVersion = '1.0.0.0'; parameters = $parameters } | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $parametersPath -Encoding utf8
$deployment = az deployment group create --resource-group $ResourceGroup --template-file (Join-Path $PSScriptRoot 'main.bicep') --parameters "@$parametersPath" --query properties.outputs -o json
Assert-Native 'VM deployment'
$portalIp = ($deployment | ConvertFrom-Json).publicIpAddress.value
Write-Host "VM address: $portalIp. Point $Domain A record to this address before browsing."
$randomBytes = New-Object byte[] 32
$rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
$rng.GetBytes($randomBytes)
$rng.Dispose()
$databasePassword = ([System.BitConverter]::ToString($randomBytes)).Replace('-', '').ToLowerInvariant()
$azureEnvPath = Join-Path $artifactPath 'azure.env'
$azureEnv = "COMPOSE_PROJECT_NAME=realsite-india`nPOSTGRES_USER=portal`nPOSTGRES_PASSWORD=$databasePassword`nPOSTGRES_DB=portal`nCOOKIE_SECURE=true`nSEED_DEMO=false`nPORTAL_DOMAIN=$Domain`n"
# Do not overwrite deployment secrets on subsequent runs; preserve the DB credentials.
if (-not (Test-Path -LiteralPath $azureEnvPath)) { [System.IO.File]::WriteAllText($azureEnvPath, $azureEnv) }
$packagePath = Join-Path $artifactPath 'portal.tar.gz'
tar -czf $packagePath -C $repoPath compose.yml frontend backend infra data/azure-postgres-bootstrap.sql
Assert-Native 'Source package creation'
$sshTarget = "azureuser@$portalIp"
Write-Host 'SSH will ask you to verify the new VM host fingerprint on first connection.'
ssh -i $privateKeyPath $sshTarget 'sudo cloud-init status --wait && mkdir -p ~/portal'
Assert-Native 'VM Docker setup'
scp -i $privateKeyPath $packagePath "${sshTarget}:portal/portal.tar.gz"
Assert-Native 'Source upload'
scp -i $privateKeyPath $azureEnvPath "${sshTarget}:portal/.env"
Assert-Native 'Environment upload'
ssh -i $privateKeyPath $sshTarget 'cd ~/portal && chmod 600 .env && tar -xzf portal.tar.gz && sudo docker compose -f compose.yml -f infra/compose.azure.yml up -d --build && sudo docker compose -f compose.yml -f infra/compose.azure.yml exec -T db sh -c '"'"'psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB"'"'"' < data/azure-postgres-bootstrap.sql'
Assert-Native 'Portal startup'
Write-Host "Deployment started. After DNS propagates, open https://$Domain."
Write-Host 'Keep artifacts/azure.env private and backed up. This single-VM topology is for evaluation; see docs/AZURE.md.'
