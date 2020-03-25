import os
import sys
import unittest
import subprocess
import contextlib
import json
import shutil
import pandas as pd

from textwrap import dedent
from subprocess import PIPE
from glob import glob
from io import StringIO
from unittest import mock

from otter import Notebook

# read in argument parser
with open("bin/otter") as f:
    exec(f.read())

TEST_FILES_PATH = "test/test-check/"

class TestIntegration(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        create_image_cmd = ["make", "docker-test"]
        create_image = subprocess.run(create_image_cmd, stdout=PIPE, stderr=PIPE)
        # TestIntegration.assertEqual(len(create_image.stderr), 0, create_image.stderr.decode("utf-8"))

    def test_docker(self):
        """
        Check that we have the right container installed and that docker is running
        """
        # use docker image inspect to see that the image is installed and tagged as otter-grader
        inspect = subprocess.run(["docker", "image", "inspect", "otter-test"], stdout=PIPE, stderr=PIPE)

        # assert that it didn't fail, it will fail if it is not installed
        self.assertEqual(len(inspect.stderr), 0, inspect.stderr.decode("utf-8"))


    def test_script_checker(self):
        """
        Checks that the script checker works
        """
        # run for each individual test
        for file in glob(TEST_FILES_PATH + "tests/*.py"):
            check_command = ["check",
                TEST_FILES_PATH + "file0.py", 
                "-q", os.path.split(file)[1][:-3],
                "-t", os.path.split(file)[0]
            ]
            args = parser.parse_args(check_command)

            # capture stdout
            output = StringIO()
            with contextlib.redirect_stdout(output):

                # mock block_print and enable_print otherwise they interfere with capture of stdout
                with mock.patch("otter.check.block_print"):
                    with mock.patch("otter.check.enable_print"):
                        args.func(args)
                        if os.path.split(file)[1] != "q2.py":
                            self.assertEqual(
                                output.getvalue().strip().split("\n")[-1].strip(), 
                                "All tests passed!", 
                                "Did not pass test at {}".format(file)
                            )

        # run checker command
        check_command = check_command = ["check",
            TEST_FILES_PATH + "file0.py", 
            "-t", TEST_FILES_PATH + "tests"
        ]
        args = parser.parse_args(check_command)

        # capture stdout
        output = StringIO()
        with contextlib.redirect_stdout(output):

            # mock block_print and enable_print otherwise they interfere with capture of stdout
            with mock.patch("otter.check.block_print"):
                with mock.patch("otter.check.enable_print"):
                    args.func(args)
                    self.assertEqual(
                        output.getvalue().strip(), 
                        dedent("""\
                            [0.         0.02002002 0.04004004 0.06006006 0.08008008]
                            4 of 5 tests passed

                            Tests passed:
                             q1  q3  q4  q5 


                            Tests failed: 
                               test/test-check/tests/q2.py

                            Test result:
                            Trying:
                                1 == 1
                            Expecting:
                                False
                            **********************************************************************
                            Line 2, in test/test-check/tests/q2.py 0
                            Failed example:
                                1 == 1
                            Expected:
                                False
                            Got:
                                True"""), 
                        "Did not pass correct tests"
                    )


    def test_notebook_class(self):
        """
        Checks that the otter.Notebook class works correctly
        """
        grader = Notebook(TEST_FILES_PATH + "tests")

        def square(x):
            return x**2

        def negate(x):
            return not x

        global_env = {
            "square" : square,
            "negate" : negate
        }

        for q_path in glob(TEST_FILES_PATH + "tests/*.py"):
            q = os.path.split(q_path)[1][:-3]
            result = grader.check(q, global_env=global_env)
            if q != "q2":
                self.assertEqual(result.grade, 1, "Test {} failed".format(q))
            else:
                self.assertEqual(result.grade, 0, "Test {} passed".format(q))