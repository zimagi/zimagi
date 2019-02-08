
provider "aws" {
  access_key = "${var.access_key}"
  secret_key = "${var.secret_key}"
  region = "${var.network.region}"
}

resource "aws_efs_file_system" "data" {
  performance_mode = "${var.performance_mode}"
  throughput_mode = "${var.throughput_mode}"
  provisioned_throughput_in_mibps = "${var.provisioned_throughput}"
  encrypted = "${var.encrypted}"

  tags = {
    Name = "cenv-storage"
  }
}
output "filesystem_id" {
  value = "${aws_efs_file_system.data.id}"
}