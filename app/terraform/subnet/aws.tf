
provider "aws" {
  access_key = "${var.access_key}"
  secret_key = "${var.secret_key}"
  region = "${var.network["region"]}"
}

resource "aws_subnet" "network" {
  vpc_id = "${var.network["vpc"]}"
  availability_zone_id = "${var.zone}"
  cidr_block = "${var.cidr}"
  map_public_ip_on_launch = "${var.public_ip}"

  tags = {
    Name = "cenv-network"
  }
}

resource "aws_route_table_association" "network" {
  subnet_id      = "${aws_subnet.network.id}"
  route_table_id = "${var.network["route_table"]}"
}