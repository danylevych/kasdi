# Deployment Guide: KaSDi on Azure AKS with CI/CD

This guide walks you through deploying the KaSDi Telegram bot to Azure Kubernetes Service (AKS) with automated CI/CD via GitHub Actions.

---

## Prerequisites

- Azure subscription
- Azure CLI installed (`az`)
- kubectl installed
- Docker (for local testing)
- GitHub repository with Actions enabled

---

## Step 1: Create Azure Resources

### 1.1 Create Resource Group
```bash
az group create \
  --name kasdi-rg \
  --location eastus
```

### 1.2 Create Azure Container Registry (ACR)
```bash
ACR_NAME=kasdiacr  # Must be globally unique, lowercase, alphanumeric only
az acr create \
  --resource-group kasdi-rg \
  --name $ACR_NAME \
  --sku Basic
```

### 1.3 Create AKS Cluster
```bash
az aks create \
  --resource-group kasdi-rg \
  --name kasdi-aks \
  --node-count 1 \
  --node-vm-size Standard_B2s \
  --enable-managed-identity \
  --attach-acr $ACR_NAME \
  --generate-ssh-keys
```

### 1.4 Get AKS Credentials
```bash
az aks get-credentials \
  --resource-group kasdi-rg \
  --name kasdi-aks \
  --overwrite-existing
```

Verify connection:
```bash
kubectl get nodes
```

---

## Step 2: Configure GitHub Secrets

Go to your GitHub repository → Settings → Secrets and variables → Actions → New repository secret

Add the following secrets:

### Azure Credentials
Create a service principal and get JSON credentials:
```bash
az ad sp create-for-rbac \
  --name "kasdi-github-actions" \
  --role contributor \
  --scopes /subscriptions/{subscription-id}/resourceGroups/kasdi-rg \
  --sdk-auth
```

Copy the JSON output and create secret:
- Name: `AZURE_CREDENTIALS`
- Value: (paste the entire JSON)

### Application Secrets
Add these secrets (from your `.env`):
- `MONGODB_URL`
- `OPENAI_API_KEY`
- `TELEGRAM_BOT_TOKEN`
- `TAVILY_API_KEY`
- `FIRE_CRAWL_API_KEY`
- `LANGSMITH_API_KEY`
- `PINECONE_API_KEY`
- `PINECONE_INDEX_NAME`

---

## Step 3: Update Kubernetes Manifests

Edit `k8s/deployment.yaml` and replace `<ACR_NAME>` with your actual ACR name:
```yaml
image: kasdiacr.azurecr.io/kasdi-bot:latest
```

---

## Step 4: Manual Initial Deployment (Optional)

Before setting up CI/CD, you can deploy manually to verify:

### 4.1 Build and Push Image to ACR
```bash
az acr login --name kasdiacr

docker build -t kasdiacr.azurecr.io/kasdi-bot:v1.0 .
docker push kasdiacr.azurecr.io/kasdi-bot:v1.0
```

### 4.2 Create Namespace
```bash
kubectl apply -f k8s/namespace.yaml
```

### 4.3 Create Secrets
```bash
kubectl create secret generic kasdi-secrets \
  --from-literal=MONGODB_URL="your-mongodb-url" \
  --from-literal=OPENAI_API_KEY="your-openai-key" \
  --from-literal=TELEGRAM_BOT_TOKEN="your-telegram-token" \
  --from-literal=TAVILY_API_KEY="your-tavily-key" \
  --from-literal=FIRE_CRAWL_API_KEY="your-firecrawl-key" \
  --from-literal=LANGSMITH_API_KEY="your-langsmith-key" \
  --from-literal=PINECONE_API_KEY="your-pinecone-key" \
  --from-literal=PINECONE_INDEX_NAME="kasdi-books" \
  --namespace=kasdi
```

### 4.4 Deploy Application
```bash
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
```

### 4.5 Check Status
```bash
kubectl get pods -n kasdi
kubectl logs -f deployment/kasdi-bot -n kasdi
```

---

