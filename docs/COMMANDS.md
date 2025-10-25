# KaSDi - Quick Commands Reference

## Local Development
```bash
# Setup
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # Edit with your values

# Run bot
cd kasdi
python start_bot.py
```

## Docker
```bash
# Build
docker build -t kasdi-bot:latest .

# Run locally
docker run --rm -it --env-file ./.env kasdi-bot:latest

# With volume mount for development
docker run --rm -it \
  --env-file ./.env \
  -v $(pwd)/kasdi:/app/kasdi \
  kasdi-bot:latest
```

## Azure AKS

### Initial Setup
```bash
# Login
az login

# Create resources
az group create --name kasdi-rg --location eastus
az acr create --resource-group kasdi-rg --name kasdiacr --sku Basic
az aks create --resource-group kasdi-rg --name kasdi-aks --node-count 1 --attach-acr kasdiacr

# Get credentials
az aks get-credentials --resource-group kasdi-rg --name kasdi-aks
```

### Deploy
```bash
# Build and push
az acr login --name kasdiacr
docker build -t kasdiacr.azurecr.io/kasdi-bot:latest .
docker push kasdiacr.azurecr.io/kasdi-bot:latest

# Apply manifests
kubectl apply -f k8s/namespace.yaml
kubectl create secret generic kasdi-secrets --from-env-file=./.env -n kasdi
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/deployment.yaml
```

### Monitor
```bash
# Watch pods
kubectl get pods -n kasdi -w

# Logs
kubectl logs -f deployment/kasdi-bot -n kasdi

# Describe
kubectl describe deployment kasdi-bot -n kasdi
```

### Update
```bash
# Rebuild and push
docker build -t kasdiacr.azurecr.io/kasdi-bot:v1.1 .
docker push kasdiacr.azurecr.io/kasdi-bot:v1.1

# Update deployment
kubectl set image deployment/kasdi-bot kasdi-bot=kasdiacr.azurecr.io/kasdi-bot:v1.1 -n kasdi
kubectl rollout status deployment/kasdi-bot -n kasdi
```

### Troubleshoot
```bash
# Pod issues
kubectl describe pod -n kasdi -l app=kasdi-bot
kubectl logs deployment/kasdi-bot -n kasdi --previous

# Restart
kubectl rollout restart deployment/kasdi-bot -n kasdi

# Debug with shell
kubectl exec -it deployment/kasdi-bot -n kasdi -- /bin/bash
```

## GitHub Actions CI/CD

Push to `main` branch automatically:
1. Builds Docker image
2. Pushes to ACR with commit SHA tag
3. Updates AKS deployment
4. Waits for rollout completion

View in: Repository → Actions tab

## Useful Kubernetes Commands
```bash
# Get all resources
kubectl get all -n kasdi

# Delete deployment
kubectl delete deployment kasdi-bot -n kasdi

# Scale (future webhook mode)
kubectl scale deployment kasdi-bot --replicas=2 -n kasdi

# Port forward (if service exposed)
kubectl port-forward svc/kasdi-bot-service 8080:8080 -n kasdi

# View events
kubectl get events -n kasdi --sort-by='.lastTimestamp'
```

## Clean Up
```bash
# Delete AKS resources
az group delete --name kasdi-rg --yes --no-wait

# Remove local docker images
docker rmi kasdiacr.azurecr.io/kasdi-bot:latest
```
