
provider "aws" {
    access_key = "${var.access_key}"
    secret_key = "${var.secret_key}"
    region = "${var.firewall.network.region}"
}

resource "aws_security_group_rule" "firewall" {
    security_group_id = "${var.firewall.security_group_id}"
    type = "${var.mode}"
    from_port = "${var.from_port}"
    to_port = "${var.to_port}"
    protocol = "${var.protocol == "all" ? "-1" : var.protocol}"
    cidr_blocks = "${var.cidrs}"
}
output "rule_id" {
  value = "${aws_security_group_rule.firewall.id}"
}