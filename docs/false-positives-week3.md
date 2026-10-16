# Consolidated False-Positive Review — Sprint 2 Week 3

> Task: Mlo Tay, Fri 16/10 — *"Full false-positive review across all 4 tools — Consolidated ignore-file review, nothing unexplained"*.
> Doc này thay thế `docs/false-positives.md` (W1) làm nguồn sự thật hiện hành.
>
**Phiên bản công cụ đã kiểm chứng (chạy local 16/10, kèm file bằng chứng trong `docs/`):**

| Công cụ | Phiên bản | Bằng chứng |
|---|---|---|
| Gitleaks | 8.30.1 (cùng bản CI self-test) | `gitleaks-week3-local-scan.json`, `gitleaks-week3-detector-proof.json` |
| Trivy | 0.76.0 | `trivy-week3-local-scan.json` |
| Semgrep | 1.181.0 (đã pin trong CI) | `semgrep-week3-local-scan.json` |
| Checkov | 3.3.29 (đã pin trong CI) | `checkov-local-scan.json` |
| TruffleHog | CI `@main` | theo thiết kế `--only-verified`, 0 finding |

Quy tắc giữ nguyên từ W1: **không ignore theo path source code**; mọi exception có **lý do + ngày review**; finding đã triage vẫn **nhìn thấy được** trong scan output.

---

## 1. Gitleaks — 2 finding, 2 đã triage (giữ nguyên)

Bỏ tạm `.gitleaksignore` để đếm finding thô (cách làm của W1): đúng **2** — đủ để chứng minh detector sống, và đủ để `.gitleaksignore` (2 fingerprint) không chứa entry chết.

