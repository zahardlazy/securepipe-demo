# Sprint 2 Review — Demo Script (phần Security, Mlo Tay)

> Task: Sun 18/10 — "Prep Sprint 2 review demo script (security parts)".
> Mục tiêu demo: *mỗi công cụ bắt được gì, tại sao pipeline đáng tin, và vì sao màu xanh là thật*. Thời lượng: ~8–10 phút.
> Quy tắc trình bày: **không nói "tất cả đều xanh"** — nói "xanh vì mọi finding đều được giải thích".

---

## 0. Chuẩn bị (trước giờ demo)

1. Mở 2 tab: **Actions** (run gần nhất trên main) + **Security tab** (Code scanning alerts).
2. Confirm run mới nhất XANH (nếu cần, chạy `workflow_dispatch` trước 15 phút).
3. Mở sẵn: `docs/quality-gate.md`, `docs/false-positives-week3.md`, `docs/accepted-findings.json`.
4. Checklist mặc định đã hỏi mentor: ["Sao biết scanner không hỏng?", "Sao dám để finding trong code?", "Image bị thay thì sao?"] — đáp án lần lượt ở mục 1, 2, 4.

## 1. Stage 1 — Secret detection (2 phút)

**Câu dẫn:** *"Bắt đầu từ lớp nguy hiểm nhất: secret. Hai scanner chạy song song với hai triết lý khác nhau."*

| Bước | Làm gì | Nói gì |
|---|---|---|
| 1.1 | Actions → job `gitleaks` → step **Self-test** | "Job này tự cài một secret giả rồi kỳ vọng scanner bắt được và exit 1. Nếu scanner hỏng thì job này ĐỎ — pipeline không thể xanh giả." |
| 1.2 | Mở `app/app.py:10-11` | "App cố ý chứa secret giả [SEEDED #1] — chứng minh detector sống. Nó nằm trong `.gitleaksignore` theo **fingerprint**, không theo đường dẫn — nên chỉ finding đã biết được bỏ qua, secret mới vẫn chặn." |
| 1.3 | Job `trufflehog` | "TruffleHog ngược lại: chỉ báo secret **verify được là còn sống** với nhà cung cấp. Hai công cụ bắt lỗi hai hướng — pattern và verification." |
| Demo nóng (nếu được phép) | Commit 1 file chứa secret giả mới trên branch test → push → job gitleaks ĐỎ | "Đây là hành vi đúng: secret chưa triage = chặn." |

## 2. Stage 2 — SAST + SCA + Gate (3 phút)

**Câu dẫn:** *"Scanning là việc dễ; phần khó là quyết định khi nào xứng đáng chặn build — đó là Quality Gate."*

| Bước | Làm gì | Nói gì |
|---|---|---|
| 2.1 | Security tab → alert Semgrep/Trivy | "Kết quả cả 3 scanner (semgrep, trivy, checkov) lên thẳng Security tab dạng SARIF — không phải mò artifact." |
| 2.2 | Mở `docs/quality-gate.md` (bảng ngưỡng) | "Ngưỡng đã chốt cùng team: CRITICAL chặn, HIGH cảnh báo, SAST ERROR chặn nếu chưa triage. Checkov đang report-mode vì infra còn là placeholder." |
| 2.3 | Actions → job `quality-gate` → log | "Gate đọc JSON kết quả, in từng finding đã chấp nhận kèm lý do, và exit 1 nếu có Critical chưa giải thích. Đây là bản địa 'reason + hạn review' — không có ignore mù." |
| 2.4 | Test case của Phúc (CVE Critical chặn deploy) | "Kịch bản test TC tương ứng: thêm dependency có CVE Critical chưa triage → gate ĐỎ. Tôi đã chạy kịch bản này khi phát triển — log trong `quality_gate.py` test." |

## 3. Stage 3 — Build + Sign + Provenance (2–3 phút)

**Câu dẫn:** *"Ở trên tôi bảo vệ source code; bây giờ bảo vệ chính artifact."*

