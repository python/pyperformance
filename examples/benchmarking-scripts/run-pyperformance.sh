#!/bin/bash


# Wrapper around pyperformance for hosts with isolated CPUs. Reserves a CPU
# (175-191) via lockfiles, renders benchmark.conf with m4, bootstraps a venv,
# and runs pyperformance pinned to that CPU. Requires kernel isolcpus=175-191
# and the lockfile utility so concurrent runs do not collide, which is
# especially helpful when backfilling multiple revisions.


set -e
set -u
set -o pipefail

lock_file=
tmpdir=
cleanup()
{
  if [[ -n "${lock_file:-}" ]]; then
    echo "Removing $lock_file"
    rm -f "$lock_file"
  fi
  if [[ -n "${tmpdir:-}" ]]; then
    echo "Removing $tmpdir"
    rm -fr "$tmpdir"
  fi
  exit
}

trap cleanup EXIT

usage()
{
  cat <<EOF

usage: run-pyperformance.sh [OPTION]...

 -h, --help
    print some basic usage information and exit
 -x
    enable tracing in this shells script

Note: if you want to pass arguments to pyperformance append "--" followed by the arguments.
EOF
}

args=$(getopt -o+hx -l help -n $(basename "$0") -- "$@")
eval set -- "$args"
while [ $# -gt 0 ]; do
  if [ -n "${opt_prev:-}" ]; then
    eval "$opt_prev=\$1"
    opt_prev=
    shift 1
    continue
  elif [ -n "${opt_append:-}" ]; then
    if [ -n "$1" ]; then
      eval "$opt_append=\"\${$opt_append:-} \$1\""
    fi
    opt_append=
    shift 1
    continue
  fi
  case $1 in
  -h | --help)
    usage
    exit 0
    ;;

  -x)
    set -x
    ;;

  --)
    shift
    break 2
    ;;
  esac
  shift 1
done


# We have the latest 16 CPUs (ID 175-191) for running pyperformance and we want
# to make sure that pyperformance runs with affinity on one of these CPUs.
# In order to do that a locking mechanism is implemented in order to "reserve"
# a CPU being used.
# Locking files are in /var/lock/pyperformance-CPUID (where CPUID is 175, 176... 191)
# Linux is booted with
#
# GRUB_CMDLINE_LINUX="isolcpus=175-191 mitigations=off"
#
# in the /etc/default/grub file
lock_prefix_path="/var/lock/pyperformance-"

for i in $(seq 175 191); do
  lock_file="$lock_prefix_path$i"
  # lockfile is provided byt the `procmail` package
  if lockfile -r0 "$lock_file"; then
    # Let's save the CPUID to set the affinity later
    cpuid=$i
    break
  fi
done

if [ -z ${cpuid+x} ]; then
  echo "Cannot find an available CPU to run pyperformance on. Exiting...";
  # Disable the trap as we don't need to clean up anything
  trap - EXIT
  exit 1
fi

# Create a temporary directory
tmpdir=$(mktemp -d -t pyperformance.XXXXXXXXX)

echo "Pyperformance will be run on CPU $cpuid"
echo "Working directory is $tmpdir"

# Snapshot the benchmark.conf file
m4 \
  -DTMPDIR="$tmpdir" \
  -DCPUID="$cpuid" \
  benchmark.conf.in > "$tmpdir/benchmark.conf"

# This is our working directory from now on
cd "$tmpdir"

# Install pyperformance in a virtual env.
python3 -m venv venv
venv/bin/pip install pyperformance==1.13.0

# Clone cpython
git clone https://github.com/python/cpython.git

# Run pyperformance
venv/bin/pyperformance "$@"
