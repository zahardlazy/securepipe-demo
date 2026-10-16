# Sprint 2 — Week 3 Retrospective

> Tuần 3: 12/10 – 18/10/2026 · Milestone day: **Wed 14/10**
> Người viết: Mlo Tay (kiêm Hieu) · Ngày: 16/10 (dự kiến chốt Sunday 18/10 sau standup)

---

## 1. Việc đã hoàn thành (Mlo Tay)

| Ngày | Task | Trạng thái | Bằng chứng |
|---|---|---|---|
| Thu 09/10 (dồn sang W3) | Cosign keyless setup + OIDC debug | ✅ | Job `build-sign` (`id-token: write`), `docs/cosign-ghcr.md` mục 1 |
| Mon 12/10 | Cosign signing step post-build | ✅ | `cosign sign` theo digest trong `build-sign` |
| Mon 12/10 | Configure Checkov cho Terraform | ✅ | Job `checkov` + `infra/main.tf` + `docs/checkov-local-scan.json` |
| Tue 13/10 | cosign verify trong CI | ✅ | Job `verify` (verify + verify-attestation) |
| Tue 13/10 | Fix/triage Checkov findings | ✅ | `docs/false-positives-week3.md` mục 5 (1 FP có bằng chứng nguồn) |
| **Wed 14/10** | **MILESTONE: sign+verify xanh end-to-end** | ✅* | Pipeline GHCR (xem ghi chú mục 3.1) |
| **Wed 14/10** | **MILESTONE: Checkov SARIF lên Security tab** | ✅ | Job `checkov` + `upload-sarif` (cùng cơ chế cho semgrep/trivy) |
| Thu 15/10 | SLSA v1.1 Build L1 provenance | ✅ | `generate_provenance.sh` + `cosign attest` + `docs/slsa-provenance.md` |
| Thu 15/10 | Tune Quality Gate thresholds | ✅ | `docs/quality-gate.md` (bảng ngưỡng đã chốt) |
| Fri 16/10 | Quality Gate logic (Critical → fail) | ✅ | Job `quality-gate` + `.github/scripts/quality_gate.py` (test 3 kịch bản) |
| Fri 16/10 | False-positive review 4 tools | ✅ | `docs/false-positives-week3.md` — sửa 1 lỗi triage Trivy |
| Sun 18/10 | Retro + Week 4 plan | ✅ | File này (mục 4) |
| Sun 18/10 | Demo script (security) | ✅ | `docs/demo-script-security.md` |
| Sun 18/10 | *(dồn từ W2)* Checkov prep | ✅ | Gộp vào task Mon W3 |

### Việc đội bạn liên quan (không thuộc scope Mlo)

