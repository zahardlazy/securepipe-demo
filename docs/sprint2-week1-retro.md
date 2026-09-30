# Sprint 2 — Week 1 Retrospective

> Tuần 1: 28/09 – 04/10/2026 · Milestone day: **Wed 30/09**
> Người viết: Mlo Tay (kiêm Hieu) · Ngày: 01/10/2026

---

## 1. Việc đã hoàn thành

### Mlo Tay

| Ngày | Task | Trạng thái | Bằng chứng |
|---|---|---|---|
| Mon 28/09 | Repo structure + branch protection | ✅ | `main` protected; cấu trúc thư mục ổn |
| Tue 29/09 | Scaffold `.github/workflows/security.yml` | ✅ | Workflow chạy được trên ubuntu-latest |
| **Wed 30/09** | **MILESTONE: Gitleaks + Semgrep** | ⚠️ **có, nhưng phải sửa** | Xem mục 2 |
| Thu 01/10 | OIDC research notes | ✅ | `docs/oidc-notes.md` (3.7 KB) |
| Fri 02/10 | Continue OIDC + sync notes | ✅ | `docs/oidc-notes.md` mục 6 (kế hoạch áp dụng) |
| Sun 04/10 | Retro + lock Week 2 | ✅ | File này + mục 5 |

### Hieu

| Ngày | Task | Trạng thái | Bằng chứng |
|---|---|---|---|
| Mon 28/09 | Cài Gitleaks + TruffleHog, scan đầu | ✅ | Report thật trong `docs/` (không còn file rỗng) |
| Tue 29/09 | `.gitleaks.toml` + pre-commit hook | ✅ | `.gitleaks.toml`, `.pre-commit-config.yaml` |
| **Wed 30/09** | **MILESTONE: Semgrep** | ⚠️ **có, nhưng ruleset sai** | Xem mục 2 |
| Thu 01/10 | Trivy SCA scan | ✅ | `docs/trivy-local-scan.json` (6 CVE) |
| Fri 02/10 | Draft `.trivyignore` | ✅ | `.trivyignore` — 6 entry, mỗi entry có lý do |
| Sun 04/10 | Finalize false-positive list | ✅ | `docs/false-positives.md` (12 finding, 11 chấp nhận, 1 cần sửa) |

---

## 2. Milestone Wed — vấn đề và cách sửa

### Vấn đề 1: allowlist che chính secret cần demo

`.gitleaks.toml` cũ allowlist **theo đường dẫn source code**:

```toml
paths = [
  '''docs/.*scan.*\.txt''',
  '''app/app\.py''',   # ← file chứa secret!
]
```

Hệ quả: `gitleaks detect` không bao giờ báo secret trong `app/app.py` → job gitleaks **luôn xanh** → done-when *"push with fake secret → failed run"* không thể chứng minh.

**Cách sửa:** bỏ allowlist theo path; chuyển sang **fingerprint** trong `.gitleaksignore` (chỉ che đúng 2 finding đã biết).

**Đã chứng minh (01/10):**

| Điều kiện | Kết quả |
|---|---|
| Có `.gitleaksignore` | `[]`, exit 0 |
| Bỏ `.gitleaksignore` | **2 finding, exit 1** |

→ Detector hoạt động thật. Ignore chỉ che cái đã biết.

### Vấn đề 2: ruleset Semgrep không bắt được lỗi đã seed

`app/app.py` có SQL injection cố ý ở dòng 35 (`[SEEDED #3]`). Nhưng `--config p/owasp-top-ten` **không bắt**:

| Config | Findings | Bắt SQLi d.35? |
|---|---|---|
| `p/owasp-top-ten` | 1 | ❌ |
| `auto` | 4 | ✅ |

**Cách sửa:** đổi sang `--config auto`.

### Vấn đề 3: scanner luôn exit 0 → pipeline xanh giả

Không có cơ chế nào chặn. Cộng với vấn đề 1, **cả hai job đều xanh** dù có 12 finding.

**Cách sửa (Week 1):**
- Gitleaks: giữ **enforcement** (đây là done-when thật của tuần)
- Thêm job **self-test**: cố tình cài secret, **kỳ vọng exit 1** — nếu detector hỏng, job fail
- Semgrep/Trivy: **report-only** (chưa bật `--error` / `exit-code: 1`)

