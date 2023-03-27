#!/usr/bin/env python3

import os
import argparse

from enum import Enum
from json import dumps
from typing import List


class Arch(Enum):
    """
    CPU architecture supported by CI.
    """

    aarch64 = "aarch64"
    s390x = "s390x"
    x86_64 = "x86_64"


SELF_HOSTED_REPOS = [
    "kernel-patches/bpf",
    "kernel-patches/vmtest",
]

MATRIX = [
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

TESTS = [
    "test_progs",
    "test_progs_parallel",
    "test_progs_no_alu32",
    "test_progs_no_alu32_parallel",
    "test_maps",
    "test_verifier",
]


def set_output(name, value):
    """Write an output variable to the GitHub output file."""
    with open(os.getenv("GITHUB_OUTPUT"), "a") as f:
        f.write(f"{name}={value}\n")


def generate_toolchain_full(compiler, llvm_version):
    """
    When the compiler used is llvm, we need to specify which version to use
    and align it with the version used to compile bpf selftests.
    """
    if compiler == "llvm":
        return f"llvm-{llvm_version}"
    return compiler


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


def get_tests(config):
    """
    Filters out parallel tests when parallel tests are disabled.
    """
    if config.get("parallel_tests", True):
        return TESTS
    return [test for test in TESTS if not test.endswith("parallel")]


def generate_toochain_full(matrix) -> List:
    return [
        item
        | {
            "toolchain_full": generate_toolchain_full(
                item["toolchain"], item["llvm-version"]
            )
        }
        for item in matrix
    ]


def run_on_github_runners(matrix) -> List:
    return [
        item | {"runs_on": ["ubuntu-latest"]}
        for item in matrix
        if item["arch"] == Arch.x86_64.value
    ]


def run_on_self_hosted(matrix) -> List:
    result = []
    for item in matrix:
        item["runs_on"].extend(["self-hosted", item["arch"]])
        result.append(item)
    return result


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-o", "--owner", required=True, help="Github owner")
    parser.add_argument("-r", "--repository", required=True, help="Github repository")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    matrix = generate_toochain_full(MATRIX)
    # Only a few repository within "kernel-patches" use self-hosted runners.
    if args.owner != "kernel-patches" or args.repository not in SELF_HOSTED_REPOS:
        # Outside of those repositories, we only run on x86_64 GH hosted runners (ubuntu-latest)
        matrix = run_on_github_runners(matrix)

    else:
        # Otherwise, run on (self-hosted, arch) runners
        matrix = run_on_self_hosted(matrix)

    build_matrix = {"include": matrix}
    set_output("build_matrix", dumps(build_matrix))

    test_matrix = {
        "include": [
            {**config, **generate_test_config(test)}
            for config in matrix
            for test in get_tests(config)
        ]
    }
    set_output("test_matrix", dumps(test_matrix))
