
provider "aws" {
  access_key = "${var.access_key}"
  secret_key = "${var.secret_key}"
  region = "${var.network.region}"
}

resource "aws_subnet" "network" {
  vpc_id = "${var.network.vpc_id}"
  availability_zone = "${var.zone}"
  cidr_block = "${var.cidr}"
  map_public_ip_on_launch = "${var.use_public_ip}"
  assign_ipv6_address_on_creation = false

  tags = {
    Name = "cenv-network"
  }
}
output "subnet_id" {
  value = "${aws_subnet.network.id}"
}

resource "aws_route_table_association" "network" {
  subnet_id      = "${aws_subnet.network.id}"
  route_table_id = "${var.network.route_table_id}"
}