**Lý do chưa bật enforcement cho Semgrep/Trivy:** demo app **cố ý** chứa lỗi. Bật ngay thì mọi push đều đỏ, không phân biệt được "push sạch" với "push có lỗi". Đây là task **Week 3** (`Integrate Security Quality Gate logic (Critical -> fail)`).

---

## 3. Phát hiện ngoài kế hoạch

### 3.1 PR #3 bị đóng không merge

PR #3 (`hieu/week1-security`) **làm đúng** — `.gitleaks.toml` không allowlist `app/app.py`, có `.pre-commit-config.yaml`:

```yaml
entry: gitleaks protect --staged --verbose --redact --config .gitleaks.toml
```

Body PR ghi: *"đã test: fake GitHub token bị chặn, exit 1"*. CI run #13 **success**.

Nhưng PR bị đóng 30/09 15:26, không merge. Main nhận bản của Mlo Tay — bản **có bug allowlist**.

**Bài học:** base của PR cũ (23/09) trong khi main đã nhảy (30/09) → stale base → nên rebase thay vì đóng. **Quy trình:** trước khi đóng PR, kiểm tra xem nội dung có giá trị chưa merge không.

### 3.2 File placeholder rỗng

`docs/gitleaks-local-scan.txt` và `docs/trufflehog-local-scan.txt` = **0 byte**; `docs/oidc-notes.md` = **6 byte** (BOM UTF-16 rác `FF FE 0D 00 0A 00`).

**Đã thay** bằng report JSON thật.

### 3.3 Trivy tự đọc `.trivyignore`

Trivy **tự động** đọc `.trivyignore` trong thư mục hiện tại. Lần đầu chạy ở workspace có file → 0 vuln (tưởng sai). Ở clone không có → 6 vuln. Xác nhận bằng `--ignorefile` tường minh.

**Bài học:** khi đo baseline, phải chỉ định ignore-file **tường minh** — đừng để scanner tự tìm.

---

## 4. Số liệu cuối tuần

| Công cụ | Findings | Chấp nhận | Cần sửa |
|---|---|---|---|
| Gitleaks | 2 | 2 | 0 |
| TruffleHog | 0 | — | — |
| Semgrep | 4 | 3 | 1 |
| Trivy | 6 | 6 | 0 |
| **Tổng** | **12** | **11** | **1** |

Finding "cần sửa": `app.run(host="0.0.0.0")` — bad practice thật, chuyển Sprint 3.

---

## 5. Kế hoạch Week 2 (05 – 11/10)

### Mlo Tay

- [ ] Mon — Finalize ngưỡng Gitleaks + Semgrep từ phát hiện tuần này
- [ ] Tue — Thêm bước sinh SBOM (Syft, CycloneDX) vào workflow
- [ ] **Wed — MILESTONE: pipeline Stage 1-2 chạy end-to-end** (secret + SAST + SCA + SBOM xanh trên commit sạch)
- [ ] Thu — Bắt đầu Cosign keyless signing
- [ ] Fri — Debug quyền OIDC cho Cosign (`id-token: write`)
- [ ] Sun — Retro + điều chỉnh Week 3

### Hieu (nay gộp vào Mlo Tay)

- [ ] Mon — Mở rộng rule Semgrep cho demo app (2-3 rule riêng)
- [ ] Tue — Chốt cấu hình Trivy, xuất report thật đầu tiên
- [ ] **Wed — MILESTONE: Trivy + Semgrep xuất SARIF**, hiện trong GitHub Security tab
- [ ] Thu — Review + triage toàn bộ false positive hiện có
- [ ] Fri — Viết `.semgrepignore` chính thức kèm tài liệu lý do
- [ ] Sun — Chuẩn bị tool config cho Checkov (Stage 4)

### Việc chặn tiến độ (làm trước Wed)

1. **Gỡ `app/app.py` khỏi allowlist** — đã xong tuần này
2. **Bật `--error` + `exit-code: 1`** — chỉ bật được sau khi SBOM xong, nếu không pipeline đỏ mọi lần
3. **Đưa SARIF lên GitHub Security tab** — cần `security-events: write` permission

---

## 6. Bài học rút ra

