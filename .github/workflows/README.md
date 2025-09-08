# GitHub Actions Workflows

This directory contains GitHub Actions workflows for automated CI/CD processes.

## Workflows

### CI Pipeline (`ci-pipeline.yml`)

**Triggers:**
- Push to `main` or `develop` branches
- Pull requests to `main` branch

**Features:**
- 🐳 **Multi-platform Docker builds** (linux/amd64, linux/arm64)
- 🧪 **Automated testing** with dummy data
- 🔒 **Trivy vulnerability scanning** (SARIF + table format)
- 📦 **GitHub Container Registry** publishing
- 💬 **PR comments** with scan results
- 🏷️ **Smart tagging** (branch, PR, SHA-based)
- 📊 **Security summaries** in GitHub Actions

**Jobs:**
1. **build-and-test**: Builds Docker image and runs functional tests
2. **security-scan**: Performs comprehensive security scanning

## Security Features

### Trivy Scanning
- **Vulnerability Types**: OS packages, application libraries
- **Severity Levels**: CRITICAL, HIGH, MEDIUM
- **Output Formats**: SARIF (GitHub Security tab), Table (artifacts)
- **Scanners**: Vulnerability scanner, secret scanner

### GitHub Integration
- **Security Tab**: SARIF results uploaded to GitHub Security
- **PR Comments**: Automatic scan results in pull requests
- **Artifacts**: Scan results stored as downloadable artifacts
- **Summaries**: Security summaries in workflow runs

## Usage

### Manual Trigger
You can manually trigger the workflow from the GitHub Actions tab:
1. Go to the "Actions" tab in your repository
2. Select "CI Pipeline" workflow
3. Click "Run workflow"

### Environment Variables
The workflow uses the following environment variables:
- `GITHUB_TOKEN`: Automatically provided by GitHub
- `REGISTRY`: Set to `ghcr.io` (GitHub Container Registry)
- `IMAGE_NAME`: Automatically set to `{owner}/{repo}/home-assistant-temperature-web`

### Container Registry
Images are automatically pushed to GitHub Container Registry:
- **Latest**: `ghcr.io/{owner}/{repo}/home-assistant-temperature-web:latest`
- **Branch**: `ghcr.io/{owner}/{repo}/home-assistant-temperature-web:{branch}`
- **SHA**: `ghcr.io/{owner}/{repo}/home-assistant-temperature-web:{sha}`

## Troubleshooting

### Common Issues

1. **Build Failures**
   - Check Dockerfile syntax
   - Verify all dependencies are available
   - Review build logs for specific errors

2. **Test Failures**
   - Ensure the application starts correctly
   - Check environment variables
   - Verify port mappings

3. **Security Scan Issues**
   - Review Trivy scan results
   - Check for false positives
   - Update base images if needed

### Debugging

1. **Enable Debug Logging**
   Add this to your workflow step:
   ```yaml
   - name: Debug
     run: |
       echo "Debug information"
       docker images
       docker ps -a
   ```

2. **Check Artifacts**
   - Download scan results from the Actions tab
   - Review SARIF files in GitHub Security tab

3. **Local Testing**
   ```bash
   # Build locally
   docker build -t test-image .
   
   # Run Trivy locally
   docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
     aquasec/trivy image test-image
   ```

## Best Practices

1. **Regular Updates**: Keep base images and dependencies updated
2. **Review Scans**: Regularly review security scan results
3. **Monitor Failures**: Set up notifications for workflow failures
4. **Document Changes**: Update this README when modifying workflows

## Support

For issues with these workflows:
1. Check the GitHub Actions logs
2. Review the troubleshooting section
3. Create an issue in the repository
4. Check GitHub Actions documentation
