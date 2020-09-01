#include <core.p4>
#include <v1model.p4>

typedef bit<48> EthernetAddress;
typedef bit<32> IPv4Address;

const bit<16> TYPE_IPV4 = 0x800;

header ethernet_t {
    EthernetAddress dst_addr;
    EthernetAddress src_addr;
    bit<16>         ether_type;
}

header ipv4_t {
    bit<4>      version;
    bit<4>      ihl;
    bit<8>      diffserv;
    bit<16>     total_len;
    bit<16>     identification;
    bit<3>      flags;
    bit<13>     frag_offset;
    bit<8>      ttl;
    bit<8>      protocol;
    bit<16>     hdr_checksum;
    IPv4Address src_addr;
    IPv4Address dst_addr;
}

struct headers_t {
    ethernet_t ethernet;
    ipv4_t     ipv4;
}

struct metadata_t {
}

error {
    IPv4IncorrectVersion,
    IPv4OptionsNotSupported
}

parser my_parser(packet_in packet,
                out headers_t hd,
                inout metadata_t meta,
                inout standard_metadata_t standard_meta)
{
    state start {
        packet.extract(hd.ethernet);
        transition select(hd.ethernet.ether_type) {
            TYPE_IPV4:  parse_ipv4;
            default: accept;
        }
    }

    state parse_ipv4 {
        packet.extract(hd.ipv4);
        verify(hd.ipv4.version == 4w4, error.IPv4IncorrectVersion);
        verify(hd.ipv4.ihl == 4w5, error.IPv4OptionsNotSupported);
        transition accept;
    }
}

control my_deparser(packet_out packet,
                   in headers_t hdr)
{
    apply {
        packet.emit(hdr.ethernet);
        packet.emit(hdr.ipv4);
    }
}

control my_verify_checksum(inout headers_t hdr,
                         inout metadata_t meta)
{
    apply { }
}

control my_compute_checksum(inout headers_t hdr,
                          inout metadata_t meta)
{
    apply { }
}

control my_ingress(inout headers_t hdr,
                  inout metadata_t meta,
                  inout standard_metadata_t standard_metadata)
{

    bool dropped = false;
    bool matched = false;

    action drop_action() {
        mark_to_drop(standard_metadata);
        dropped = true;
    }

    action set_egress_spec(bit<9> port){
        standard_metadata.egress_spec = port;
        matched = true;
    }
    
    table drop_src {
        key = {
            hdr.ipv4.src_addr: exact;
        }
        actions = {
            drop_action;
            NoAction;
        }
        size = 1024;
        default_action = NoAction;
    }
    
    table drop_dst {
        key = {
            hdr.ipv4.dst_addr: exact;
        }
        actions = {
            drop_action;
            NoAction;
        }
        size = 1024;
        default_action = NoAction;
    }
    
    table forward_by_addr {
        key = {
            hdr.ipv4.dst_addr: exact;
        }
        actions = {
            set_egress_spec;
            NoAction;
        }
        size = 1024;
        default_action = NoAction;
    }
    
    table forward_by_port {
        key = { standard_metadata.ingress_port: exact; }
        actions = {
            set_egress_spec;
            drop_action;
        }
        size = 1024;
        default_action = drop_action;
    }    
    
    apply {
        drop_src.apply();
        drop_dst.apply();
        forward_by_addr.apply(); 
        if(!matched){
            forward_by_port.apply(); 
        }
        if(dropped){
            return;
        }
    }
}

control my_egress(inout headers_t hdr,
                 inout metadata_t meta,
                 inout standard_metadata_t standard_metadata)
{
    apply { }
}

V1Switch(my_parser(),
         my_verify_checksum(),
         my_ingress(),
         my_egress(),
         my_compute_checksum(),
         my_deparser()) main;
