# Consolidated False-Positive Review — Sprint 2 Week 1

> Task: Hieu (Sun 04/10) — "Finalize false-positive list for the week".
> Người tổng hợp: Mlo Tay (kiêm Hieu), 01/10/2026.
>
> Công cụ trong phạm vi: **Gitleaks · TruffleHog · Semgrep · Trivy**.

## Quy tắc

1. Mỗi entry phải có **lý do** và **ngày review lại**.
2. **Không** ignore theo đường dẫn source code — chỉ theo **fingerprint** từng finding.
3. Finding trong source code phải **nhìn thấy được** trong output scanner, kể cả khi đã chấp nhận.
4. Không có ignore nào được thêm chỉ để làm pipeline xanh.

---

## 1. Gitleaks — 2 finding, đã chấp nhận

| # | Fingerprint | Rule | File:Line |
|---|---|---|---|
| 1 | `app/app.py:aws-access-token:10` | `aws-access-token` | `app/app.py:10` |
| 2 | `app/app.py:generic-api-key:11` | `generic-api-key` | `app/app.py:11` |

**Bản chất:** KHÔNG phải false positive. Đây là secret **cố ý cài** để test scanner (`[SEEDED #1]` trong `app/app.py`). Giá trị là AWS public example key, không hoạt động.

**Xử lý:** ghi vào `.gitleaksignore` theo fingerprint (không theo path), kèm comment lý do.

**Đã kiểm chứng cơ chế (01/10):**
- Có `.gitleaksignore` → `gitleaks detect` trả `[]`, exit 0 (push sạch xanh)
- Tạm bỏ `.gitleaksignore` → bắt đúng 2 finding, **exit 1**
- Kết luận: detector hoạt động; ignore chỉ che 2 finding đã biết, không che cái mới.

---

## 2. Semgrep — 4 finding, 3 chấp nhận + 1 cần sửa

Chạy `semgrep scan --config auto` trên `app/app.py`:

| # | Rule | Line | Đánh giá |
|---|---|---|---|
| 1 | `generic.secrets...detected-aws-access-key-id-value` | 10 | Trùng Gitleaks #1 — chấp nhận (seeded) |
| 2 | `generic.secrets...detected-aws-secret-access-key` | 11 | Trùng Gitleaks #2 — chấp nhận (seeded) |
| 3 | `python.lang.security.audit.formatted-sql-query` | 35 | **Seeded `[SEEDED #3]`** — chấp nhận |
| 4 | `python.flask.security.audit.app-run-param-config` | 43 | **Không seeded** — xem mục dưới |

### Lưu ý quan trọng về ruleset

Bản trước dùng `--config p/owasp-top-ten` và **chỉ ra 1 finding** (dòng 43) — **bỏ sót SQL injection dòng 35**, đúng cái lỗi được cài để Semgrep bắt.

Đã đổi sang `--config auto`: bắt đủ **4 finding**. Đây là fix, không phải regression.

| Config | Findings | Bắt SQLi d.35? |
|---|---|---|
| `p/owasp-top-ten` | 1 | ❌ |
| `auto` | 4 | ✅ |

### Finding #4 — `app.run(host="0.0.0.0")`

Không nằm trong danh sách seeded. Trong demo app thì vô hại (chạy local), nhưng là bad practice thật.

**Quyết định:** giữ nguyên + ghi nhận ở đây; **không** ignore. Task sửa (đổi sang `127.0.0.1` hoặc đọc từ env) đưa vào Sprint 3.

---

## 3. Trivy — 6 CVE, cả 6 chấp nhận

Quét `requirements.txt`:

| CVE | Severity | Package | Fixed in |
|---|---|---|---|
| `CVE-2026-27205` | LOW | flask 3.0.3 | 3.1.3 |
| `CVE-2018-18074` | **HIGH** | requests 2.19.1 | 2.20.0 |
| `CVE-2023-32681` | MEDIUM | requests 2.19.1 | 2.31.0 |
| `CVE-2024-35195` | MEDIUM | requests 2.19.1 | 2.32.0 |
| `CVE-2024-47081` | MEDIUM | requests 2.19.1 | 2.32.4 |
| `CVE-2026-25645` | MEDIUM | requests 2.19.1 | 2.33.0 |

**Bản chất:** không phải false positive. Dependency **cố ý cũ** (`[SEEDED #2]` trong `requirements.txt`) để chứng minh SCA hoạt động. `CVE-2018-18074` chính là CVE được ghi trong comment seed.

**Xử lý:** 6 entry trong `.trivyignore`, mỗi entry kèm lý do + ngày review lại.

**Đã kiểm chứng (01/10):** `trivy fs --ignorefile .trivyignore` → còn **0 vuln**.

---

## 4. TruffleHog — không có finding mới

Chạy ở chế độ `--only-verified`. Secret trong `app.py` là key giả, **không verify được** với AWS, nên TruffleHog không báo (khác Gitleaks — bắt theo pattern).

Đây là hành vi đúng: TruffleHog giảm false positive bằng cách chỉ báo secret **xác minh được là còn sống**.

---

## 5. Tổng kết

| Công cụ | Findings | Chấp nhận (có lý do) | Cần sửa |
|---|---|---|---|
| Gitleaks | 2 | 2 | 0 |
| TruffleHog | 0 | — | — |
| Semgrep | 4 | 3 | **1** (dòng 43) |
| Trivy | 6 | 6 | 0 |
| **Tổng** | **12** | **11** | **1** |

**"Không có gì không giải thích được"** — mọi finding đều có entry hoặc ghi nhận ở trên.

---

## 6. Việc chuyển sang Sprint 3

- [ ] Sửa `app.run(host="0.0.0.0")` → `127.0.0.1` hoặc env var
- [ ] Xoá `[SEEDED #1..#3]` khỏi demo app khi hết nhu cầu demo
- [ ] Nâng cấp `requests` và `flask` sau khi demo xong
- [ ] Bật enforcement (`--error`, `exit-code: 1`) — task Week 3
