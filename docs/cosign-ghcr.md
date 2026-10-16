# Cosign Keyless + GHCR — Quyết định kỹ thuật Week 3

> Task liên quan: Mlo Tay — Sprint 2 W2 (Thu/Fri: OIDC cho Cosign, "Begin Cosign keyless signing setup", "Debug OIDC permission issues") hoàn tất tại W3 (Mon/Tue/Wed).
> Doc này ghi lại: (1) OIDC hoạt động thế nào cho Cosign keyless, (2) vì sao tạm dùng GHCR thay ECR, (3) đường chuyển sang ECR khi infra của The sẵn sàng.

---

## 1. OIDC cho Cosign keyless — "permission" đã chạy đúng

Vấn đề của Week 2 (task Fri "Debug OIDC permission issues for Cosign — `id-token: write` working, no permission errors") được đóng gọn trong 1 khối `permissions` của job `build-sign`:

```yaml
build-sign:
  permissions:
    contents: read
    packages: write   # đẩy image + signature lên GHCR
    id-token: write   # xin OIDC token của workflow — BẮT BUỘC cho keyless
```

Ba điểm đã kiểm chứng khi thiết kế:

1. **Thiếu `id-token: write` thì cosign keyless nhận lỗi kiểu** `no credential available` / `getting key from fulcio: ...` — vì không xin được JWT ngắn hạn của workflow. Đây chính là "OIDC permission issue" mà task đề cập.
2. Token chỉ cấp cho job có quyền trên; giới hạn ở đúng job cần (build-sign) — job khác giữ `contents: read`.
3. Danh tính trong cert (SAN) có dạng `https://github.com/zahardlazy/securepipe-demo/.github/workflows/security.yml@refs/heads/main` — đây là chuỗi mà bước `verify` khóa bằng `--certificate-identity-regexp`. Nghiên cứu nền tảng nằm ở `docs/oidc-notes.md` (Week 1).

Cơ chế: workflow xin JWT từ GitHub OIDC provider → cosign dùng JWT xin cert ngắn hạn từ Fulcio → ký → chữ ký + cert được ghi lên registry (và Transparency Log Rekor). Không có key nào phải lưu, xoay vòng, hay lộ trong secrets.

## 2. Vì sao GHCR, không phải ECR (quyết định 16/10)

Milestone Week 3 ghi *"Signed image pushed to ECR"*. Thực tế repo tại 16/10:

| Điều kiện ECR cần | Trạng thái repo |
|---|---|
| IAM role tin GitHub OIDC (task W2 của The) | Chưa thấy trong repo (chưa có file Terraform nào) |
| ECR repository tồn tại | Chưa có |
| Credentials/role ARN cấu hình cho workflow | Chưa có |

→ Nếu ghim ECR ngay, pipeline sign+verify sẽ **đỏ vô hạn** vì thiếu hạ tầng — sai với tinh thần milestone *"end-to-end sign+verify runs green in Actions"*.

**Quyết định:** dùng **GHCR** (`ghcr.io/zahardlazy/securepipe-demo`) — registry có sẵn, xác thực bằng chính `GITHUB_TOKEN`, không cần setup gì thêm. Milestone "signed image + verified in pipeline" được thỏa **đủ chất** (ký keyless, verify keyless, provenance attach) trên hạ tầng chạy được ngay. ECR là thay đổi "chuyển địa chỉ", không phải thay đổi logic (xem mục 3).

Lưu ý vận hành GHCR: lần đẩy đầu tiên tạo package **private**. Job `verify` đọc được nhờ `packages: read` của `GITHUB_TOKEN` (package sinh ra từ repo này được liên kết repo). Nếu muốn demo verify từ máy ngoài mà không login → đổi package thành public trong Settings → Packages.

## 3. Đường chuyển sang ECR (khi The hoàn tất infra)

Bước 1 — Terraform (The): IAM role tin `token.actions.githubusercontent.com` + điều kiện `sub` theo repo, policy tối thiểu cho ECR (`ecr:PutImage`, `BatchGetImage`...), kèm ECR repo.

Bước 2 — Thêm 2 secrets repo: `AWS_ROLE_ARN` (và region nếu cần).

Bước 3 — Trong job `build-sign`, thay bước login GHCR bằng:

```yaml
      - name: Configure AWS credentials (OIDC — khong can access key)
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ secrets.AWS_ROLE_ARN }}
          aws-region: ap-southeast-1

      - name: Login to ECR
        uses: aws-actions/amazon-ecr-login@v2
```

và đổi tag `ghcr.io/${{ github.repository }}:...` thành URI ECR (lấy từ output Terraform của The). Các bước `cosign sign / attest / verify` giữ nguyên — **cosign ký theo digest, chẳng quan tâm registry nào**; chỉ cần `verify` login đúng registry.

Bước 4 — GHCR giữ làm mirror dự phòng 1–2 sprint cho kịch bản AWS lỗi (tùy The đánh giá chi phí lưu trữ).

## 4. Quy ước đã chốt cho pipeline

- **Ký digest, không ký tag** (`image@sha256:...`) — tag mutable có thể bị re-point; digest là bất biến.
- **Verify khóa chặt danh tính**: `--certificate-identity-regexp` chỉ đúng workflow `security.yml` của repo này. Không dùng matching rộng (ví dụ `.*`) — mất toàn bộ ý nghĩa của verify.
- **Tắt attestation mặc định của buildx** (`provenance: false`) vì buildx gắn SLSA **v0.2** (schema cũ); pipeline tự sinh SLSA **v1.1** bằng `cosign attest` (xem `docs/slsa-provenance.md`).
- Image chỉ build+push trên **main** và **workflow_dispatch** — PR không sinh image (build PR chỉ smoke-test trong workflow Build Image của Phuc).
