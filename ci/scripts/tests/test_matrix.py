import unittest
from dataclasses import dataclass


from ..get_test_matrix import generate_toolchain_full


class TestMatrix(unittest.TestCase):
    def test_generate_toolchain_full(self):
        @dataclass
        class T:
            compiler: str
            llvm_version: str
            expects: str

        test_cases = [
            T(compiler="llvm", llvm_version="16", expects="llvm-16"),
            T(compiler="foobar", llvm_version="16", expects="foobar"),
        ]
        for case in test_cases:
            with self.subTest(msg=f"{case.compiler}/{case.llvm_version}"):
                self.assertEqual(
                    generate_toolchain_full(case.compiler, case.llvm_version),
                    case.expects,
                )


if __name__ == "__main__":
    unittest.main()
