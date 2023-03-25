#!/usr/bin/env python3

import os
import argparse

from enum import Enum
from json import dumps


class Arch(Enum):
    """
    CPU architecture supported by CI.
    """

    aarch64 = "aarch64"
    s390x = "s390x"
    x86_64 = "x86_64"


def set_output(name, value):
    """Write an output variable to the GitHub output file."""
    with open(os.getenv("GITHUB_OUTPUT"), "a") as f:
        f.write(f"{name}={value}\n")


def generate_test_config(test):
    """Create the configuration for the provided test."""
    experimental = test.endswith("_parallel")
    config = {
        "test": test,
        "continue_on_error": experimental,
        # While in experimental mode, parallel jobs may get stuck
        # anywhere, including in user space where the kernel won't detect
        # a problem and panic. We add a second layer of (smaller) timeouts
        # here such that if we get stuck in a parallel run, we hit this
        # timeout and fail without affecting the overall job success (as
        # would be the case if we hit the job-wide timeout). For
        # non-experimental jobs, 360 is the default which will be
        # superseded by the overall workflow timeout (but we need to
        # specify something).
        "timeout_minutes": 30 if experimental else 360,
    }
    return config


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-o", "--owner", required=True, help="Github owner")
    parser.add_argument("-r", "--repository", required=True, help="Github repository")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    matrix = [
        {
            "kernel": "LATEST",
            "runs_on": [],
            "arch": Arch.x86_64.value,
            "toolchain": "gcc",
            "llvm-version": "16",
        },
        {
            "kernel": "LATEST",
            "runs_on": [],
            "arch": Arch.x86_64.value,
            "toolchain": "llvm",
            "llvm-version": "16",
        },
        {
            "kernel": "LATEST",
            "runs_on": [],
            "arch": Arch.aarch64.value,
            "toolchain": "gcc",
            "llvm-version": "16",
        },
        {
            "kernel": "LATEST",
            "runs_on": [],
            "arch": Arch.aarch64.value,
            "toolchain": "llvm",
            "llvm-version": "16",
        },
        {
            "kernel": "LATEST",
            "runs_on": [],
            "arch": Arch.s390x.value,
            "toolchain": "gcc",
            "llvm-version": "16",
            "parallel_tests": False,
        },
    ]
    self_hosted_repos = [
        "kernel-patches/bpf",
        "kernel-patches/vmtest",
    ]

    for idx in range(len(matrix) - 1, -1, -1):
        if matrix[idx]["toolchain"] == "gcc":
            matrix[idx]["toolchain_full"] = "gcc"
        else:
            matrix[idx]["toolchain_full"] = "llvm-" + matrix[idx]["llvm-version"]
    # Only a few repository within "kernel-patches" use self-hosted runners.
    if args.owner != "kernel-patches" or args.repository not in self_hosted_repos:
        # Outside of those repositories, we only run on x86_64 GH hosted runners (ubuntu-latest)
        for idx in range(len(matrix) - 1, -1, -1):
            if matrix[idx]["arch"] != Arch.x86_64.value:
                del matrix[idx]
            else:
                matrix[idx]["runs_on"] = ["ubuntu-latest"]
    else:
        # Otherwise, run on (self-hosted, arch) runners
        for idx in range(len(matrix) - 1, -1, -1):
            matrix[idx]["runs_on"].extend(["self-hosted", matrix[idx]["arch"]])

    build_matrix = {"include": matrix}
    set_output("build_matrix", dumps(build_matrix))

    def get_tests(config):
        tests = [
            "test_progs",
            "test_progs_parallel",
            "test_progs_no_alu32",
            "test_progs_no_alu32_parallel",
            "test_maps",
            "test_verifier",
        ]
        if config.get("parallel_tests", True):
            return tests
        return [test for test in tests if not test.endswith("parallel")]

    test_matrix = {
        "include": [
            {**config, **generate_test_config(test)}
            for config in matrix
            for test in get_tests(config)
        ]
    }
    set_output("test_matrix", dumps(test_matrix))
