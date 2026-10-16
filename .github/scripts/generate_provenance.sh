#!/usr/bin/env bash
# ============================================================================
# Generate SLSA v1.1 provenance predicate cho image build (Sprint 2, Week 3).
# Task (Thu 16/10): "Implement SLSA v1.1 Build L1 provenance attestation".
#
# Cach dung (goi tu job build-sign trong security.yml):
#   .github/scripts/generate_provenance.sh \
#       "ghcr.io/zahardlazy/securepipe-demo@sha256:..." "2026-10-16T08:00:00Z"
#
# Output: slsa-provenance.json (predicate theo schema https://slsa.dev/provenance/v1)
# Sau do workflow chay:
#   cosign attest --type slsaprovenance1 --predicate slsa-provenance.json ...
#
# Ve "Build L1": provenance duoc tao BOI build platform (GitHub Actions runner),
# ky bang identity tam thoi cua chinh workflow do (Cosign keyless + Fulcio),
# nen dap ung yeu cau "provenance exists + signed by builder" cua SLSA Build L1.
# Chi tiet: docs/slsa-provenance.md
# ============================================================================
set -euo pipefail

IMAGE_REF="${1:?usage: generate_provenance.sh <image-ref-with-digest> <started-on-RFC3339>}"
STARTED_ON="${2:?usage: generate_provenance.sh <image-ref-with-digest> <started-on-RFC3339>}"

# Bien GITHUB_* do GitHub Actions cung cap san trong moi job.
REPO_SLUG="${GITHUB_REPOSITORY:?GITHUB_REPOSITORY chua duoc set}"
GIT_SHA="${GITHUB_SHA:?GITHUB_SHA chua duoc set}"
REF="${GITHUB_REF:?GITHUB_REF chua duoc set}"
RUN_ID="${GITHUB_RUN_ID:?GITHUB_RUN_ID chua duoc set}"
RUN_ATTEMPT="${GITHUB_RUN_ATTEMPT:-1}"
EVENT_NAME="${GITHUB_EVENT_NAME:-unknown}"
ACTOR="${GITHUB_ACTOR:-unknown}"
# VD: "zahardlazy/securepipe-demo/.github/workflows/security.yml@refs/heads/main"
WORKFLOW_REF="${GITHUB_WORKFLOW_REF:?GITHUB_WORKFLOW_REF chua duoc set}"

FINISHED_ON="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

# builder.id / buildType: URI workflow chinh la noi build chay — theo khuyen nghi
# "index of build types" cua SLSA nen dat ten buildType theo URI workflow.
jq -n \
  --arg build_type "https://github.com/${WORKFLOW_REF}" \
  --arg builder_id "https://github.com/${WORKFLOW_REF}" \
  --arg repo_slug "${REPO_SLUG}" \
  --arg repo_uri "git+https://github.com/${REPO_SLUG}" \
  --arg ref "${REF}" \
  --arg image "${IMAGE_REF}" \
  --arg trigger "${EVENT_NAME}" \
  --arg sender "${ACTOR}" \
  --arg run_id "${RUN_ID}" \
  --arg run_attempt "${RUN_ATTEMPT}" \
  --arg sha "${GIT_SHA}" \
  --arg started "${STARTED_ON}" \
  --arg finished "${FINISHED_ON}" \
  '{
    buildDefinition: {
      buildType: $build_type,
      externalParameters: {
        repository: $repo_uri,
        ref: $ref,
        image: $image,
        trigger: $trigger,
        sender: $sender
      },
      internalParameters: {
        runner: "github-hosted-ubuntu-latest",
        githubRunId: $run_id,
        githubRunAttempt: $run_attempt
      },
      resolvedDependencies: [
        {
          name: "source",
          uri: $repo_uri,
          digest: { gitCommit: $sha }
        }
      ]
    },
    runDetails: {
      builder: { id: $builder_id },
      metadata: {
        invocationID: ("https://github.com/" + $repo_slug + "/actions/runs/" + $run_id + "/attempts/" + $run_attempt),
        startedOn: $started,
        finishedOn: $finished
      }
    }
  }' > slsa-provenance.json

# Sanity check: 2 truong bat buoc cua schema v1 phai ton tai
jq -e '.buildDefinition.buildType and .runDetails.builder.id' slsa-provenance.json > /dev/null

echo "=== slsa-provenance.json (SLSA v1.1) ==="
cat slsa-provenance.json
