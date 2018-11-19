#!/bin/bash
set -e

if [ "$#" -ne 2 ]; then
    echo "Usage: setup_net_console.sh <remote ip> <remote port>"
    exit 1
fi

remote_ip=$1
remote_port=$2
echo "Remote IP address:" $remote_ip
echo "Remote port:" $remote_port

local_ip=$(ip route | grep default | awk '{print $9}')
echo "Local IP address:" $local_ip

remote_mac=$(arp -a | grep $(ip route show | grep default | awk '{print $3}') | awk '{print $4}')
echo "Remote mac address:" $remote_mac

echo "Setting kernel log level to 8"
dmesg -n 8

echo "Loading module: configfs"
modprobe configfs

echo "Loading module: netconsole"
modprobe netconsole

target_dir=/sys/kernel/config/netconsole/t0

if [ ! -d "$target_dir" ]; then
    echo "Making netconsole target directory:" $target_dir
    mkdir $target_dir
else
    echo "Target directory already exists:" $target_dir
fi

echo "Disabling netconsole target"
echo 0 > $target_dir/enabled || true

echo "Disabling netconsole target again to get a kernel log entry saying it's already stopped"
echo 0 > $target_dir/enabled || true

echo "Configuring local_ip:" $local_ip
echo $local_ip > $target_dir/local_ip

echo "Configuring remote_ip:" $remote_ip
echo $remote_ip > $target_dir/remote_ip

echo "Configuring remote_port:" $remote_port
echo $remote_port > $target_dir/remote_port

echo "Configuring remote_mac:" $remote_mac
echo $remote_mac > $target_dir/remote_mac

echo "Everything configured ok before enabling?"
tail $target_dir/*

echo "Enabling netconsole target"
echo 1 > $target_dir/enabled

echo "Everything configured ok after enabling?"
tail $target_dir/*