| # | Fingerprint | Đánh giá |
|---|---|---|
| 1 | `app/app.py:aws-access-token:10` | [SEEDED #1] — **phát hiện mới W3**: dòng 10 hiện chỉ còn placeholder `[REDACTED:aws_access_key]` (bị push protection redacted từ trước), **nhưng rule vẫn bắt** — pattern khớp theo *tên biến* `AWS_ACCESS_KEY_ID` + chuỗi trong ngoặc. Entry `.gitleaksignore` dòng 10 **KHÔNG stale** — giữ nguyên. |
| 2 | `app/app.py:generic-api-key:11` | [SEEDED #1] — secret giả 40 ký tự (public example, không hoạt động). Giữ nguyên đến hết nhu cầu demo. |

Kết luận: **0 finding trong CI** (2/2 đã ignore theo fingerprint). Không có gì phải thay đổi.

## 2. TruffleHog — 0 finding (đúng thiết kế)

Chạy `--only-verified`: secret giả không verify được với AWS nên không báo. Đây là hành vi đúng (giảm false positive bằng verification) — đã giải thích trong W1, không đổi. Không cần ignore file cho TruffleHog.

## 3. Semgrep — 41 finding: 3 ERROR (đã triage vào baseline) + 38 WARNING (report)

`--config auto` trên trạng thái repo cuối W3 (41 = 3 ERROR + 38 WARNING):

### 3.1. ERROR — chặn nếu ngoài baseline, hiện đã hết trong baseline

| # | Rule | Vị trí | Xử lý |
|---|---|---|---|
| 1 | `generic.secrets…detected-aws-access-key-id-value` | app.py:10 | [SEEDED #1] — baseline |
| 2 | `generic.secrets…detected-aws-secret-access-key` | app.py:11 | [SEEDED #1] — baseline |
| 3 | `dockerfile.security.missing-user` | Dockerfile:12 | **Finding mới xuất hiện từ 16/10** (Dockerfile PR #17 của Phuc): image chạy root. Chấp nhận tạm (baseline) — quick win Sprint 3 thêm `USER`; không sửa ngay để giữ smoke-test Build Image vừa xanh ổn định |

Cả 3 nằm trong `docs/accepted-findings.json` (fingerprint `path:rule:line`, kèm `review_by: 2026-10-22`). Quality Gate sẽ in dòng `[accepted]` cho từng finding khi chạy — đối chiếu trực tiếp được.

### 3.2. WARNING — không chặn (theo ngưỡng `docs/quality-gate.md`)

| Nhóm | Số lượng | Đánh giá |
|---|---|---|
| `yaml.github-actions…mutable-action-tag` | 34 | **True positive về best-practice** (pin action theo SHA). Cả workflow security.yml + build-image.yml đều dùng major tag động. Chấp nhận đến Sprint 3 — có tiền lệ thực tế: sự cố trivy-action v0.28.0 tag bị gỡ 01/10 (xem comment trong security.yml) chính là rủi ro của tag động. Việc pin-by-SHA đã lên danh sách việc Sprint 3. |
| `python.lang…formatted-sql-query` | 1 | [SEEDED #3] — SQLi dòng 35 cố ý cài. |
| `python.flask…avoid_app_run_with_bad_host` | 1 | Đã ghi nhận từ W1 (dòng 43) — sửa Sprint 3. |
| `terraform.*` (ecr-image-scan-on-push, aws-ecr-mutable-image-tags) | 2 | Semgrep cũng quét Terraform: 2 finding trên `infra/main.tf` — **cùng 2 vấn đề Checkov bắt** (mục 5), một finding trùng [SEEDED #4], một trùng false-positive mutable-tags. Nhất quán với Checkov, không triage riêng. |

## 4. Trivy — 6 CVE seeded, 6 entry `.trivyignore`; **phát hiện và sửa 1 lỗi triage**

**Phát hiện chính của đợt review này:** commit 30/09 (`b9f563a`) xoá `CVE-2018-18074` khỏi `.trivyignore` với lý do "obsolete" — nhưng Trivy 0.76.0 **vẫn báo CVE này** (HIGH, requests 2.19.1, bằng chứng `trivy-week3-local-scan.json` quét CHƯA có entry đó). Đây chính là dạng "finding không giải thích được" mà task nhắm tới: finding sống nhưng không có entry triage.

Nguyên nhân khả dĩ: hiểu nhầm `Status: fixed` trong output Trivy — trường này có nghĩa là *"đã có bản vá 2.20.0"*, **không** phải *"CVE không còn áp dụng"*. requests 2.19.1 đang cài thì CVE vẫn áp dụng.

**Đã xử lý (16/10):** khôi phục `CVE-2018-18074` vào `.trivyignore` với lý do đầy đủ (CVE thuộc [SEEDED #2] — chính là CVE được ghi trong comment `requirements.txt`). Sau khi khôi phục: quét lại → **0 finding** sau ignore. Trạng thái lúc này: 6/6 CVE seeded đều có entry triage đúng như thiết kế ban đầu của W1.

## 5. Checkov (mới ở W3) — 3 finding trên `infra/main.tf`, đủ 3 loại để demo

Checkov 3.3.29 quét placeholder `infra/main.tf` (chạy `-s` soft-fail — report only):

| # | Check | Phân loại | Chi tiết |
|---|---|---|---|
| 1 | `CKV_AWS_51` (immutable tags) | **FALSE POSITIVE có bằng chứng** | Check dò key `image_tag_mutability`, nhưng attribute đúng của AWS provider là `image_tag_immutability` — file .tf đã đặt `"IMMUTABLE"` đúng cú pháp. Bằng chứng: source check `checkov/terraform/checks/resource/aws/ECRImmutableTags.py` (hàm `get_inspected_key` trả về `"image_tag_mutability"`), và output `evaluated_keys: ["image_tag_mutability"]` trong `checkov-local-scan.json`. Với Terraform đúng chuẩn, check này LUÔN fail — không phải lỗi của repo. |
| 2 | `CKV_AWS_136` (KMS encryption) | Chấp nhận cho placeholder | Mã hoá KMS cần key riêng — ngoài phạm vi file mẫu. The quyết định khi thay bằng infra thật. |
| 3 | `CKV_AWS_163` (scan on push) | [SEEDED #4] — lỗi cài có chủ ý | `scan_on_push = false` để chứng minh Checkov bắt được IaC issue. Đổi thành `true` khi hết nhu cầu demo. |

Chính sách: **không** dùng comment `# checkov:skip=…` để dìm finding (phá nguyên tắc "finding phải nhìn thấy"), vì job Checkov đang soft-fail nên finding hiển thị ở Security tab mà không chặn pipeline. Khi bật enforcement (Week 4/Sprint 3) sẽ quyết định lại: skip có lý do hoặc fix.

## 6. Tổng kết — "không có gì không giải thích được"

| Công cụ | Finding sống (không ignore) | Trong ignore/baseline | FP thật | Chưa triage tồn đọng |
|---|---|---|---|---|
| Gitleaks | 0 (trong CI) | 2 | 0 | **0** |
| TruffleHog | 0 | — | 0 | **0** |
| Semgrep | 41 (hiện đủ) | 3 ERROR trong baseline | 0 | **0** |
| Trivy | 0 (sau ignore) | 6 | 0 | **0** (đã sửa lỗi triage CVE-2018-18074) |
| Checkov | 3 (report mode) | 0 (chưa cần) | 1 (có bằng chứng) | **0** |

Thay đổi so với W1: `.trivyignore` +1 entry khôi phục; mới `docs/accepted-findings.json` (baseline Semgrep ERROR); mới infra/main.tf (Checkov target). Không có ignore entry nào **chết** (entry không còn finding tương ứng) — đã kiểm tra bằng cách bỏ từng ignore file và quét lại.

## 7. Chuyển sang Sprint 3

- [ ] Pin toàn bộ action theo SHA (dọn 34 finding mutable-tag) — kèm cảnh báo incident trivy tag bị gỡ 01/10
- [ ] Thêm `USER` vào Dockerfile (dọn ERROR thứ 3)
- [ ] Sửa `app.run(host="0.0.0.0")` → `127.0.0.1`/env (dọn finding W1 cũ)
- [ ] Khi hết demo: xoá [SEEDED #1..#4] + dọn đồng loạt ignore/baseline
- [ ] Bật enforcement Checkov (`--hard-fail-on`) khi infra thật lên
- [ ] Báo checkov upstream issue sai key `image_tag_mutability` (kèm bằng chứng)
