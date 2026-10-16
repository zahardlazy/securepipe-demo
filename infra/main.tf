# ============================================================================
# PLACEHOLDER cho infra AWS cua The (Sprint 2: VPC -> ECR -> IAM -> ECS).
# File nay duoc tao boi Mlo Tay (Week 3, Mon 13/10) de Checkov co target quet
# trong pipeline (Stage 4 - IaC scan). Khi The day infra that len, HAY THAY THE
# file nay hoac giu lai neu phu hop.
#
# Ket qua Checkov 3.3.29 (local, 13/10) - 3 finding, ca 3 deu co giai thich:
#   CKV_AWS_163 (scan_on_push = false)  -> [SEEDED #4] loi CO Y de demo
#   CKV_AWS_51  (tag immutability)      -> FALSE POSITIVE: check do doc key
#       "image_tag_mutability", nhung attribute dung cua AWS provider la
#       "image_tag_immutability" (da dat "IMMUTABLE"). Xem chi tiet + bang
#       chung: docs/false-positives-week3.md, muc 4.
#   CKV_AWS_136 (KMS encryption)        -> chap nhan cho placeholder: can KMS
#       key rieng, ngoai pham vi file mau. The quyet dinh khi lam infra that.
# ============================================================================

terraform {
  required_version = ">= 1.9.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

resource "aws_ecr_repository" "demo" {
  name = "securepipe-demo"

  # [SEEDED #4] CKV_AWS_163: doi thanh true khi het nhu cau demo
  image_scanning_configuration {
    scan_on_push = false # [SEEDED #4]
  }

  # Tag immutable de chan tag-squatting (CKV_AWS_51 luon FAIL vi loi key cua
  # checkov — xem ghi chu dau file; day KHONG phai loi cua file .tf nay)
  image_tag_immutability = "IMMUTABLE"

  tags = {
    Project = "securepipe-demo"
    Managed = "terraform"
    Owner   = "the"
  }
}
