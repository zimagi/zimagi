
provider "aws" {
  access_key = "${var.access_key}"
  secret_key = "${var.secret_key}"
  region = "${var.region}"
}

resource "aws_vpc" "network" {
  cidr_block = "${var.cidr}"
  instance_tenancy = "${var.tenancy}"
  enable_dns_support = "${var.dns_support}"
  enable_dns_hostnames = "${var.dns_hostnames}"
  
  tags = {
    Name = "cenv-network"
  }
}
output "vpc_id" {
  value = "${aws_vpc.network.id}"
}

resource "aws_internet_gateway" "network" {
  vpc_id = "${aws_vpc.network.id}"

  tags = {
    Name = "cenv-network"
  }
}
output "ig_id" {
  value = "${aws_internet_gateway.network.id}"
}

resource "aws_route_table" "network" {
  vpc_id = "${aws_vpc.network.id}"

  tags = {
    Name = "cenv-network"
  }
}
output "route_table_id" {
  value = "${aws_route_table.network.id}"
}

resource "aws_route" "gateway" {
  route_table_id  = "${aws_route_table.network.id}"
  destination_cidr_block = "0.0.0.0/0"
  gateway_id = "${aws_internet_gateway.network.id}"
}
output "route_id" {
  value = "${aws_route.gateway.id}"
}