## Step 5: Enable CI/CD

Once you've added GitHub Secrets (Step 2), CI/CD is automatic:

1. **Push to `main` branch** → triggers build, push to ACR, and deploy to AKS
2. **Pull Request to `main`** → triggers build and tests (no deploy)
3. **Manual trigger** → Go to Actions tab → "CI/CD to Azure AKS" → Run workflow

### Monitor Deployment
```bash
# Watch pods
kubectl get pods -n kasdi -w

# Check logs
kubectl logs -f deployment/kasdi-bot -n kasdi

# Describe pod for events
kubectl describe pod -n kasdi -l app=kasdi-bot
```

---

## Step 6: Verify Bot is Running

1. Open Telegram and find your bot: `@kasdi_book_bot`
2. Send `/start` command
3. Check logs in AKS:
```bash
kubectl logs -f deployment/kasdi-bot -n kasdi
```

You should see logs like:
```
INFO - kasdi.start_bot - Starting bot application: initializing dependencies
INFO - kasdi.database.client - Initializing MongoDB (Beanie)
INFO - kasdi.bot - Starting Telegram bot
```

---

## Step 7: Update Application

To deploy a new version:
1. Make code changes
2. Commit and push to `main` branch
3. GitHub Actions will automatically:
   - Build new image with commit SHA tag
   - Push to ACR
   - Update AKS deployment
   - Wait for rollout to complete

---

## Troubleshooting

### Pod not starting
```bash
kubectl describe pod -n kasdi -l app=kasdi-bot
kubectl logs deployment/kasdi-bot -n kasdi --previous
```

### ImagePullBackOff error
Check ACR integration:
```bash
az aks check-acr --name kasdi-aks --resource-group kasdi-rg --acr kasdiacr.azurecr.io
```

### Environment variables not loaded
```bash
kubectl get secret kasdi-secrets -n kasdi -o yaml
kubectl get configmap kasdi-config -n kasdi -o yaml
```

### View all resources
```bash
kubectl get all -n kasdi
```

### Restart deployment
```bash
kubectl rollout restart deployment/kasdi-bot -n kasdi
```

---

## Scaling (Future)

Currently, bot runs with 1 replica (Telegram polling requires single instance).

For webhook mode (future), you can scale:
```bash
kubectl scale deployment kasdi-bot --replicas=3 -n kasdi
```

---

## Cost Optimization

### Use Spot Instances
```bash
az aks nodepool add \
  --resource-group kasdi-rg \
  --cluster-name kasdi-aks \
  --name spotpool \
  --priority Spot \
  --eviction-policy Delete \
  --spot-max-price -1 \
  --node-count 1 \
  --node-vm-size Standard_B2s
```

### Auto-shutdown (Dev/Test)
Stop cluster when not in use:
```bash
az aks stop --name kasdi-aks --resource-group kasdi-rg
az aks start --name kasdi-aks --resource-group kasdi-rg
```

---

## Security Best Practices

1. **Use Azure Key Vault** for secrets instead of Kubernetes secrets:
   - Install Key Vault CSI driver
   - Reference secrets from Key Vault

2. **Enable Pod Identity** for Azure resource access

3. **Network Policies** to restrict pod communication

4. **Private AKS cluster** for production

5. **Rotate secrets regularly** via GitHub Actions

---

## Monitoring (Optional)

### Enable Azure Monitor
```bash
az aks enable-addons \
  --resource-group kasdi-rg \
  --name kasdi-aks \
  --addons monitoring
```

### View logs in Azure Portal
- Go to AKS cluster → Logs
- Query container logs

---

## Clean Up Resources

When done testing:
```bash
az group delete --name kasdi-rg --yes --no-wait
```

---

## Next Steps

- [ ] Add health check endpoint to bot
- [ ] Implement webhook mode for better scaling
- [ ] Add Horizontal Pod Autoscaler (HPA)
- [ ] Set up Azure Key Vault integration
- [ ] Configure Azure Application Insights
- [ ] Add Helm chart for easier management