| Bước | Làm gì | Nói gì |
|---|---|---|
| 3.1 | Job `build-sign` | "Image build và đẩy lên GHCR với tag theo commit SHA, rồi **ký số keyless** — cosign xin certificate tạm thời qua OIDC của workflow, không có key nào nằm trong secrets để lộ." |
| 3.2 | Bước `Generate SLSA v1.1 provenance` (log) | "Mỗi lần build sinh một bản **provenance** theo schema SLSA v1.1: built từ commit nào, workflow nào, runner nào, lúc nào — rồi attach vào image như attestation có chữ ký." |
| 3.3 | Job `verify` | "Cùng pipeline đó, một job riêng **xác minh lại**: chữ ký phải đến từ đúng workflow security.yml của repo này (khóa bằng identity regexp), attestation provenance phải hợp lệ. Ai đẩy tay image cùng tag cũng qua không được." |
| 3.4 | Nói rõ quyết định registry | "Tracker ghi ECR; hôm nay image nằm trên **GHCR** vì IAM role OIDC cho AWS chưa sẵn sàng (infra của The đang hoàn tất). Logic ký/xác minh không đổi khi chuyển — kịch bản 4 bước trong docs/cosign-ghcr.md." |

## 4. Stage 4 — IaC (Checkov) (1–2 phút)

| Bước | Làm gì | Nói gì |
|---|---|---|
| 4.1 | Security tab → alert Checkov (3 finding trên `infra/main.tf`) | "Checkov quét Terraform. Trong 3 finding: một cái là lỗi cài cố ý để demo [SEEDED #4], một cái chấp nhận (chưa cần KMS cho placeholder), và một cái là **false positive của chính Checkov**." |
| 4.2 | `docs/false-positives-week3.md` mục 5 | "Check CKV_AWS_51 dò nhầm tên attribute — tôi đối chiếu source code của checkov làm bằng chứng. Bài học: chúng tôi kiểm chứng cả scanner, không chỉ tin màu xanh." |

## 5. Chốt (30 giây)

**Câu kết gợi ý:** *"Pipeline xanh không có nghĩa là không có lỗ hổng — demo app này đầy lỗi cố ý. Xanh có nghĩa là: mọi lỗi đều có chủ sở hữu, lý do, và hạn chót. Đó là điều một pipeline bảo mật phải cam kết."*

## 6. Q&A dự phòng

| Câu hỏi | Điểm trả lời |
|---|---|
| "Sao không chặn hết mọi finding?" | Ngưỡng Critical chặn; chặn hết = mọi push đỏ vì app demo cố ý chứa lỗi, không phân biệt được finding đã và chưa được xử lý. Cơ chế baseline cho phép phân biệt (docs/quality-gate.md mục 1–2). |
| "Secret giả trong repo, lỡ ai đó dùng thật thì sao?" | Secret thật sẽ bị TruffleHog verify và gitleaks fingerprint mới không nằm trong ignore → chặn. Placeholder hiện tại không hoạt động với AWS. |
| "Vì sao semgrep pin 1.181.0?" | Rule tự update có thể đổi kịch bản giữa sprint — pin để demo ổn định, nâng cấp có chủ đích kèm re-triage baseline (incident trivy tag bị gỡ 01/10 là tiền lệ). |
| "Provenance này đạt SLSA level mấy?" | Build L1 (provenance tồn tại, sinh trong build) + ký bởi danh tính build platform theo tinh thần L2; không claim mức cô lập của L3 (docs/slsa-provenance.md mục 5). |
| "Nếu GitHub/GHCR bị nghi ngờ?" | Chữ ký xác minh độc lập với registry qua Fulcio/Rekor; digest bất biến; có thể tái verify bằng cosign ở bất kỳ đâu với cùng lệnh trong docs/slsa-provenance.md mục 6. |
| "Checkov sao chỉ report?" | Infra hiện là placeholder chờ The; bật enforcement khi infra thật (đã lên plan Week 4/Sprint 3 — retro mục 4). |
