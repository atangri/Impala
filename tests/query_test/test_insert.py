#!/usr/bin/env python
# Copyright (c) 2012 Cloudera, Inc. All rights reserved.
# Targeted Impala insert tests
#
import logging
import pytest
from tests.beeswax.impala_beeswax import ImpalaBeeswaxException
from tests.common.test_vector import *
from tests.common.impala_test_suite import *
from tests.common.test_dimensions import create_exec_option_dimension

# TODO: Add Gzip back.  IMPALA-424
PARQUET_CODECS = ['none', 'snappy']

class TestInsertQueries(ImpalaTestSuite):
  @classmethod
  def get_workload(self):
    return 'functional-query'

  @classmethod
  def add_test_dimensions(cls):
    super(TestInsertQueries, cls).add_test_dimensions()
    # Fix the exec_option vector to have a single value. This is needed should we decide
    # to run the insert tests in parallel (otherwise there will be two tests inserting
    # into the same table at the same time for the same file format).
    # TODO: When we do decide to run these tests in parallel we could create unique temp
    # tables for each test case to resolve the concurrency problems.
    cls.TestMatrix.add_dimension(create_exec_option_dimension(
        cluster_sizes=[0], disable_codegen_options=[False], batch_sizes=[0],
        sync_ddl=[0, 1]))

    cls.TestMatrix.add_dimension(TestDimension("compression_codec", *PARQUET_CODECS));

    # Insert is currently only supported for text and parquet
    # For parquet, we want to iterate through all the compression codecs
    # TODO: each column in parquet can have a different codec.  We could
    # test all the codecs in one table/file with some additional flags.
    cls.TestMatrix.add_constraint(lambda v:\
        v.get_value('table_format').file_format == 'parquet' or \
          (v.get_value('table_format').file_format == 'text' and \
           v.get_value('compression_codec') == 'none'))
    cls.TestMatrix.add_constraint(lambda v:\
        v.get_value('table_format').compression_codec == 'none')

  @classmethod
  def setup_class(cls):
    super(TestInsertQueries, cls).setup_class()

  @pytest.mark.execute_serially
  def test_insert(self, vector):
    vector.get_value('exec_option')['PARQUET_COMPRESSION_CODEC'] = \
        vector.get_value('compression_codec')
    self.run_test_case('QueryTest/insert', vector,
        multiple_impalad=vector.get_value('exec_option')['sync_ddl'] == 1)

  @pytest.mark.execute_serially
  def test_insert_overwrite(self, vector):
    self.run_test_case('QueryTest/insert_overwrite', vector,
        multiple_impalad=vector.get_value('exec_option')['sync_ddl'] == 1)

class TestUnsupportedInsertFormats(ImpalaTestSuite):
  @classmethod
  def get_workload(self):
    return 'functional-query'

  @classmethod
  def add_test_dimensions(cls):
    super(TestUnsupportedInsertFormats, cls).add_test_dimensions()
    # Only run on file formats we can't write to
    cls.TestMatrix.add_constraint(lambda v: \
        not (v.get_value('table_format').file_format == 'parquet' or
             v.get_value('table_format').file_format == 'hbase' or
             (v.get_value('table_format').file_format == 'text' and
              v.get_value('table_format').compression_codec == 'none')))

  def test_unsupported_formats(self, vector):
    try:
      self.execute_query_using_client(
        self.client, 'insert into table tinytable values("hi", "there")', vector)
      assert False, 'Query was expected to fail'
    except ImpalaBeeswaxException, e: pass

class TestInsertPartKey(ImpalaTestSuite):
  """Regression test for IMPALA-875"""
  @classmethod
  def get_workload(self):
    return 'functional-query'

  @classmethod
  def add_test_dimensions(cls):
    super(TestInsertPartKey, cls).add_test_dimensions()
    # Only run for a single table type
    cls.TestMatrix.add_dimension(create_exec_option_dimension(
        cluster_sizes=[0], disable_codegen_options=[False], batch_sizes=[0],
        sync_ddl=[1]))

    cls.TestMatrix.add_constraint(lambda v:
        (v.get_value('table_format').file_format == 'text'))
    cls.TestMatrix.add_constraint(lambda v:\
        v.get_value('table_format').compression_codec == 'none')

  @pytest.mark.execute_serially
  def test_insert_part_key(self, vector):
    """Test that partition column exprs are cast to the correct type. See IMPALA-875."""
    self.run_test_case('QueryTest/insert_part_key', vector,
        multiple_impalad=vector.get_value('exec_option')['sync_ddl'] == 1)
