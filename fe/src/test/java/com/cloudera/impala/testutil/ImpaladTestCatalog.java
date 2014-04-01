// Copyright 2012 Cloudera Inc.
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
// http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

package com.cloudera.impala.testutil;

import com.cloudera.impala.authorization.AuthorizationConfig;
import com.cloudera.impala.authorization.Privilege;
import com.cloudera.impala.authorization.User;
import com.cloudera.impala.catalog.AuthorizationException;
import com.cloudera.impala.catalog.CatalogServiceCatalog;
import com.cloudera.impala.catalog.DatabaseNotFoundException;
import com.cloudera.impala.catalog.Db;
import com.cloudera.impala.catalog.ImpaladCatalog;
import com.cloudera.impala.catalog.Table;
import com.cloudera.impala.catalog.TableLoadingException;
import com.google.common.base.Preconditions;

/**
 * Mock catalog used for running FE tests that allows lazy-loading of tables without a
 * running catalogd/statestored.
 */
public class ImpaladTestCatalog extends ImpaladCatalog {
  // Used to load missing table metadata when running the FE tests.
  private final CatalogServiceCatalog srcCatalog_;

  public ImpaladTestCatalog(AuthorizationConfig authzConfig) {
    super(authzConfig);
    CatalogServiceCatalog catalogServerCatalog =
        CatalogServiceCatalog.createForTesting(false);
    // Bootstrap the catalog by adding all dbs, tables, and functions.
    for (String dbName: catalogServerCatalog.getDbNames(null)) {
      // Adding DB should include all tables/fns in that database.
      addDb(catalogServerCatalog.getDb(dbName));
    }
    srcCatalog_ = catalogServerCatalog;
    setIsReady();
  }

  /**
   * Overrides ImpaladCatalog.getTable to load the table metadata if it is missing.
   */
  @Override
  public Table getTable(String dbName, String tableName, User user,
      Privilege privilege) throws AuthorizationException, DatabaseNotFoundException,
      TableLoadingException {
    Table existingTbl = super.getTable(dbName, tableName, user, privilege);
    // Table doesn't exist or is already loaded. Just return it.
    if (existingTbl == null || existingTbl.isLoaded()) return existingTbl;

    // The table was not yet loaded. Load it in to the catalog and try getTable()
    // again.
    Table newTbl = srcCatalog_.getOrLoadTable(dbName,  tableName);
    Preconditions.checkNotNull(newTbl);
    Preconditions.checkState(newTbl.isLoaded());
    Db db = getDb(dbName);
    Preconditions.checkNotNull(db);
    db.addTable(newTbl);
    return super.getTable(dbName, tableName, user, privilege);
  }
}