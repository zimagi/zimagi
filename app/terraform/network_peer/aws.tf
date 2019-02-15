
provider "aws" {
  access_key = "${var.access_key}"
  secret_key = "${var.secret_key}"
  region = "${var.region}"
}

resource "aws_vpc_peering_connection" "peers" {
  count = "${var.peer_count}"
  vpc_id = "${var.vpc_id}"
  peer_vpc_id = "${element(var.peer_vpcs, count.index)}"
  peer_region = "${element(var.peer_regions, count.index)}"
  
  tags = {
    Name = "cenv-network"
  }
}
