"""Batch guards protect cloud ownership and keep completed evidence reusable."""
import pytest

import run_image_e2e_batch as batch


def test_every_explicitly_selected_template_runs_again(monkeypatch, tmp_path):
    monkeypatch.setattr(batch, 'catalog_names', lambda root: ['a', 'b'])
    assert batch.selection(tmp_path, None) == ['a', 'b']
    assert batch.selection(tmp_path, 'b') == ['b']
    with pytest.raises(ValueError, match='unique'):
        batch.selection(tmp_path, 'a,a')


def test_uncertain_cleanup_stops_new_operations_and_cannot_complete():
    called = []
    saved = []

    def operation(name, artifact):
        called.append(name)
        return {'template': name, 'passed': False, 'unresolved_owned_cleanup': True}

    rows, stopped = batch.execute(['a', 'b', 'c'], {'a': 1, 'b': 2, 'c': 3}, operation,
                                  1, lambda rows, stopped: saved.append((len(rows), stopped)))
    assert called == ['a'] and stopped and len(rows) == 1
    assert saved == [(1, True)]


def test_worker_exception_keeps_details_private_and_stops_new_operations():
    def operation(name, artifact):
        raise RuntimeError('synthetic sensitive upstream details')

    rows, stopped = batch.execute(['a', 'b'], {'a': 1, 'b': 2}, operation,
                                  1, lambda *args: None)
    assert stopped and len(rows) == 1
    assert rows[0]['error_type'] == 'RuntimeError'
    assert 'synthetic sensitive' not in str(rows)


def test_failed_but_independently_cleaned_source_does_not_hide_other_templates():
    called = []

    def operation(name, artifact):
        called.append(name)
        return {'template': name, 'passed': name != 'a', 'unresolved_owned_cleanup': False}

    rows, stopped = batch.execute(['a', 'b', 'c'], {'a': 1, 'b': 2, 'c': 3}, operation,
                                  2, lambda *args: None)
    assert not stopped and set(called) == {'a', 'b', 'c'}
    assert sum(row['passed'] for row in rows) == 2


def test_export_requires_success_and_the_exact_unexpired_source_artifact(monkeypatch):
    def response(path):
        if '/artifacts?' in path:
            return {'artifacts': [{'name': 'image-a-' + 'b' * 40, 'id': 12, 'expired': False}]}
        return {'status': 'completed', 'conclusion': 'success', 'event': 'workflow_dispatch',
                'head_sha': 'a' * 40}

    monkeypatch.setattr(batch, 'github', response)
    with pytest.raises(ValueError, match='missing or ambiguous'):
        batch.exported_artifacts(99, ['a'])


def test_pending_or_failed_export_cannot_start_native_acceptance(monkeypatch):
    monkeypatch.setattr(batch, 'github', lambda path: {'status': 'completed', 'conclusion': 'failure'})
    with pytest.raises(ValueError, match='successful'):
        batch.exported_artifacts(99, ['a'])
