# Security Quality Gate — Ngưỡng & Logic

> Task: Mlo Tay — Sprint 2, Week 3.
> Thu 15/10: "Tune Quality Gate severity thresholds" (doc này).
> Fri 16/10: "Integrate Security Quality Gate logic (Critical -> fail)" (job `quality-gate` trong `.github/workflows/security.yml`).
> Người chốt ngưỡng: Mlo Tay (security) — review cùng team tại standup Fri 16/10.

---

## 1. Nguyên tắc thiết kế

1. **Critical phải chặn** — đây là yêu cầu cốt lõi của tracker: *"Pipeline fails build when a Critical finding exists"*.
2. **Không che finding** — theo quy tắc số 3 đã chốt từ Week 1 (`docs/false-positives.md`): finding trong source code phải **nhìn thấy được** trong output scanner. Do đó việc "cho qua" 1 finding không được làm bằng cách bỏ quét file, mà bằng cách **ghi nhận vào baseline kèm lý do** và tìm nó trong baseline lúc chặn.
3. **Fail-closed** — nếu gate không đọc được kết quả scan (artifact thiếu / JSON hỏng) thì gate **ĐỎ**, không phải xanh. Một cánh cửa không đọc được trạng thái phải coi như đang đóng.
4. **Mọi ngoại lệ có hạn** — mỗi entry baseline phải có `reason` và `review_by`. Quá hạn thì gate in cảnh báo (không chặn) — lý lịch nợ phải lộ ra, không nằm im.

## 2. Bảng ngưỡng (đã chốt 16/10)

| Công cụ | Severity | Hành vi | Lý do |
|---|---|---|---|
| **Gitleaks** | Mọi secret mới (ngoài `.gitleaksignore`) | **CHAN** (exit 1 ngay trong job) | Secret = rủi ro trực tiếp cao nhất; đã enforcement từ Week 1 |
| **TruffleHog** | Secret **verified** | **CHAN** (native) | `--only-verified` → chỉ báo secret xác minh được là còn sống |
| **Trivy (SCA)** | `CRITICAL` | **CHAN** | Yêu cầu core của Quality Gate |
| **Trivy (SCA)** | `HIGH` | **Cảnh báo** (`::warning`), không chặn | requests 2.19.1 đang nợ 1 HIGH đã triage; chặn HIGH sẽ sai với trạng thái demo |
| **Semgrep (SAST)** | `ERROR` **ngoài baseline** | **CHAN** | Finding mới chưa ai nhìn = phải dừng để triage |
| **Semgrep (SAST)** | `ERROR` **có trong baseline** | Cho qua + in ra để đối chiếu | Đã có lý do + hạn review trong `docs/accepted-findings.json` |
| **Semgrep (SAST)** | `WARNING` / `INFO` | Báo cáo | WARNING hiện tại gồm cả 13 finding "mutable action tag" trên chính workflow — nhiễu nếu chặn |
| **Checkov (IaC)** | Mọi finding | Báo cáo (`-s` soft-fail) | Infra hiện là placeholder cho The; enforcement Checkov là quyết định cho Week 4/Sprint 3 khi infra thật xuất hiện |

Lưu ý quan trọng về **Trivy**: kết quả JSON mà gate đọc đã áp dụng `.trivyignore` ngay từ bước scan (workflow truyền `trivyignores: .trivyignore`). Nghĩa là những CVE đã triage thì **không xuất hiện** trong đầu ra gate — gate chỉ nhìn thấy CVE chưa ai xử lý. Đây là điểm khác biệt so với Semgrep (semgrep không bỏ file source khỏi scan, nên baseline nằm ở lớp gate).

## 3. Kiến trúc trong pipeline

```
 push/PR                 push main / workflow_dispatch
    │                              │
    ├─► gitleaks (chan)            ├─► build-sign ──► verify
    ├─► trufflehog (chan)          │    (GHCR +       (cosign verify
    ├─► semgrep ──┐                │     cosign        + verify-attestation)
    ├─► trivy ────┼──► quality-gate│
    ├─► checkov ──┘   (Critical=   │
    └─► syft          fail)        │
```

- 5 job quét chạy song song. Job `quality-gate` `needs` cả 5 — nếu một job quét **đỏ** thì toàn run đỏ (đó chính là cơ chế chặn của Gitleaks/TruffleHog, không cần đợi gate).
- `quality-gate` tải 2 artifact (`trivy-results-json`, `semgrep-results-json`), chạy `.github/scripts/quality_gate.py`, đối chiếu `docs/accepted-findings.json`.
- Chuỗi `build-sign → verify` tách khỏi gate (supply chain ≠ findings), cùng phải xanh thì run mới xanh.

## 4. Cách gate "đỏ có chủ đích" hoạt động trên demo

| Thao tác thử | Kết quả mong đợi |
|---|---|
| Commit chứa secret thật (không có trong `.gitleaksignore`) | Job `gitleaks` ĐỎ ngay |
| Thêm dependency có CVE Critical (chưa nằm trong `.trivyignore`) | Job `quality-gate` ĐỎ, annotation nêu rõ CVE |
| Thêm code `eval(...)` mới | Job `quality-gate` ĐỎ (SAST ERROR ngoài baseline) |
| Push "sạch" (trạng thái repo hiện tại) | Toàn bộ XANH |

Ba dòng đầu là kịch bản demo cho Sprint 2 review — xem `docs/demo-script-security.md`.

## 5. Vòng đời một finding (quy trình)

1. **Xuất hiện** → gate đỏ (nếu thuộc nhóm chặn).
2. **Triage** — 2 lựa chọn:
   - **Sửa code** (ưu tiên) → gate xanh tự nhiên;
   - **Chấp nhận** → thêm entry vào `docs/accepted-findings.json` (Semgrep ERROR) hoặc `.trivyignore` (Trivy) **kèm lý do + ngày review lại**.
3. **Hết hạn review** (`review_by`) → gate in `::warning` nhắc re-triage.
4. **Sprint review** — Mlo Tay rà toàn bộ baseline: entry nào đã xử lý thì xoá (finding biến mất khỏi scan → baseline giữ lại entry chết là nợ phễu).

## 6. Quan hệ với các cấp Stage

Quality Gate hiện phủ Stage 1 (secret), Stage 2 (SAST/SCA) và "cửa" tổng của pipeline. Stage 3 (sign/verify) tự enforcement bằng chữ ký số — không cần ngưỡng severity. Stage 4 (Checkov) đang report-only, sẽ nâng lên enforcement (khuyến nghị `--hard-fail-on HIGH` cho IaC thật) trong Week 4/Sprint 3 — đã ghi trong retro.
