import datetime
import csv
import os
from typing import List, Tuple

import pytest

from doltcli import Dolt

TEST_TABLE = 'characters'
TEST_DATA_INITIAL = [
    {'name': 'Anna', 'adjective': 'tragic', 'id': 1, 'date_of_death': datetime.datetime(1877, 1, 1)},
    {'name': 'Vronksy', 'adjective': 'honorable', 'id': 2, 'date_of_death': None},
    {'name': 'Oblonksy', 'adjective': 'buffoon', 'id': 3, 'date_of_death': None},
]

TEST_DATA_UPDATE = [
    {'name': 'Vronksy', 'adjective': 'honorable', 'id': 2, 'date_of_death': datetime.datetime(1879, 1, 1)},
    {'name': 'Levin', 'adjective': 'tiresome', 'id': 4, 'date_of_death': None},
]

TEST_DATA_FINAL = [TEST_DATA_INITIAL[0], TEST_DATA_INITIAL[2]] + TEST_DATA_UPDATE

def get_repo_path_tmp_path(path: str, subpath: str = None) -> Tuple[str, str]:
    if subpath:
        return os.path.join(path, subpath), os.path.join(path, subpath, '.dolt')
    else:
        return path, os.path.join(path, '.dolt')


def compare_rows_helper(expected: List[dict], actual: List[dict]):
    assert len(expected) == len(actual), f'Unequal row counts: {len(expected)} != {len(actual)}'
    errors = []
    for l, r in zip(expected, actual):
        l_cols, r_cols = set(l.keys()), set(r.keys())
        assert l_cols == r_cols, f'Unequal sets of columns: {l_cols} != {r_cols}'
        for col in l_cols:
            l_val, r_val = l[col], r[col]
            if col.startswith('date'):
                l_val, r_val = l_val[:10], r_val[:10]
            if l_val != r_val and not (l_val is None and r_val == ''):
                errors.append(f'{col}: {l_val} != {r_val}')

    error_str = '\n'.join(errors)
    assert not errors, f'Failed with the following unequal columns:\n{error_str}'

@pytest.fixture()
def with_test_data_initial_file(tmp_path):
    return _test_data_to_file(tmp_path, TEST_DATA_INITIAL)


@pytest.fixture()
def with_test_table(init_empty_test_repo):
    dolt = init_empty_test_repo
    dolt.sql(query=f'''
        CREATE TABLE `{TEST_TABLE}` (
            `name` VARCHAR(32),
            `adjective` VARCHAR(32),
            `id` INT NOT NULL,
            `date_of_death` DATETIME, 
            PRIMARY KEY (`id`)
        );
    ''')
    dolt.add(TEST_TABLE)
    dolt.commit('Created test table')
    return dolt


@pytest.fixture()
def with_test_data_initial_file(tmp_path):
    return _test_data_to_file(tmp_path, 'initial', TEST_DATA_INITIAL)


@pytest.fixture()
def with_test_data_final_file(tmp_path):
    return _test_data_to_file(tmp_path, 'final', TEST_DATA_FINAL)


def _test_data_to_file(file_path, file_name, test_data):
    path = os.path.join(file_path, file_name)
    with open(path, 'w') as fh:
        csv_writer = csv.DictWriter(fh, fieldnames=test_data[0].keys())
        csv_writer.writeheader()
        csv_writer.writerows(test_data)

    return path


@pytest.fixture
def init_empty_test_repo(tmpdir) -> Dolt:
    return _init_helper(tmpdir)


@pytest.fixture
def init_other_empty_test_repo(tmpdir) -> Dolt:
    return _init_helper(tmpdir, 'other')


def _init_helper(path: str, ext: str = None):
    repo_path, repo_data_dir = get_repo_path_tmp_path(path, ext)
    return Dolt.init(repo_path)
