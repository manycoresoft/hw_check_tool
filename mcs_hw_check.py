#!/bin/python3

import os
import time
import sys
import dmiparser
import psutil
import traceback
import json
import xml.etree.ElementTree as ET

# Global constant
TABSIZE=4

def space_print(s, t: int):
    ss = ' '*t + s;
    print(ss);
    return;

def search_list_dict(list_dict, k, v, return_k):
    r = list(filter(lambda f: f[k] == v, list_dict))[0];
    return r[return_k];

def get_cpuinfo(cpu_dict):
    lscpu_list = [];
    lscpu_list = json.load(os.popen("/usr/bin/lscpu -J"))["lscpu"];

    cpu_dict["cpu_name"] = search_list_dict(lscpu_list, 
                                            "field", 
                                            "Model name:", 
                                            "data");
    cpu_dict["cpu_socket"] = search_list_dict(lscpu_list, 
                                              "field", 
                                              "Socket(s):", 
                                              "data");
    cpu_dict["core_per_socket"] = search_list_dict(lscpu_list, 
                                                   "field", 
                                                   "Core(s) per socket:", 
                                                   "data");
    cpu_dict["thread_per_socket"] = search_list_dict(lscpu_list, 
                                                     "field", 
                                                     "Thread(s) per core:", 
                                                     "data");
    cpu_dict["threads"] = search_list_dict(lscpu_list, 
                                           "field", 
                                           "CPU(s):", 
                                           "data");
    return;

def print_cpuinfo(cpu_dict):
    print("[ CPU Information ]");
    space_print("CPU Name : %s" % cpu_dict["cpu_name"], TABSIZE*1);
    space_print("The number of CPUs : %s" % cpu_dict["cpu_socket"], TABSIZE*1);
    space_print("The number of threads per core : %s" % cpu_dict["thread_per_socket"], TABSIZE*1);
    space_print("Total threads : %s" % cpu_dict["threads"], TABSIZE*1);
    print("");
    return;

def get_meminfo(mem_dict):
    dmidecode_result_str = os.popen("/usr/sbin/dmidecode -t memory").read();
    dmi_parser = dmiparser.DmiParser(dmidecode_result_str, sort_keys=True, indent=2);
    dmi_parsed_list = json.loads(str(dmi_parser));

    total_mem_gib = psutil.virtual_memory().total / (1024 * 1024 * 1024);
    mem_dict["total"] = round(total_mem_gib);

    mem_dict["mems"] = [];
    for dmi_mem_dict in dmi_parsed_list:
        if dmi_mem_dict["name"] == "Memory Device":
            temp_dict = {};
            temp_dict["loc"] = dmi_mem_dict["props"]["Locator"]["values"][0];
            temp_dict["vendor"] = dmi_mem_dict["props"]["Manufacturer"]["values"][0];
            temp_dict["PN"] = dmi_mem_dict["props"]["Part Number"]["values"][0];
            temp_dict["size"] = dmi_mem_dict["props"]["Size"]["values"][0];
            mem_dict["mems"].append(temp_dict);
    return;

def print_meminfo(mem_dict):
    print("[ Memory Information ]");
    space_print("Total Memory Size : %4d GiB" % mem_dict["total"], TABSIZE*1);
    for mem in mem_dict["mems"]:
        space_print("%10s %10s %20s %10s"
                % (mem["loc"], mem["vendor"], mem["PN"], mem["size"]),
                TABSIZE*2);
    print("");
    return;

def get_nvsmiq():
    tree = ET.ElementTree(ET.fromstring(os.popen("nvidia-smi -x -q").read()));
    return tree;

def get_gpuinfo(gpu_dict):
    gpu_dict["gpus"] = [];

    # NVIDIA GPU
    root = get_nvsmiq().getroot();

    gpu_dict["numgpus"] = int(root.find("attached_gpus").text);
    gpu_dict["cuda_version"] = root.find("cuda_version").text; # FIXME
    gpu_dict["driver_version"] = root.find("driver_version").text;

    for gpu in root.findall("gpu"):
        gpuinfo = {};
        gpuinfo["tag"] = gpu.tag;
        gpuinfo["attrib"] = gpu.attrib;
        gpuinfo["name"] = gpu.find("product_name").text;
        gpuinfo["arch"] = gpu.find("product_architecture").text
        gpuinfo["serial"] = gpu.find("serial").text;
        gpuinfo["pci_bus_id"] = gpu.find("pci") \
                                   .find("pci_bus_id").text;
        gpuinfo["mem"] = gpu.find("fb_memory_usage") \
                            .find("total").text;
        gpuinfo["width"] = gpu.find("pci") \
                              .find("pci_gpu_link_info") \
                              .find("link_widths") \
                              .find("current_link_width").text;
        gpu_dict["gpus"].append(gpuinfo); 

    return;

def print_gpuinfo(gpu_dict):
    print("[ GPU Information ]");
    space_print("The number of GPUs : %s" % gpu_dict["numgpus"], TABSIZE*1);
    for idx, gpu in enumerate(gpu_dict["gpus"]):
        space_print("GPU #%2d: %10s %10s %10s %15s %5s" 
                % (idx, 
                   gpu["name"], 
                   gpu["pci_bus_id"].split(':',1)[1], 
                   gpu["mem"], 
                   gpu["serial"], 
                   gpu["width"]), TABSIZE*2);
    print("")
    return;

def get_strinfo(str_dict):
    lsblk_filter = "NAME,SIZE,TYPE,MODEL,SERIAL";

    blk_list = [];
    blk_list = json.load(os.popen("/usr/bin/lsblk -Jd -o " + lsblk_filter))["blockdevices"];
    blk_list = list(filter(lambda f: f["type"] == "disk", blk_list));

    str_dict["blk_devs"] = blk_list;

    return;

def print_strinfo(str_dict):
    print("[ Storage Information ]");
    space_print("The number of block devices : %s" % len(str_dict["blk_devs"]), TABSIZE*1);
    for idx, blk in enumerate(str_dict["blk_devs"]):
        space_print("BLK #%2d: %10s %30s %10s %20s"
                % (idx,
                   blk["name"],
                   blk["model"],
                   blk["size"],
                   blk["serial"]), TABSIZE*2);
    print("");
    return;

def main(): 
    if os.getuid() != 0:
        exit("You need root previlege to execute this script. Please try with sudo");

    hwinfo_dict = {};
    hwinfo_dict["CPU"] = {};
    hwinfo_dict["GPU"] = {};
    hwinfo_dict["MEM"] = {};
    hwinfo_dict["STR"] = {};

    print("ManyCoreSoft Hardware Component Check Tool");
    print("");

    get_cpuinfo(hwinfo_dict["CPU"]);
    print_cpuinfo(hwinfo_dict["CPU"]);

    get_meminfo(hwinfo_dict["MEM"]);
    print_meminfo(hwinfo_dict["MEM"]);

    get_gpuinfo(hwinfo_dict["GPU"]);
    print_gpuinfo(hwinfo_dict["GPU"]);

    get_strinfo(hwinfo_dict["STR"]);
    print_strinfo(hwinfo_dict["STR"]);

    return;

if __name__ == "__main__":
    main();
