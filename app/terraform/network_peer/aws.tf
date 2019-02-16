
provider "aws" {
  alias = "source"
  access_key = "${var.access_key}"
  secret_key = "${var.secret_key}"
  region = "${var.region}"
}

provider "aws" {
  alias = "peer"
  access_key = "${var.access_key}"
  secret_key = "${var.secret_key}"
  region = "${var.peer_region}"
}

resource "aws_vpc_peering_connection" "peer" {
  provider = "aws.source"
  vpc_id = "${var.vpc_id}"
  peer_vpc_id = "${var.peer_vpc_id}"
  peer_region = "${var.peer_region}"
  
  tags = {
    Name = "cenv-network"
    Side = "Requester"
  }
}

resource "aws_vpc_peering_connection_accepter" "peer" {
  provider = "aws.peer"
  vpc_peering_connection_id = "${aws_vpc_peering_connection.peer.id}"
  auto_accept = true

  tags = {
    Name = "cenv-network"
    Side = "Accepter"
  }
}
