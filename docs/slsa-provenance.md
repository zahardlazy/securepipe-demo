# SLSA v1.1 Build L1 Provenance — Thiết kế & Cách kiểm chứng

> Task: Mlo Tay — Sprint 2, Week 3, Thu 16/10:
> "Implement SLSA v1.1 Build L1 provenance attestation — Provenance file generated and attached to build".
> Vị trí trong pipeline: job `build-sign` (sinh + attach), job `verify` (kiểm chứng) trong `.github/workflows/security.yml`.

---

## 1. Provenance là gì, vì sao cần cho SecurePipe

SBOM (đã có từ Week 2) trả lời *"image này chứa những gì?"*. Provenance trả lời câu hỏi khó hơn: *"image này được ai build, từ source nào, bằng workflow nào, lúc nào?"*. Với một pipeline bảo mật như SecurePipe, đó chính là bằng chứng liên kết **image trên registry** với **commit trên main** và **workflow đã chạy** — không thể giả mạo bằng cách đẩy tay một image cùng tag, vì chữ ký số không khớp.

Cụ thể trong demo: `ghcr.io/zahardlazy/securepipe-demo:sha-<commit>` luôn đi kèm một attestation nói rõ *"tôi được build từ commit X bởi workflow security.yml@refs/heads/main, runner GitHub-hosted"*. Người kiểm chứng không cần tin ai — chỉ cần kiểm chứng chữ ký.

## 2. Chuỗi thực thi trong pipeline

```
build-sign job
 1. docker build + push GHCR (provenance: false)     ← build
 2. cosign sign (keyless)                            ← ký image
 3. generate_provenance.sh → slsa-provenance.json    ← sinh predicate
 4. cosign attest --type slsaprovenance1             ← attach attestation
 5. upload slsa-provenance.json (artifact)           ← bằng chứng

verify job
 6. cosign verify                                    ← kiểm chứng chữ ký image
 7. cosign verify-attestation --type slsaprovenance1 ← kiểm chứng provenance
 8. upload attestation-verified.json (artifact)      ← đầu ra để đối chiếu
```

## 3. Vì sao chọn `--type slsaprovenance1`

Predicate type chuẩn của SLSA v1 là URI `https://slsa.dev/provenance/v1`. Cosign hỗ trợ tên ngắn cho từng loại predicate — đã đối chiếu trực tiếp source code của cosign (`pkg/cosign/attestation/attestation.go` + `cmd/cosign/cli/options/predicate.go`):

- `slsaprovenance` → `https://slsa.dev/provenance/v0.2` (**schema cũ — không dùng**)
- `slsaprovenance1` → `https://slsa.dev/provenance/v1` ✅ (đồng thời cosign **validate schema** predicate trước khi ký — 2 trường bắt buộc `buildDefinition`, `runDetails` phải đủ)
- URI đầy đủ cũng được chấp nhận, nhưng tên ngắn + validation là lựa chọn an toàn hơn.

Kết quả: attestation sinh ra là một **in-toto Statement** bọc trong **DSSE envelope**, `predicateType = https://slsa.dev/provenance/v1`.

## 4. Nội dung predicate (file sinh bởi `.github/scripts/generate_provenance.sh`)

| Trường | Giá trị | Ý nghĩa |
|---|---|---|
| `buildDefinition.buildType` | URI workflow (`...security.yml@refs/heads/main`) | "Template" build chính là workflow này |
| `buildDefinition.externalParameters` | repository, ref, image (kèm digest), trigger, sender | Đầu vào **không tin cậy** từ bên ngoài — downstream phải kiểm tra |
| `buildDefinition.internalParameters` | runner, run id, run attempt | Bối cảnh nội bộ của platform |
| `buildDefinition.resolvedDependencies` | git commit SHA của source | Liên kết artifact ↔ source |
| `runDetails.builder.id` | URI workflow | Chủ thể build (danh tính ký số khớp với cái này) |
| `runDetails.metadata` | invocationID (URL run), startedOn/finishedOn | Lần chạy cụ thể nào |

Lưu ý kỹ thuật: `subject` (image + digest) không nằm trong predicate — **cosign tự gắn** khi thực hiện attest, dựa trên tham số image truyền vào. Đây là điểm dễ nhầm khi viết tay provenance.

## 5. Vì sao đây là Build **L1** (và không thổi phầm lên L2/L3)

SLSA định nghĩa các mức theo độ tin cậy của provenance:

- **L1 — Provenance tồn tại**: có bản ghi, sinh ra trong quá trình build. ✅ đạt.
- **L1+ (mục tiêu của thiết kế này)**: provenance **được ký bởi danh tính của build platform** (keyless cert của workflow qua Fulcio/Sigstore) — đúng tinh thần "signed by hosted build service" của L2.
- **L2** đòi hỏi build platform có mô hình cô lập rõ ràng giữa các tenant. GitHub Actions *tiếp cận* nhưng chưa có cam kết chính thức về definition này — vì vậy doc này **không claim L2**.
- **L3** đòi hỏi build không thể bị ảnh hưởng bởi trạng thái trước đó (hardened, ephemeral). Không claim.

Cách nói chuyện đúng cho demo: *"SecurePipe sinh provenance theo schema SLSA v1.1, ký keyless bởi danh tính workflow — thỏa mãn Build L1 và theo tinh thần L2 về chữ ký; chưa claim mức cô lập của L3."*

## 6. Cách kiểm chứng bằng tay (ngoài pipeline)

```bash
docker login ghcr.io -u <user>
cosign verify \
  --certificate-identity-regexp '^https://github\.com/zahardlazy/securepipe-demo/\.github/workflows/security\.yml@.*$' \
  --certificate-oidc-issuer https://token.actions.githubusercontent.com \
  ghcr.io/zahardlazy/securepipe-demo@sha256:<digest>

cosign verify-attestation \
  --type slsaprovenance1 \
  --certificate-identity-regexp '^https://github\.com/zahardlazy/securepipe-demo/\.github/workflows/security\.yml@.*$' \
  --certificate-oidc-issuer https://token.actions.githubusercontent.com \
  ghcr.io/zahardlazy/securepipe-demo@sha256:<digest>
```

Hai regexp ở trên là "họ khóa" của pipeline: chỉ chữ ký được ký bởi **đúng workflow này của đúng repo này** mới được chấp nhận. Một image bị đẩy tay lên registry (kể cả cùng tag) sẽ không có chữ ký khớp → `verify` thất bại → demo kịch bản "unsigned image bị từ chối" cho test case của Phúc.

## 7. Việc để Sprint 3

- Cân nhắc `slsa-framework/slsa-github-generator` (provenance sinh bởi reusable workflow riêng — độc lập hơn về mức tin cậy, hướng tới L3).
- Đưa digest + invocationID vào release notes mỗi lần deploy.
- Ky thêm SBOM attestation (`cosign attest --type cyclonedx`) để SBOM cũng gắn với image theo cơ chế signature thay vì chỉ artifact.
