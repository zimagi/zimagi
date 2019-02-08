
provider "aws" {
  access_key = "${var.access_key}"
  secret_key = "${var.secret_key}"
  region = "${var.subnet.network.region}"
}

resource "aws_efs_mount_target" "data" {
  file_system_id = "${var.storage.filesystem_id}"
  subnet_id      = "${var.subnet.subnet_id}"
  security_groups = "${var.security_groups}"
}
output "mount_id" {
  value = "${aws_efs_mount_target.data.id}"
}
output "mount_ip" {
  value = "${aws_efs_mount_target.data.ip_address}"
}