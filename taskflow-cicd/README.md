# TaskFlow CI/CD Pipeline

A small task-management REST API (Flask) used as the workload for an
end-to-end, security-gated CI/CD pipeline: **Jenkins → SonarQube → Trivy →
Docker → Kubernetes**.

This repo is the working implementation behind the "Independent DevOps
Contributor" project on my resume: a business web app deployed through a
fully automated, secure delivery pipeline, eliminating manual release steps.

## Architecture

```
Developer push
      │
      ▼
┌─────────────┐     ┌───────────────┐     ┌─────────────┐
│   Jenkins   │────▶│   SonarQube   │────▶│    Trivy    │
│  (checkout, │     │ static code   │     │  container  │
│  unit tests)│     │   analysis    │     │  vuln scan  │
└─────────────┘     └───────────────┘     └──────┬──────┘
                                                   │ pass
                                                   ▼
                                          ┌─────────────────┐
                                          │  Docker build    │
                                          │  & push to       │
                                          │  registry         │
                                          └────────┬────────┘
                                                   │
                                                   ▼
                                          ┌─────────────────┐
                                          │   Kubernetes     │
                                          │  rolling deploy   │
                                          │  (3 replicas)     │
                                          └─────────────────┘
```

The pipeline fails fast at any gate: broken tests, a failed SonarQube quality
gate, or a HIGH/CRITICAL vulnerability found by Trivy all stop the build
before a bad image ever reaches Kubernetes.

## What's in this repo

| Path | Purpose |
|---|---|
| `app/app.py` | Flask API: `/health`, `/tasks` (CRUD) |
| `app/tests/` | Pytest unit tests, run by Jenkins on every build |
| `Dockerfile` | Multi-stage build, non-root user, built-in healthcheck |
| `Jenkinsfile` | Declarative pipeline: test → scan → build → scan image → push → deploy |
| `sonar-project.properties` | SonarQube static analysis config |
| `k8s/deployment.yaml` | Rolling-update deployment, readiness/liveness probes, resource limits |
| `k8s/service.yaml` | ClusterIP service exposing the app inside the cluster |
| `k8s/configmap.yaml` | Non-secret runtime config |

## Pipeline stages

1. **Checkout** — pulls the repo from source control.
2. **Unit tests** — `pytest` against the Flask app; results published as JUnit XML.
3. **SonarQube static analysis** — scans `app/` for code smells, bugs, and security hotspots.
4. **Quality gate** — pipeline aborts if SonarQube's gate fails.
5. **Docker build** — multi-stage build, non-root runtime user.
6. **Trivy image scan** — fails the build on any HIGH or CRITICAL CVE in the image.
7. **Push** — tagged image pushed to the container registry.
8. **Deploy** — `kubectl apply` with a rolling update (`maxUnavailable: 0`) for zero-downtime releases.

## Running it locally

```bash
# App only
cd app
pip install -r requirements.txt
python app.py                     # http://localhost:5000/health

# Tests
pytest tests/

# Container
docker build -t taskflow-api:local .
docker run -p 5000:5000 taskflow-api:local

# Kubernetes (kind/minikube)
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl port-forward svc/taskflow-api 8080:80
```

## Jenkins setup notes

The `Jenkinsfile` expects these credentials to be configured in
**Jenkins → Manage Jenkins → Credentials**:

- `dockerhub-creds` — username/password for the container registry
- `sonarqube-token` — SonarQube auth token
- `kubeconfig-file` — kubeconfig for the target cluster

And a SonarQube server named `sonarqube-server` configured under
**Manage Jenkins → System → SonarQube servers**.

## Why these choices

- **Non-root container user** — reduces blast radius if the container is
  compromised; also flagged as a best practice by most image scanners.
- **Rolling update with `maxUnavailable: 0`** — guarantees zero-downtime
  deploys, matching the blue-green/rolling strategy used in production at
  my previous role.
- **Security gates before deploy, not after** — shifting SonarQube/Trivy
  left in the pipeline means vulnerable code and images never reach the
  cluster, rather than being caught post-deployment.

## Roadmap / possible extensions

- [ ] Add ArgoCD for GitOps-based deployment instead of `kubectl apply` from Jenkins
- [ ] Add Prometheus/Grafana manifests for monitoring the deployed service
- [ ] Terraform module to provision the EKS cluster this deploys to (see companion repo: `taskflow-infra`)