- Phuc (16/10): Dockerfile (PR #17) + workflow Build Image smoke test (PR #18) — input trực tiếp cho Stage 3 của mình; xuất hiện 1 finding ERROR mới (`missing-user`) → đã triage baseline.
- The: infra Terraform (VPC/ECR/IAM/ECS) **chưa lên repo** tại 16/10 → mình tạo `infra/main.tf` placeholder để Checkov có target (đã đánh dấu rõ để The thay thế).

## 2. Phát hiện đáng chú ý (lessons learned)

1. **Trigger workflow có lỗi chính tả từ Sprint trước**: `branches: ain]` (thiếu `[m`) trong cả `security.yml` lẫn `build-image.yml`. Workflow vẫn chạy (GitHub dường như lơ thấy pattern không hợp lệ) nhưng đây là nợ kỹ thuật — đã sửa `security.yml` thành `[main]` trong PR này; **`build-image.yml` của Phuc cần Phuc sửa tương tự**.
2. **Hiểu nhầm `Status: fixed` của Trivy** dẫn đến xoá nhầm `CVE-2018-18074` khỏi `.trivyignore` (30/09). `fixed` = có bản vá, không phải "không còn áp dụng". Đã khôi phục + ghi lý do. Bài học: không dọn ignore entry khi chưa quét lại thấy finding biến mất.
3. **Checkov CKV_AWS_51 là false positive thật** — check đọc sai tên attribute (`image_tag_mutability` thay vì `image_tag_immutability`). Lần đầu team có bằng chứng FP của chính scanner (nguồn check + output evaluated_keys). Giá trị demo cao: "scanner cũng cần được kiểm chứng".
4. **Gitleaks bắt cả placeholder đã redacted** (dòng 10 app.py) vì pattern khớp theo tên biến — reminder rằng fingerprint-based ignore vẫn cần thiết kể cả khi giá trị không còn "như key thật".

## 3. Quyết định kỹ thuật tuần này

### 3.1. GHCR thay ECR cho milestone "signed image pushed to ECR"

Milestone ghi ECR, nhưng repo chưa có IAM role OIDC + ECR (infra của The chưa lên). Ghim ECR = pipeline đỏ vô hạn, sai tinh thần *"runs green in Actions"*. Quyết định: **GHCR ngay** (GITHUB_TOKEN, zero setup), kèm doc đường chuyển ECR 4 bước (`docs/cosign-ghcr.md` mục 3) — cosign ký theo digest nên việc chuyển registry không đổi logic ký/xác minh. Đây là điểm **cần nói rõ với mentor trong demo** để tránh hiểu lầm là "làm lệch milestone".

### 3.2. Baseline-based gate thay vì `--error` cứng

`semgrep --error` không phân biệt finding đã triage — mọi push đều đỏ vì app demo cố ý chứa lỗi. Gate đọc JSON + đối chiếu `docs/accepted-findings.json` (fingerprint + lý do + hạn review): finding cũ đã triage thì qua, finding **mới** thì chặn. Đây là mô hình triage bền vững hơn cho Sprint 3 (khi xoá seed thì baseline tự rỗng dần).

### 3.3. Pin phiên bản semgrep/checkov trong CI

`pip install semgrep==1.181.0` / `checkov==3.3.29` — cùng bản đã kiểm chứng local cùng baseline. Tránh cảnh "rule mới tự rơi xuống pipeline giữa sprint" (đã từng xảy ra với trivy DB). Nâng cấp có chủ đích, kèm re-triage; đóng góp phần cho task Week 4 "Ruleset frozen for demo stability".

## 4. Plan Week 4 (19–22/10, sprint kết thúc Thu)

Việc của Mlo Tay theo tracker + rút ra từ tuần này:

| Ngày | Việc | Ghi chú |
|---|---|---|
| Mon | Final integration pass 5 stage, fix bug còn lại | Chạy `workflow_dispatch` dry-run; rà cả workflow Build Image của Phuc (trigger typo) |
| Mon | Final scan tuning, đóng băng ruleset | Giữ pin 1.181.0/3.3.29; rà baseline hết hạn review_by 22/10 |
| Tue | Rehearse demo end-to-end cùng team | Theo `docs/demo-script-security.md` + infra của The |
| Tue | Freeze các file .ignore | Không thêm entry mới sau thời điểm này |
| Wed | **MILESTONE: dry-run 5 stage sạch trước team** | Kịch bản dự phòng nếu GHCR chậm: dùng artifact lần chạy trước |
| Wed | **MILESTONE: 0 false positive không giải thích được** | Đối chiếu `docs/false-positives-week3.md` mục 6 |
| Thu | Sprint 2 Review với mentor | Nói rõ quyết định GHCR + FP Checkov (mục 3.1, 2.3) |
| Thu | Hỗ trợ Q&A security | Script có sẵn phần hỏi-đáp |

Blockers cần xử lý sớm tuần sau: (1) The đẩy infra thật lên repo để Checkov quét thứ thật thay placeholder; (2) Phuc sửa trigger `build-image.yml`; (3) ai đó review PR của mình (branch protection yêu cầu 1 review).

## 5. Số liệu tuần (cho standup)

- Job mới trong pipeline: +4 (checkov, build-sign, verify, quality-gate) — tổng 9 job.
- SARIF lên Security tab: 3 nguồn (semgrep, trivy, checkov) — trước đó 0.
- Finding đã triage tổng: 2 (gitleaks) + 6 (trivy) + 3 (semgrep baseline) + 3 (checkov report) = 14, mọi entry có lý do.
- Lỗi triage phát hiện & sửa: 1 (CVE-2018-18074). False positive có bằng chứng nguồn: 1 (CKV_AWS_51).