1. **Allowlist theo path là bẫy.** Che theo đường dẫn source code có thể vô hiệu hoá cả scanner. Dùng fingerprint.
2. **"Pipeline xanh" không có nghĩa "code sạch".** Phải có self-test chứng minh detector hoạt động.
3. **Ruleset mặc định không đủ.** `p/owasp-top-ten` bỏ sót SQL injection — phải kiểm chứng bằng lỗi đã cài.
4. **File rỗng vẫn "tồn tại".** `docs/*.txt` = 0 byte trông như đã làm xong. Phải kiểm tra nội dung, không chỉ sự tồn tại.
5. **PR đóng không merge là mất mát thật.** Công của Hieu (tuần này) suýt mất hoàn toàn.
6. **Gitleaks có allowlist mặc định — đừng dùng key ví dụ trong tài liệu.**

   Lần đầu viết self-test, tao dùng `AKIAIOSFODNN7EXAMPLE` (key mẫu trong tài liệu AWS). Kết quả: `gitleaks detect` trả **exit 0** — không bắt. Nếu giữ nguyên, job self-test sẽ **fail sai lý do** và pipeline đỏ dù detector hoàn toàn khoẻ.

   | Key | Kết quả |
   |---|---|
   | `AKIAIOSFODNN7EXAMPLE` | exit 0 — **KHÔNG bắt** (allowlist mặc định) |
   | `AKIA` + `ZZ7XQ2WPLMN4RTUV` | exit 1 — **bắt** ✓ |
   | `ghp_AAAA...` (GitHub PAT) | exit 0 — không bắt theo pattern này |
   | `xoxb-...` (Slack token) | exit 1 — bắt ✓ |

   **Bài học:** khi viết self-test cho scanner, phải **kiểm chứng key mẫu thật sự bị bắt** trước. Đừng giả định "key trông giống secret thì sẽ bị bắt".

7. **Luôn test 2 chiều.** Một chiều "push sạch → xanh" không đủ — phải chứng minh "push có secret → đỏ". Nếu chỉ test một chiều, allowlist che hết secret vẫn cho ra "xanh" và ta tưởng mọi thứ ổn.

---

## Phụ lục — Fix CI run #36746789965 (01/10, sau retro)

Run trên `feat/sprint1-finish` (commit 846ce77) fail với 2 lỗi thật, được phát hiện qua GitHub API annotations:

| Job | Triệu chứng | Nguyên nhân gốc | Fix
|---|---|---|---|
| `trivy` | Fail ngay bước "Set up job" | `aquasecurity/trivy-action@0.28.0` — tag **không tồn tại** (tag thật là `v0.28.0`, có chữ `v`) | Đổi sang `@v0.28.0` (đã xác minh tag tồn tại qua GitHub API) |
| `semgrep` | Job "success" nhưng scan exit 2, SARIF rỗng — bị `continue-on-error` che | Lệnh dùng `--sarif --output` **và** `--json --output` trong cùng 1 lệnh — semgrep không cho lặp `--output` (đã tái hiện local: `option '--output' cannot be repeated`) | Tách thành 2 step riêng: 1 SARIF, 1 JSON |

**Bài học thêm:**

8. **Job "success" chưa chắc làm đúng việc.** `continue-on-error: true` + step upload artifact `if: always()` khiến job semgrep xanh dù scan chưa chạy. Phải đọc annotations/log, không chỉ nhìn conclusion.
9. **Pin version action thì phải verify tag tồn tại.** `0.28.0` vs `v0.28.0` — một ký tự làm cả job fail từ "Set up job". Khi pin, kiểm tra tag qua API hoặc fetch `action.yml` từ tag đó.

**Kiểm chứng local lần cuối (01/10, gitleaks 8.30.1 + trufflehog 3.97.9 trên Windows):**

| Điều kiện | Kết quả |
|---|---|
| `gitleaks detect` với `.gitleaksignore` | 15 commits, **0 finding**, exit 0 |
| Bỏ `.gitleaksignore` | **2 finding**, exit 1 — detector bắt thật |
| `gitleaks protect --staged` (mô phỏng pre-commit, file planted) | **1 finding, exit 1** — hook chặn commit như thiết kế |
| `trufflehog git file://. --only-verified` | **0 verified** (đúng: key giả không verify được với AWS) — report: `docs/trufflehog-local-scan.json` |
